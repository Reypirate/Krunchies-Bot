import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.database import (
    get_pending_reminder_events,
    get_pending_reminder_tasks,
    mark_event_reminded,
    mark_task_reminded,
)
from src.utils.formatting import md, mention
from src.utils.time import bot_timezone, now_local

logger = logging.getLogger(__name__)


def _configured_chat_ids():
    chat_ids = []
    for raw_chat_id in os.getenv("ALLOWED_CHAT_IDS", "").split(","):
        raw_chat_id = raw_chat_id.strip()
        if not raw_chat_id:
            continue
        try:
            chat_ids.append(int(raw_chat_id))
        except ValueError:
            logger.warning("Ignoring invalid ALLOWED_CHAT_IDS entry: %s", raw_chat_id)
    return chat_ids


async def _send_message(app, chat_id, text):
    try:
        await app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        return True
    except Exception:
        logger.exception("Failed to send scheduled message to chat %s", chat_id)
        return False


async def check_reminders(app):
    now = now_local()

    for task in get_pending_reminder_tasks():
        try:
            deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
        except ValueError:
            continue

        diff = deadline - now
        target = mention(task["assigned_to"]) if task["assigned_to"] else "team"

        if timedelta(hours=23, minutes=45) <= diff <= timedelta(hours=24, minutes=15):
            if not task["reminded_24h"]:
                sent = await _send_message(
                    app,
                    task["chat_id"],
                    f"*Reminder!* Task #{task['id']} - *{md(task['title'])}* is due in about 24 hours.\n"
                    f"Assigned to: {target}",
                )
                if sent:
                    mark_task_reminded(task["id"], "24h")

        elif timedelta(minutes=45) <= diff <= timedelta(hours=1, minutes=15):
            if not task["reminded_1h"]:
                sent = await _send_message(
                    app,
                    task["chat_id"],
                    f"*1 Hour Left!* Task #{task['id']} - *{md(task['title'])}* is due soon.\n"
                    f"Assigned to: {target}",
                )
                if sent:
                    mark_task_reminded(task["id"], "1h")

    for event in get_pending_reminder_events():
        try:
            event_date = datetime.strptime(event["event_date"], "%Y-%m-%d %H:%M")
        except ValueError:
            continue

        diff = event_date - now

        if timedelta(hours=23, minutes=45) <= diff <= timedelta(hours=24, minutes=15):
            if not event["reminded_24h"]:
                sent = await _send_message(
                    app,
                    event["chat_id"],
                    f"*Event Tomorrow!* *{md(event['title'])}* is happening in about 24 hours.\n"
                    f"{md(event['description'] or '')}",
                )
                if sent:
                    mark_event_reminded(event["id"], "24h")

        elif timedelta(minutes=45) <= diff <= timedelta(hours=1, minutes=15):
            if not event["reminded_1h"]:
                sent = await _send_message(
                    app,
                    event["chat_id"],
                    f"*1 Hour Left!* *{md(event['title'])}* is starting soon.\n"
                    f"{md(event['description'] or '')}",
                )
                if sent:
                    mark_event_reminded(event["id"], "1h")


async def send_weekly_training_reminder(app, message):
    chat_ids = _configured_chat_ids()
    if not chat_ids:
        logger.info("Skipping weekly training reminder because ALLOWED_CHAT_IDS is empty.")
        return

    for chat_id in chat_ids:
        await _send_message(app, chat_id, message)


def setup_scheduler(app):
    scheduler = AsyncIOScheduler(timezone=bot_timezone())
    scheduler.add_job(check_reminders, "interval", minutes=15, args=[app])
    scheduler.add_job(
        send_weekly_training_reminder,
        "cron",
        day_of_week="tue",
        hour=20,
        minute=0,
        args=[app, "*Training Reminder!* Technique session tomorrow (Wed) 7-9 PM.\nCheck /training for details."],
    )
    scheduler.add_job(
        send_weekly_training_reminder,
        "cron",
        day_of_week="fri",
        hour=20,
        minute=0,
        args=[app, "*Training Reminder!* See you tomorrow (Sat) for training.\nCheck /training for details."],
    )
    scheduler.start()
