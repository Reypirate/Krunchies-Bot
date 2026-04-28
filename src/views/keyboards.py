from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_signup_keyboard(
    sheet_id,
    options,
    include_close=True,
    include_delete=False,
    is_closed=False,
    publish_query=None,
):
    keyboard = []

    if publish_query is not None:
        keyboard.append([InlineKeyboardButton("Publish poll", switch_inline_query=str(publish_query))])

    if not is_closed:
        # Keep callback data compact; Telegram limits it to 64 bytes.
        for index, option in enumerate(options):
            keyboard.append([InlineKeyboardButton(option, callback_data=f"signup:{sheet_id}:{index}")])

    controls = []
    if include_close:
        action = "reopen" if is_closed else "close"
        label = "Reopen (Admin/Owner)" if is_closed else "Close (Admin/Owner)"
        controls.append(InlineKeyboardButton(label, callback_data=f"{action}:{sheet_id}"))
    if include_delete:
        controls.append(InlineKeyboardButton("Delete (Owner)", callback_data=f"delete:{sheet_id}"))
    if controls:
        keyboard.append(controls)

    return InlineKeyboardMarkup(keyboard)
