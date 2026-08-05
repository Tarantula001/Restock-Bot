"""
FirstCry restock notifier (v2 - uses a real headless browser).

v1 checked raw page text for phrases like "notify me" — but FirstCry
includes that text in a hidden template on EVERY product page, in stock
or not, so v1 misfired constantly. This version actually renders the
page like a real browser and checks whether the "ADD TO CART" button is
genuinely visible, which is a much more reliable signal.

Setup:
    1. pip install -r requirements.txt
    2. playwright install chromium      <-- new one-time step, needed
       locally AND is handled automatically in the GitHub Actions workflow
    3. Fill in watchlist.json with real product URLs
    4. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables
    5. Run: python bot.py
"""

import json
import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

WATCHLIST_FILE = "watchlist.json"
STATE_FILE = "state.json"  # remembers last known stock status so you're only notified on a change

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


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


def check_stock(page, url: str) -> bool:
    """Loads the page in a real browser and checks if ADD TO CART is visible."""
    page.goto(url, timeout=30000, wait_until="domcontentloaded")
    # Give client-side JS a moment to finish rendering the buy box.
    page.wait_for_timeout(2000)

    locator = page.get_by_text("ADD TO CART", exact=False)
    count = locator.count()
    for i in range(count):
        try:
            if locator.nth(i).is_visible():
                return True
        except Exception:
            continue
    return False


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

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=USER_AGENT)

        for product in products:
            name = product["name"]
            url = product["url"]

            if "PASTE-PRODUCT-URL-HERE" in url:
                print(f"Skipping '{name}' — placeholder URL not filled in yet.")
                continue

            try:
                in_stock = check_stock(page, url)
            except Exception as e:
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

        browser.close()

    save_state(state)


if __name__ == "__main__":
    main()
