from src.database.connection import get_conn
from src.utils.security import sanitize_text

def create_signup_sheet(entity_type, entity_id, chat_id, title, details, options_json, created_by=None):
    conn = get_conn()
    c = conn.execute("""
        INSERT INTO signup_sheets (entity_type, entity_id, chat_id, created_by, title, details, options)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (entity_type, entity_id, chat_id, created_by, title, details, options_json))
    conn.commit(); sheet_id = c.lastrowid; conn.close()
    return sheet_id

def update_signup_message(sheet_id, message_id):
    conn = get_conn()
    conn.execute("UPDATE signup_sheets SET message_id=? WHERE id=?", (message_id, sheet_id))
    conn.commit(); conn.close()

def get_signup_sheet(sheet_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM signup_sheets WHERE id=? AND is_deleted=0", (sheet_id,)).fetchone()
    conn.close(); return row

def get_signup_sheets_by_creator(created_by, entity_type=None, limit=30):
    conn = get_conn()
    if entity_type:
        rows = conn.execute("""
            SELECT * FROM signup_sheets
            WHERE created_by=? AND entity_type=? AND is_deleted=0
            ORDER BY created_at DESC
            LIMIT ?
        """, (created_by, entity_type, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM signup_sheets
            WHERE created_by=? AND is_deleted=0
            ORDER BY created_at DESC
            LIMIT ?
        """, (created_by, limit)).fetchall()
    conn.close(); return rows

def toggle_signup(sheet_id, user_id, display_name, option):
    conn = get_conn()
    display_name = sanitize_text(display_name, max_length=64)
    option = sanitize_text(option, max_length=100)

    existing = conn.execute("""
        SELECT id FROM signup_responses 
        WHERE sheet_id=? AND user_id=? AND option_chosen=?
    """, (sheet_id, user_id, option)).fetchone()

    if existing:
        conn.execute("DELETE FROM signup_responses WHERE id=?", (existing["id"],))
    else:
        sheet = conn.execute("SELECT entity_type FROM signup_sheets WHERE id=?", (sheet_id,)).fetchone()
        if not sheet:
            conn.close()
            return

        if sheet["entity_type"] in ["training", "event"]:
            conn.execute("DELETE FROM signup_responses WHERE sheet_id=? AND user_id=?", (sheet_id, user_id))
        elif sheet["entity_type"] == "comp":
            if option.lower() == "not competing":
                conn.execute("DELETE FROM signup_responses WHERE sheet_id=? AND user_id=?", (sheet_id, user_id))
            else:
                conn.execute("""
                    DELETE FROM signup_responses
                    WHERE sheet_id=? AND user_id=? AND lower(option_chosen)='not competing'
                """, (sheet_id, user_id))
        
        conn.execute("""
            INSERT INTO signup_responses (sheet_id, user_id, display_name, option_chosen)
            VALUES (?, ?, ?, ?)
        """, (sheet_id, user_id, display_name, option))
    
    conn.commit(); conn.close()

def get_signup_responses(sheet_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM signup_responses WHERE sheet_id=?", (sheet_id,)).fetchall()
    conn.close(); return rows

def close_signup_sheet(sheet_id):
    conn = get_conn()
    conn.execute("UPDATE signup_sheets SET is_closed=1 WHERE id=?", (sheet_id,))
    conn.commit(); conn.close()

def reopen_signup_sheet(sheet_id):
    conn = get_conn()
    conn.execute("UPDATE signup_sheets SET is_closed=0 WHERE id=?", (sheet_id,))
    conn.commit(); conn.close()

def delete_signup_sheet(sheet_id):
    conn = get_conn()
    conn.execute("UPDATE signup_sheets SET is_deleted=1, is_closed=1 WHERE id=?", (sheet_id,))
    conn.commit(); conn.close()
