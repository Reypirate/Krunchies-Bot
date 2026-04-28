from telegram.helpers import escape_markdown


def md(value) -> str:
    """Escape dynamic text before inserting it into Telegram Markdown."""
    if value is None:
        return ""
    return escape_markdown(str(value), version=1)


def mention(username) -> str:
    if not username:
        return "Unassigned"
    return f"@{md(str(username).lstrip('@'))}"
