import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import time
from datetime import datetime
import os
from aiohttp import web  # Render ke liye zaroori hai

# --- TESTING CREDENTIALS (FILLED) ---
API_ID = 37314366
API_HASH = "bd4c934697e7e91942ac911a5a287b46"
BOT_TOKEN = "8319710991:AAEQMtAC0t_r3lwyg7sGXWH18CXsExQ3jF8"

# Global variables
user_sessions = {}
cleanup_task = None

# Bot ID aur Session Name setup
bot_id = BOT_TOKEN.split(":")[0]
session_name = f"my_bot_{bot_id}"

app = Client(
    session_name, 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN
)

# --- FAKE WEB SERVER FOR RENDER ---
# Ye Render ko 24/7 active rakhne ke liye zaroori hai
async def web_server():
    async def handle(request):
        return web.Response(text="Testing Bot is Running on Render!")
    
    app_web = web.Application()
    app_web.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app_web)
    await runner.setup()
    # Render automatically PORT assign karta hai
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🕸️ Web server started on port {port}")

# --- CLEANUP FUNCTION ---
async def cleanup_expired_sessions():
    """Clean up expired user sessions every minute"""
    while True:
        try:
            current_time = time.time()
            expired_users = []
            
            for user_id, session_data in list(user_sessions.items()):
                if current_time - session_data.get("timestamp", 0) > 600:  # 10 minutes
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                try:
                    if user_id in user_sessions and user_sessions[user_id].get("client"):
                        await user_sessions[user_id]["client"].disconnect()
                    del user_sessions[user_id]
                except:
                    pass
            
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Cleanup error: {e}")
            await asyncio.sleep(60)

# --- BOT COMMANDS ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        "🤖 **Testing Session Bot**\n\n"
        "This is a testing bot running on Render.\n"
        "Send /get to generate session."
    )

@app.on_message(filters.command("get"))
async def get_session(client, message):
    user_id = message.from_user.id
    
    if user_id in user_sessions:
        await message.reply("⚠️ Session process already running. Type /cancel first.")
        return
    
    user_sessions[user_id] = {
        "step": "phone",
        "phone": None,
        "client": None,
        "phone_code_hash": None,
        "timestamp": time.time()
    }
    
    await message.reply(
        "📱 **Testing Mode**\n\n"
        "Please send your phone number:\n"
        "Example: `+919876543210`"
    )

@app.on_message(filters.command("cancel"))
async def cancel_session(client, message):
    user_id = message.from_user.id
    
    if user_id in user_sessions:
        if user_sessions[user_id].get("client"):
            try:
                await user_sessions[user_id]["client"].disconnect()
            except:
                pass
        del user_sessions[user_id]
        await message.reply("✅ Cancelled.")
    else:
        await message.reply("⚠️ Nothing to cancel.")

# Function to get session string
async def get_session_string(temp_client):
    session_string = None
    try:
        session_string = await temp_client.export_session_string()
        return session_string
    except:
        pass
    
    try:
        session_string = temp_client.export_session_string()
        if asyncio.iscoroutine(session_string):
            session_string = await session_string
        return session_string
    except:
        pass

    return "ERROR: Could not generate session string"

@app.on_message(filters.text & filters.private)
async def handle_text(client, message):
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        return
    
    text = message.text.strip()
    
    # Timeout check
    if time.time() - user_sessions[user_id]["timestamp"] > 600:
        if user_sessions[user_id].get("client"):
            try: await user_sessions[user_id]["client"].disconnect()
            except: pass
        del user_sessions[user_id]
        await message.reply("⏰ Time out. Start again with /get")
        return
    
    step = user_sessions[user_id]["step"]
    
    # Step 1: Phone
    if step == "phone":
        if text.lower() == "/cancel":
            await cancel_session(client, message)
            return
        
        user_sessions[user_id]["phone"] = text
        user_sessions[user_id]["step"] = "otp"
        user_sessions[user_id]["timestamp"] = time.time()
        
        try:
            temp_client = Client(
                f"session_memory_{user_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                in_memory=True,
                no_updates=True
            )
            
            await temp_client.connect()
            sent_code = await temp_client.send_code(text)
            
            user_sessions[user_id]["client"] = temp_client
            user_sessions[user_id]["phone_code_hash"] = sent_code.phone_code_hash
            
            await message.reply("✅ OTP Sent! Send the code (e.g., `1 2 3 4 5`).")
            
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")
            if user_id in user_sessions: del user_sessions[user_id]
    
    # Step 2: OTP
    elif step == "otp":
        if text.lower() == "/cancel":
            await cancel_session(client, message)
            return
        
        otp = text.replace(" ", "")
        
        try:
            phone = user_sessions[user_id]["phone"]
            temp_client = user_sessions[user_id]["client"]
            phone_code_hash = user_sessions[user_id]["phone_code_hash"]
            
            try:
                await temp_client.sign_in(phone, phone_code_hash, otp)
            except Exception as e:
                if "SESSION_PASSWORD_NEEDED" in str(e):
                    user_sessions[user_id]["step"] = "2fa"
                    user_sessions[user_id]["timestamp"] = time.time()
                    await message.reply("🔐 2FA Password Required. Please send it.")
                    return
                else:
                    raise e
            
            # Success
            session_string = await get_session_string(temp_client)
            await message.reply(f"🎉 **Session:**\n\n`{session_string}`")
            
            await temp_client.disconnect()
            del user_sessions[user_id]
            
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")
            if "PHONE_CODE" not in str(e) and "PASSWORD" not in str(e):
                if user_id in user_sessions: del user_sessions[user_id]

    # Step 3: 2FA
    elif step == "2fa":
        try:
            temp_client = user_sessions[user_id]["client"]
            await temp_client.check_password(text)
            
            session_string = await get_session_string(temp_client)
            await message.reply(f"🎉 **Session:**\n\n`{session_string}`")
            
            await temp_client.disconnect()
            del user_sessions[user_id]
            
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")

# --- MAIN EXECUTION ---
async def main():
    print("🚀 Testing Bot Starting...")
    
    # Start Bot
    await app.start()
    print("✅ Bot is running!")
    
    # Start Web Server (For Render)
    global cleanup_task
    cleanup_task = asyncio.create_task(cleanup_expired_sessions())
    await web_server()
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Stopped!")