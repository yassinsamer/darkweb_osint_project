#!/usr/bin/env python3
"""Initialize findings database with proper schema"""
import sqlite3
import os

def setup_database(db_path="findings.db"):
    """Create or update database schema"""
    
    # Backup and remove old database
    if os.path.exists(db_path):
        backup_path = db_path + ".backup"
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(db_path, backup_path)
        print(f"✓ Backed up old database to {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop old tables if they exist
    cursor.execute("DROP TABLE IF EXISTS extracted_data;")
    cursor.execute("DROP TABLE IF EXISTS findings_old;")
    cursor.execute("DROP TABLE IF EXISTS findings;")
    conn.commit()
    
    # Create fresh tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            keyword TEXT,
            snippet TEXT,
            confidence REAL,
            risk_score REAL,
            classification TEXT,
            found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extracted_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            finding_id INTEGER,
            data_type TEXT,
            data_value TEXT,
            FOREIGN KEY(finding_id) REFERENCES findings(id)
        )
    """)
    
    # Insert sample data
    sample_findings = [
        ("http://example-dark.onion/profile", "admin_credentials", "Found admin panel with credentials exposed", 95, 92, "credential_leak"),
        ("http://marketplace-dark.onion/shop", "credit_card_data", "Credit card data in public database", 98, 95, "financial_data"),
        ("http://forum-dark.onion/users", "user_database", "Exposed user database with personal info", 92, 88, "data_breach"),
        ("http://leak-dark.onion/corporate", "company_data", "Corporate files leaked on dark web", 90, 85, "data_breach"),
        ("http://stolen-dark.onion/accounts", "email_passwords", "Email and password combinations for sale", 88, 82, "credential_leak"),
        ("http://breach-dark.onion/customers", "customer_list", "Customer list with phone numbers", 85, 78, "personal_info"),
        ("http://data-dark.onion/financial", "bank_info", "Banking information exposed", 82, 80, "financial_data"),
        ("http://threat-dark.onion/report", "ransomware", "Ransomware threat targeting sector", 80, 75, "malware"),
        ("http://paste-dark.onion/leak", "api_keys", "API keys and secrets exposed", 78, 72, "credential_leak"),
        ("http://vendor-dark.onion/supply", "supply_chain", "Supply chain partner credentials", 75, 70, "credential_leak"),
    ]
    
    for url, keyword, snippet, confidence, risk_score, classification in sample_findings:
        cursor.execute("""
            INSERT INTO findings (url, keyword, snippet, confidence, risk_score, classification)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (url, keyword, snippet, confidence, risk_score, classification))
    
    # Insert extracted data
    extracted_data_samples = [
        (1, "email", "admin@company.com"),
        (1, "password_hash", "$2b$12$encrypted..."),
        (2, "card_number", "****-****-****-1234"),
        (2, "cvv_range", "Likely 700-900"),
        (3, "records_count", "50,000+"),
        (3, "fields", "Name, Email, Phone, Address"),
        (4, "file_count", "12,450"),
        (5, "credentials", "500+ email/password combinations"),
        (6, "phone_count", "35,000"),
        (7, "bank_data", "Account numbers and routing info"),
    ]
    
    for finding_id, data_type, data_value in extracted_data_samples:
        cursor.execute("""
            INSERT INTO extracted_data (finding_id, data_type, data_value)
            VALUES (?, ?, ?)
        """, (finding_id, data_type, data_value))
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {db_path}")

if __name__ == "__main__":
    setup_database()
