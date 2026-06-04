#!/usr/bin/env python3
"""
bot_polling.py — Always-on Telegram polling bot.

Runs a getUpdates loop every POLL_INTERVAL seconds.
Routes incoming messages to daily_report.analyze() and replies.

Deploy on Railway / Render for 24x7 operation.
Run locally:  python bot_polling.py
"""

import os
import sys
import time
import traceback
import requests

from daily_report import analyze, send_telegram

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
POLL_INTERVAL  = 3   # seconds between getUpdates calls

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

HELP_TEXT = """*Indian Stock Market Bot* 🇮🇳📈

Available commands:
• /report — Full daily report (10 stocks + macro)
• /quick  — Top 5 picks with entry/target/stop
• /macro  — Macro summary only (Nifty, crude, FII/DII)
• /sector — Sector rotation theme of the week
• /help   — Show this message

Or just type any question and I'll answer as your personal equity analyst!

_Examples:_
• "Is HDFC Bank a buy right now?"
• "Best pharma stocks for next month"
• "Explain the current FII selling"
"""


def get_updates(offset: int | None) -> list[dict]:
    params: dict = {"timeout": 20, "allowed_updates": ["message"]}
    if offset is not None:
        params["offset"] = offset
    resp = requests.get(f"{TELEGRAM_API}/getUpdates", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("result", [])


def send_typing(chat_id: str | int) -> None:
    """Show 'typing…' indicator while Claude thinks."""
    try:
        requests.post(
            f"{TELEGRAM_API}/sendChatAction",
            json={"chat_id": chat_id, "action": "typing"},
            timeout=10,
        )
    except Exception:
        pass


def handle_message(message: dict) -> None:
    chat_id  = message["chat"]["id"]
    text     = message.get("text", "").strip()
    username = message.get("from", {}).get("username", "unknown")

    print(f"[{username}] {chat_id}: {text!r}")

    if not text:
        return

    if text.lower() in ("/start", "/help"):
        send_telegram(HELP_TEXT, chat_id=str(chat_id))
        return

    send_typing(chat_id)

    try:
        reply = analyze(text)
    except Exception as exc:
        traceback.print_exc()
        reply = f"❌ Error generating analysis: {exc}\n\nPlease try again in a moment."

    send_telegram(reply, chat_id=str(chat_id))


def main() -> None:
    print("Bot polling started. Ctrl+C to stop.")
    offset: int | None = None

    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update:
                    handle_message(update["message"])

        except requests.exceptions.ConnectionError:
            print("Network error — retrying in 10 s…")
            time.sleep(10)
            continue

        except requests.exceptions.HTTPError as exc:
            print(f"HTTP error: {exc} — retrying in 15 s…")
            time.sleep(15)
            continue

        except KeyboardInterrupt:
            print("\nStopped by user.")
            sys.exit(0)

        except Exception:
            traceback.print_exc()
            print("Unexpected error — retrying in 5 s…")
            time.sleep(5)
            continue

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
