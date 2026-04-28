import json
from datetime import datetime

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from src.database import add_event, create_signup_sheet, delete_event, get_events, is_admin, update_event_signup
from src.utils.security import sanitize_text
from src.views.keyboards import get_signup_keyboard
from src.views.templates import format_event_list, format_signup_card

E_TITLE, E_DESC, E_DATE = range(3)
DATE_FMT = "%Y-%m-%d %H:%M"


async def addevent_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return ConversationHandler.END

    await update.message.reply_text("*New Event*\nWhat's the event name?", parse_mode="Markdown")
    return E_TITLE


async def e_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["e_title"] = sanitize_text(update.message.text, max_length=120)
    await update.message.reply_text("Add a description (or `-` to skip):", parse_mode="Markdown")
    return E_DESC


async def e_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text
    ctx.user_data["e_desc"] = None if raw == "-" else sanitize_text(raw, max_length=700)
    await update.message.reply_text("Enter event date as `YYYY-MM-DD HH:MM`:", parse_mode="Markdown")
    return E_DATE


async def e_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    date_str = update.message.text.strip()
    try:
        datetime.strptime(date_str, DATE_FMT)
    except ValueError:
        await update.message.reply_text("Invalid format. Try `YYYY-MM-DD HH:MM`:", parse_mode="Markdown")
        return E_DATE

    name = ctx.user_data["e_title"]
    desc = ctx.user_data["e_desc"]
    chat_id = update.effective_chat.id

    event_id = add_event(name, desc, date_str, update.effective_user.username, chat_id)

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

    return ConversationHandler.END


async def list_events_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    events = get_events(update.effective_chat.id)
    await update.message.reply_text(format_event_list(events), parse_mode="Markdown")


async def del_event_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("Usage: /deleteevent <event_id>")
        return

    delete_event(int(ctx.args[0]), update.effective_chat.id)
    await update.message.reply_text(f"Event #{ctx.args[0]} deleted.")


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


event_conv = ConversationHandler(
    entry_points=[CommandHandler("addevent", addevent_start)],
    states={
        E_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, e_title)],
        E_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, e_desc)],
        E_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, e_date)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
