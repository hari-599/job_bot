# Keep the Telegram bot running

The bot uses Telegram long polling, so it does not need a public web port.
Choose one deployment option below.

## Deploy on Render

The included `render.yaml` defines a Docker background worker with a persistent
disk for the SQLite database. Render restarts the worker when it exits and
starts it again after deploys. A paid worker plan is required to keep a
background worker and its disk running continuously.

1. Push this project to a private GitHub repository. Do **not** add `.env`,
   `jobbot.db`, or `__pycache__`; `.gitignore` excludes them. `.dockerignore`
   also prevents them from entering the Docker build context.
2. In Render, create a Blueprint from that repository and apply the
   `render.yaml` configuration.
3. When prompted, enter `TELEGRAM_BOT_TOKEN` and `OWNER_ID` as environment
   values in Render. Do not commit the token or paste it into `render.yaml`.
4. Wait for the worker to deploy. In Telegram, send `/start` to the bot from
   the configured owner account to register the chat for job alerts.
5. Check the worker's logs in the Render dashboard. The database is stored on
   the mounted persistent disk at `/data/jobbot.db`.

If the token in your local `.env` has been shared outside your device, revoke
it with Telegram's `@BotFather` and use the replacement as the Render secret.
The bot token should be treated as a password.

## Deploy on a Linux VPS with systemd

systemd starts the bot at boot and restarts it if it exits unexpectedly.

### 1. Prepare the VPS

Install Python 3, venv support, and systemd (on Debian/Ubuntu):

```sh
sudo apt update
sudo apt install -y python3 python3-venv
```

Create a dedicated service account and application directory:

```sh
sudo useradd --system --home /opt/job-scanner --shell /usr/sbin/nologin job-scanner
sudo install -d -o root -g root -m 0755 /opt/job-scanner
```

Copy `bot.py`, `core.py`, `companies.py`, and `requirements.txt` into
`/opt/job-scanner`. Do **not** copy `.env`, `jobbot.db`, or `__pycache__` from
your development machine. The database will be created in systemd's persistent
state directory instead.

Install the Python dependencies:

```sh
sudo python3 -m venv /opt/job-scanner/.venv
sudo /opt/job-scanner/.venv/bin/pip install -r /opt/job-scanner/requirements.txt
```

### 2. Configure the bot securely

Revoke the existing bot token in Telegram's `@BotFather` and generate a new
one before deployment. Keep the new token private.

Create a protected environment file:

```sh
sudo install -d -o root -g job-scanner -m 0750 /etc/job-scanner
sudo install -o root -g job-scanner -m 0640 /dev/null /etc/job-scanner/job-scanner.env
sudoedit /etc/job-scanner/job-scanner.env
```

Add the new token and your Telegram numeric user ID:

```dotenv
TELEGRAM_BOT_TOKEN=your-new-token
OWNER_ID=your-telegram-user-id
POLL_MINUTES=10
```

Optional settings such as `DISCORD_WEBHOOK_URL`, `RAPIDAPI_KEY`,
`JSEARCH_EVERY_MIN`, `IMAP_USER`, and `IMAP_PASSWORD` can also be added there.

### 3. Install and start the service

From the project directory containing `deploy/job-scanner.service`:

```sh
sudo install -m 0644 deploy/job-scanner.service /etc/systemd/system/job-scanner.service
sudo systemctl daemon-reload
sudo systemctl enable --now job-scanner
```

In Telegram, send `/start` to the bot from the configured owner account to
register the chat for job alerts. Check service health and logs with:

```sh
sudo systemctl status job-scanner
sudo journalctl -u job-scanner -f
```

The SQLite database is stored at `/var/lib/job-scanner/jobbot.db` and survives
service restarts and VPS reboots. To apply code or environment changes, restart
the service:

```sh
sudo systemctl restart job-scanner
```
