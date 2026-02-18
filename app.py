from flask import Flask, request, jsonify, render_template
from database import get_db_connection
from ingestion import ingest_data
import statistics
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reingest", methods=["POST"])
def reingest():
    import subprocess
    try:
        # 1. Generate new data
        subprocess.run(["python3", "generate_data.py"], check=True)
        # 2. Run ingestion
        from ingestion import ingest_data
        diagnostics = ingest_data()
        return jsonify({"status": "Data regenerated and ingested", "diagnostics": diagnostics})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/diagnostics", methods=["GET"])
def get_diagnostics():
    # To get full quality issues, we'll run a quick validation check
    # Instead of re-ingesting, we just scan for the 'dirty' signatures
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tickets")
    ticket_count = cursor.fetchone()[0]
    
    # Identify issues
    cursor.execute("""
        SELECT ticket_id, priority, created_at, first_response_time_hours 
        FROM tickets 
        WHERE created_at IS NULL 
           OR priority NOT IN ('low', 'medium', 'high', 'urgent') 
           OR first_response_time_hours IS NULL
    """)
    rows = cursor.fetchall()
    
    issues = []
    for row in rows:
        if row["created_at"] is None:
            issues.append(f"Ticket {row['ticket_id']}: Missing/Invalid created_at")
        if row["priority"] not in ['low', 'medium', 'high', 'urgent']:
            issues.append(f"Ticket {row['ticket_id']}: Invalid priority '{row['priority']}'")
        if row["first_response_time_hours"] is None:
            issues.append(f"Ticket {row['ticket_id']}: Missing response time")

    conn.close()
    
    return jsonify({
        "customer_count": customer_count,
        "ticket_count": ticket_count,
        "dirty_count": len(rows),
        "issues": issues[:50], # Return first 50 issues
        "status": "success"
    })

@app.route("/stats/overview", methods=["GET"])
def get_stats_overview():
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    category = request.args.get("category")
    priority = request.args.get("priority")
    
    query = "SELECT t.*, c.plan, c.region FROM tickets t JOIN customers c ON t.customer_id = c.customer_id WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND t.created_at >= ?"
        params.append(start_date)
    if end_date:
        query += " AND t.created_at <= ?"
        params.append(end_date)
    if category:
        query += " AND t.category = ?"
        params.append(category)
    if priority:
        query += " AND t.priority = ?"
        params.append(priority)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return jsonify({"message": "No data found for the given filters"}), 404
    
    # Process results
    daily_volume = {}
    breach_count = 0
    categories = {}
    resolution_times = []
    customer_breach_rates = {} # {customer_id: [breached, total]}

    for row in rows:
        # Daily volume
        if row["created_at"]:
            date = row["created_at"][:10]
            daily_volume[date] = daily_volume.get(date, 0) + 1
        
        # Category volume
        cat = row["category"]
        categories[cat] = categories.get(cat, 0) + 1
        
        # SLA Breach
        if row["breached_sla"]:
            breach_count += 1
            
        # Resolution Time
        if row["resolution_time_hours"] is not None:
            resolution_times.append(row["resolution_time_hours"])
            
        # Problem Customers
        cid = row["customer_id"]
        if cid not in customer_breach_rates:
            customer_breach_rates[cid] = [0, 0]
        customer_breach_rates[cid][1] += 1
        if row["breached_sla"]:
            customer_breach_rates[cid][0] += 1
            
    # Calculate stats
    sla_breach_rate = (breach_count / len(rows)) * 100 if rows else 0
    median_res = statistics.median(resolution_times) if resolution_times else 0
    p95_res = statistics.quantiles(resolution_times, n=20)[18] if len(resolution_times) >= 2 else (resolution_times[0] if resolution_times else 0)
    
    # Top categories
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Problem customers (highest breach rate, min 5 tickets)
    problem_customers = []
    for cid, counts in customer_breach_rates.items():
        if counts[1] >= 5:
            rate = (counts[0] / counts[1]) * 100
            problem_customers.append({"customer_id": cid, "breach_rate": rate, "total_tickets": counts[1]})
    
    problem_customers = sorted(problem_customers, key=lambda x: x["breach_rate"], reverse=True)[:5]
    
    return jsonify({
        "daily_volume": daily_volume,
        "top_categories": top_categories,
        "sla_breach_rate": sla_breach_rate,
        "median_resolution_time": median_res,
        "p95_resolution_time": p95_res,
        "problem_customers": problem_customers
    })

@app.route("/train", methods=["POST"])
def train():
    from model_service import train_model
    metrics = train_model()
    return jsonify({"status": "Model trained", "metrics": metrics})

@app.route("/model/metrics", methods=["GET"])
def get_metrics():
    # In a real app, we'd store metrics in a DB or file. For now, let's just return placeholders or re-train (not ideal)
    # Let's assume the user calls /train first. We'll return a message if model doesn't exist.
    import os
    if not os.path.exists("model.joblib"):
        return jsonify({"error": "Model not trained yet"}), 404
    # Re-running training to get metrics for this demo/test
    from model_service import train_model
    metrics = train_model()
    return jsonify(metrics)

@app.route("/predict", methods=["POST"])
def predict():
    from model_service import predict_sla
    data = request.json
    prediction = predict_sla(data)
    if prediction is None:
        return jsonify({"error": "Model not available"}), 400
    return jsonify(prediction)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
