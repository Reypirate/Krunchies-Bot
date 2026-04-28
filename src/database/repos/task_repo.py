from src.database.connection import get_conn

def add_task(title, description, deadline, assigned_to, created_by, chat_id):
    conn = get_conn()
    c = conn.execute("""
        INSERT INTO tasks (title, description, deadline, assigned_to, created_by, chat_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, description, deadline, assigned_to, created_by, chat_id))
    conn.commit(); task_id = c.lastrowid; conn.close()
    return task_id

def get_tasks(chat_id=None, status="pending"):
    conn = get_conn()
    if chat_id:
        rows = conn.execute("SELECT * FROM tasks WHERE chat_id=? AND status=? ORDER BY deadline", (chat_id, status)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tasks WHERE status=? ORDER BY deadline", (status,)).fetchall()
    conn.close(); return rows

def get_my_tasks(username, chat_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM tasks WHERE assigned_to=? AND chat_id=? AND status='pending' ORDER BY deadline
    """, (username, chat_id)).fetchall()
    conn.close(); return rows

def complete_task(task_id, chat_id):
    conn = get_conn()
    conn.execute("UPDATE tasks SET status='done' WHERE id=? AND chat_id=?", (task_id, chat_id))
    conn.commit(); conn.close()

def delete_task(task_id, chat_id):
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id=? AND chat_id=?", (task_id, chat_id))
    conn.commit(); conn.close()

def get_pending_reminder_tasks():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM tasks WHERE status='pending'").fetchall()
    conn.close(); return rows

def mark_task_reminded(task_id, level):
    conn = get_conn()
    if level == "24h":
        conn.execute("UPDATE tasks SET reminded_24h=1 WHERE id=?", (task_id,))
    else:
        conn.execute("UPDATE tasks SET reminded_1h=1 WHERE id=?", (task_id,))
    conn.commit(); conn.close()
