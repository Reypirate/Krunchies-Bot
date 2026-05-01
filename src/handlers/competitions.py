import json

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from src.database import add_competition, create_signup_sheet, is_admin, update_comp_signup
from src.utils.formatting import md
from src.utils.security import sanitize_text, validate_username
from src.utils.time import STORED_FMT, _parse_natural_date, friendly_date_hint, now_local
from src.views.keyboards import get_signup_keyboard
from src.views.templates import format_signup_card

C_NAME, C_DATE, C_VENUE, C_DEADLINE, C_STYLES = range(5)
COMP_USER_DATA_KEYS = ("c_name", "c_date", "c_venue", "c_deadline")


def _clear_comp_data(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    for key in COMP_USER_DATA_KEYS:
        ctx.user_data.pop(key, None)


async def add_comp_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return ConversationHandler.END

    await update.message.reply_text("*Add Competition*\nEnter name:", parse_mode="Markdown")
    return C_NAME


async def c_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["c_name"] = sanitize_text(update.message.text, max_length=120)
    await update.message.reply_text(friendly_date_hint(), parse_mode="Markdown")
    return C_DATE


async def c_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    parsed = _parse_natural_date(update.message.text)
    if not parsed:
        await update.message.reply_text(
            "Couldn't understand that date.\n" + friendly_date_hint(),
            parse_mode="Markdown",
        )
        return C_DATE
    if parsed < now_local():
        await update.message.reply_text(
            f"That date ({parsed.strftime(STORED_FMT)}) is in the past. "
            "Please enter a future competition date:",
            parse_mode="Markdown",
        )
        return C_DATE

    date_str = parsed.strftime(STORED_FMT)
    ctx.user_data["c_date"] = date_str
    await update.message.reply_text(f"Got it: *{md(date_str)}*\n\nEnter venue:", parse_mode="Markdown")
    return C_VENUE


async def c_venue(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["c_venue"] = sanitize_text(update.message.text, max_length=160)
    await update.message.reply_text(
        "Enter registration deadline.\n" + friendly_date_hint(),
        parse_mode="Markdown",
    )
    return C_DEADLINE


async def c_deadline(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    parsed = _parse_natural_date(update.message.text)
    if not parsed:
        await update.message.reply_text(
            "Couldn't understand that date.\n" + friendly_date_hint(),
            parse_mode="Markdown",
        )
        return C_DEADLINE
    if parsed < now_local():
        await update.message.reply_text(
            f"That date ({parsed.strftime(STORED_FMT)}) is in the past. "
            "Please enter a future registration deadline:",
            parse_mode="Markdown",
        )
        return C_DEADLINE

    deadline = parsed.strftime(STORED_FMT)
    ctx.user_data["c_deadline"] = deadline
    await update.message.reply_text(
        f"Got it: *{md(deadline)}*\n\nEnter dance styles separated by commas:",
        parse_mode="Markdown",
    )
    return C_STYLES


async def c_styles(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
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
    created_by = validate_username((update.effective_user.username or "").lstrip("@"))[:32] or None

    comp_id = add_competition(name, date, venue, deadline, json.dumps(styles), created_by, chat_id)

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

    _clear_comp_data(ctx)
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_comp_data(ctx)
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# Flow: NAME -> DATE -> VENUE -> DEADLINE -> STYLES
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
