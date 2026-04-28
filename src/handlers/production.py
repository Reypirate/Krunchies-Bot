from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from src.database import add_milestone, get_milestones, is_admin
from src.utils.formatting import md
from src.utils.security import sanitize_text
from src.views.templates import format_production_status

DATE_FMT = "%Y-%m-%d"


async def prod_status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    milestones = get_milestones(update.effective_chat.id)
    await update.message.reply_text(format_production_status(milestones), parse_mode="Markdown")


async def add_milestone_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return

    text = " ".join(ctx.args)
    if "|" not in text:
        await update.message.reply_text("Usage: /addmilestone Title | YYYY-MM-DD")
        return

    title, date = [part.strip() for part in text.split("|", 1)]
    title = sanitize_text(title, max_length=120)
    try:
        datetime.strptime(date, DATE_FMT)
    except ValueError:
        await update.message.reply_text("Invalid date. Use YYYY-MM-DD.")
        return

    add_milestone(title, date, update.effective_chat.id)
    await update.message.reply_text(f"Milestone added: *{md(title)}* ({md(date)})", parse_mode="Markdown")
