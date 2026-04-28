from telegram import Update
from telegram.ext import ContextTypes
from src.database import upsert_user
from src.services.gemini_service import ask_gemini
from src.utils.security import sanitize_text

async def ai_chat_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    upsert_user(u.id, u.first_name, u.username, update.effective_chat.id)
    
    # Sanitize user input to prevent prompt injection or abuse
    user_input = sanitize_text(update.message.text, max_length=1000)
    
    await update.message.chat.send_action("typing")
    reply = await ask_gemini(user_input, update.effective_chat.id)
    await update.message.reply_text(reply)
