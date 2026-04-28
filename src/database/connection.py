import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "club.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def _column_exists(conn, table_name, column_name):
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(column["name"] == column_name for column in columns)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            display_name TEXT,
            username TEXT,
            chat_id INTEGER,
            role TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            deadline TEXT NOT NULL,
            assigned_to TEXT,
            created_by TEXT,
            status TEXT DEFAULT 'pending',
            category TEXT DEFAULT 'general',
            production_role TEXT,
            chat_id INTEGER,
            reminded_24h INTEGER DEFAULT 0,
            reminded_1h INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            event_date TEXT NOT NULL,
            created_by TEXT,
            signup_sheet_id INTEGER,
            chat_id INTEGER,
            reminded_24h INTEGER DEFAULT 0,
            reminded_1h INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS training_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            location TEXT,
            focus TEXT,
            recurrence TEXT DEFAULT 'none',
            signup_sheet_id INTEGER,
            chat_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            training_id INTEGER,
            user_id INTEGER,
            checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            comp_date TEXT NOT NULL,
            venue TEXT,
            registration_deadline TEXT,
            dance_styles TEXT, -- JSON list
            created_by TEXT,
            signup_sheet_id INTEGER,
            chat_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS competition_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comp_id INTEGER,
            user_id INTEGER,
            dance_style TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member1_id TEXT,
            member2_id TEXT,
            context TEXT, -- comp_id or training_id
            chat_id INTEGER,
            paired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS production_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            deadline TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            chat_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS signup_sheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            message_id INTEGER,
            chat_id INTEGER,
            created_by INTEGER,
            title TEXT,
            details TEXT,
            options TEXT,
            is_closed INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS signup_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sheet_id INTEGER,
            user_id INTEGER,
            display_name TEXT,
            option_chosen TEXT,
            responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            sent_by TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            chat_id INTEGER
        );
    """)
    if not _column_exists(conn, "partners", "chat_id"):
        conn.execute("ALTER TABLE partners ADD COLUMN chat_id INTEGER")
    if not _column_exists(conn, "signup_sheets", "created_by"):
        conn.execute("ALTER TABLE signup_sheets ADD COLUMN created_by INTEGER")
    if not _column_exists(conn, "signup_sheets", "is_deleted"):
        conn.execute("ALTER TABLE signup_sheets ADD COLUMN is_deleted INTEGER DEFAULT 0")

    conn.execute("""
        DELETE FROM attendance
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM attendance
            GROUP BY training_id, user_id
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_training_user
        ON attendance(training_id, user_id)
    """)
    conn.commit()
    conn.close()
