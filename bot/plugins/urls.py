import datetime
import logging

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ..utils import Utilities
from ..screenshotbot import ScreenShotBot
from ..config import Config


log = logging.getLogger(__name__)


@ScreenShotBot.on_message(
    filters.private
    & (filters.text | filters.media)
    & filters.incoming
)
async def _(c, m):

    # 🔍 Validate input
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

    # 🔗 Build file link
    if m.media:
        file_link = Utilities.generate_stream_link(m)
    else:
        file_link = m.text

    # ⏱ Get duration
    duration = await Utilities.get_duration(file_link)

    # ❌ Error handling (NO forward, SAFE logging)
    if isinstance(duration, str):
        await snt.edit_text("😟 Sorry! I cannot open the file.")

        try:
            if Config.LOG_CHANNEL:
                await c.send_message(
                    Config.LOG_CHANNEL,
                    f"⚠️ Failed to process file\n\n{duration}"
                )
        except Exception as e:
            log.error(f"LOG_CHANNEL error: {e}")

        return

    # 🎛 Buttons
    btns = Utilities.gen_ik_buttons()

    if duration >= 600:
        btns.append([InlineKeyboardButton("Generate Sample Video!", "smpl")])

    await snt.edit_text(
        text=(
            "Choose one of the options.\n\n"
            f"Total duration: `{datetime.timedelta(seconds=duration)}` (`{duration}s`)"
        ),
        reply_markup=InlineKeyboardMarkup(btns),
    )
