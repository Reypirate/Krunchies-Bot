import os

from telegram import Update
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    TypeHandler,
    filters,
)

from src.database import upsert_user
from src.handlers.ai import ai_chat_handler
from src.handlers.announce import announce_cmd
from src.handlers.competitions import comp_conv
from src.handlers.events import del_event_cmd, event_conv, list_events_cmd
from src.handlers.partners import add_pair_cmd, list_partners_cmd
from src.handlers.polls import deletepoll_cmd, headcount_cmd, inline_poll_query, poll_conv, polls_cmd, viewpoll_cmd
from src.handlers.production import add_milestone_cmd, prod_status_cmd
from src.handlers.signups import handle_signup_callback
from src.handlers.tasks import del_task_cmd, done_task_cmd, list_tasks_cmd, my_tasks_cmd, task_conv
from src.handlers.training import here_cmd, list_training, training_conv
from src.utils.formatting import md
from src.utils.security import is_rate_limited


async def gatekeeper(update, context):
    if not update.effective_chat or not update.effective_user:
        return

    allowed_ids_str = os.getenv("ALLOWED_CHAT_IDS", "")
    if allowed_ids_str:
        allowed_ids = [chat_id.strip() for chat_id in allowed_ids_str.split(",")]
        admin_ids = [
            int(admin_id.strip())
            for admin_id in os.getenv("ADMIN_IDS", "").split(",")
            if admin_id.strip().isdigit()
        ]
        is_allowed_chat = str(update.effective_chat.id) in allowed_ids
        is_admin_private_chat = (
            update.effective_chat.type == "private"
            and update.effective_user.id in admin_ids
        )
        if not is_allowed_chat and not is_admin_private_chat:
            raise ApplicationHandlerStop()

    if is_rate_limited(update.effective_user.id):
        raise ApplicationHandlerStop()


async def start(update, ctx):
    user = update.effective_user
    upsert_user(user.id, user.first_name, user.username, update.effective_chat.id)
    await update.message.reply_text(
        f"Hey *{md(user.first_name)}*! Welcome to SMU Krunchies Club Planner.\n\n"
        "Use /help to see all commands.",
        parse_mode="Markdown",
    )


async def help_cmd(update, ctx):
    help_text = """
*SMU Krunchies Bot Help*

*Tasks*
/addtask - Add a new task
/tasks - View all tasks
/mytasks - View your tasks
/done <id> - Mark as done

*Training & Events*
/addtraining - Post training (Admin)
/training - This week's schedule
/here - Attendance check-in
/addevent - Post club event (Admin)
/events - Upcoming events

*CountMeIn Polls*
/newpoll - Create a custom named poll
/polls - View your polls
/viewpoll <id> - Repost one of your polls
/headcount <id> - Show a sign-up summary
/deletepoll <id> - Delete one of your polls

*Competitions & Partners*
/addcomp - Post competition (Admin)
/partners - View pairings
/addpair - Log pairing (Admin)

*Production*
/prodstatus - Milestone checklist
/addmilestone - Add milestone (Admin)

*Announce*
/announce - Broadcast (Admin)
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


def register_handlers(app):
    app.add_handler(TypeHandler(Update, gatekeeper), group=-1)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    app.add_handler(task_conv)
    app.add_handler(event_conv)
    app.add_handler(training_conv)
    app.add_handler(comp_conv)
    app.add_handler(poll_conv)

    app.add_handler(CommandHandler("tasks", list_tasks_cmd))
    app.add_handler(CommandHandler("mytasks", my_tasks_cmd))
    app.add_handler(CommandHandler("done", done_task_cmd))
    app.add_handler(CommandHandler("deletetask", del_task_cmd))

    app.add_handler(CommandHandler("events", list_events_cmd))
    app.add_handler(CommandHandler("deleteevent", del_event_cmd))

    app.add_handler(CommandHandler("polls", polls_cmd))
    app.add_handler(CommandHandler("viewpoll", viewpoll_cmd))
    app.add_handler(CommandHandler("headcount", headcount_cmd))
    app.add_handler(CommandHandler("deletepoll", deletepoll_cmd))
    app.add_handler(InlineQueryHandler(inline_poll_query))

    app.add_handler(CommandHandler("here", here_cmd))
    app.add_handler(CommandHandler("training", list_training))

    app.add_handler(CommandHandler("partners", list_partners_cmd))
    app.add_handler(CommandHandler("addpair", add_pair_cmd))

    app.add_handler(CommandHandler("prodstatus", prod_status_cmd))
    app.add_handler(CommandHandler("addmilestone", add_milestone_cmd))

    app.add_handler(CommandHandler("announce", announce_cmd))

    app.add_handler(CallbackQueryHandler(handle_signup_callback))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handler))
