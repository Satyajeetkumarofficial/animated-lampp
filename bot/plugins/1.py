import time
import datetime
import asyncio

from pyrogram import filters
from pyrogram.errors import FloodWait

from bot.screenshotbot import ScreenShotBot
from bot.config import Config
from bot.database import Database


db = Database()


@ScreenShotBot.on_callback_query()
async def __(c, m):
    await foo(c, m, cb=True)


@ScreenShotBot.on_message(filters.private)
async def _(c, m):
    await foo(c, m)


async def safe_log(client, text):
    """
    Safely send logs to LOG_CHANNEL without crashing the bot
    """
    if not Config.LOG_CHANNEL:
        return

    try:
        await client.send_message(Config.LOG_CHANNEL, text)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            await client.send_message(Config.LOG_CHANNEL, text)
        except Exception:
            pass
    except Exception:
        pass


async def foo(c, m, cb=False):
    if not m.from_user:
        return

    chat_id = m.from_user.id
    now = int(time.time())

    # ⏳ Anti-flood per user
    if now - c.CHAT_FLOOD[chat_id] < Config.SLOW_SPEED_DELAY:
        if cb:
            try:
                await m.answer()
            except Exception:
                pass
        return

    c.CHAT_FLOOD[chat_id] = now

    # 🆕 New user logging
    if not await db.is_user_exist(chat_id):
        await db.add_user(chat_id)
        await safe_log(c, f"🆕 New User {m.from_user.mention}")

    # 🚫 Ban check
    ban_status = await db.get_ban_status(chat_id)
    if ban_status.get("is_banned"):
        banned_on = datetime.date.fromisoformat(ban_status["banned_on"])
        if (datetime.date.today() - banned_on).days > ban_status["ban_duration"]:
            await db.remove_ban(chat_id)
        else:
            return

    # 📅 Daily usage update
    today = datetime.date.today().isoformat()
    last_used_on = await db.get_last_used_on(chat_id)
    if last_used_on != today:
        await db.update_last_used_on(chat_id)

    # ▶️ Continue to other plugins
    await m.continue_propagation()
