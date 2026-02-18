import sqlite3
import os

DB_PATH = "support_tickets.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            region TEXT,
            plan TEXT,
            tenure_months INTEGER,
            employees INTEGER
        )
    """)
    
    # Create tickets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            customer_id TEXT,
            created_at DATETIME,
            category TEXT,
            channel TEXT,
            priority TEXT,
            first_response_time_hours REAL,
            resolution_time_hours REAL,
            is_open INTEGER,
            breached_sla INTEGER,
            summary TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
