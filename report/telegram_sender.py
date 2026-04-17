"""Telegram Sender — delivers reports via Telegram Bot API."""

import html
import json
import os
import re
import time

import requests

from config import SUBSCRIBERS_PATH
from utils.helpers import retry
from utils.logger import get_logger

logger = get_logger("telegram")

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramSender:
    def __init__(self):
        self.token = os.environ["TELEGRAM_BOT_TOKEN"]
        raw = os.environ.get("TELEGRAM_CHAT_ID", "")
        env_ids = [cid.strip() for cid in raw.split(",") if cid.strip()]

        # Merge .env IDs with self-registered subscribers
        sub_ids = []
        if os.path.exists(SUBSCRIBERS_PATH):
            try:
                with open(SUBSCRIBERS_PATH, "r") as f:
                    subs = json.load(f)
                sub_ids = list(subs.keys())
            except Exception as e:
                logger.warning("Could not load subscribers file: %s", e)

        self.chat_ids = list(dict.fromkeys(env_ids + sub_ids))  # deduplicated, order preserved
        self.url = TELEGRAM_API.format(token=self.token)
        logger.info("Delivering to %d recipient(s) (%d env, %d subscribers)",
                     len(self.chat_ids), len(env_ids), len(sub_ids))

    def send(self, report_parts: list[str]):
        """Send multi-part report to all recipients."""
        logger.info("Sending %d message(s) to %d recipient(s)", len(report_parts), len(self.chat_ids))
        for chat_id in self.chat_ids:
            for i, part in enumerate(report_parts, 1):
                self._send_message(part, chat_id)
                if i < len(report_parts):
                    time.sleep(1)  # respect rate limits between messages
        logger.info("Report delivered successfully")

    def send_error_alert(self, error_msg: str):
        """Send a brief error notification to all recipients."""
        text = f"<b>ALPHA ADVISORY ERROR</b>\n\n<i>{html.escape(error_msg[:500])}</i>"
        for chat_id in self.chat_ids:
            try:
                self._send_message(text, chat_id)
            except Exception as e:
                logger.error("Failed to send error alert to %s: %s", chat_id, e)

    @retry(max_attempts=3, delay=3.0)
    def _send_message(self, text: str, chat_id: str):
        """Send a single message with retry logic."""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        resp = requests.post(self.url, json=payload, timeout=30)

        if resp.status_code == 429:
            retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
            logger.warning("Rate limited, waiting %d seconds", retry_after)
            time.sleep(retry_after)
            raise Exception("Rate limited")

        if not resp.ok:
            logger.error("Telegram API error %d: %s", resp.status_code, resp.text[:300])
            if "can't parse entities" in resp.text.lower():
                logger.warning("Falling back to plain text")
                payload["parse_mode"] = ""
                payload["text"] = re.sub(r"<[^>]+>", "", text)  # strip HTML tags
                resp2 = requests.post(self.url, json=payload, timeout=30)
                resp2.raise_for_status()
                return

        resp.raise_for_status()
        logger.debug("Message sent successfully")

