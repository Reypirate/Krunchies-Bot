from src.database.connection import get_conn
from src.utils.time import now_local_str

# ── Events ─────────────────────────────────────────────
def add_event(title, description, event_date, created_by, chat_id):
    conn = get_conn()
    c = conn.execute("""
        INSERT INTO events (title, description, event_date, created_by, chat_id)
        VALUES (?, ?, ?, ?, ?)
    """, (title, description, event_date, created_by, chat_id))
    conn.commit(); event_id = c.lastrowid; conn.close()
    return event_id

def get_events(chat_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM events WHERE chat_id=? AND event_date >= ? ORDER BY event_date
    """, (chat_id, now_local_str())).fetchall()
    conn.close(); return rows

def delete_event(event_id, chat_id):
    conn = get_conn()
    event = conn.execute("SELECT signup_sheet_id FROM events WHERE id=? AND chat_id=?", (event_id, chat_id)).fetchone()
    if event and event["signup_sheet_id"]:
        conn.execute("UPDATE signup_sheets SET is_closed=1 WHERE id=?", (event["signup_sheet_id"],))
    conn.execute("DELETE FROM events WHERE id=? AND chat_id=?", (event_id, chat_id))
    conn.commit(); conn.close()

def update_event_signup(event_id, sheet_id):
    conn = get_conn()
    conn.execute("UPDATE events SET signup_sheet_id=? WHERE id=?", (sheet_id, event_id))
    conn.commit(); conn.close()

def get_pending_reminder_events():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM events WHERE event_date >= ?",
                        (now_local_str(),)).fetchall()
    conn.close(); return rows

def mark_event_reminded(event_id, level):
    conn = get_conn()
    if level == "24h":
        conn.execute("UPDATE events SET reminded_24h=1 WHERE id=?", (event_id,))
    else:
        conn.execute("UPDATE events SET reminded_1h=1 WHERE id=?", (event_id,))
    conn.commit(); conn.close()

# ── Training ───────────────────────────────────────────
def add_training(date, location, focus, recurrence, chat_id):
    conn = get_conn()
    c = conn.execute("""
        INSERT INTO training_sessions (date, location, focus, recurrence, chat_id)
        VALUES (?, ?, ?, ?, ?)
    """, (date, location, focus, recurrence, chat_id))
    conn.commit(); tid = c.lastrowid; conn.close()
    return tid

def update_training_signup(training_id, sheet_id):
    conn = get_conn()
    conn.execute("UPDATE training_sessions SET signup_sheet_id=? WHERE id=?", (sheet_id, training_id))
    conn.commit(); conn.close()

def get_trainings(chat_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM training_sessions WHERE chat_id=? ORDER BY date", (chat_id,)).fetchall()
    conn.close(); return rows

def log_attendance(training_id, user_id):
    conn = get_conn()
    c = conn.execute("INSERT OR IGNORE INTO attendance (training_id, user_id) VALUES (?, ?)", (training_id, user_id))
    conn.commit(); inserted = c.rowcount > 0; conn.close()
    return inserted

# ── Competitions ───────────────────────────────────────
def add_competition(name, date, venue, deadline, styles_json, created_by, chat_id):
    conn = get_conn()
    c = conn.execute("""
        INSERT INTO competitions (name, comp_date, venue, registration_deadline, dance_styles, created_by, chat_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, date, venue, deadline, styles_json, created_by, chat_id))
    conn.commit(); cid = c.lastrowid; conn.close()
    return cid

def update_comp_signup(comp_id, sheet_id):
    conn = get_conn()
    conn.execute("UPDATE competitions SET signup_sheet_id=? WHERE id=?", (sheet_id, comp_id))
    conn.commit(); conn.close()

def get_competitions(chat_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM competitions WHERE chat_id=? ORDER BY comp_date", (chat_id,)).fetchall()
    conn.close(); return rows

# ── Partners ───────────────────────────────────────────
def add_pairing(m1, m2, context, chat_id):
    conn = get_conn()
    conn.execute(
        "INSERT INTO partners (member1_id, member2_id, context, chat_id) VALUES (?, ?, ?, ?)",
        (m1, m2, context, chat_id)
    )
    conn.commit(); conn.close()

def get_pairings(context=None, chat_id=None):
    conn = get_conn()
    if context and chat_id is not None:
        rows = conn.execute("SELECT * FROM partners WHERE context=? AND chat_id=?", (context, chat_id)).fetchall()
    elif context:
        rows = conn.execute("SELECT * FROM partners WHERE context=?", (context,)).fetchall()
    elif chat_id is not None:
        rows = conn.execute("SELECT * FROM partners WHERE chat_id=?", (chat_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM partners").fetchall()
    conn.close(); return rows

# ── Production ─────────────────────────────────────────
def add_milestone(title, deadline, chat_id):
    conn = get_conn()
    conn.execute("INSERT INTO production_milestones (title, deadline, chat_id) VALUES (?, ?, ?)", (title, deadline, chat_id))
    conn.commit(); conn.close()

def get_milestones(chat_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM production_milestones WHERE chat_id=? ORDER BY deadline", (chat_id,)).fetchall()
    conn.close(); return rows

# ── Announcements ──────────────────────────────────────
def add_announcement(text, sent_by, chat_id):
    conn = get_conn()
    conn.execute("INSERT INTO announcements (text, sent_by, chat_id) VALUES (?, ?, ?)", (text, sent_by, chat_id))
    conn.commit(); conn.close()
