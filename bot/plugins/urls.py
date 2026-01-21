import datetime

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils import Utilities
from bot.screenshotbot import ScreenShotBot
from bot.config import Config


@ScreenShotBot.on_message(
    filters.private & (filters.text | filters.media)
)
async def url_handler(client, message):

    # ---------- VALIDATION ----------
    if message.media:
        if not Utilities.is_valid_file(message):
            return
    else:
        if not Utilities.is_url(message.text):
            return

    # ---------- PROCESS MESSAGE ----------
    status = await message.reply_text(
        "⏳ Please wait, processing your request...",
        quote=True
    )

    # ---------- GET FILE / URL ----------
    if message.media:
        file_link = Utilities.generate_stream_link(message)
    else:
        file_link = message.text

    # ---------- GET DURATION ----------
    duration = await Utilities.get_duration(file_link)

    if isinstance(duration, str):
        # ❗ duration error (string = error message)
        if Config.LOG_CHANNEL:
            try:
                await client.send_message(
                    Config.LOG_CHANNEL,
                    f"⚠️ Media Error\n\n{duration}"
                )
            except Exception:
                pass

        await status.edit_text("❌ Failed to process this file.")
        return

    # ---------- BUTTONS ----------
    buttons = Utilities.gen_ik_buttons()

    if duration >= 600:
        buttons.append([
            InlineKeyboardButton(
                "🎞 Generate Sample Video",
                callback_data="smpl"
            )
        ])

    # ---------- FINAL MESSAGE ----------
    await status.edit_text(
        text=(
            "✅ Choose an option below:\n\n"
            f"⏱ Duration: `{datetime.timedelta(seconds=duration)}` "
            f"(`{duration}s`)"
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
