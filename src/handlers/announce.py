from telegram import Update
from telegram.ext import ContextTypes

from src.database import add_announcement, is_admin
from src.utils.formatting import md
from src.utils.security import sanitize_text


async def announce_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return

    if not ctx.args:
        await update.message.reply_text("Usage: /announce <message>")
        return

    msg_text = sanitize_text(" ".join(ctx.args), max_length=2000)
    broadcast = f"*Krunchies Announcement*\n\n{md(msg_text)}"

    add_announcement(msg_text, update.effective_user.username, update.effective_chat.id)

    await update.message.reply_text(broadcast, parse_mode="Markdown")
