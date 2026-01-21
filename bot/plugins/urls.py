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

    # ❗ MEDIA ERROR CASE
    if isinstance(duration, str):
        if Config.LOG_CHANNEL:
            try:
                await c.send_message(
                    Config.LOG_CHANNEL,
                    f"⚠️ Media error\n\n{duration}"
                )
            except Exception:
                pass
        return

    btns = Utilities.gen_ik_buttons()

    if duration >= 600:
        btns.append(
            [InlineKeyboardButton("Generate Sample Video!", "smpl")]
        )

    await snt.edit_text(
        text=(
            "Choose one of the options.\n\n"
            f"Total duration: `{datetime.timedelta(seconds=duration)}` "
            f"(`{duration}s`)"
        ),
        reply_markup=InlineKeyboardMarkup(btns),
    )
