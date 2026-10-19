"""One-shot runner for GitHub Actions: check once, send Telegram messages, exit."""
import html, os
from datetime import datetime, timedelta

import requests

import core

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT = os.environ.get("OWNER_ID")          # your Telegram user id (press Start on your bot once first)


def send(text):
    if TOKEN and CHAT:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", timeout=20,
                          data={"chat_id": CHAT, "text": text, "parse_mode": "HTML",
                                "disable_web_page_preview": "true"})
        r.raise_for_status()
        if not r.json().get("ok"):
            raise RuntimeError("Telegram rejected the message")
def card(j):
    e = html.escape
    return (f"🆕 <b>{e(j['title'])}</b>\n🏢 {e(j['company'])}\n📍 {e(j['location'] or 'India')}\n"
            f"🎯 Experience: {e(j['tag'])}\n🔎 {e(j['source'])}\n<a href=\"{e(j['url'])}\">Open &amp; apply</a>")


def main():
    if not TOKEN or not CHAT:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN and OWNER_ID in GitHub Actions secrets")

    manual_run = os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"
    core.kv_set("strict", os.getenv("STRICT", "1"))
    jobs = core.run_cycle()
    print(f"new matches: {len(jobs)}")
    if len(jobs) > 8:
        for i in range(0, len(jobs), 8):
            send("🆕 New matches\n\n" + "\n".join(
                f"• <b>{html.escape(j['title'])}</b> — {html.escape(j['company'])} ({html.escape(j['tag'])})\n"
                f"  {html.escape(j['url'])}" for j in jobs[i:i + 8]))
    else:
        for j in jobs:
            send(card(j))
    if manual_run:
        send(f"✅ Job scan complete. {len(jobs)} new match(es).")
    # daily health report so broken company slugs don't fail silently
    last = core.kv_get("health_ts")
    if not last or datetime.now() - datetime.fromisoformat(last) > timedelta(hours=24):
        core.kv_set("health_ts", datetime.now().isoformat())
        bad = [f"❌ {k}: {v}" for k, v in sorted(core.HEALTH.items()) if v.startswith("ERR")]
        if bad:
            send("⚠️ Sources failing (fix slugs in companies.py):\n" + "\n".join(bad[:25]))


if __name__ == "__main__":
    main()
