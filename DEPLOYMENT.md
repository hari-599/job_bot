# Free scheduled job alerts with GitHub Actions

The workflow at `.github/workflows/jobbot.yml` scans for jobs approximately
every 10 minutes. GitHub-hosted runners are free for public repositories.
Scheduled runs are best-effort and may be delayed; this is not a guaranteed
always-on service.

## Set up Telegram secrets

In the repository, open **Settings > Secrets and variables > Actions** and add:

- `TELEGRAM_BOT_TOKEN`: your Telegram bot token.
- `OWNER_ID`: your numeric Telegram user ID. Send `/start` to the bot once so
  it is allowed to message you.

Enable the **jobbot** workflow under **Actions** and run it once with **Run
workflow** to test it. It will then run on its schedule.

GitHub Actions cache is used to remember previously seen jobs. It is
best-effort, not a database backup; if the cache is removed, some jobs may be
reported again.

## Keep credentials private

`.gitignore` excludes `.env`, the local Python environment, cache files, and
the local SQLite database. Keep these exclusions so local credentials and data
are not committed. Do not put tokens or other credentials in the repository.
If a Telegram token has been shared, revoke it with `@BotFather` and update the
Actions secret with the replacement.
