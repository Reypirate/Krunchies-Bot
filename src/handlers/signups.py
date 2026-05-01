import json
import logging
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from src.database import (
    close_signup_sheet,
    delete_signup_sheet,
    get_signup_sheet,
    is_admin,
    reopen_signup_sheet,
    toggle_signup,
)
from src.views.keyboards import get_signup_keyboard
from src.views.templates import format_signup_card, format_signup_summary

logger = logging.getLogger(__name__)


def _option_from_callback(sheet: Any, token: str) -> str | None:
    options = json.loads(sheet["options"])

    try:
        return options[int(token)]
    except (ValueError, IndexError):
        # Backward compatibility for older messages that stored the full option.
        if token in options:
            return token
        return None


def _can_manage_sheet(sheet: Any, user_id: int) -> bool:
    return is_admin(user_id) or sheet["created_by"] == user_id


def _keyboard_for_sheet(sheet: Any, options: list[str], management: bool = True) -> Any:
    is_poll = sheet["entity_type"] == "poll"
    return get_signup_keyboard(
        sheet["id"],
        options,
        include_close=management,
        include_delete=is_poll and management,
        is_closed=bool(sheet["is_closed"]),
        publish_query=str(sheet["id"]) if is_poll and management else None,
    )


async def _handle_signup(query: Any, sheet: Any, sheet_id: int, data: list[str]) -> None:
    if sheet["is_closed"]:
        await query.answer("Sorry, this sign-up is closed.")
        return
    if len(data) < 3:
        await query.answer("Invalid sign-up option.", show_alert=True)
        return

    option = _option_from_callback(sheet, data[2])
    if option is None:
        await query.answer("That option is no longer available.", show_alert=True)
        return

    user = query.from_user
    action_result, option_label = toggle_signup(sheet_id, user.id, user.first_name, option)
    toast = (
        f"Signed up: {option_label}"
        if action_result == "added"
        else f"Removed: {option_label}"
    )
    await query.answer(toast)

    options = json.loads(sheet["options"])
    new_text = format_signup_card(sheet_id, sheet["title"], sheet["details"], options)

    try:
        await query.edit_message_text(
            text=new_text,
            reply_markup=_keyboard_for_sheet(sheet, options, management=query.message is not None),
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Failed to refresh signup sheet %s", sheet_id)


async def _handle_close(query: Any, sheet: Any, sheet_id: int) -> None:
    if not _can_manage_sheet(sheet, query.from_user.id):
        await query.answer("Only admins or the poll owner can close this.", show_alert=True)
        return

    close_signup_sheet(sheet_id)
    await query.answer("Sign-up closed.")

    options = json.loads(sheet["options"])
    final_text = format_signup_summary(sheet_id, sheet["title"], sheet["details"], options)
    await query.edit_message_text(
        text=f"*CLOSED*\n\n{final_text}",
        reply_markup=get_signup_keyboard(
            sheet_id,
            options,
            include_close=True,
            include_delete=sheet["entity_type"] == "poll",
            is_closed=True,
            publish_query=str(sheet_id) if sheet["entity_type"] == "poll" else None,
        ),
        parse_mode="Markdown",
    )


async def _handle_reopen(query: Any, sheet: Any, sheet_id: int) -> None:
    if not _can_manage_sheet(sheet, query.from_user.id):
        await query.answer("Only admins or the poll owner can reopen this.", show_alert=True)
        return

    reopen_signup_sheet(sheet_id)
    await query.answer("Sign-up reopened.")

    options = json.loads(sheet["options"])
    final_text = format_signup_card(sheet_id, sheet["title"], sheet["details"], options)
    await query.edit_message_text(
        text=final_text,
        reply_markup=get_signup_keyboard(
            sheet_id,
            options,
            include_close=True,
            include_delete=sheet["entity_type"] == "poll",
            is_closed=False,
            publish_query=str(sheet_id) if sheet["entity_type"] == "poll" else None,
        ),
        parse_mode="Markdown",
    )


async def _handle_delete(query: Any, sheet: Any, sheet_id: int) -> None:
    if sheet["entity_type"] != "poll" or not _can_manage_sheet(sheet, query.from_user.id):
        await query.answer("Only the poll owner or admins can delete this poll.", show_alert=True)
        return

    delete_signup_sheet(sheet_id)
    await query.answer("Poll deleted.")
    await query.edit_message_text(text="This poll has been deleted.")


async def handle_signup_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = (query.data or "").split(":", 2)

    if len(data) < 2:
        await query.answer("Invalid sign-up action.", show_alert=True)
        return

    action = data[0]
    try:
        sheet_id = int(data[1])
    except ValueError:
        await query.answer("Invalid sign-up sheet.", show_alert=True)
        return

    sheet = get_signup_sheet(sheet_id)
    if not sheet:
        await query.answer("Sorry, this sign-up no longer exists.", show_alert=True)
        return

    if action == "signup":
        await _handle_signup(query, sheet, sheet_id, data)

    elif action == "close":
        await _handle_close(query, sheet, sheet_id)

    elif action == "reopen":
        await _handle_reopen(query, sheet, sheet_id)

    elif action == "delete":
        await _handle_delete(query, sheet, sheet_id)

    else:
        await query.answer("Invalid sign-up action.", show_alert=True)
