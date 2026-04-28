from telegram import Update
from telegram.ext import ContextTypes

from src.database import add_pairing, get_pairings, is_admin
from src.utils.formatting import md
from src.utils.security import sanitize_text, validate_username


async def add_pair_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return

    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: /addpair @member1 @member2 [context]")
        return

    member1 = validate_username(ctx.args[0].lstrip("@"))[:32]
    member2 = validate_username(ctx.args[1].lstrip("@"))[:32]
    context = sanitize_text(" ".join(ctx.args[2:]) if len(ctx.args) > 2 else "General", max_length=80)

    if not member1 or not member2:
        await update.message.reply_text("Please provide valid Telegram usernames.")
        return

    add_pairing(member1, member2, context, update.effective_chat.id)
    await update.message.reply_text(f"Pair logged: @{member1} & @{member2} ({context})")


async def list_partners_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    pairings = get_pairings(chat_id=update.effective_chat.id)
    if not pairings:
        await update.message.reply_text("No pairings logged yet.")
        return

    msg = "*Current Pairings*\n\n"
    for pairing in pairings:
        msg += f"- @{md(pairing['member1_id'])} & @{md(pairing['member2_id'])} - {md(pairing['context'])}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")
