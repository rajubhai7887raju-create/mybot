import os
import re
import json
import asyncio
import logging
from datetime import datetime

import yt_dlp
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ═══════════════════════════════════════════════════════════
# ⚠️ CONFIG — yahan apni details daalo
# ═══════════════════════════════════════════════════════════
BOT_TOKEN = "8983990219:AAG8CIMvSj_2YstIOnIWdr9m4Y-i0BAHqZ8"

ADMIN_ID = 8147130832

DOWNLOAD_DIR = "downloads"
DATA_FILE = "bot_data.json"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# DATA STORE
# ═══════════════════════════════════════════════════════════
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}, "banned": [], "stats": {"downloads": 0, "started": 0}}


def save_data(data: dict):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Data save error: {e}")


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def is_banned(user_id: int) -> bool:
    return str(user_id) in load_data().get("banned", [])


def register_user(user_id: int, username: str, first_name: str):
    data = load_data()
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "username": username or "",
            "first_name": first_name or "",
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "downloads": 0,
        }
    else:
        data["users"][uid]["username"] = username or data["users"][uid]["username"]
        data["users"][uid]["first_name"] = first_name or data["users"][uid]["first_name"]
    save_data(data)


def bump_stat(key: str, user_id: int = None):
    data = load_data()
    data["stats"][key] = data["stats"].get(key, 0) + 1
    if user_id is not None:
        uid = str(user_id)
        if uid in data["users"]:
            data["users"][uid]["downloads"] = data["users"][uid].get("downloads", 0) + 1
    save_data(data)


# ═══════════════════════════════════════════════════════════
# URL VALIDATION — sirf Instagram
# ═══════════════════════════════════════════════════════════
INSTAGRAM_REGEX = re.compile(r"(instagram\.com|instagr\.am)")


def is_valid_url(url: str) -> bool:
    return bool(INSTAGRAM_REGEX.search(url))


# ═══════════════════════════════════════════════════════════
# DOWNLOAD
# ═══════════════════════════════════════════════════════════
def download_video_sync(url: str, user_id: int) -> str:
    out_template = os.path.join(DOWNLOAD_DIR, f"{user_id}_%(id)s.%(ext)s")
    ydl_opts = {
        "outtmpl": out_template,
        "format": "best[filesize<50M]/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
    return filepath


# ═══════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════
def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📸 Instagram Video Download", callback_data="insta_help"
                )
            ]
        ]
    )


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
                InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
                InlineKeyboardButton("🚫 Ban/Unban", callback_data="admin_ban"),
            ],
            [
                InlineKeyboardButton("📋 Banned List", callback_data="admin_banned"),
                InlineKeyboardButton("🧹 Clear Data", callback_data="admin_clear"),
            ],
            [
                InlineKeyboardButton("🔙 Close Panel", callback_data="admin_close"),
            ],
        ]
    )


# ═══════════════════════════════════════════════════════════
# START
# ═══════════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username, user.first_name)
    bump_stat("started")

    await update.message.reply_text(
        "✨ Keyboard Button...", reply_markup=ReplyKeyboardRemove()
    )

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )
    await asyncio.sleep(0.4)

    text = (
        "🎀 <b>Ritesh AI Assistant</b> 🎀\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🙏🏻 <b>Swagat hai!</b>\n\n"
        "Main <b>Instagram</b> ka video/reel download karke\n"
        "tumhe bhej dunga. Bas link bhejo! 🚀\n\n"
        "📥 <b>How to use:</b>\n"
        "📸 Instagram video/reel kholo\n"
        "🖇️ Copy Link karo\n"
        "✍🏻 Yahan paste karke bhejo\n\n"
        "⚠️ <i>Sirf apni ya permission wali content download karo.</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML, reply_markup=main_keyboard()
    )


async def insta_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("📸 Instagram link bhejo!", show_alert=False)
    await query.message.reply_text(
        "📸 <b>Instagram Video Download</b>\n\n"
        "Bas Instagram ka video/reel link copy karke yahan bhejo.\n\n"
        "✅ Example:\n"
        "<code>https://www.instagram.com/reel/XXXXX/</code>",
        parse_mode=ParseMode.HTML,
    )


