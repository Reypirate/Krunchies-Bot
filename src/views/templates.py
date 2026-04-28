from collections import defaultdict

from src.database import get_signup_responses
from src.utils.formatting import md


def format_signup_card(sheet_id, title, details, options_list):
    responses = get_signup_responses(sheet_id)

    grouped = defaultdict(list)
    for response in responses:
        grouped[response["option_chosen"]].append(response["display_name"])

    text = f"*{md(title)}*\n"
    if details:
        text += f"{md(details)}\n"
    text += "\n"

    for option in options_list:
        users = grouped.get(option, [])
        text += f"*{md(option)}* ({len(users)})\n"
        for index, name in enumerate(users, 1):
            text += f"{index}. {md(name)}\n"
        text += "\n"

    text += "_Tap a button below to sign up!_"
    return text


def format_signup_summary(sheet_id, title, details, options_list):
    text = format_signup_card(sheet_id, title, details, options_list)
    return text.replace("_Tap a button below to sign up!_", "_This sign-up is closed._")


def format_poll_list(polls):
    if not polls:
        return "You don't have any polls yet. Use /newpoll to create one."

    msg = "*Your Polls*\n\n"
    for poll in polls:
        status = "closed" if poll["is_closed"] else "open"
        msg += f"- #{poll['id']} {md(poll['title'])} ({status})\n"
    msg += "\nUse `/viewpoll <id>` to repost one."
    return msg


def format_task_list(tasks):
    if not tasks:
        return "No pending tasks!"

    msg = "*Pending Tasks*\n\n"
    for task in tasks:
        msg += (
            f"*[{task['id']}] {md(task['title'])}*\n"
            f"Description: {md(task['description'] or 'No description')}\n"
            f"Due: `{md(task['deadline'])}`\n"
            f"Assigned: {md(task['assigned_to'] or 'Unassigned')}\n\n"
        )
    return msg


def format_event_list(events):
    if not events:
        return "No upcoming events!"

    msg = "*Upcoming Events*\n\n"
    for event in events:
        msg += f"- {md(event['title'])} - {md(event['event_date'])}\n"
    return msg


def format_production_status(milestones):
    if not milestones:
        return "No production milestones set."

    msg = "*Un Paso Production Status*\n\n"
    for milestone in milestones:
        status_icon = "Done" if milestone["status"] == "done" else "Pending"
        msg += f"{status_icon}: *{md(milestone['title'])}* - {md(milestone['deadline'])}\n"
    return msg
