# FirstCry restock notifier

Watches FirstCry product pages (LEGO, Hot Wheels, anything) and pings you
on Telegram the moment something goes from out-of-stock to in-stock.

## 1. Test it locally first

```
cd restock-bot
pip install -r requirements.txt
```

Open `watchlist.json` and replace the placeholder URLs with real FirstCry
product page URLs (open the product on firstcry.com, copy the URL — it
should end in `/product-detail`).

Run it once:

```
python bot.py
```

You should see each product printed as "in stock" or "out of stock". If a
product is wrongly detected, see the **Verify detection** section below
before relying on this.

## 2. Set up Telegram alerts (5 minutes)

1. In Telegram, message **@BotFather**, send `/newbot`, follow the prompts.
   You'll get a **bot token** that looks like `123456789:AAExample...`.
2. Send any message (e.g. "hi") to your new bot from your own account —
   Telegram bots can't message you until you've messaged them first.
3. Visit this URL in a browser (with your real token):
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Find `"chat":{"id":123456789,...}` in the response — that number is
   your **chat ID**.
4. Set both as environment variables and re-run:

   ```
   set TELEGRAM_BOT_TOKEN=123456789:AAExample...      (Windows cmd)
   set TELEGRAM_CHAT_ID=123456789
   python bot.py
   ```

   (On Mac/Linux use `export` instead of `set`.)

You should get a Telegram message for anything currently in stock the
first time you run it (since it has no prior state yet).

## 3. Make it run while you're away (free, no PC needed)

This is the part that covers "even when I'm not there":

1. Create a free GitHub account if you don't have one, and a **private**
   repo (private matters — don't make your watchlist public).
2. Push this whole folder to that repo.
3. In the repo: **Settings → Secrets and variables → Actions → New
   repository secret**. Add two secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Go to the **Actions** tab, enable workflows if prompted. The included
   workflow (`.github/workflows/check-stock.yml`) will now run
   automatically every 15 minutes, forever, for free — no computer of
   yours needs to be on.
5. You can trigger a manual test run any time from the Actions tab
   ("Run workflow" button) instead of waiting for the schedule.

To add or remove products later, just edit `watchlist.json` and push the
change — no need to touch the workflow.

## Verify detection before you trust it

I built the out-of-stock detection (`OUT_OF_STOCK_MARKERS` in `bot.py`)
based on FirstCry's out-of-stock "Notify Me" form text, but I haven't
loaded a real out-of-stock FirstCry product page to confirm the exact
wording still matches — sites change this over time. Before relying on
this:

1. Find a FirstCry product that's currently out of stock.
2. View page source (Ctrl+U in your browser) and search for whatever text
   appears near the "Notify Me" button.
3. Compare it against the list in `bot.py` and adjust if needed.

## A couple of things worth knowing

- **Polling interval**: 15 minutes is deliberately conservative to avoid
  hammering FirstCry's servers or tripping any bot-detection. You can
  lower the cron interval if you want faster alerts, but faster polling
  = higher chance of your requests getting rate-limited or blocked.
- **Pincode-dependent stock**: FirstCry shows availability based on a
  delivery pincode. This script checks the page as an anonymous visitor,
  so double check the product is actually deliverable to *you* before
  rushing to buy.
- **This only notifies — it doesn't buy anything.** You still complete
  checkout yourself, which sidesteps FirstCry's login/OTP/payment flow
  entirely (all of which would be a much bigger, more fragile project to
  automate).
