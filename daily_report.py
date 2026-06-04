#!/usr/bin/env python3
"""
Indian Stock Market Telegram Bot — daily_report.py

MODE A: Scheduled run (python daily_report.py)
  → Calls Anthropic API, sends daily report to CHAT_ID

MODE B: Single-message webhook (python daily_report.py --webhook <chat_id> <text>)
  → Used internally by bot_polling.py to reply to a specific user message
"""

import os
import sys
import argparse
from datetime import datetime
import requests

# ── env ──────────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
TELEGRAM_TOKEN     = os.environ["TELEGRAM_TOKEN"]
CHAT_ID            = os.environ["CHAT_ID"]          # default / owner chat

MODEL      = "anthropic/claude-haiku-4-5"   # cheap & fast; swap to anthropic/claude-opus-4 for best quality
MAX_TOKENS = 2000

# ── prompts ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an elite Indian equity analyst, thinking like a
top-tier fund manager (Dolat Capital / Marcellus / Motilal Oswal PMS-tier
rigour) but speaking plainly and practically to a swing trader with a
weeks-to-months horizon.

Core rules:
• Sector first, stock second — smart money rotates before retail notices.
• Every trade needs entry, target, and stop-loss. No exceptions.
• Prefer NSE stocks with avg daily volume >5 lakh shares or >₹5 Cr turnover.
• Use ₹ for prices. Reference NSE ticker codes.
• Be direct. Give a view. Never hedge everything."""


def _full_report_prompt() -> str:
    today = datetime.now().strftime("%A, %d %B %Y")
    return f"""Today is {today}.

Generate a complete daily Indian stock market swing-trade report with the
following sections:

---
## 📊 MACRO SUMMARY
- Nifty 50 trend & key levels (support / resistance)
- Crude oil price & direction
- FII / DII net flow (latest available)
- USD/INR outlook
- Key events this week (RBI, earnings, global data)
- India VIX reading

---
## 🔟 TODAY'S TOP 10 SWING TRADE IDEAS

For each stock provide:
| Field | Detail |
|---|---|
| **Ticker** | NSE symbol |
| **Sector** | |
| **CMP Zone** | Approx price range |
| **Why on Radar** | 1–2 line thesis |
| **Entry Zone** | ₹ range |
| **Target** | ₹ (% upside) |
| **Stop Loss** | ₹ (% risk) |
| **R:R Ratio** | 1 : X |
| **Timeframe** | weeks / months |

Cover a mix of large-cap, mid-cap, and small-cap. Include at least one
defensive (pharma/FMCG) and one high-beta (PSU/infra) idea.

---
## ⚠️ KEY RISK OF THE DAY
One paragraph on the single biggest macro or market risk to watch today.

---
## 🔄 SECTOR ROTATION THEME OF THE WEEK
Which sector(s) are seeing institutional accumulation right now, and why.
Name 2–3 specific themes with supporting logic.

---
Keep the total response under 1900 tokens. Use Telegram-friendly formatting
(bold with *, no markdown tables — use plain text alignment instead)."""


def _quick_prompt() -> str:
    today = datetime.now().strftime("%d %b %Y")
    return f"""Today is {today}.

Give me the TOP 5 highest-conviction NSE swing trade ideas right now.
For each, one line only:
TICKER | Entry ₹ | Target ₹ | Stop ₹ | R:R | Why

Then a 2-line macro context at the end."""


def _macro_prompt() -> str:
    today = datetime.now().strftime("%d %b %Y")
    return f"""Today is {today}.

Give me a concise Indian market macro summary:
• Nifty 50 — trend, key levels, bias
• Crude oil — price, direction, impact
• FII / DII — net flow trend this week
• USD/INR — direction
• India VIX — fear level
• Top 2 events to watch this week

Keep it under 300 words. Be direct."""


def _sector_prompt() -> str:
    today = datetime.now().strftime("%d %b %Y")
    return f"""Today is {today}.

Sector rotation analysis for Indian markets this week:
1. Which 2–3 sectors are seeing smart-money accumulation? Why?
2. Which 1–2 sectors to avoid / reduce? Why?
3. One specific stock in each buy-sector as a representative play.
4. What macro catalyst is driving the rotation?

Keep it crisp — under 400 words."""


def _custom_prompt(user_text: str) -> str:
    today = datetime.now().strftime("%d %b %Y")
    return f"""Today is {today}.

User query: {user_text}

Answer as an elite Indian equity analyst focused on NSE/BSE swing trading.
Be direct, data-backed, and always state a clear view. If asking about a
specific stock, include entry / target / stop-loss."""


PROMPT_MAP = {
    "/report": _full_report_prompt,
    "/quick":  _quick_prompt,
    "/macro":  _macro_prompt,
    "/sector": _sector_prompt,
}

# ── core ──────────────────────────────────────────────────────────────────────
def analyze(user_input: str | None = None) -> str:
    """
    Core analysis function used by both modes.
    user_input=None → full scheduled report
    user_input=str  → command or free-text query
    """
    if user_input is None or user_input.strip() == "":
        prompt = _full_report_prompt()
    else:
        cmd = user_input.strip().split()[0].lower()
        if cmd in PROMPT_MAP:
            prompt = PROMPT_MAP[cmd]()
        else:
            prompt = _custom_prompt(user_input)

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ── telegram helpers ──────────────────────────────────────────────────────────
def send_telegram(text: str, chat_id: str = CHAT_ID) -> None:
    """Send text to a Telegram chat, splitting if >4096 chars."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    chunk_size = 4000
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    for chunk in chunks:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"},
            timeout=30,
        )
        resp.raise_for_status()


# ── entry points ──────────────────────────────────────────────────────────────
def run_scheduled():
    """MODE A — called by GitHub Actions cron."""
    print("Running scheduled daily report…")
    report = analyze()
    send_telegram(report)
    print("Report sent.")


def run_webhook(chat_id: str, user_text: str):
    """MODE B — called by bot_polling.py for each incoming message."""
    print(f"Webhook: chat_id={chat_id}, text={user_text!r}")
    reply = analyze(user_text)
    send_telegram(reply, chat_id=chat_id)
    print("Reply sent.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--webhook",
        nargs=2,
        metavar=("CHAT_ID", "TEXT"),
        help="Reply mode: pass chat_id and user message text",
    )
    args = parser.parse_args()

    if args.webhook:
        run_webhook(chat_id=args.webhook[0], user_text=args.webhook[1])
    else:
        run_scheduled()
