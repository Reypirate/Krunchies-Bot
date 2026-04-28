import os
import logging
from dotenv import load_dotenv

# Load .env before importing modules that read environment variables.
load_dotenv()

from telegram.ext import ApplicationBuilder
from src.database import init_db
from src.handlers import register_handlers
from src.services.scheduler_service import setup_scheduler

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found in environment variables.")
        return

    # 1. Initialize Database
    init_db()

    # 2. Build Application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 3. Register Handlers
    register_handlers(app)

    # 4. Setup Scheduler
    setup_scheduler(app)

    # 5. Start Bot
    print("Krunchies Bot v2.0 (Professional Edition) is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
