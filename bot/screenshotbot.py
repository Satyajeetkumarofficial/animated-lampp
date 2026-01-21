from collections import defaultdict
import logging
import time
import string
import random
import asyncio
from contextlib import contextmanager
from threading import Thread

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from flask import Flask, abort

from bot.config import Config
from bot.workers import Worker
from bot.utils.broadcast import Broadcast


# -------------------------------------------------------------------
# 🌐 Flask app (Health check only)
# -------------------------------------------------------------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive", 200


def run_flask():
    app.run(host="0.0.0.0", port=8080)


Thread(target=run_flask, daemon=True).start()


# -------------------------------------------------------------------
# 🤖 Bot
# -------------------------------------------------------------------

log = logging.getLogger(__name__)


class ScreenShotBot(Client):
    def __init__(self):
        super().__init__(
            Config.SESSION_NAME,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="bot/plugins"),
        )

        self.process_pool = Worker()
        self.CHAT_FLOOD = defaultdict(
            lambda: int(time.time()) - Config.SLOW_SPEED_DELAY - 1
        )
        self.broadcast_ids = {}

    # ----------------------------------------------------------------
    # ✅ START — LOG_CHANNEL HARD RESOLVE (REQUIRED)
    # ----------------------------------------------------------------
    async def start(self):
        await super().start()

        # 🔥 HARD REQUIREMENT: LOG_CHANNEL MUST RESOLVE
        if not Config.LOG_CHANNEL:
            raise RuntimeError("LOG_CHANNEL is REQUIRED but not set")

        try:
            # Step 1: Direct resolve
            await self.get_chat(Config.LOG_CHANNEL)

            # Step 2: Force peer cache via dialogs
            async for dialog in self.get_dialogs():
                if dialog.chat and dialog.chat.id == Config.LOG_CHANNEL:
                    break

            print("LOG_CHANNEL resolved & cached successfully")

        except Exception as e:
            print(f"FATAL: Cannot access LOG_CHANNEL: {e}")
            raise RuntimeError("LOG_CHANNEL is required but not accessible")

        await self.process_pool.start()

        me = await self.get_me()
        print(f"New session started for {me.first_name} ({me.username})")

    async def stop(self):
        await self.process_pool.stop()
        await super().stop()
        print("Session stopped. Bye!!")

    # ----------------------------------------------------------------
    # 📢 Broadcast helpers
    # ----------------------------------------------------------------
    @contextmanager
    def track_broadcast(self, handler):
        broadcast_id = ""
        while True:
            broadcast_id = "".join(
                random.choice(string.ascii_letters) for _ in range(3)
            )
            if broadcast_id not in self.broadcast_ids:
                break

        self.broadcast_ids[broadcast_id] = handler
        try:
            yield broadcast_id
        finally:
            self.broadcast_ids.pop(broadcast_id, None)

    async def start_broadcast(self, broadcast_message, admin_id):
        asyncio.create_task(
            self._start_broadcast(broadcast_message, admin_id)
        )

    async def _start_broadcast(self, broadcast_message, admin_id):
        try:
            broadcast_handler = Broadcast(
                client=self,
                broadcast_message=broadcast_message
            )

            with self.track_broadcast(broadcast_handler) as broadcast_id:
                reply_message = await self.send_message(
                    chat_id=admin_id,
                    text=(
                        "Broadcast started.\n\n"
                        "Use the buttons to check progress or cancel."
                    ),
                    reply_to_message_id=getattr(
                        broadcast_message, "id", None
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Check Progress",
                                    callback_data=f"sts_bdct+{broadcast_id}",
                                ),
                                InlineKeyboardButton(
                                    "Cancel!",
                                    callback_data=f"cncl_bdct+{broadcast_id}",
                                ),
                            ]
                        ]
                    ),
                )

                await broadcast_handler.start()
                await reply_message.edit_text("Broadcast completed ✅")

        except Exception:
            log.error("Broadcast error", exc_info=True)
