import html
import re
import time
from collections import defaultdict
from telegram import Update
from telegram.ext import ContextTypes

# ── Rate Limiting ─────────────────────────────────────
# Simple in-memory store for rate limiting: {user_id: [timestamps]}
_user_calls = defaultdict(list)
RATE_LIMIT = 5  # Max 5 calls
TIME_WINDOW = 10  # per 10 seconds

def is_rate_limited(user_id: int) -> bool:
    now = time.time()
    # Filter out old timestamps
    _user_calls[user_id] = [t for t in _user_calls[user_id] if now - t < TIME_WINDOW]
    
    if len(_user_calls[user_id]) >= RATE_LIMIT:
        return True
    
    _user_calls[user_id].append(now)
    return False

# ── Input Sanitization ────────────────────────────────
def sanitize_text(text: str, max_length: int = 4000) -> str:
    """
    Strictly cleans user input to prevent injection and abuse.
    """
    if not text:
        return ""
        
    # 1. Truncate to prevent memory exhaustion
    text = text[:max_length]
    
    # 2. Escape HTML tags (even though we use Markdown, safety first)
    text = html.escape(text)
    
    # 3. Strip potentially harmful control characters
    text = "".join(ch for ch in text if ch.isprintable())
    
    return text.strip()

def validate_username(username: str) -> str:
    """Ensures username follows Telegram format."""
    if not username:
        return ""
    # Only alphanumeric and underscores
    return "".join(re.findall(r"[a-zA-Z0-9_]+", username))

# ── SQL Injection Safety ─────────────────────────────
# Note: Always use parameterized queries (?). Never f-strings in SQL.
# This project uses sqlite3's native parameterization which is safe.
