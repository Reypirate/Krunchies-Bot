import json

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from src.database import add_event, create_signup_sheet, delete_event, get_events, is_admin, update_event_signup
from src.utils.formatting import md
from src.utils.security import sanitize_text, validate_username
from src.utils.time import STORED_FMT, _parse_natural_date, friendly_date_hint, now_local
from src.views.keyboards import get_signup_keyboard
from src.views.templates import format_event_list, format_signup_card

E_TITLE, E_DESC, E_DATE = range(3)
EVENT_USER_DATA_KEYS = ("e_title", "e_desc")


def _clear_event_data(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    for key in EVENT_USER_DATA_KEYS:
        ctx.user_data.pop(key, None)


async def addevent_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return ConversationHandler.END

    await update.message.reply_text("*New Event*\nWhat's the event name?", parse_mode="Markdown")
    return E_TITLE


async def e_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["e_title"] = sanitize_text(update.message.text, max_length=120)
    await update.message.reply_text("Add a description (or `-` to skip):", parse_mode="Markdown")
    return E_DESC


async def e_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text
    ctx.user_data["e_desc"] = None if raw == "-" else sanitize_text(raw, max_length=700)
    await update.message.reply_text(friendly_date_hint(), parse_mode="Markdown")
    return E_DATE


async def e_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    parsed = _parse_natural_date(update.message.text)
    if not parsed:
        await update.message.reply_text(
            "Couldn't understand that date.\n" + friendly_date_hint(),
            parse_mode="Markdown",
        )
        return E_DATE
    if parsed < now_local():
        await update.message.reply_text(
            f"That date ({parsed.strftime(STORED_FMT)}) is in the past. "
            "Please enter a future event date:",
            parse_mode="Markdown",
        )
        return E_DATE

    date_str = parsed.strftime(STORED_FMT)
    await update.message.reply_text(f"Got it: *{md(date_str)}*", parse_mode="Markdown")

    name = ctx.user_data["e_title"]
    desc = ctx.user_data["e_desc"]
    chat_id = update.effective_chat.id
    created_by = validate_username((update.effective_user.username or "").lstrip("@"))[:32] or None

    event_id = add_event(name, desc, date_str, created_by, chat_id)

    title = f"Event: {name}"
    details = f"Date: {date_str}\n{desc or 'No description'}"
    options = ["Coming", "Can't Make It"]

    sheet_id = create_signup_sheet(
        "event",
        event_id,
        chat_id,
        title,
        details,
        json.dumps(options),
        created_by=update.effective_user.id,
    )
    update_event_signup(event_id, sheet_id)

    text = format_signup_card(sheet_id, title, details, options)
    await update.message.reply_text(
        text,
        reply_markup=get_signup_keyboard(sheet_id, options),
        parse_mode="Markdown",
    )

    _clear_event_data(ctx)
    return ConversationHandler.END


async def list_events_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    events = get_events(update.effective_chat.id)
    await update.message.reply_text(format_event_list(events), parse_mode="Markdown")


async def del_event_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("Usage: /deleteevent <event_id>")
        return

    delete_event(int(ctx.args[0]), update.effective_chat.id)
    await update.message.reply_text(f"Event #{ctx.args[0]} deleted.")


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_event_data(ctx)
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# Flow: TITLE -> DESC -> DATE
event_conv = ConversationHandler(
    entry_points=[CommandHandler("addevent", addevent_start)],
    states={
        E_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, e_title)],
        E_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, e_desc)],
        E_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, e_date)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
