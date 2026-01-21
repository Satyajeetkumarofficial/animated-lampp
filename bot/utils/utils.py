import os
import random
import asyncio
import logging
from urllib.parse import urljoin

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import Config


log = logging.getLogger(__name__)


class ProcessTypes:
    SAMPLE_VIDEO = 1
    TRIM_VIDEO = 2
    MANNUAL_SCREENSHOTS = 3
    SCREENSHOTS = 4
    MEDIAINFO = 5


class Utilities:
    @staticmethod
    def is_valid_file(msg):
        if not msg or not msg.media:
            return False
        if msg.video:
            return True
        if msg.document and msg.document.mime_type:
            return any(
                mime in msg.document.mime_type
                for mime in ["video", "application/octet-stream"]
            )
        return False

    @staticmethod
    def is_url(text: str):
        return bool(text) and text.startswith("http")

    @staticmethod
    def get_random_start_at(seconds, dur=0):
        if seconds <= dur:
            return 0
        return random.randint(0, seconds - dur)

    @staticmethod
    async def run_subprocess(cmd):
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return await process.communicate()

    @staticmethod
    async def generate_thumbnail_file(file_path, output_folder):
        os.makedirs(output_folder, exist_ok=True)
        thumb_file = os.path.join(output_folder, "thumb.jpg")

        ffmpeg_cmd = [
            "ffmpeg",
            "-ss", "0",
            "-i", file_path,
            "-vframes", "1",
            "-vf", "scale=320:-1",
            "-y", thumb_file,
        ]

        output = await Utilities.run_subprocess(ffmpeg_cmd)
        log.debug(output)

        if not os.path.exists(thumb_file):
            return None
        return thumb_file

    # 🔥 MAIN FIX: Pyrogram v1 + v2 compatible
    @staticmethod
    def generate_stream_link(media_msg):
        """
        Pyrogram v1  -> message.message_id
        Pyrogram v2  -> message.id
        """
        msg_id = getattr(media_msg, "id", None) or getattr(media_msg, "message_id", None)
        if not msg_id:
            raise ValueError("Unable to resolve message id")

        chat_id = str(media_msg.chat.id).replace("-100", "")
        return urljoin(Config.HOST, f"file/{chat_id}/{msg_id}")

    @staticmethod
    async def get_media_info(file_link):
        ffprobe_cmd = [
            "ffprobe",
            "-headers", f"IAM:{Config.IAM_HEADER}",
            "-i", file_link,
            "-v", "quiet",
            "-of", "json",
            "-show_streams",
            "-show_format",
            "-show_chapters",
            "-show_programs",
        ]
        data, err = await Utilities.run_subprocess(ffprobe_cmd)
        return data

    @staticmethod
    async def get_dimentions(file_link):
        ffprobe_cmd = [
            "ffprobe",
            "-headers", f"IAM:{Config.IAM_HEADER}",
            "-i", file_link,
            "-v", "error",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            "-select_streams", "v:0",
        ]

        out, err = await Utilities.run_subprocess(ffprobe_cmd)
        log.debug((out, err))

        try:
            width, height = [int(i) for i in out.decode().strip().split("x")]
        except Exception:
            width, height = 1280, 720

        return width, height

    @staticmethod
    async def get_duration(file_link):
        ffprobe_cmd = [
            "ffprobe",
            "-headers", f"IAM:{Config.IAM_HEADER}",
            "-i", file_link,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
        ]

        out, err = await Utilities.run_subprocess(ffprobe_cmd)
        out = out.decode().strip()

        if not out:
            return err.decode()

        try:
            return round(float(out))
        except Exception:
            return "No duration!"

    @staticmethod
    async def fix_subtitle_codec(file_link):
        fixable_codecs = ["mov_text"]

        ffprobe_cmd = [
            "ffprobe",
            "-headers", f"IAM:{Config.IAM_HEADER}",
            "-i", file_link,
            "-v", "error",
            "-select_streams", "s",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
        ]

        out, err = await Utilities.run_subprocess(ffprobe_cmd)
        out = out.decode().strip()

        if not out:
            return []

        fix_cmd = []
        codecs = out.splitlines()
        for i, codec in enumerate(codecs):
            if any(c in codec for c in fixable_codecs):
                fix_cmd += [f"-c:s:{i}", "srt"]

        return fix_cmd

    @staticmethod
    def get_watermark_coordinates(pos, width, height):
        x_pad = round(width * 0.02)
        y_pad = round(height * 0.02)

        positions = {
            0: (x_pad, y_pad),
            1: ("(w-text_w)/2", y_pad),
            2: (f"w-tw-{x_pad}", y_pad),
            3: (x_pad, "(h-text_h)/2"),
            4: ("(w-text_w)/2", "(h-text_h)/2"),
            5: (f"w-tw-{x_pad}", "(h-text_h)/2"),
            6: (x_pad, f"h-th-{y_pad}"),
            7: ("(w-text_w)/2", f"h-th-{y_pad}"),
        }

        return positions.get(pos, (f"w-tw-{x_pad}", f"h-th-{y_pad}"))

    @staticmethod
    async def display_settings(c, m, db, cb=False):
        chat_id = m.from_user.id if cb else m.chat.id

        as_file = await db.is_as_file(chat_id)
        watermark_text = await db.get_watermark_text(chat_id)
        sample_duration = await db.get_sample_duration(chat_id)
        watermark_color_code = await db.get_watermark_color(chat_id)
        watermark_position = await db.get_watermark_position(chat_id)
        screenshot_mode = await db.get_screenshot_mode(chat_id)
        font_size = await db.get_font_size(chat_id)

        buttons = [
            [
                InlineKeyboardButton("Upload Mode", "rj"),
                InlineKeyboardButton(
                    "📁 Document" if as_file else "🖼️ Image",
                    "set+af",
                ),
            ],
            [
                InlineKeyboardButton("Watermark", "rj"),
                InlineKeyboardButton(
                    watermark_text or "No watermark", "set+wm"
                ),
            ],
            [
                InlineKeyboardButton("Watermark Color", "rj"),
                InlineKeyboardButton(
                    Config.COLORS[watermark_color_code], "set+wc"
                ),
            ],
            [
                InlineKeyboardButton("Font Size", "rj"),
                InlineKeyboardButton(
                    Config.FONT_SIZES_NAME[font_size], "set+fs"
                ),
            ],
            [
                InlineKeyboardButton("Position", "rj"),
                InlineKeyboardButton(
                    Config.POSITIONS[watermark_position], "set+wp"
                ),
            ],
            [
                InlineKeyboardButton("Sample Duration", "rj"),
                InlineKeyboardButton(f"{sample_duration}s", "set+sv"),
            ],
            [
                InlineKeyboardButton("Screenshot Mode", "rj"),
                InlineKeyboardButton(
                    "Equally spaced" if screenshot_mode == 0 else "Random",
                    "set+sm",
                ),
            ],
        ]

        markup = InlineKeyboardMarkup(buttons)

        if cb:
            try:
                await m.edit_message_reply_markup(markup)
            except Exception:
                pass
            return

        await m.reply_text(
            "Here you can configure my behavior.\n\nPress buttons to change settings.",
            reply_markup=markup,
            quote=True,
        )

    @staticmethod
    def gen_ik_buttons():
        btns = []
        row = []

        for i in range(2, 11):
            row.append(InlineKeyboardButton(str(i), f"scht+{i}"))
            if len(row) == 2:
                btns.append(row)
                row = []

        if row:
            btns.append(row)

        btns.append([InlineKeyboardButton("Manual Screenshots", "mscht")])
        btns.append([InlineKeyboardButton("Trim Video", "trim")])
        btns.append([InlineKeyboardButton("Get Media Info", "mi")])

        return btns
