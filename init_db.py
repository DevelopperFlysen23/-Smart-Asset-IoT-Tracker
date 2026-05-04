import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # User Management with department info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            rfid_uid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            authorized_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Industrial Assets with telemetry data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            serial_number TEXT UNIQUE,
            status TEXT DEFAULT 'Ready',
            health_score INTEGER DEFAULT 100,
            last_user TEXT,
            FOREIGN KEY (last_user) REFERENCES users(rfid_uid)
        )
    ''')

    # Extended Event Logging for Analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            severity TEXT DEFAULT 'INFO',
            message TEXT NOT NULL,
            device_id TEXT DEFAULT 'ESP32_ST_01'
        )
    ''')

    # Professional Seed Data
    users = [
        ('A1B2C3D4', 'Dr. James Wilson', 'Senior Engineer', 'IT Department'),
        ('E5F6G7H8', 'Sarah Chen', 'Lab Technician', 'Electronics')
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (rfid_uid, name, role, department) VALUES (?,?,?,?)", users)

    assets = [
        ('High-Precision Oscilloscope', 'Measurement', 'OSC-7822-X'),
        ('Industrial 3D Printer', 'Prototyping', 'PRNT-K3-09'),
        ('Workstation Node 01', 'Computing', 'WS-DELL-P89')
    ]
    cursor.executemany("INSERT OR IGNORE INTO assets (name, category, serial_number) VALUES (?,?,?)", assets)

    conn.commit()
    conn.close()
    print("Industrial Database Schema Deployed.")

if __name__ == '__main__':
    init_db()
