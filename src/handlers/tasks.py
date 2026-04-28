from datetime import datetime

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from src.database import add_task, complete_task, delete_task, get_my_tasks, get_tasks, is_admin, upsert_user
from src.utils.formatting import md
from src.utils.security import sanitize_text, validate_username
from src.views.templates import format_task_list

TASK_TITLE, TASK_DESC, TASK_DEADLINE, TASK_ASSIGN = range(4)
DATE_FMT = "%Y-%m-%d %H:%M"


async def addtask_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.first_name, user.username, update.effective_chat.id)
    await update.message.reply_text("*New Task*\nWhat's the task title?", parse_mode="Markdown")
    return TASK_TITLE


async def task_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["task_title"] = sanitize_text(update.message.text, max_length=100)
    await update.message.reply_text("Add a description (or send `-` to skip):", parse_mode="Markdown")
    return TASK_DESC


async def task_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text
    ctx.user_data["task_desc"] = None if raw == "-" else sanitize_text(raw, max_length=500)
    await update.message.reply_text(
        "Enter deadline as `YYYY-MM-DD HH:MM` (e.g. `2026-06-15 18:00`):",
        parse_mode="Markdown",
    )
    return TASK_DEADLINE


async def task_deadline(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    deadline = update.message.text.strip()
    try:
        datetime.strptime(deadline, DATE_FMT)
    except ValueError:
        await update.message.reply_text("Invalid format. Try `YYYY-MM-DD HH:MM`:", parse_mode="Markdown")
        return TASK_DEADLINE

    ctx.user_data["task_deadline"] = deadline
    await update.message.reply_text(
        "Assign to a username (e.g. `john_doe`) or `-` to leave unassigned:",
        parse_mode="Markdown",
    )
    return TASK_ASSIGN


async def task_assign(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip()
    assigned = None if raw == "-" else validate_username(raw.lstrip("@"))[:32]
    user = update.effective_user

    task_id = add_task(
        ctx.user_data["task_title"],
        ctx.user_data.get("task_desc"),
        ctx.user_data["task_deadline"],
        assigned,
        user.username,
        update.effective_chat.id,
    )
    await update.message.reply_text(
        f"*Task #{task_id} created!*\n"
        f"{md(ctx.user_data['task_title'])}\n"
        f"Due: `{md(ctx.user_data['task_deadline'])}`\n"
        f"Assigned: {md(assigned or 'Unassigned')}",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def list_tasks_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tasks = get_tasks(chat_id=update.effective_chat.id)
    await update.message.reply_text(format_task_list(tasks), parse_mode="Markdown")


async def my_tasks_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tasks = get_my_tasks(update.effective_user.username, update.effective_chat.id)
    await update.message.reply_text(format_task_list(tasks), parse_mode="Markdown")


async def done_task_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("Usage: /done <task_id>")
        return
    task_id = int(ctx.args[0])
    complete_task(task_id, update.effective_chat.id)
    await update.message.reply_text(f"Task #{task_id} marked as done!")


async def del_task_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admins only.")
        return
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("Usage: /deletetask <task_id>")
        return

    task_id = int(ctx.args[0])
    delete_task(task_id, update.effective_chat.id)
    await update.message.reply_text(f"Task #{task_id} deleted.")


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


task_conv = ConversationHandler(
    entry_points=[CommandHandler("addtask", addtask_start)],
    states={
        TASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_title)],
        TASK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_desc)],
        TASK_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_deadline)],
        TASK_ASSIGN: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_assign)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
