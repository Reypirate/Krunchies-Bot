import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_TIMEZONE = "Asia/Singapore"


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
