import os
from src.database.connection import get_conn

def upsert_user(telegram_id, display_name, username, chat_id, role="member"):
    conn = get_conn()
    conn.execute("""
        INSERT INTO users (telegram_id, display_name, username, chat_id, role)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET 
            display_name=excluded.display_name, 
            username=excluded.username, 
            chat_id=excluded.chat_id
    """, (telegram_id, display_name, username, chat_id, role))
    conn.commit(); conn.close()

def get_user(telegram_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    conn.close(); return row

def is_admin(telegram_id):
    # 1. Check Super Admins from environment
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        admin_ids = [int(i.strip()) for i in admin_ids_str.split(",") if i.strip().isdigit()]
        if telegram_id in admin_ids:
            return True

    # 2. Check Database roles
    u = get_user(telegram_id)
    return u and u["role"] == "admin"

def set_admin(telegram_id):
    conn = get_conn()
    conn.execute("UPDATE users SET role='admin' WHERE telegram_id=?", (telegram_id,))
    conn.commit(); conn.close()
