"""
FirstCry restock notifier.

Checks each product URL in watchlist.json. When a product that was
previously out of stock becomes available, sends a Telegram message.

Setup:
    1. pip install -r requirements.txt
    2. Fill in watchlist.json with real product URLs
    3. Set the TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment
       variables (see README.md for how to get these)
    4. Run: python bot.py
       (runs once and exits — see README.md for how to run it on a
       schedule so it works while you're away)
"""

import json
import os
import sys
import time
import requests
from bs4 import BeautifulSoup

WATCHLIST_FILE = "watchlist.json"
STATE_FILE = "state.json"  # remembers last known stock status per product, so you're not re-notified every run

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# Phrases FirstCry shows on an out-of-stock product page. If a page contains
# any of these, we treat the product as OUT of stock. Otherwise, in stock.
#
# IMPORTANT: verify this against a real out-of-stock FirstCry product page
# before relying on this bot — open one in your browser, view page source
# (Ctrl+U), and search for the actual out-of-stock text/button so you can
# confirm or adjust this list. Site markup changes over time.
OUT_OF_STOCK_MARKERS = [
    "notify me",
    "would be notified by email",
    "out of stock",
    "currently unavailable",
    "sold out",
]


def load_watchlist():
    with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("products", [])


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def check_stock(url: str) -> bool:
    """Returns True if the product looks in-stock, False if out-of-stock."""
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    text = resp.text.lower()
    for marker in OUT_OF_STOCK_MARKERS:
        if marker in text:
            return False
    return True


def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured — printing instead:")
        print(message)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to send Telegram message: {e}")


def main():
    products = load_watchlist()
    if not products:
        print("watchlist.json has no products yet — add some and re-run.")
        sys.exit(1)

    state = load_state()

    for product in products:
        name = product["name"]
        url = product["url"]

        if "PASTE-PRODUCT-URL-HERE" in url:
            print(f"Skipping '{name}' — placeholder URL not filled in yet.")
            continue

        try:
            in_stock = check_stock(url)
        except requests.RequestException as e:
            print(f"Could not check '{name}': {e}")
            continue

        was_in_stock = state.get(url, {}).get("in_stock", False)

        if in_stock and not was_in_stock:
            msg = f"IN STOCK: {name}\n{url}"
            print(msg)
            send_telegram(msg)
        else:
            print(f"{name}: {'in stock' if in_stock else 'out of stock'} (no change)")

        state[url] = {"in_stock": in_stock, "checked_at": time.time()}

    save_state(state)


if __name__ == "__main__":
    main()
