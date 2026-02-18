import csv
import json
import sqlite3
from datetime import datetime
from database import get_db_connection, init_db

# Load SLA Policy for reference (if needed during ingestion or diagnostics)
with open("data/sla_policy.json", "r") as f:
    SLA_POLICY = json.load(f)

VALID_PRIORITIES = set(SLA_POLICY["sla_hours_by_priority"].keys())

def validate_date(date_str):
    try:
        return datetime.fromisoformat(date_str) if date_str else None
    except ValueError:
        return None

def validate_float(value):
    try:
        return float(value) if value is not None and value != "" else None
    except ValueError:
        return None

def ingest_data():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing data for a fresh ingestion
    cursor.execute("DELETE FROM tickets")
    cursor.execute("DELETE FROM customers")
    conn.commit()
    
    diagnostics = {
        "customers_ingested": 0,
        "tickets_ingested": 0,
        "dirty_rows": 0,
        "issues": []
    }
    
    # Ingest Customers
    with open("data/customers.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO customers (customer_id, region, plan, tenure_months, employees)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["customer_id"],
                row["region"],
                row["plan"],
                int(row["tenure_months"]),
                int(row["employees"])
            ))
            diagnostics["customers_ingested"] += 1
            
    # Ingest Tickets
    with open("data/tickets.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            is_dirty = False
            
            # Validation
            created_at = validate_date(row["created_at"])
            if not created_at:
                is_dirty = True
                diagnostics["issues"].append(f"Ticket {row['ticket_id']}: Invalid/Missing created_at")
            
            priority = row["priority"]
            if priority not in VALID_PRIORITIES:
                is_dirty = True
                diagnostics["issues"].append(f"Ticket {row['ticket_id']}: Invalid priority '{priority}'")
                # Fallback or correction logic if needed
                if priority == "med": priority = "medium"
            
            first_response = validate_float(row["first_response_time_hours"])
            if first_response is None:
                is_dirty = True
                diagnostics["issues"].append(f"Ticket {row['ticket_id']}: Missing first_response_time_hours")

            if is_dirty:
                diagnostics["dirty_rows"] += 1

            cursor.execute("""
                INSERT OR REPLACE INTO tickets (
                    ticket_id, customer_id, created_at, category, channel, 
                    priority, first_response_time_hours, resolution_time_hours, 
                    is_open, breached_sla, summary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["ticket_id"],
                row["customer_id"],
                created_at.isoformat() if created_at else None,
                row["category"],
                row["channel"],
                priority,
                first_response,
                validate_float(row["resolution_time_hours"]),
                int(row["is_open"]),
                int(row["breached_sla"]),
                row["summary"]
            ))
            diagnostics["tickets_ingested"] += 1
            
    conn.commit()
    conn.close()
    return diagnostics

if __name__ == "__main__":
    results = ingest_data()
    print(f"Ingestion complete.")
    print(f"Customers: {results['customers_ingested']}")
    print(f"Tickets: {results['tickets_ingested']}")
    print(f"Dirty Rows: {results['dirty_rows']}")
