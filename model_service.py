import pandas as pd
import joblib
import os
import json
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from database import get_db_connection

MODEL_PATH = "model.joblib"
ENCODERS_PATH = "encoders.joblib"

FEATURES = ["category", "channel", "priority", "region", "plan", "tenure_months", "employees"]

def prepare_data():
    conn = get_db_connection()
    # Join with customers to get features available at ticket creation
    query = """
        SELECT t.category, t.channel, t.priority, c.region, c.plan, c.tenure_months, c.employees, t.breached_sla
        FROM tickets t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE t.created_at IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Simple feature engineering: Label Encoding for categorical features
    categorical_cols = ["category", "channel", "priority", "region", "plan"]
    encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
        
    X = df[FEATURES]
    y = df["breached_sla"]
    
    return X, y, encoders

def train_model():
    X, y, encoders = prepare_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss')
    clf.fit(X_train, y_train)
    
    # Save model and encoders
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(encoders, ENCODERS_PATH)
    
    # Metrics
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    
    metrics = {
        "auc": roc_auc_score(y_test, y_prob),
        "f1": f1_score(y_test, y_pred),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist()
    }
    
    with open("metrics.json", "w") as f:
        json.dump(metrics, f)
    
    return metrics

def predict_sla(ticket_data):
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODERS_PATH):
        return None
    
    clf = joblib.load(MODEL_PATH)
    encoders = joblib.load(ENCODERS_PATH)
    
    # Create DataFrame and enforce order
    input_df = pd.DataFrame([ticket_data])
    
    # Ensure all required columns are present (handle missing with defaults if necessary)
    for feat in FEATURES:
        if feat not in input_df.columns:
            # Fallback for missing features if any
            if feat == "tenure_months" or feat == "employees":
                input_df[feat] = 0
            else:
                input_df[feat] = "unknown"
                
    input_df = input_df[FEATURES]
    
    # Encode
    for col, le in encoders.items():
        if col in input_df.columns:
            # Handle unseen labels by mapping to first seen label or logic (simplified for demo)
            # le.classes_ contains the labels seen during fit
            labels = set(le.classes_)
            input_df[col] = input_df[col].apply(lambda x: x if str(x) in labels else le.classes_[0])
            input_df[col] = le.transform(input_df[col].astype(str))
            
    prob = clf.predict_proba(input_df)[0][1]
    label = int(clf.predict(input_df)[0])
    
    return {"probability": float(prob), "label": label}
