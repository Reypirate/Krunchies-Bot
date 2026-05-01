from typing import Any

from src.database.connection import get_conn
from src.utils.security import sanitize_text


def create_signup_sheet(
    entity_type: str,
    entity_id: int | None,
    chat_id: int,
    title: str,
    details: str | None,
    options_json: str,
    created_by: int | None = None,
) -> int:
    conn = get_conn()
    try:
        c = conn.execute(
            """
            INSERT INTO signup_sheets (entity_type, entity_id, chat_id, created_by, title, details, options)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (entity_type, entity_id, chat_id, created_by, title, details, options_json),
        )
        conn.commit()
        return c.lastrowid
    finally:
        conn.close()


def update_signup_message(sheet_id: int, message_id: int) -> None:
    conn = get_conn()
    try:
        conn.execute("UPDATE signup_sheets SET message_id=? WHERE id=?", (message_id, sheet_id))
        conn.commit()
    finally:
        conn.close()


def get_signup_sheet(sheet_id: int) -> Any:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM signup_sheets WHERE id=? AND is_deleted=0",
            (sheet_id,),
        ).fetchone()
    finally:
        conn.close()


def get_signup_sheets_by_creator(
    created_by: int,
    entity_type: str | None = None,
    limit: int = 30,
) -> list[Any]:
    conn = get_conn()
    try:
        if entity_type:
            return conn.execute(
                """
                SELECT * FROM signup_sheets
                WHERE created_by=? AND entity_type=? AND is_deleted=0
                ORDER BY created_at DESC LIMIT ?
                """,
                (created_by, entity_type, limit),
            ).fetchall()

        return conn.execute(
            """
            SELECT * FROM signup_sheets
            WHERE created_by=? AND is_deleted=0
            ORDER BY created_at DESC LIMIT ?
            """,
            (created_by, limit),
        ).fetchall()
    finally:
        conn.close()


def toggle_signup(sheet_id: int, user_id: int, display_name: str, option: str) -> tuple[str, str]:
    """Toggle a signup response and return the action plus the option label."""
    display_name = sanitize_text(display_name, max_length=64)
    option = sanitize_text(option, max_length=100)

    conn = get_conn()
    # Serialize read-then-write taps so concurrent button presses cannot double-count.
    conn.execute("BEGIN IMMEDIATE")

    try:
        sheet = conn.execute(
            "SELECT entity_type FROM signup_sheets WHERE id=?",
            (sheet_id,),
        ).fetchone()

        # Competitions are multi-choice; all other sheet types are single-choice.
        is_multi_choice = sheet and sheet["entity_type"] == "comp"

        existing_same = conn.execute(
            """
            SELECT id FROM signup_responses
            WHERE sheet_id=? AND user_id=? AND option_chosen=?
            """,
            (sheet_id, user_id, option),
        ).fetchone()

        if existing_same:
            conn.execute("DELETE FROM signup_responses WHERE id=?", (existing_same["id"],))
            conn.commit()
            return ("removed", option)

        if not is_multi_choice:
            conn.execute(
                """
                DELETE FROM signup_responses
                WHERE sheet_id=? AND user_id=?
                """,
                (sheet_id, user_id),
            )

        conn.execute(
            """
            INSERT INTO signup_responses (sheet_id, user_id, display_name, option_chosen)
            VALUES (?, ?, ?, ?)
            """,
            (sheet_id, user_id, display_name, option),
        )

        conn.commit()
        return ("added", option)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_signup_responses(sheet_id: int) -> list[Any]:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM signup_responses WHERE sheet_id=? ORDER BY responded_at",
            (sheet_id,),
        ).fetchall()
    finally:
        conn.close()


def close_signup_sheet(sheet_id: int) -> None:
    conn = get_conn()
    try:
        conn.execute("UPDATE signup_sheets SET is_closed=1 WHERE id=?", (sheet_id,))
        conn.commit()
    finally:
        conn.close()


def reopen_signup_sheet(sheet_id: int) -> None:
    conn = get_conn()
    try:
        conn.execute("UPDATE signup_sheets SET is_closed=0 WHERE id=?", (sheet_id,))
        conn.commit()
    finally:
        conn.close()


def delete_signup_sheet(sheet_id: int) -> None:
    conn = get_conn()
    try:
        conn.execute("UPDATE signup_sheets SET is_deleted=1 WHERE id=?", (sheet_id,))
        conn.commit()
    finally:
        conn.close()
