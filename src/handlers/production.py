from telegram import Update
from telegram.ext import ContextTypes

from src.database import add_milestone, get_milestones, is_admin
from src.utils.formatting import md
from src.utils.security import sanitize_text
from src.utils.time import STORED_FMT, _parse_natural_date, friendly_date_hint, now_local
from src.views.templates import format_production_status


async def prod_status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    milestones = get_milestones(update.effective_chat.id)
    await update.message.reply_text(format_production_status(milestones), parse_mode="Markdown")


async def add_milestone_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return

    text = " ".join(ctx.args)
    if "|" not in text:
        await update.message.reply_text(
            "Usage: /addmilestone Title | date/time\n" + friendly_date_hint(),
            parse_mode="Markdown",
        )
        return

    title, raw_date = [part.strip() for part in text.split("|", 1)]
    title = sanitize_text(title, max_length=120)
    parsed = _parse_natural_date(raw_date)
    if not parsed:
        await update.message.reply_text(
            "Couldn't understand that date.\n" + friendly_date_hint(),
            parse_mode="Markdown",
        )
        return
    if parsed < now_local():
        await update.message.reply_text(
            f"That date ({parsed.strftime(STORED_FMT)}) is in the past. "
            "Please enter a future milestone deadline:",
            parse_mode="Markdown",
        )
        return

    date = parsed.strftime(STORED_FMT)
    add_milestone(title, date, update.effective_chat.id)
    await update.message.reply_text(f"Milestone added: *{md(title)}* ({md(date)})", parse_mode="Markdown")
