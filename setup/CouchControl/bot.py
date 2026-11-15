import asyncio
import io
import json
import logging
import os
import subprocess
import ctypes
import tempfile
import time

import cv2
import numpy as np
from ctypes import wintypes

import pyautogui
import pyperclip
from dotenv import load_dotenv
from web_server import start_web_server, stop_web_server
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://kroshixxx-pixel.github.io/CouchControl_en/").strip()
try:
    ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0").strip() or "0")
except ValueError:
    ALLOWED_USER_ID = 0

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("couchcontrol")
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.04

# Only these known applications can be launched. No arbitrary shell commands.
APP_COMMANDS = {
    "notepad": ("Notepad", ["notepad.exe"]),
    "calculator": ("Calculator", ["calc.exe"]),
    "explorer": ("File Explorer", ["explorer.exe"]),
    "paint": ("Paint", ["mspaint.exe"]),
}

# Windows multimedia virtual-key codes.
VK = {
    "volume_up": 0xAF,
    "volume_down": 0xAE,
    "volume_mute": 0xAD,
    "media_play_pause": 0xB3,
    "media_next": 0xB0,
    "media_previous": 0xB1,
}


def authorized(update: Update) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    return bool(
        user and chat and chat.type == "private"
        and ALLOWED_USER_ID and user.id == ALLOWED_USER_ID
    )


def main_keyboard() -> InlineKeyboardMarkup:
    rows = []
    rows.extend([
        [InlineKeyboardButton("🖱 Mouse", callback_data="page:mouse"),
         InlineKeyboardButton("⌨️ Keyboard", callback_data="page:keyboard")],
        [InlineKeyboardButton("🔊 Volume", callback_data="page:volume"),
         InlineKeyboardButton("🎵 Media", callback_data="page:media")],
        [InlineKeyboardButton("⚡ Shortcuts", callback_data="page:shortcuts"),
         InlineKeyboardButton("📸 Capture", callback_data="page:capture")],
        [InlineKeyboardButton("🗂 Apps", callback_data="page:apps")],
        [InlineKeyboardButton("⏻ Power", callback_data="page:power"),
         InlineKeyboardButton("ℹ️ Status", callback_data="action:status")],
        [InlineKeyboardButton("🛑 Stop bot", callback_data="action:stop_bot")],
    ])
    return InlineKeyboardMarkup(rows)


def capture_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Take screenshot", callback_data="action:screenshot")],
        [InlineKeyboardButton("🎥 Record 15 seconds", callback_data="action:record_video")],
        [InlineKeyboardButton("⬅️ Main menu", callback_data="page:home")],
    ])


def shortcuts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Alt + F4 — Close window", callback_data="shortcut:alt_f4")],
        [InlineKeyboardButton("Win + D — Show desktop", callback_data="shortcut:win_d")],
        [InlineKeyboardButton("Win + I — Settings", callback_data="shortcut:win_i")],
        [InlineKeyboardButton("Ctrl + Shift + Esc — Task Manager", callback_data="shortcut:taskmgr")],
        [InlineKeyboardButton("Alt + Tab — Switch window", callback_data="shortcut:alt_tab")],
        [InlineKeyboardButton("Win + E — File Explorer", callback_data="shortcut:win_e")],
        [InlineKeyboardButton("Win + R — Run", callback_data="shortcut:win_r")],
        [InlineKeyboardButton("⬅️ Main menu", callback_data="page:home")],
    ])


