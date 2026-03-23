"""
Project Alpha: Advisory — Daily Investment Advisory System
==========================================================
Advisory Only — No Real Trades
Generates daily recommendations for a $50,000 paper portfolio
and delivers them via Telegram at 06:00 CST (UTC+8).

Usage:
    python main.py              # Start scheduler (runs daily at 06:00 CST)
    python main.py --run-now    # Run pipeline immediately (for testing)
"""

import argparse
import os
import sys

from dotenv import load_dotenv

# Load environment variables before any other imports
load_dotenv()

from config import WATCHLIST, DB_PATH
from modules.macro_scout import MacroScout
from modules.value_hunter import ValueHunter
from modules.sentiment_engine import SentimentEngine
from modules.registration_listener import RegistrationListener
from portfolio.manager import PortfolioManager
from report.builder import ReportBuilder
from report.telegram_sender import TelegramSender
from utils.logger import get_logger

logger = get_logger("main")


def run_daily_pipeline():
    """Execute the full advisory pipeline: analyze → recommend → report → deliver."""
    logger.info("=" * 50)
    logger.info("Starting daily advisory pipeline")
    logger.info("=" * 50)

    pm = PortfolioManager(DB_PATH)
    sender = TelegramSender()

    try:
        # 1. Macro analysis
        logger.info("[1/6] Running Macro Scout...")
        try:
            macro_data = MacroScout().analyze()
        except Exception as e:
            logger.error("Macro Scout failed: %s", e)
            macro_data = {
                "fed_sentiment": "N/A", "fed_detail": "Data unavailable",
                "key_events": [], "risk_level": "N/A",
                "macro_summary": "Macro data unavailable.", "fred_data": {},
            }

        # 2. Fundamental screening
        logger.info("[2/6] Running Value Hunter...")
        try:
            stock_picks = ValueHunter().scan(WATCHLIST)
        except Exception as e:
            logger.error("Value Hunter failed: %s", e)
            stock_picks = []

        # 3. Sentiment analysis
        logger.info("[3/6] Running Sentiment Engine...")
        try:
            sentiment_data = SentimentEngine().analyze(WATCHLIST)
        except Exception as e:
            logger.error("Sentiment Engine failed: %s", e)
            sentiment_data = {
                "ticker_sentiments": {}, "supply_chain_alerts": [],
                "overall_market_mood": "N/A",
            }

        # 4. Update paper portfolio
        logger.info("[4/6] Updating paper portfolio...")
        pm.apply_recommendations(stock_picks)

        # 5. Build report
        logger.info("[5/6] Building report...")
        snapshot = pm.get_snapshot()
        performance = pm.get_performance_vs_spy()
        report_parts = ReportBuilder().build(
            macro_data, stock_picks, sentiment_data, snapshot, performance
        )

        # 6. Deliver via Telegram
        logger.info("[6/6] Sending via Telegram...")
        sender.send(report_parts)

        # Save daily snapshot for tracking
        pm.save_daily_snapshot()

        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        try:
            sender.send_error_alert(str(e))
        except Exception:
            logger.error("Could not send error alert to Telegram")


def main():
    parser = argparse.ArgumentParser(description="Project Alpha: Advisory")
    parser.add_argument(
        "--run-now", action="store_true",
        help="Run the pipeline immediately instead of waiting for schedule",
    )
    args = parser.parse_args()

    # Validate required env vars
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)
    if not os.environ.get("TELEGRAM_CHAT_ID") or os.environ["TELEGRAM_CHAT_ID"] == "REPLACE_WITH_YOUR_NUMERIC_CHAT_ID":
        print("ERROR: TELEGRAM_CHAT_ID not set in .env")
        print("To get your chat ID:")
        print("  1. Message your bot on Telegram")
        print(f"  2. Visit: https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN', 'TOKEN')}/getUpdates")
        print("  3. Look for \"chat\":{\"id\": YOUR_NUMERIC_ID }")
        sys.exit(1)

    # Initialize database
    pm = PortfolioManager(DB_PATH)
    pm.init_db()

    # Start registration listener in background thread
    import threading
    listener = RegistrationListener()
    listener_thread = threading.Thread(target=listener.run, daemon=True)
    listener_thread.start()
    logger.info("Registration listener running in background (/start, /stop)")

    if args.run_now:
        logger.info("Running pipeline immediately (--run-now)")
        run_daily_pipeline()
    else:
        # Scheduled mode
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BlockingScheduler(timezone="Asia/Shanghai")
        scheduler.add_job(
            run_daily_pipeline,
            CronTrigger(hour=6, minute=0),
            id="daily_advisory",
            name="Daily Investment Advisory Report",
            misfire_grace_time=3600,
            max_instances=1,
        )
        logger.info("Scheduler started — next report at 06:00 CST daily")
        logger.info("Press Ctrl+C to stop")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            listener.stop()
            logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
