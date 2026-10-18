# Run the Telegram bot for free on Windows

This runs the bot on your own PC; there is no hosting service or hosting bill.
The PC must stay on, awake, and connected to the internet. The bot stops while
the PC is shut down, asleep, or offline.

## 1. Prepare the PC

Install Python 3 if it is not already installed. Open PowerShell in this project
folder and install the bot's dependencies:

```powershell
py -3 -m pip install -r requirements.txt
```

Keep the existing `.env` file in the project folder. Do not share it or commit
it to a repository. If its Telegram token has been shared outside your device,
revoke it with `@BotFather` and replace it in `.env` before starting the bot.

## 2. Test the bot

Run the bot from PowerShell:

```powershell
py -3 bot.py
```

Leave that window open to keep it running. Press Ctrl+C to stop it. In Telegram,
send `/start` to the bot from the account configured by `OWNER_ID`.

## 3. Start it automatically when you sign in

After stopping any manually running copy of the bot, run this once in
PowerShell from the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows_startup.ps1
```

This creates and starts a Task Scheduler task for your Windows account. It will
start the bot when you sign in and restart it after a failure. You can inspect
or stop it in Task Scheduler under **Task Scheduler Library > JobScannerBot**.

To stop automatic startup, open PowerShell and run:

```powershell
Unregister-ScheduledTask -TaskName JobScannerBot -Confirm:$false
```

The SQLite database remains in this project folder as `jobbot.db`. Back it up
if you want to preserve the bot's job history.