def record_screen_video(duration: int = 15) -> str:
    """Capture the desktop for a fixed period and return an MP4 file path."""
    screenshot = pyautogui.screenshot()
    width, height = screenshot.size
    scale = min(1.0, 1280 / width)
    out_width = max(2, int(width * scale) // 2 * 2)
    out_height = max(2, int(height * scale) // 2 * 2)
    fps = 8
    file_handle = tempfile.NamedTemporaryFile(prefix="couchcontrol-", suffix=".mp4", delete=False)
    video_path = file_handle.name
    file_handle.close()
    writer = cv2.VideoWriter(
        video_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (out_width, out_height)
    )
    if not writer.isOpened():
        writer.release()
        os.remove(video_path)
        raise RuntimeError("Could not create the MP4 video.")

    try:
        deadline = time.monotonic() + duration
        interval = 1.0 / fps
        while time.monotonic() < deadline:
            frame_start = time.monotonic()
            frame = np.array(pyautogui.screenshot())
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            if (out_width, out_height) != (width, height):
                frame = cv2.resize(frame, (out_width, out_height), interpolation=cv2.INTER_AREA)
            writer.write(frame)
            remaining = interval - (time.monotonic() - frame_start)
            if remaining > 0:
                time.sleep(remaining)
    except Exception:
        writer.release()
        try:
            os.remove(video_path)
        except OSError:
            pass
        raise
    writer.release()
    return video_path


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main menu", callback_data="page:home")]])


def mouse_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↖", callback_data="mouse:ul"), InlineKeyboardButton("⬆️", callback_data="mouse:u"), InlineKeyboardButton("↗", callback_data="mouse:ur")],
        [InlineKeyboardButton("⬅️", callback_data="mouse:l"), InlineKeyboardButton("🖱 Left click", callback_data="mouse:left"), InlineKeyboardButton("➡️", callback_data="mouse:r")],
        [InlineKeyboardButton("↙", callback_data="mouse:dl"), InlineKeyboardButton("⬇️", callback_data="mouse:d"), InlineKeyboardButton("↘", callback_data="mouse:dr")],
        [InlineKeyboardButton("Right click", callback_data="mouse:right"), InlineKeyboardButton("Scroll up", callback_data="mouse:su"), InlineKeyboardButton("Scroll down", callback_data="mouse:sd")],
        [InlineKeyboardButton("⬅️ Main menu", callback_data="page:home")],
    ])


def keyboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ Type text", callback_data="keyboard:type")],
        [InlineKeyboardButton("Enter", callback_data="key:enter"), InlineKeyboardButton("Esc", callback_data="key:esc"), InlineKeyboardButton("Tab", callback_data="key:tab")],
        [InlineKeyboardButton("Ctrl+C", callback_data="key:copy"), InlineKeyboardButton("Ctrl+V", callback_data="key:paste"), InlineKeyboardButton("Alt+Tab", callback_data="key:alt_tab")],
        [InlineKeyboardButton("⬆️", callback_data="key:up")],
        [InlineKeyboardButton("⬅️", callback_data="key:left"), InlineKeyboardButton("⬇️", callback_data="key:down"), InlineKeyboardButton("➡️", callback_data="key:right")],
        [InlineKeyboardButton("Space", callback_data="key:space"), InlineKeyboardButton("Backspace", callback_data="key:backspace")],
        [InlineKeyboardButton("⬅️ Main menu", callback_data="page:home")],
    ])


def volume_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔉 −", callback_data="volume:down"), InlineKeyboardButton("🔊 +", callback_data="volume:up")],
        [InlineKeyboardButton("🔇 Mute / unmute", callback_data="volume:mute")],
        [InlineKeyboardButton("⬅️ Main menu", callback_data="page:home")],
    ])


def media_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏮ Previous", callback_data="media:previous"), InlineKeyboardButton("⏯ Play / pause", callback_data="media:play_pause"), InlineKeyboardButton("⏭ Next", callback_data="media:next")],
        [InlineKeyboardButton("⬅️ Main menu", callback_data="page:home")],
    ])


def apps_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(label, callback_data=f"app:{key}")] for key, (label, _cmd) in APP_COMMANDS.items()]
    rows.append([InlineKeyboardButton("⬅️ Main menu", callback_data="page:home")])
    return InlineKeyboardMarkup(rows)


