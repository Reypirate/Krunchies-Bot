import json

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from src.database import add_training, create_signup_sheet, get_trainings, is_admin, log_attendance, update_training_signup
from src.utils.formatting import md
from src.utils.security import sanitize_text
from src.utils.time import STORED_FMT, _parse_natural_date, friendly_date_hint, now_local
from src.views.keyboards import get_signup_keyboard
from src.views.templates import format_signup_card

T_DATE, T_LOC, T_FOCUS = range(3)
TRAINING_USER_DATA_KEYS = ("t_date", "t_loc")


def _clear_training_data(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    for key in TRAINING_USER_DATA_KEYS:
        ctx.user_data.pop(key, None)


async def add_training_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return ConversationHandler.END

    await update.message.reply_text(
        "*New Training Session*\n" + friendly_date_hint(),
        parse_mode="Markdown",
    )
    return T_DATE


async def t_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    parsed = _parse_natural_date(update.message.text)
    if not parsed:
        await update.message.reply_text(
            "Couldn't understand that date.\n" + friendly_date_hint(),
            parse_mode="Markdown",
        )
        return T_DATE
    if parsed < now_local():
        await update.message.reply_text(
            f"That date ({parsed.strftime(STORED_FMT)}) is in the past. "
            "Please enter a future training date:",
            parse_mode="Markdown",
        )
        return T_DATE

    date_str = parsed.strftime(STORED_FMT)
    ctx.user_data["t_date"] = date_str
    await update.message.reply_text(
        f"Got it: *{md(date_str)}*\n\nEnter location (e.g. `SMU Sports Hall B`):",
        parse_mode="Markdown",
    )
    return T_LOC


async def t_loc(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["t_loc"] = sanitize_text(update.message.text, max_length=120)
    await update.message.reply_text("Enter focus (e.g. `Technique / Comp Prep`):", parse_mode="Markdown")
    return T_FOCUS


async def t_focus(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    focus = sanitize_text(update.message.text, max_length=160)
    date_str = ctx.user_data["t_date"]
    location = ctx.user_data["t_loc"]
    chat_id = update.effective_chat.id

    training_id = add_training(date_str, location, focus, "none", chat_id)

    title = f"Training - {date_str}"
    details = f"Location: {location}\nFocus: {focus}"
    options = ["Count Me In", "Can't Make It"]

    sheet_id = create_signup_sheet(
        "training",
        training_id,
        chat_id,
        title,
        details,
        json.dumps(options),
        created_by=update.effective_user.id,
    )
    update_training_signup(training_id, sheet_id)

    text = format_signup_card(sheet_id, title, details, options)
    await update.message.reply_text(
        text,
        reply_markup=get_signup_keyboard(sheet_id, options),
        parse_mode="Markdown",
    )

    _clear_training_data(ctx)
    return ConversationHandler.END


async def here_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    today = now_local().strftime("%Y-%m-%d")
    trainings = [training for training in get_trainings(update.effective_chat.id) if training["date"].startswith(today)]
    if not trainings:
        await update.message.reply_text("No training session found for today.")
        return

    latest = trainings[-1]
    inserted = log_attendance(latest["id"], update.effective_user.id)
    if inserted:
        await update.message.reply_text(f"Attendance marked for {latest['date']}!")
    else:
        await update.message.reply_text(f"You're already marked present for {latest['date']}.")


async def list_training(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    trainings = get_trainings(update.effective_chat.id)
    if not trainings:
        await update.message.reply_text("No training sessions scheduled.")
        return

    msg = "*Training Schedule*\n\n"
    for training in trainings:
        msg += f"- {md(training['date'])} @ {md(training['location'])} ({md(training['focus'])})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    _clear_training_data(ctx)
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# Flow: DATE -> LOCATION -> FOCUS
training_conv = ConversationHandler(
    entry_points=[CommandHandler("addtraining", add_training_start)],
    states={
        T_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, t_date)],
        T_LOC: [MessageHandler(filters.TEXT & ~filters.COMMAND, t_loc)],
        T_FOCUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, t_focus)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
