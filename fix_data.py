#!/usr/bin/env python3
"""
DATA FIXING UTILITY
Clean and validate monitoring data
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def fix_json_data():
    """Fix JSON data file"""
    data_file = Path("data/tracking_data.json")
    
    if not data_file.exists():
        print("No JSON data file found")
        return
    
    with open(data_file, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("JSON file is corrupted. Creating backup and resetting.")
            data_file.rename(data_file.with_suffix('.json.bak'))
            data = {"checks": [], "statistics": {"uptime": 100, "total_checks": 0}}
    
    # Remove duplicates based on timestamp
    if "checks" in data:
        seen_timestamps = set()
        unique_checks = []
        
        for check in data["checks"]:
            if isinstance(check, dict) and "timestamp" in check:
                if check["timestamp"] not in seen_timestamps:
                    seen_timestamps.add(check["timestamp"])
                    unique_checks.append(check)
        
        data["checks"] = unique_checks
    
    # Update statistics
    if data["checks"]:
        successful = sum(1 for c in data["checks"] if c.get("success"))
        total = len(data["checks"])
        data["statistics"]["uptime"] = round((successful / total * 100), 2)
        data["statistics"]["total_checks"] = total
    
    # Save fixed data
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Fixed JSON data: {len(data['checks'])} checks")

def fix_database():
    """Fix SQLite database issues"""
    db_file = Path("data/tracking.db")
    
    if not db_file.exists():
        print("No database file found")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("Database is empty. Creating tables...")
            cursor.execute('''
                CREATE TABLE website_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    url TEXT,
                    status_code INTEGER,
                    response_time REAL,
                    success BOOLEAN,
                    error_message TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE uptime_stats (
                    date DATE PRIMARY KEY,
                    checks_total INTEGER,
                    checks_successful INTEGER,
                    avg_response_time REAL
                )
            ''')
        
        # Clean old data (older than 30 days)
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute("DELETE FROM website_checks WHERE timestamp < ?", (cutoff,))
        
        conn.commit()
        conn.close()
        
        print("Database cleaned and verified")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # Create backup and new database
        backup_file = db_file.with_suffix('.db.bak')
        db_file.rename(backup_file)
        print(f"Created backup: {backup_file}")
        print("New database will be created on next run")

def main():
    """Main fixing function"""
    print("Starting data fix process...")
    
    # Fix JSON data
    fix_json_data()
    
    # Fix database
    fix_database()
    
    print("Data fix completed!")

if __name__ == "__main__":
    main()