def power_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔒 Lock PC", callback_data="power:lock")],
        [InlineKeyboardButton("⏻ Shut down…", callback_data="power:ask_shutdown"), InlineKeyboardButton("🔄 Restart…", callback_data="power:ask_restart")],
        [InlineKeyboardButton("⬅️ Main menu", callback_data="page:home")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        await update.effective_message.reply_text(
            "Access is not configured yet. To set it up, send /myid, "
            "put your ID in ALLOWED_USER_ID in the .env file, and restart the bot."
        )
        return
    context.user_data["awaiting_text"] = False
    # Remove the persistent Mini App reply keyboard left by older versions.
    await update.effective_message.reply_text(
        "The Mini App launch button has been removed.", reply_markup=ReplyKeyboardRemove()
    )
    await update.effective_message.reply_text(
        "🛋 CouchControl\nChoose what you want to control:", reply_markup=main_keyboard()
    )


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update) or not update.effective_message or not update.effective_message.web_app_data:
        return
    try:
        payload = json.loads(update.effective_message.web_app_data.data)
    except (ValueError, TypeError):
        return
    if payload.get("action") != "screenshot":
        return
    try:
        image = pyautogui.screenshot()
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=75, optimize=True)
        buffer.seek(0)
        await update.effective_message.reply_photo(
            photo=buffer,
            caption="📸 PC screenshot from CouchControl",
        )
    except Exception:
        log.exception("Mini App screenshot failed")
        await update.effective_message.reply_text("Could not take a PC screenshot.")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if user and chat and chat.type == "private":
        await update.effective_message.reply_text(f"Your Telegram user ID: {user.id}\nAdd this number to ALLOWED_USER_ID in the .env file.")
    elif update.effective_message:
        await update.effective_message.reply_text("Open the bot in a private chat and send /myid.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["awaiting_text"] = False
    if authorized(update):
        await update.effective_message.reply_text("Text input cancelled.", reply_markup=main_keyboard())


async def text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return
    if not context.user_data.get("awaiting_text"):
        return
    text = update.effective_message.text or ""
    if not text:
        return
    if len(text) > 2000:
        await update.effective_message.reply_text("The text is too long. Maximum length: 2,000 characters.")
        return
    try:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        context.user_data["awaiting_text"] = False
        await update.effective_message.reply_text("✅ Text pasted into the active PC window.", reply_markup=keyboard_keyboard())
    except Exception as exc:
        log.exception("Text paste failed")
        await update.effective_message.reply_text(f"Could not paste the text: {exc}")


def press_vk(code: int) -> None:
    ctypes.windll.user32.keybd_event(code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(code, 0, 2, 0)


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    if not authorized(update):
        await query.answer("Access denied", show_alert=True)
        return
    await query.answer()
    data = query.data or ""

    pages = {
        "home": ("🛋 CouchControl\nChoose what you want to control:", main_keyboard),
        "mouse": ("🖱 Mouse control\nUse the arrows to move the cursor.", mouse_keyboard),
        "keyboard": ("⌨️ Keyboard\nTap “Type text”, then send a message. The text will be pasted into the active PC window.", keyboard_keyboard),
        "volume": ("🔊 Volume control", volume_keyboard),
        "media": ("🎵 Media controls", media_keyboard),
        "capture": ("📸 Capture\nChoose a screenshot or a screen recording.", capture_keyboard),
        "shortcuts": ("⚡ Keyboard shortcuts", shortcuts_keyboard),
        "apps": ("🗂 Launch apps", apps_keyboard),
        "power": ("⏻ PC power", power_keyboard),
    }
    if data.startswith("page:"):
        page = data.split(":", 1)[1]
        text, markup_fn = pages.get(page, pages["home"])
        context.user_data["awaiting_text"] = False
        await query.edit_message_text(text, reply_markup=markup_fn())
        return

    if data.startswith("mouse:"):
        action = data.split(":", 1)[1]
        step = 55
        moves = {
            "ul": (-step, -step), "u": (0, -step), "ur": (step, -step),
            "l": (-step, 0), "r": (step, 0),
            "dl": (-step, step), "d": (0, step), "dr": (step, step),
        }
        if action in moves:
            pyautogui.moveRel(*moves[action], duration=0.05)
        elif action == "left":
            pyautogui.click(button="left")
        elif action == "right":
            pyautogui.click(button="right")
        elif action == "su":
            pyautogui.scroll(3)
        elif action == "sd":
            pyautogui.scroll(-3)
        return

    if data.startswith("key:"):
        action = data.split(":", 1)[1]
        if action == "copy": pyautogui.hotkey("ctrl", "c")
        elif action == "paste": pyautogui.hotkey("ctrl", "v")
        elif action == "alt_tab": pyautogui.hotkey("alt", "tab")
        elif action in {"enter", "esc", "tab", "space", "backspace", "up", "down", "left", "right"}:
            pyautogui.press({"esc": "esc"}.get(action, action))
        return

    if data == "keyboard:type":
        context.user_data["awaiting_text"] = True
        await query.message.reply_text("✍️ Send the text you want to paste into the PC in your next message. Send /cancel to cancel.")
        return

    if data.startswith("shortcut:"):
        shortcuts = {
            "alt_f4": ("alt", "f4"),
            "win_d": ("win", "d"),
            "win_i": ("win", "i"),
            "taskmgr": ("ctrl", "shift", "esc"),
            "alt_tab": ("alt", "tab"),
            "win_e": ("win", "e"),
            "win_r": ("win", "r"),
        }
        keys = shortcuts.get(data.split(":", 1)[1])
        if keys:
            pyautogui.hotkey(*keys)
        return

    if data.startswith("volume:"):
        action = data.split(":", 1)[1]
        press_vk({"up": VK["volume_up"], "down": VK["volume_down"], "mute": VK["volume_mute"]}[action])
        return

    if data.startswith("media:"):
        action = data.split(":", 1)[1]
        press_vk(VK[action])
        return

    if data.startswith("app:"):
        key = data.split(":", 1)[1]
        if key not in APP_COMMANDS:
            return
        label, command = APP_COMMANDS[key]
        try:
            subprocess.Popen(command, shell=False)
            await query.message.reply_text(f"✅ Launching: {label}")
        except Exception:
            log.exception("App launch failed")
            await query.message.reply_text(f"Could not launch: {label}")
        return

    if data == "action:screenshot":
        try:
            image = pyautogui.screenshot()
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=75)
            buffer.seek(0)
            await query.message.reply_photo(photo=buffer, caption="📸 Current PC screen")
        except Exception:
            log.exception("Screenshot failed")
            await query.message.reply_text("Could not take a screenshot.")
        return

    if data == "action:record_video":
        status_message = await query.message.reply_text(
            "🎥 Recording the screen for 15 seconds. The MP4 will be sent here when finished."
        )
        video_path = None
        try:
            video_path = await asyncio.to_thread(record_screen_video, 15)
            with open(video_path, "rb") as video_file:
                await query.message.reply_video(
                    video=video_file,
                    caption="🎥 Screen recording — 15 seconds",
                    supports_streaming=True,
                )
            await status_message.edit_text("✅ Video sent.")
        except Exception:
            log.exception("Screen recording failed")
            await status_message.edit_text(
                "Could not record or send the video. Check available disk space and try again."
            )
        finally:
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except OSError:
                    log.warning("Could not remove temporary video: %s", video_path)
        return

    if data == "action:status":
        await query.message.reply_text("🟢 CouchControl is running. The PC is reachable through Telegram.")
        return

    if data == "action:stop_bot":
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Yes, stop the bot", callback_data="action:confirm_stop_bot")],
            [InlineKeyboardButton("Cancel", callback_data="page:home")],
        ])
        await query.message.reply_text(
            "🛑 Stop CouchControl? The bot will disconnect from Telegram "
            "until you start it again on the PC.",
            reply_markup=markup,
        )
        return

    if data == "action:confirm_stop_bot":
        await query.message.reply_text(
            "⏹ CouchControl is stopping. To start it again, open the CouchControl shortcut on your PC."
        )
        context.application.stop_running()
        return

    if data in {"power:ask_shutdown", "power:ask_restart"}:
        action = "shutdown" if data.endswith("shutdown") else "restart"
        label = "shut down" if action == "shutdown" else "restart"
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Confirm: {label}", callback_data=f"power:confirm_{action}")],
            [InlineKeyboardButton("Cancel", callback_data="page:power")],
        ])
        await query.message.reply_text(
            f"⚠️ Are you sure you want to {label} the PC? The action will be scheduled for 30 seconds so you can cancel it.",
            reply_markup=markup,
        )
        return

    if data.startswith("power:confirm_"):
        action = data.rsplit("_", 1)[1]
        flag = "/s" if action == "shutdown" else "/r"
        subprocess.Popen(["shutdown", flag, "/t", "30"], shell=False)
        await query.message.reply_text(
            "⏳ The action is scheduled for 30 seconds. If you change your mind, tap cancel:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel shutdown / restart", callback_data="power:abort")]])
        )
        return

    if data == "power:abort":
        subprocess.Popen(["shutdown", "/a"], shell=False)
        await query.message.reply_text("✅ The scheduled action has been cancelled.", reply_markup=power_keyboard())
        return

    if data == "power:lock":
        ctypes.windll.user32.LockWorkStation()
        await query.message.reply_text("🔒 The PC is locked.")
        return


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Unhandled bot error", exc_info=context.error)


def main() -> None:
    if not TOKEN:
        raise SystemExit("BOT_TOKEN was not found. Create the .env file using .env.example as a template.")
    if os.name != "nt":
        raise SystemExit("CouchControl Agent is designed for Windows 10/11.")

    app = (Application.builder().token(TOKEN)
           .post_init(start_web_server)
           .post_shutdown(stop_web_server)
           .build())
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_input))
    app.add_error_handler(error_handler)
    log.info("CouchControl started. Allowed Telegram user ID: %s", ALLOWED_USER_ID or "not configured")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
