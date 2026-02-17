# ---------------------------------------------------------
# 🚑 CRITICAL FIX FOR PYTHON 3.10+ / 3.14
# Yeh hissa sabse upar hona chahiye, imports se bhi pehle
# ---------------------------------------------------------
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# ---------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant, SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired
from pyrogram.enums import ChatMemberStatus
import time
import os
from flask import Flask
from threading import Thread

# ---------------------------------------------------------
# ⚠️ CONFIGURATION (Apna Data Yahan Rakhein)
# ---------------------------------------------------------
API_ID = 37314366
API_HASH = "bd4c934697e7e91942ac911a5a287b46"
BOT_TOKEN = "8321333186:AAEWHHj7OpeS8lARdm1vNjcWOd2ilrc2vWE"

# Force Subscribe Channels
FORCE_CHANNELS = [
    {"title": "First Channel", "id": -1003387459132, "url": "https://t.me/+wZ9rDQC5fkYxOWJh"},
    {"title": "Second Channel", "id": -1003892920891, "url": "https://t.me/+Om1HMs2QTHk1N2Zh"}
]

SESSION_NAME = "magma_force_v8"

# Global variables
user_sessions = {}

# ---------------------------------------------------------
# 🌐 FLASK WEB SERVER
# ---------------------------------------------------------
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is Running 24/7 with Force Sub 🚀"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# ---------------------------------------------------------
# 🤖 BOT CLIENT
# ---------------------------------------------------------
app = Client(
    SESSION_NAME, 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN,
    in_memory=True
)

# ---------------------------------------------------------
# 🔒 FORCE SUBSCRIBE CHECKER
# ---------------------------------------------------------

