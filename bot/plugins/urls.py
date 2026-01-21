import datetime

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ..utils import Utilities
from ..screenshotbot import ScreenShotBot
from ..config import Config


@ScreenShotBot.on_message(
    filters.private
    & (filters.text | filters.media)
)
async def _(c, m):

    if m.media:
        if not Utilities.is_valid_file(m):
            return
    else:
        if not Utilities.is_url(m.text):
            return

    snt = await m.reply_text(
        "Hi there, Please wait while I'm getting everything ready to process your request!",
        quote=True,
    )

    if m.media:
        file_link = Utilities.generate_stream_link(m)
    else:
        file_link = m.text

    duration = await Utilities.get_duration(file_link)
    if isinstance(duration, str):
        try:
    log = await m.forward(Config.LOG_CHANNEL)
    await log.reply_text(duration, quote=True)
except Exception as e:
    # ❗ Log channel error should NEVER break the bot
    print("LOG_CHANNEL forward failed:", e)
        return

    btns = Utilities.gen_ik_buttons()

    if duration >= 600:
        btns.append([InlineKeyboardButton("Generate Sample Video!", "smpl")])

    await snt.edit_text(
        text=f"Choose one of the options.\n\nTotal duration: `{datetime.timedelta(seconds=duration)}` (`{duration}s`)",
        reply_markup=InlineKeyboardMarkup(btns),
    )
