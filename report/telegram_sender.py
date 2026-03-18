"""Telegram Sender — delivers reports via Telegram Bot API."""

import os
import time

import requests

from utils.helpers import retry
from utils.logger import get_logger

logger = get_logger("telegram")

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramSender:
    def __init__(self):
        self.token = os.environ["TELEGRAM_BOT_TOKEN"]
        self.chat_id = os.environ["TELEGRAM_CHAT_ID"]
        self.url = TELEGRAM_API.format(token=self.token)

    def send(self, report_parts: list[str]):
        """Send multi-part report to Telegram."""
        logger.info("Sending %d message(s) to Telegram", len(report_parts))
        for i, part in enumerate(report_parts, 1):
            self._send_message(part)
            if i < len(report_parts):
                time.sleep(1)  # respect rate limits between messages
        logger.info("Report delivered successfully")

    def send_error_alert(self, error_msg: str):
        """Send a brief error notification."""
        text = f"*ALPHA ADVISORY ERROR*\n\n_{self._escape_basic(error_msg[:500])}_"
        try:
            self._send_message(text)
        except Exception as e:
            logger.error("Failed to send error alert: %s", e)

    @retry(max_attempts=3, delay=3.0)
    def _send_message(self, text: str):
        """Send a single message with retry logic."""
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True,
        }
        resp = requests.post(self.url, json=payload, timeout=30)

        if resp.status_code == 429:
            # Rate limited — wait and retry
            retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
            logger.warning("Rate limited, waiting %d seconds", retry_after)
            time.sleep(retry_after)
            raise Exception("Rate limited")

        if not resp.ok:
            logger.error("Telegram API error %d: %s", resp.status_code, resp.text[:300])
            # If MarkdownV2 fails, try without formatting
            if "can't parse entities" in resp.text.lower():
                logger.warning("Falling back to plain text")
                payload["parse_mode"] = ""
                resp2 = requests.post(self.url, json=payload, timeout=30)
                resp2.raise_for_status()
                return

        resp.raise_for_status()
        logger.debug("Message sent successfully")

    @staticmethod
    def _escape_basic(text: str) -> str:
        """Minimal escape for error messages."""
        for ch in "_*[]()~`>#+-=|{}.!":
            text = text.replace(ch, f"\\{ch}")
        return text
