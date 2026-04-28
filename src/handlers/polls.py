import json

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from src.database import (
    create_signup_sheet,
    delete_signup_sheet,
    get_signup_sheet,
    get_signup_sheets_by_creator,
    is_admin,
)
from src.utils.formatting import md
from src.utils.security import sanitize_text
from src.views.keyboards import get_signup_keyboard
from src.views.templates import format_poll_list, format_signup_card, format_signup_summary

POLL_TITLE, POLL_OPTIONS = range(2)
MAX_OPTIONS = 10


def _can_manage_poll(sheet, user_id):
    return sheet and sheet["entity_type"] == "poll" and (is_admin(user_id) or sheet["created_by"] == user_id)


def _poll_keyboard(sheet, options):
    return get_signup_keyboard(
        sheet["id"],
        options,
        include_close=True,
        include_delete=True,
        is_closed=bool(sheet["is_closed"]),
        publish_query=str(sheet["id"]),
    )


def _poll_vote_keyboard(sheet, options):
    if sheet["is_closed"]:
        return None
    return get_signup_keyboard(
        sheet["id"],
        options,
        include_close=False,
        include_delete=False,
        is_closed=False,
    )


async def newpoll_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["poll_options"] = []
    await update.message.reply_text(
        "*New CountMeIn Poll*\nSend me the poll title.",
        parse_mode="Markdown",
    )
    return POLL_TITLE


async def poll_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    title = sanitize_text(update.message.text, max_length=200)
    if not title:
        await update.message.reply_text("Please send a non-empty title.")
        return POLL_TITLE

    ctx.user_data["poll_title"] = title
    ctx.user_data["poll_options"] = []
    await update.message.reply_text(
        f"New poll: *{md(title)}*\n\nSend the first answer option.",
        parse_mode="Markdown",
    )
    return POLL_OPTIONS


async def poll_option(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    option = sanitize_text(update.message.text, max_length=80)
    if not option:
        await update.message.reply_text("Please send a non-empty option.")
        return POLL_OPTIONS

    options = ctx.user_data.setdefault("poll_options", [])
    if option in options:
        await update.message.reply_text("That option already exists. Send another option or /done.")
        return POLL_OPTIONS

    options.append(option)
    if len(options) >= MAX_OPTIONS:
        return await finish_poll(update, ctx)

    await update.message.reply_text(
        f"Added: {option}\nSend another option, or /done to publish.",
    )
    return POLL_OPTIONS


async def finish_poll(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    title = ctx.user_data.get("poll_title")
    options = ctx.user_data.get("poll_options", [])
    if not title:
        await update.message.reply_text("No poll is being created. Use /newpoll to start one.")
        return ConversationHandler.END
    if not options:
        await update.message.reply_text("A poll needs at least one option. Send an option or /cancel.")
        return POLL_OPTIONS

    sheet_id = create_signup_sheet(
        "poll",
        None,
        update.effective_chat.id,
        title,
        None,
        json.dumps(options),
        created_by=update.effective_user.id,
    )
    sheet = get_signup_sheet(sheet_id)
    text = format_signup_card(sheet_id, title, None, options)

    await update.message.reply_text("Poll created.")
    await update.message.reply_text(
        text,
        reply_markup=_poll_keyboard(sheet, options),
        parse_mode="Markdown",
    )

    ctx.user_data.pop("poll_title", None)
    ctx.user_data.pop("poll_options", None)
    return ConversationHandler.END


async def polls_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    polls = get_signup_sheets_by_creator(update.effective_user.id, entity_type="poll")
    await update.message.reply_text(format_poll_list(polls), parse_mode="Markdown")


async def viewpoll_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("Usage: /viewpoll <poll_id>")
        return

    sheet = get_signup_sheet(int(ctx.args[0]))
    if not _can_manage_poll(sheet, update.effective_user.id):
        await update.message.reply_text("Poll not found, or you do not manage it.")
        return

    options = json.loads(sheet["options"])
    if sheet["is_closed"]:
        text = f"*CLOSED*\n\n{format_signup_summary(sheet['id'], sheet['title'], sheet['details'], options)}"
    else:
        text = format_signup_card(sheet["id"], sheet["title"], sheet["details"], options)

    await update.message.reply_text(
        text,
        reply_markup=_poll_keyboard(sheet, options),
        parse_mode="Markdown",
    )


async def headcount_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("Usage: /headcount <sheet_id>")
        return

    sheet = get_signup_sheet(int(ctx.args[0]))
    if not sheet:
        await update.message.reply_text("Sign-up sheet not found.")
        return
    if sheet["chat_id"] != update.effective_chat.id and not _can_manage_poll(sheet, update.effective_user.id):
        await update.message.reply_text("That sign-up sheet is not available in this chat.")
        return

    options = json.loads(sheet["options"])
    await update.message.reply_text(
        format_signup_summary(sheet["id"], sheet["title"], sheet["details"], options),
        parse_mode="Markdown",
    )


async def deletepoll_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("Usage: /deletepoll <poll_id>")
        return

    sheet = get_signup_sheet(int(ctx.args[0]))
    if not _can_manage_poll(sheet, update.effective_user.id):
        await update.message.reply_text("Poll not found, or you do not manage it.")
        return

    delete_signup_sheet(sheet["id"])
    await update.message.reply_text(f"Poll #{sheet['id']} deleted.")


async def inline_poll_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    search = (query.query or "").strip().lower()
    polls = get_signup_sheets_by_creator(query.from_user.id, entity_type="poll", limit=50)

    if search:
        polls = [
            poll for poll in polls
            if search in str(poll["id"]) or search in (poll["title"] or "").lower()
        ]

    results = []
    for poll in polls[:20]:
        options = json.loads(poll["options"])
        if poll["is_closed"]:
            text = f"*CLOSED*\n\n{format_signup_summary(poll['id'], poll['title'], poll['details'], options)}"
        else:
            text = format_signup_card(poll["id"], poll["title"], poll["details"], options)

        description = " / ".join(options[:4])
        if len(options) > 4:
            description += " / ..."

        results.append(
            InlineQueryResultArticle(
                id=f"poll-{poll['id']}",
                title=poll["title"],
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode="Markdown",
                ),
                reply_markup=_poll_vote_keyboard(poll, options),
            )
        )

    await query.answer(results, cache_time=0, is_personal=True)


async def cancel_poll(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.pop("poll_title", None)
    ctx.user_data.pop("poll_options", None)
    await update.message.reply_text("Poll creation cancelled.")
    return ConversationHandler.END


poll_conv = ConversationHandler(
    entry_points=[CommandHandler("newpoll", newpoll_start)],
    states={
        POLL_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, poll_title)],
        POLL_OPTIONS: [
            CommandHandler("done", finish_poll),
            MessageHandler(filters.TEXT & ~filters.COMMAND, poll_option),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_poll)],
)