async def get_force_sub_buttons(client, user_id):
    buttons = []
    not_joined = False

    for channel in FORCE_CHANNELS:
        try:
            member = await client.get_chat_member(channel["id"], user_id)
            if member.status in [ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
                buttons.append([InlineKeyboardButton(f"🔔 Join {channel['title']}", url=channel['url'])])
                not_joined = True
        except UserNotParticipant:
            buttons.append([InlineKeyboardButton(f"🔔 Join {channel['title']}", url=channel['url'])])
            not_joined = True
        except Exception as e:
            pass

    if not_joined:
        buttons.append([InlineKeyboardButton("✅ I Have Joined", callback_data="check_joined")])
        return InlineKeyboardMarkup(buttons)
    return None

@app.on_callback_query(filters.regex("check_joined"))
async def on_check_joined(client, callback: CallbackQuery):
    buttons = await get_force_sub_buttons(client, callback.from_user.id)
    if buttons:
        await callback.answer("❌ You haven't joined all channels yet!", show_alert=True)
    else:
        await callback.message.delete()
        await callback.message.reply(
            "✅ **Verification Successful!**\n\n"
            "Now you can use the bot.\n"
            "👉 Send /get to generate session."
        )

# ---------------------------------------------------------
# 🛠 HELPER FUNCTIONS
# ---------------------------------------------------------

async def get_session_string(temp_client):
    try:
        return await temp_client.export_session_string()
    except:
        return None

# ---------------------------------------------------------
# 🤖 BOT COMMANDS
# ---------------------------------------------------------

@app.on_message(filters.command("start"))
async def start_command(client, message):
    buttons = await get_force_sub_buttons(client, message.from_user.id)
    if buttons:
        await message.reply(
            "🔒 **Access Denied!**\n\n"
            "You must join our channels to use this bot.",
            reply_markup=buttons
        )
        return

    await message.reply(
        "🤖 **Session Generator Bot**\n\n"
        "📱 Send /get to generate your Telegram session string!\n"
        "🔒 **Safe & Secure** - No API_ID/HASH needed!\n\n"
        "🔧 **Developer:** @MAGMAxRICH"
    )

@app.on_message(filters.command("get"))
async def get_session_command(client, message):
    buttons = await get_force_sub_buttons(client, message.from_user.id)
    if buttons:
        await message.reply("🔒 Join channels first!", reply_markup=buttons)
        return

    user_id = message.from_user.id
    if user_id in user_sessions:
        await message.reply("⚠️ You already have an active process. Type /cancel to start new.")
        return

    user_sessions[user_id] = {
        "step": "phone",
        "phone": None,
        "client": None,
        "hash": None,
        "timestamp": time.time()
    }

    await message.reply(
        "📱 **Step 1/2: Phone Number**\n\n"
        "📞 Send your phone number:\n"
        "**Example:** `+919876543210`\n"
        "**Example:** `+1234567890`\n\n"
        "❌ Type /cancel to stop."
    )

@app.on_message(filters.command("cancel"))
async def cancel_session(client, message):
    user_id = message.from_user.id
    if user_id in user_sessions:
        if user_sessions[user_id].get("client"):
            try: await user_sessions[user_id]["client"].disconnect()
            except: pass
        del user_sessions[user_id]
        await message.reply("✅ Process cancelled.")
    else:
        await message.reply("⚠️ No active session to cancel.")

# ---------------------------------------------------------
# 📨 MESSAGE HANDLER
# ---------------------------------------------------------

@app.on_message(filters.text & filters.private)
async def handle_text(client, message):
    user_id = message.from_user.id
    if user_id not in user_sessions: return

    if time.time() - user_sessions[user_id]["timestamp"] > 600:
        if user_sessions[user_id].get("client"):
            try: await user_sessions[user_id]["client"].disconnect()
            except: pass
        del user_sessions[user_id]
        await message.reply("⏰ Session expired. Please use /get to start again.")
        return

    step = user_sessions[user_id]["step"]
    text = message.text.strip()

    if text.lower() == "/cancel":
        await cancel_session(client, message)
        return

    if step == "phone":
        if not text.startswith("+") or len(text) < 10:
            await message.reply("❌ **Invalid!** Example: `+919876543210`")
            return
        user_sessions[user_id]["phone"] = text
        user_sessions[user_id]["step"] = "otp"
        try:
            temp_client = Client(f"mem_{user_id}_{time.time()}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await temp_client.connect()
            sent_code = await temp_client.send_code(text)
            user_sessions[user_id]["client"] = temp_client
            user_sessions[user_id]["hash"] = sent_code.phone_code_hash
            await message.reply("✅ **OTP Sent!**\n\nEnter OTP with spaces:\n`1 2 3 4 5`")
        except Exception as e:
            await message.reply(f"❌ Error: {e}\nTry again with /get")
            if user_sessions[user_id].get("client"):
                try: await user_sessions[user_id]["client"].disconnect()
                except: pass
            del user_sessions[user_id]

    elif step == "otp":
        otp = text.replace(" ", "")
        try:
            tc = user_sessions[user_id]["client"]
            ph = user_sessions[user_id]["phone"]
            ch = user_sessions[user_id]["hash"]
            try:
                await tc.sign_in(ph, ch, phone_code=otp)
            except SessionPasswordNeeded:
                user_sessions[user_id]["step"] = "2fa"
                await message.reply("🔐 **2FA Detected!**\nEnter Password.")
                return
            except Exception as e:
                raise e
            await send_session_data(client, message, tc, ph)
        except Exception as e:
            await message.reply(f"❌ OTP Error: {e}")

    elif step == "2fa":
        try:
            tc = user_sessions[user_id]["client"]
            ph = user_sessions[user_id]["phone"]
            await tc.check_password(text)
            await send_session_data(client, message, tc, ph)
        except Exception as e:
            await message.reply(f"❌ Password Error: {e}")

async def send_session_data(bot, message, temp_client, phone):
    try:
        session_string = await get_session_string(temp_client)
        user_info = await temp_client.get_me()
        user_id = message.from_user.id
        name = user_info.first_name or ""
        text = f"🎉 **SESSION GENERATED!**\n👤 {name}\n📱 `{phone}`\n\n`{session_string}`"
        await message.reply(text)
        try: await temp_client.send_message("me", text)
        except: pass
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
    finally:
        await temp_client.disconnect()
        if user_id in user_sessions: del user_sessions[user_id]

# ---------------------------------------------------------
# 🚀 MAIN EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":
    print("🚀 Session Bot Starting...")
    keep_alive() # Flask Server
    app.run()