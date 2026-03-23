"""Registration Listener — handles /start and /stop commands via Telegram polling."""

import json
import os
import time
import threading

import requests

from config import SUBSCRIBERS_PATH
from utils.logger import get_logger

logger = get_logger("registration")

TELEGRAM_API = "https://api.telegram.org/bot{token}"


def _load_subscribers() -> dict:
    """Load subscribers from JSON file."""
    if os.path.exists(SUBSCRIBERS_PATH):
        with open(SUBSCRIBERS_PATH, "r") as f:
            return json.load(f)
    return {}


def _save_subscribers(subs: dict):
    """Save subscribers to JSON file."""
    os.makedirs(os.path.dirname(SUBSCRIBERS_PATH), exist_ok=True)
    with open(SUBSCRIBERS_PATH, "w") as f:
        json.dump(subs, f, indent=2)


def _send_reply(token: str, chat_id: int, text: str):
    """Send a plain-text reply to a chat."""
    url = f"{TELEGRAM_API.format(token=token)}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
    }, timeout=15)


class RegistrationListener:
    """Polls Telegram for /start and /stop commands to manage subscribers."""

    def __init__(self):
        self.token = os.environ["TELEGRAM_BOT_TOKEN"]
        self.base_url = TELEGRAM_API.format(token=self.token)
        self.offset = 0
        self._stop_event = threading.Event()

    def run(self):
        """Start polling for updates (blocking — run in a thread)."""
        logger.info("Registration listener started")
        while not self._stop_event.is_set():
            try:
                self._poll()
            except Exception as e:
                logger.error("Polling error: %s", e)
                time.sleep(5)

    def stop(self):
        """Signal the listener to stop."""
        self._stop_event.set()

    def _poll(self):
        """Fetch and process new updates."""
        url = f"{self.base_url}/getUpdates"
        params = {"offset": self.offset, "timeout": 30, "allowed_updates": ["message"]}
        resp = requests.get(url, params=params, timeout=35)

        if not resp.ok:
            time.sleep(2)
            return

        updates = resp.json().get("result", [])
        for update in updates:
            self.offset = update["update_id"] + 1
            self._handle_update(update)

    def _handle_update(self, update: dict):
        """Process a single update for /start or /stop commands."""
        message = update.get("message", {})
        text = message.get("text", "").strip()
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        first_name = chat.get("first_name", "")

        if not chat_id or not text:
            return

        if text == "/start":
            self._register(chat_id, first_name)
        elif text == "/stop":
            self._unregister(chat_id, first_name)

    def _register(self, chat_id: int, name: str):
        """Add a subscriber."""
        subs = _load_subscribers()
        key = str(chat_id)

        if key in subs:
            _send_reply(self.token, chat_id,
                        f"You're already subscribed, {name}! "
                        "You'll receive the daily Alpha Briefing every morning at 06:00 CST.\n\n"
                        "Send /stop to unsubscribe.")
            logger.info("Already registered: %s (%s)", key, name)
            return

        subs[key] = {"name": name, "registered": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}
        _save_subscribers(subs)

        _send_reply(self.token, chat_id,
                    f"Welcome, {name}! You're now subscribed to the Schelle Investor Bot.\n\n"
                    "You'll receive a daily Alpha Briefing every morning at 06:00 CST with:\n"
                    "- Macro outlook & Fed sentiment\n"
                    "- Stock picks with scores\n"
                    "- Market sentiment signals\n"
                    "- Paper portfolio performance vs S&P 500\n\n"
                    "Send /stop to unsubscribe at any time.")
        logger.info("New subscriber: %s (%s)", key, name)

    def _unregister(self, chat_id: int, name: str):
        """Remove a subscriber."""
        subs = _load_subscribers()
        key = str(chat_id)

        if key not in subs:
            _send_reply(self.token, chat_id,
                        "You're not currently subscribed. Send /start to sign up.")
            return

        del subs[key]
        _save_subscribers(subs)

        _send_reply(self.token, chat_id,
                    f"You've been unsubscribed, {name}. "
                    "Send /start if you'd like to rejoin.")
        logger.info("Unsubscribed: %s (%s)", key, name)
