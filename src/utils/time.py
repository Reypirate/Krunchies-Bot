import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import dateparser


DEFAULT_TIMEZONE = "Asia/Singapore"
STORED_FMT = "%Y-%m-%d %H:%M"
MAX_NATURAL_DATE_LENGTH = 120


def bot_timezone() -> ZoneInfo:
    timezone_name = os.getenv("BOT_TIMEZONE", DEFAULT_TIMEZONE)
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def now_local() -> datetime:
    # Stored dates are local naive strings, so compare using local naive time.
    return datetime.now(bot_timezone()).replace(tzinfo=None)


def now_local_str(fmt: str = "%Y-%m-%d %H:%M") -> str:
    return now_local().strftime(fmt)


def _parse_natural_date(text: str) -> datetime | None:
    cleaned = text.strip()[:MAX_NATURAL_DATE_LENGTH]
    if not cleaned:
        return None

    tz = bot_timezone()
    settings = {
        "PREFER_DATES_FROM": "future",
        "RETURN_AS_TIMEZONE_AWARE": False,
        "TIMEZONE": str(tz),
        "TO_TIMEZONE": str(tz),
    }
    return dateparser.parse(cleaned, settings=settings)


def friendly_date_hint() -> str:
    """Return a Markdown-safe hint for natural-language date prompts."""
    return (
        "Enter a date/time - you can type naturally:\n"
        "- `next wednesday 7pm`\n"
        "- `15 june 6pm`\n"
        "- `tomorrow 18:00`\n"
        "- `2026-06-15 18:00` (strict format also works)"
    )
