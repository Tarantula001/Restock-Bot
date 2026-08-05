# FirstCry restock notifier (v2)

Watches FirstCry product pages and pings you on Telegram the moment
something goes from out-of-stock to in-stock.

**v2 changes:** the old version checked raw page text, which caused false
"out of stock" alerts (FirstCry hides a "Notify Me" template in every
product page's HTML, in stock or not). v2 uses a real headless browser
(Playwright) and checks whether the "ADD TO CART" button is actually
visible — a much more reliable signal. This also fixes the "runs every
2+ hours instead of every 15 minutes" problem by no longer depending on
GitHub's own scheduler (see Section C).

## A. Test it locally

```
pip install -r requirements.txt
playwright install chromium
```

Edit `watchlist.json` with real FirstCry product URLs (copy the pattern —
each entry is a `{ "name": ..., "url": ... }` block, comma-separated, no
comma after the last one).

Run once:
```
python bot.py
```

You should see accurate in-stock/out-of-stock lines per product.

## B. Telegram alerts

(Same as before — skip if you already did this.)

1. Message **@BotFather** on Telegram, send `/newbot`, follow the prompts,
   save the token it gives you.
2. Open a chat with your new bot and send it any message first.
3. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser —
   find `"chat":{"id":...}` — that number is your chat ID.
4. Test locally:
   ```
   $env:TELEGRAM_BOT_TOKEN="your-token"
   $env:TELEGRAM_CHAT_ID="your-chat-id"
   python bot.py
   ```

## C. Reliable scheduling (important — read this)

GitHub's built-in `schedule:` cron trigger is best-effort only — it can be
delayed by hours, especially on repos without much other Actions
activity. This is a widely reported GitHub limitation, not something
specific to your setup. The workaround: use a free external service to
trigger the workflow on a real schedule via GitHub's API, instead of
relying on GitHub's own clock.

**1. Create a GitHub token** so an outside service is allowed to trigger
your workflow:
   - Go to github.com → your profile photo (top right) → **Settings**
   - Left sidebar, scroll down → **Developer settings**
   - **Personal access tokens** → **Fine-grained tokens** → **Generate new token**
   - Give it a name like `restock-bot-trigger`
   - Under **Repository access**, choose "Only select repositories" → pick `restock-bot`
   - Under **Permissions** → **Repository permissions**, find **Actions** → set to **Read and write**
   - Generate it, and **copy the token immediately** (starts with `github_pat_...`) — you won't see it again.

**2. Set up cron-job.org**
   - Go to cron-job.org, create a free account.
   - Click **Create cronjob**.
   - **Title**: `restock-bot trigger`
   - **URL**:
     ```
     https://api.github.com/repos/Tarantula001/restock-bot/actions/workflows/check-stock.yml/dispatches
     ```
   - **Schedule**: every 60 minutes (matches the free-minutes budget from earlier — you can go lower later if you switch the repo to public)
   - Under **Advanced** (or "Request method/headers" section):
     - Request method: **POST**
     - Add these headers:
       - `Authorization` → `Bearer <your token from step 1>`
       - `Accept` → `application/vnd.github+json`
       - `Content-Type` → `application/json`
     - Request body:
       ```
       {"ref":"main"}
       ```
   - Save.

**3. Test it**: on the cron-job.org job page, there's usually a "Run now" /
   "Execute" button — click it, then check your GitHub repo's Actions tab.
   A new run should appear within seconds, labeled as triggered by
   `workflow_dispatch`. Check Telegram too if anything's in stock.

From here it runs on its own, reliably, on the schedule you set in
cron-job.org — not GitHub's flaky internal clock.

## Cost note

Every run — whether triggered by cron-job.org or GitHub's own scheduler —
uses the same GitHub Actions minutes. A private repo gets ~2,000 free
minutes/month; a public repo gets unlimited. With the real-browser check,
hourly runs should land safely inside the free private-repo budget, but
actual cost depends on your watchlist size. Check real usage anytime:
github.com → profile photo → **Settings** → **Billing and plans** →
**Actions minutes**.

## Verifying detection

The "ADD TO CART" text check should be far more reliable than v1's text
search, but if you ever see a product misreported, check the run's logs
(Actions tab → the run → "Run stock check" step) — it'll tell you exactly
what it saw.
