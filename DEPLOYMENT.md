# Run job alerts for free

## Option 1: GitHub Actions

GitHub Actions can run a one-shot job scan on a schedule without keeping a
server online. Scheduled runs are **best effort**: GitHub may delay them during
busy periods, so this is not a guaranteed always-on service.

Standard GitHub-hosted runners are free for public repositories. Private
repositories use the account's monthly Actions minutes allowance; excess use
may be billed. To avoid hosting charges, use a public repository only if you
are comfortable making the source code public, or use the Windows option
below. Never put bot tokens or other credentials in the repository.

1. Push the project to GitHub. The workflow must be on the repository's
   default branch at `.github/workflows/jobbot.yml`.
2. In **Settings > Secrets and variables > Actions**, add repository secrets:
   - `TELEGRAM_BOT_TOKEN`: your Telegram bot token.
   - `OWNER_ID`: your numeric Telegram user ID. Send `/start` to the bot once
     so it is allowed to message you.
   - Optional: `DISCORD_WEBHOOK_URL`, `RAPIDAPI_KEY`, `IMAP_USER`, and
     `IMAP_PASSWORD`.
3. In the repository's **Actions** tab, enable workflows if prompted. Run
   **jobbot** once with **Run workflow** to test it; otherwise it is scheduled
   approximately every 10 minutes.

The workflow caches `jobbot.db` between runs to reduce duplicate alerts. GitHub
Actions cache is best-effort storage, not a database backup; if the cache is
removed, previously seen jobs may be reported again. The workflow prints only
the number of matches, not job details.

## Option 2: Run on your Windows PC

This option has no hosting charge and keeps the job database on your PC, but
the PC must stay on, awake, and connected to the internet. The bot stops while
the PC is shut down, asleep, or offline.

Install Python 3 if needed, then open PowerShell in the project folder:

```powershell
py -3 -m pip install -r requirements.txt
py -3 bot.py
```

Leave the window open to keep the bot running. Press Ctrl+C to stop it. In
Telegram, send `/start` to the bot from the account configured by `OWNER_ID`.

To start the bot automatically when you sign in, stop any manually running
copy, then run this once from the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows_startup.ps1
```

Remove the startup task with:

```powershell
Unregister-ScheduledTask -TaskName JobScannerBot -Confirm:$false
```

The local SQLite database is `jobbot.db`. Back it up if you want to preserve
the bot's job history.

## Keep credentials private

The local `.env` file is excluded from Git. Do not commit or share it. If the
Telegram token has been shared outside your device, revoke it with
`@BotFather` and replace it in your local `.env` or GitHub Actions secrets.
