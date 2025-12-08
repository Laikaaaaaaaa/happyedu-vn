#!/usr/bin/env python3
"""Reset and initialize database"""

import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'student_protect.db')

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("Creating tables...")
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        name TEXT,
        verified BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # OTP table
    c.execute('''CREATE TABLE IF NOT EXISTS otp_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        code TEXT NOT NULL,
        type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    )''')
    
    # Mail logs
    c.execute('''CREATE TABLE IF NOT EXISTS mail_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id TEXT NOT NULL,
        recipient_email TEXT NOT NULL,
        subject TEXT,
        body TEXT,
        mail_type TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # SOS alerts
    c.execute('''CREATE TABLE IF NOT EXISTS sos_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        user_role TEXT NOT NULL,
        alert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # SOS Reports
    c.execute('''CREATE TABLE IF NOT EXISTS sos_reports (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        student_name TEXT,
        student_email TEXT,
        student_phone TEXT,
        student_class TEXT,
        location TEXT,
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved BOOLEAN DEFAULT 0,
        resolved_at TIMESTAMP,
        dismissed_by_admin BOOLEAN DEFAULT 0,
        dismissed_at TIMESTAMP
    )''')
    
    # Quiz Submissions table
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_submissions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        user_name TEXT NOT NULL,
        user_email TEXT NOT NULL,
        user_role TEXT NOT NULL,
        quiz_role TEXT NOT NULL,
        total_questions INTEGER,
        max_score FLOAT,
        total_score FLOAT,
        answers TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    
    print("✅ Database initialized successfully")
    print(f"Database location: {DB_PATH}")
    
    # Show table info
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print(f"\n📊 Tables created: {len(tables)}")
    for table in tables:
        print(f"   - {table[0]}")
    
    conn.close()

if __name__ == '__main__':
    print("🔄 Resetting database...\n")
    init_db()
    print("\n✨ Done!")
