import json
from datetime import datetime

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from src.database import add_competition, create_signup_sheet, is_admin, update_comp_signup
from src.utils.security import sanitize_text
from src.views.keyboards import get_signup_keyboard
from src.views.templates import format_signup_card

C_NAME, C_DATE, C_VENUE, C_DEADLINE, C_STYLES = range(5)
DATE_FMT = "%Y-%m-%d"


async def add_comp_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return ConversationHandler.END

    await update.message.reply_text("*Add Competition*\nEnter name:", parse_mode="Markdown")
    return C_NAME


async def c_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["c_name"] = sanitize_text(update.message.text, max_length=120)
    await update.message.reply_text("Enter competition date (`YYYY-MM-DD`):", parse_mode="Markdown")
    return C_DATE


async def c_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    date_str = update.message.text.strip()
    try:
        datetime.strptime(date_str, DATE_FMT)
    except ValueError:
        await update.message.reply_text("Invalid format. Try `YYYY-MM-DD`:", parse_mode="Markdown")
        return C_DATE

    ctx.user_data["c_date"] = date_str
    await update.message.reply_text("Enter venue:")
    return C_VENUE


async def c_venue(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["c_venue"] = sanitize_text(update.message.text, max_length=160)
    await update.message.reply_text("Enter registration deadline (`YYYY-MM-DD`):", parse_mode="Markdown")
    return C_DEADLINE


async def c_deadline(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    deadline = update.message.text.strip()
    try:
        datetime.strptime(deadline, DATE_FMT)
    except ValueError:
        await update.message.reply_text("Invalid format. Try `YYYY-MM-DD`:", parse_mode="Markdown")
        return C_DEADLINE

    ctx.user_data["c_deadline"] = deadline
    await update.message.reply_text("Enter dance styles separated by commas:")
    return C_STYLES


async def c_styles(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    styles = []
    for raw_style in update.message.text.split(","):
        style = sanitize_text(raw_style.strip(), max_length=40)
        if style and style.lower() != "not competing" and style not in styles:
            styles.append(style)

    styles = styles[:12]
    if not styles:
        await update.message.reply_text("Please provide at least one dance style.")
        return C_STYLES

    styles.append("Not Competing")

    name = ctx.user_data["c_name"]
    date = ctx.user_data["c_date"]
    venue = ctx.user_data["c_venue"]
    deadline = ctx.user_data["c_deadline"]
    chat_id = update.effective_chat.id

    comp_id = add_competition(name, date, venue, deadline, json.dumps(styles), update.effective_user.username, chat_id)

    title = name
    details = f"Date: {date}\nVenue: {venue}\nRegistration Deadline: {deadline}"

    sheet_id = create_signup_sheet(
        "comp",
        comp_id,
        chat_id,
        title,
        details,
        json.dumps(styles),
        created_by=update.effective_user.id,
    )
    update_comp_signup(comp_id, sheet_id)

    text = format_signup_card(sheet_id, title, details, styles)
    await update.message.reply_text(
        text,
        reply_markup=get_signup_keyboard(sheet_id, styles),
        parse_mode="Markdown",
    )

    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


comp_conv = ConversationHandler(
    entry_points=[CommandHandler("addcomp", add_comp_start)],
    states={
        C_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_name)],
        C_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_date)],
        C_VENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_venue)],
        C_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_deadline)],
        C_STYLES: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_styles)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
