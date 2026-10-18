"""Telegram job bot. Run: python bot.py"""
import asyncio, html, logging, os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

load_dotenv()
import core  # noqa: E402  (after load_dotenv so env vars are visible)

logging.basicConfig(level=logging.INFO)
OWNER = int(os.getenv("OWNER_ID", "0"))          # your Telegram user id (get it from @userinfobot)
INTERVAL = int(os.getenv("POLL_MINUTES", "10")) * 60


def allowed(u: Update):
    return not OWNER or (u.effective_user and u.effective_user.id == OWNER)


def card(j):
    e = html.escape
    return (f"🆕 <b>{e(j['title'])}</b>\n🏢 {e(j['company'])}\n📍 {e(j['location'] or 'India')}\n"
            f"🎯 Experience: {e(j['tag'])}\n🔎 {e(j['source'])}\n<a href=\"{e(j['url'])}\">Open &amp; apply</a>")


def buttons(h):
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Applied", callback_data=f"applied:{h}"),
                                  InlineKeyboardButton("🙈 Skip", callback_data=f"skipped:{h}")]])


async def broadcast(bot, jobs):
    for cid in core.chats():
        if len(jobs) > 8:  # first run / burst: compact digest instead of spam
            for i in range(0, len(jobs), 8):
                lines = [f"• <b>{html.escape(j['title'])}</b> — {html.escape(j['company'])} "
                         f"({html.escape(j['tag'])})\n  {html.escape(j['url'])}" for j in jobs[i:i + 8]]
                await bot.send_message(cid, "🆕 New matches\n\n" + "\n".join(lines),
                                       parse_mode="HTML", disable_web_page_preview=True)
        else:
            for j in jobs:
                await bot.send_message(cid, card(j), parse_mode="HTML", reply_markup=buttons(j["h"]),
                                       disable_web_page_preview=True)
async def poll(ctx: ContextTypes.DEFAULT_TYPE):
    if core.kv_get("paused") == "1":
        return
    jobs = await asyncio.to_thread(core.run_cycle)
    if jobs:
        await broadcast(ctx.bot, jobs)


async def start(u: Update, c):
    if not allowed(u):
        return
    core.add_chat(u.effective_chat.id)
    await u.message.reply_text(
        "👋 Job bot is on. I check ~40 company portals every "
        f"{INTERVAL // 60} min and only ping roles needing ≤{core.MAX_MIN_YEARS} yrs experience in India.\n\n"
        "/latest – last 10 matches\n/status – source health\n/stats – counts\n"
        "/strict on|off – hide/show roles that don't state experience\n/pause /resume /checknow")


async def latest(u, c):
    if not allowed(u):
        return
    rows = core.latest(10)
    msg = "\n\n".join(f"<b>{html.escape(t)}</b> — {html.escape(co)}\n{html.escape(l or '')} · {html.escape(e)}\n{html.escape(url)}"
                      for t, co, l, url, e in rows) or "No matches yet."
    await u.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)


async def status(u, c):
    if not allowed(u):
        return
    bad = [f"❌ {k}: {v}" for k, v in sorted(core.HEALTH.items()) if v.startswith("ERR")]
    ok = sum(1 for v in core.HEALTH.values() if v.startswith("ok"))
    await u.message.reply_text(f"✅ {ok} sources OK, {len(bad)} failing\n" + "\n".join(bad[:25])
                               + ("\n\nFix failing slugs in companies.py" if bad else ""))


async def stats(u, c):
    if allowed(u):
        await u.message.reply_text("\n".join(f"{s}: {n}" for s, n in core.stats()) or "empty")


async def strict(u, c):
    if not allowed(u):
        return
    if c.args and c.args[0] in ("on", "off"):
        core.kv_set("strict", "1" if c.args[0] == "on" else "0")
    s = core.kv_get("strict", "1") == "1"
    await u.message.reply_text("Strict ON: only roles that explicitly fit your experience." if s else
                               "Strict OFF: also showing roles that don't state experience (tagged 'not stated').")


async def pause(u, c):
    if allowed(u):
        core.kv_set("paused", "1")
        await u.message.reply_text("⏸ Paused")


async def resume(u, c):
    if allowed(u):
        core.kv_set("paused", "0")
        await u.message.reply_text("▶️ Resumed")


async def checknow(u, c):
    if not allowed(u):
        return
    await u.message.reply_text("Checking…")
    jobs = await asyncio.to_thread(core.run_cycle)
    await broadcast(c.bot, jobs)
    await u.message.reply_text(f"Done: {len(jobs)} new match(es).")


async def on_button(u: Update, c):
    q = u.callback_query
    action, h = q.data.split(":")
    core.set_status(h, action)
    await q.answer("Saved")
    await q.edit_message_reply_markup(None)


def main():
    app = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    for name, fn in [("start", start), ("latest", latest), ("status", status), ("stats", stats),
                     ("strict", strict), ("pause", pause), ("resume", resume), ("checknow", checknow)]:
        app.add_handler(CommandHandler(name, fn))
    app.add_handler(CallbackQueryHandler(on_button))
    app.job_queue.run_repeating(poll, interval=INTERVAL, first=10)
    app.run_polling()


if __name__ == "__main__":
    main()