# ═══════════════════════════════════════════════════════════
# MESSAGE HANDLER (Instagram download)
# ═══════════════════════════════════════════════════════════
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    url = update.message.text.strip()

    if is_banned(user.id):
        await update.message.reply_text(
            "🚫 Aap is bot se banned ho. Contact admin."
        )
        return

    if not is_valid_url(url):
        await update.message.reply_text(
            "❌ Ye valid <b>Instagram</b> link nahi lag raha.\n\n"
            "Sahi link bhejo jaise:\n"
            "<code>https://www.instagram.com/reel/XXXXX/</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=main_keyboard(),
        )
        return

    register_user(user.id, user.username, user.first_name)
    status_msg = await update.message.reply_text(
        "⏳ <b>Download ka jaadu chal raha hai...</b> 🪄✨",
        parse_mode=ParseMode.HTML,
    )

    filepath = None
    try:
        filepath = await asyncio.to_thread(download_video_sync, url, user.id)

        if not os.path.exists(filepath):
            base = os.path.splitext(filepath)[0]
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(os.path.basename(base)):
                    filepath = os.path.join(DOWNLOAD_DIR, f)
                    break

        filesize = os.path.getsize(filepath) / (1024 * 1024)
        if filesize > 50:
            await status_msg.edit_text(
                f"⚠️ Video <b>{filesize:.1f}MB</b> ka hai, "
                f"Telegram limit (50MB) se bada hai.",
                parse_mode=ParseMode.HTML,
            )
            return

        await status_msg.edit_text(
            "📤 <b>Upload ho raha hai...</b>", parse_mode=ParseMode.HTML
        )

        with open(filepath, "rb") as video:
            await update.message.reply_video(
                video=video,
                caption="✅ <b>Done!</b> Enjoy 🎬✨",
                parse_mode=ParseMode.HTML,
                supports_streaming=True,
            )

        await status_msg.delete()
        bump_stat("downloads", user.id)

    except yt_dlp.utils.DownloadError as e:
        await status_msg.edit_text(
            "❌ <b>Download fail hua.</b>\n\n"
            "Ho sakta hai:\n"
            "• Link private/deleted ho\n"
            "• Instagram ne block kiya ho\n"
            f"\n<b>Error:</b> <code>{str(e)[:200]}</code>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.exception(f"Error: {e}")
        try:
            await status_msg.edit_text(
                f"❌ <b>Unexpected Error:</b>\n<code>{str(e)[:200]}</code>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
    finally:
        # ✅ FIX: os.remove() hosting rules ki wajah se hata diya.
        # Hosting temp dir khud clean kar deta hai; file delete karne ki zaroorat nahi.
        pass


# ═══════════════════════════════════════════════════════════
# ADMIN PANEL
# ═══════════════════════════════════════════════════════════
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Sirf admin ke liye.")
        return

    data = load_data()
    total_users = len(data["users"])
    total_downloads = data["stats"].get("downloads", 0)
    banned_count = len(data["banned"])

    text = (
        "🛡️ <b>ADMIN PANEL</b> 🛡️\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Users: <b>{total_users}</b>\n"
        f"📥 Downloads: <b>{total_downloads}</b>\n"
        f"🚫 Banned: <b>{banned_count}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Neeche se option chuno 👇"
    )
    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard()
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("❌ Sirf admin ke liye.", show_alert=True)
        return

    data = query.data
    await query.answer()

    if data == "admin_stats":
        d = load_data()
        text = (
            "📊 <b>BOT STATISTICS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Total Users: <b>{len(d['users'])}</b>\n"
            f"📥 Total Downloads: <b>{d['stats'].get('downloads', 0)}</b>\n"
            f"🚀 Total Starts: <b>{d['stats'].get('started', 0)}</b>\n"
            f"🚫 Banned Users: <b>{len(d['banned'])}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        await query.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard()
        )

    elif data == "admin_users":
        d = load_data()
        if not d["users"]:
            await query.message.reply_text("❌ Koi user nahi.")
            return
        lines = ["👥 <b>USER LIST</b>\n━━━━━━━━━━━━━━━━━━━━━━"]
        for uid, info in list(d["users"].items())[-30:]:
            status = "🚫" if uid in d["banned"] else "✅"
            uname = f"@{info['username']}" if info.get("username") else "no-username"
            lines.append(
                f"{status} <code>{uid}</code> — {uname} — {info.get('downloads', 0)} dl"
            )
        await query.message.reply_text(
            "\n".join(lines)[:4000], parse_mode=ParseMode.HTML
        )

    elif data == "admin_broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.message.reply_text(
            "📢 <b>Broadcast Mode ON</b>\n\n"
            "Ab jo message bhejoge wo sab users ko jayega.\n"
            "Cancel karne ke liye /cancel bhejo.",
            parse_mode=ParseMode.HTML,
        )

    elif data == "admin_ban":
        await query.message.reply_text(
            "🚫 <b>Ban/Unban</b>\n\n"
            "Format bhejo:\n"
            "<code>/ban USER_ID</code>\n"
            "<code>/unban USER_ID</code>",
            parse_mode=ParseMode.HTML,
        )

    elif data == "admin_banned":
        d = load_data()
        if not d["banned"]:
            await query.message.reply_text("✅ Koi banned user nahi.")
            return
        text = "🚫 <b>BANNED USERS</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
        text += "\n".join(f"<code>{uid}</code>" for uid in d["banned"])
        await query.message.reply_text(text, parse_mode=ParseMode.HTML)

    elif data == "admin_clear":
        context.user_data["awaiting_clear_confirm"] = True
        await query.message.reply_text(
            "🧹 <b>Data clear confirmation</b>\n\n"
            "Sach mein saara data (users, stats) clear karna hai?\n"
            "Confirm karne ke liye <code>/confirm_clear</code> bhejo.",
            parse_mode=ParseMode.HTML,
        )

    elif data == "admin_close":
        await query.message.edit_text("🛡️ Admin Panel closed.")


async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Use: /ban USER_ID")
        return
    uid = context.args[0]
    data = load_data()
    if uid not in data["banned"]:
        data["banned"].append(uid)
        save_data(data)
    await update.message.reply_text(
        f"🚫 User <code>{uid}</code> banned.", parse_mode=ParseMode.HTML
    )


async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Use: /unban USER_ID")
        return
    uid = context.args[0]
    data = load_data()
    if uid in data["banned"]:
        data["banned"].remove(uid)
        save_data(data)
    await update.message.reply_text(
        f"✅ User <code>{uid}</code> unbanned.", parse_mode=ParseMode.HTML
    )


async def confirm_clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.user_data.get("awaiting_clear_confirm"):
        return
    context.user_data["awaiting_clear_confirm"] = False
    save_data({"users": {}, "banned": [], "stats": {"downloads": 0, "started": 0}})
    await update.message.reply_text("🧹 Data cleared!")


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_broadcast"] = False
    context.user_data["awaiting_clear_confirm"] = False
    await update.message.reply_text("✅ Cancelled.")


async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.user_data.get("awaiting_broadcast"):
        return

    context.user_data["awaiting_broadcast"] = False
    data = load_data()
    sent, failed = 0, 0
    status = await update.message.reply_text("📢 Broadcasting...")

    for uid in data["users"]:
        if uid in data["banned"]:
            continue
        try:
            await context.bot.copy_message(
                chat_id=int(uid),
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
            )
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await status.edit_text(
        f"✅ <b>Broadcast Done</b>\n\n"
        f"📤 Sent: {sent}\n"
        f"❌ Failed: {failed}",
        parse_mode=ParseMode.HTML,
    )


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("confirm_clear", confirm_clear_cmd))

    app.add_handler(CallbackQueryHandler(insta_help_callback, pattern="^insta_help$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID),
            broadcast_handler,
        ),
        group=0,
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message), group=1
    )

    print("🤖 Bot chal raha hai... Ctrl+C se band karo")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()