import sqlite3
import datetime

def init_database():
    """Fungsi untuk membuat semua tabel database"""
    
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    
    # ===== TABEL 1: PROJECTS (DIPERBARUI) =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            site_id TEXT UNIQUE NOT NULL,
            site_name TEXT NOT NULL,
            site_coordinate TEXT,
            vendor TEXT,
            site TEXT,
            start_date TEXT,
            end_date TEXT,
            start_date_actual TEXT,
            end_date_actual TEXT,
            status TEXT DEFAULT 'ON_TRACK',
            progress REAL DEFAULT 0.0,
            pm TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ===== TABEL 2: MILESTONES =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS milestones (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            site_name TEXT NOT NULL,
            planned_start TEXT,
            planned_end TEXT,
            actual_start TEXT,
            actual_end TEXT,
            dependency_id TEXT,
            weight REAL DEFAULT 0.0,
            status TEXT DEFAULT 'PENDING',
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')
    
    # ===== TABEL 3: MATERIALS =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            site_name TEXT NOT NULL,
            unit TEXT,
            min_stock REAL,
            current_stock REAL DEFAULT 0.0,
            unit_price REAL DEFAULT 0.0
        )
    ''')
    
    # ===== TABEL 4: INVENTORY TRANSACTIONS =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            id TEXT PRIMARY KEY,
            material_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            project_id TEXT,
            transaction_date TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (material_id) REFERENCES materials(id)
        )
    ''')
    
    # ===== TABEL 5: PROJECT MATERIAL REQUIREMENTS =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_material_requirements (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            material_id TEXT NOT NULL,
            required_quantity REAL DEFAULT 0.0,
            allocated_quantity REAL DEFAULT 0.0,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (material_id) REFERENCES materials(id)
        )
    ''')
    
    # ===== TABEL 6: USERS =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            usersite_name TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'VIEWER',
            full_site_name TEXT
        )
    ''')
    
    # ===== TABEL 7: AI INSIGHTS =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_insights (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            insight_type TEXT,
            risk_score INTEGER,
            description TEXT,
            recommendation TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    ''')
    
        # ===== TABEL 8: CHAT MESSAGES =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            site_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES projects(id)
        )
    ''')
    
    # ===== TABEL 9: NOTIFICATIONS =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            site_id TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES projects(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Database berhasil dibuat!")

if __name__ == "__main__":
    init_database()