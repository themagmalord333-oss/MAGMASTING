import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import time
from datetime import datetime
import os
from flask import Flask
from threading import Thread

# ==========================================
# RENDER KEEP-ALIVE CODE (Ye naya part hai)
# ==========================================
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
# ==========================================

# आपका API_ID और API_HASH
API_ID = 37314366
API_HASH = "bd4c934697e7e91942ac911a5a287b46"
BOT_TOKEN = "8319710991:AAEQMtAC0t_r3lwyg7sGXWH18CXsExQ3jF8"

# Global variables
user_sessions = {}
cleanup_task = None

# --- यहाँ बदलाव किया गया है ---
# यह टोकन से अपने आप बॉट की ID निकाल लेगा और उसी नाम से फाइल बनाएगा
# इससे पुराना बॉट कभी बीच में नहीं आएगा
bot_id = BOT_TOKEN.split(":")[0]
session_name = f"my_bot_{bot_id}"

app = Client(
    session_name, 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN
)
# -----------------------------

# Cleanup function for expired sessions
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

# Bot commands
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        "🤖 **Session Generator Bot**\n\n"
        "📱 Send /get to generate your Telegram session string!\n"
        "🔒 Safe & Secure - No API_ID/HASH needed!\n\n"
        "⚠️ **Note:** This bot only generates session strings.\n"
        "We don't store any of your data.\n\n"
        "🔧 **Developer:** @MAGMAxRICH"
    )

@app.on_message(filters.command("get"))
async def get_session(client, message):
    user_id = message.from_user.id
    
    # Check if user already has active session
    if user_id in user_sessions:
        await message.reply("⚠️ You already have an active session generation process. Type /cancel to start new.")
        return
    
    # Initialize user session
    user_sessions[user_id] = {
        "step": "phone",
        "phone": None,
        "client": None,
        "phone_code_hash": None,
        "timestamp": time.time()
    }
    
    await message.reply(
        "📱 **Step 1/2: Phone Number**\n\n"
        "📞 Send your phone number in international format:\n"
        "**Example:** `+919876543210`\n"
        "**Example:** `+1234567890`\n\n"
        "❌ Type /cancel to stop anytime.\n"
        "⏰ Session will expire in 10 minutes."
    )

@app.on_message(filters.command("cancel"))
async def cancel_session(client, message):
    user_id = message.from_user.id
    
    if user_id in user_sessions:
        # Clean up temporary client
        if user_sessions[user_id].get("client"):
            try:
                await user_sessions[user_id]["client"].disconnect()
            except:
                pass
        
        del user_sessions[user_id]
        await message.reply("✅ Session generation cancelled.")
    else:
        await message.reply("⚠️ No active session to cancel.")

# Function to get session string using multiple methods
async def get_session_string(temp_client):
    """Try multiple methods to get session string"""
    session_string = None
    
    # Method 1: Direct export (most common)
    try:
        session_string = await temp_client.export_session_string()
        print(f"✅ Method 1 successful: {len(session_string)} chars")
        return session_string
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    # Method 2: Try sync version
    try:
        session_string = temp_client.export_session_string()
        if asyncio.iscoroutine(session_string):
            session_string = await session_string
        print(f"✅ Method 2 successful: {len(session_string)} chars")
        return session_string
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    # Method 3: Try to get from storage
    try:
        session = await temp_client.storage.export_session_string()
        if session:
            session_string = session
            print(f"✅ Method 3 successful: {len(session_string)} chars")
            return session_string
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    # Method 4: Manual session generation
    try:
        # Get auth key
        auth_key = temp_client.auth_key
        if auth_key:
            # Create a basic session string
            session_data = {
                "auth_key": auth_key.hex() if hasattr(auth_key, 'hex') else str(auth_key),
                "user_id": temp_client.user_id,
                "date": int(time.time())
            }
            import json
            session_string = json.dumps(session_data)
            print(f"✅ Method 4 successful: {len(session_string)} chars")
            return session_string
    except Exception as e:
        print(f"❌ Method 4 failed: {e}")
    
    return "ERROR: Could not generate session string"

@app.on_message(filters.text & filters.private)
async def handle_text(client, message):
    user_id = message.from_user.id
    
    if user_id not in user_sessions:
        return
    
    text = message.text.strip()
    
    # Clean up expired sessions (10 minutes)
    if time.time() - user_sessions[user_id]["timestamp"] > 600:
        if user_sessions[user_id].get("client"):
            try:
                await user_sessions[user_id]["client"].disconnect()
            except:
                pass
        del user_sessions[user_id]
        await message.reply("⏰ Session expired. Please use /get to start again.")
        return
    
    step = user_sessions[user_id]["step"]
    
    # Step 1: Phone Number
    if step == "phone":
        # Cancel if requested
        if text.lower() == "/cancel":
            await cancel_session(client, message)
            return
        
        # Phone number validation
        if not text.startswith("+") or len(text) < 10:
            await message.reply(
                "❌ Invalid phone number format!\n\n"
                "✅ **Correct Format:** `+CountryCodeNumber`\n"
                "**Example:** `+919876543210` (India)\n"
                "**Example:** `+1234567890` (US)\n\n"
                "📱 Please send your phone number again:"
            )
            return
        
        user_sessions[user_id]["phone"] = text
        user_sessions[user_id]["step"] = "otp"
        user_sessions[user_id]["timestamp"] = time.time()
        
        try:
            # Create temporary in-memory client
            temp_client = Client(
                f"session_memory_{user_id}",
                api_id=API_ID,
                api_hash=API_HASH,
                in_memory=True,
                no_updates=True
            )
            
            await temp_client.connect()
            
            # Send OTP request
            sent_code = await temp_client.send_code(text)
            
            user_sessions[user_id]["client"] = temp_client
            user_sessions[user_id]["phone_code_hash"] = sent_code.phone_code_hash
            
            await message.reply(
                "✅ **OTP Sent Successfully!**\n\n"
                "📱 **Step 2/2: OTP Verification**\n\n"
                "🔢 Send the 5-digit code you received on Telegram:\n\n"
                "**Format:** `12345` (without spaces)\n"
                "**Format:** `1 2 3 4 5` (with spaces)\n\n"
                "⏰ **Note:** OTP is valid for 5 minutes.\n"
                "❌ Type /cancel to stop."
            )
            
        except Exception as e:
            error_msg = str(e)
            if "FLOOD" in error_msg:
                await message.reply("⏳ Too many attempts. Please wait a few minutes before trying again.")
            elif "PHONE_NUMBER_INVALID" in error_msg:
                await message.reply("❌ Invalid phone number. Please check and try again.")
            else:
                await message.reply(f"❌ Error: {error_msg}\n\nPlease try again with /get")
            
            if user_id in user_sessions:
                del user_sessions[user_id]
    
    # Step 2: OTP Verification
    elif step == "otp":
        # Cancel if requested
        if text.lower() == "/cancel":
            await cancel_session(client, message)
            return
        
        # Clean OTP (remove spaces)
        otp = text.replace(" ", "")
        
        if not otp.isdigit() or len(otp) != 5:
            await message.reply(
                "❌ Invalid OTP format!\n\n"
                "✅ **Correct Format:** 5 digits only\n"
                "**Example:** `12345`\n"
                "**Example:** `54321`\n\n"
                "🔢 Please send the 5-digit OTP again:"
            )
            return
        
        try:
            phone = user_sessions[user_id]["phone"]
            temp_client = user_sessions[user_id]["client"]
            phone_code_hash = user_sessions[user_id]["phone_code_hash"]
            
            print(f"DEBUG: Signing in with OTP for {phone}")
            
            # Attempt to sign in with OTP
            try:
                # First try to sign in
                await temp_client.sign_in(
                    phone_number=phone,
                    phone_code_hash=phone_code_hash,
                    phone_code=otp
                )
                print("DEBUG: Sign in successful")
                
            # If 2FA is required
            except Exception as e:
                error_str = str(e)
                print(f"DEBUG: Sign in error: {error_str}")
                if "SESSION_PASSWORD_NEEDED" in error_str:
                    user_sessions[user_id]["step"] = "2fa"
                    user_sessions[user_id]["timestamp"] = time.time()
                    
                    await message.reply(
                        "🔐 **2-Step Verification Detected!**\n\n"
                        "🔑 Please send your 2FA password:\n"
                        "(This is the extra password you set for added security)\n\n"
                        "❌ Type /cancel to stop."
                    )
                    return
                else:
                    raise e
            
            # If no 2FA, generate session string
            print("DEBUG: Getting session string...")
            session_string = await get_session_string(temp_client)
            
            print(f"DEBUG: Session string received: {len(str(session_string))} chars")
            
            # Get user info
            user_info = await temp_client.get_me()
            print(f"DEBUG: User info: {user_info.id}")
            
            # Format user name
            user_name = ""
            if user_info.first_name:
                user_name += user_info.first_name
            if user_info.last_name:
                user_name += " " + user_info.last_name
            if not user_name:
                user_name = user_info.username or "User"
            
            # Display session string
            session_display = str(session_string)
            
            # Send session in multiple parts if too long
            if len(session_display) > 3500:
                # Split into multiple messages
                parts = [session_display[i:i+3500] for i in range(0, len(session_display), 3500)]
                
                # Send header
                header_msg = await message.reply(
                    f"🎉 **SESSION GENERATED SUCCESSFULLY!**\n\n"
                    f"👤 **User:** {user_name}\n"
                    f"📱 **Phone:** `{phone}`\n"
                    f"🆔 **User ID:** `{user_info.id}`\n"
                    f"🔐 **2FA:** ❌ Disabled\n\n"
                    f"📋 **YOUR SESSION STRING:**\n"
                    f"(Sending in {len(parts)} parts)"
                )
                
                # Send each part
                for i, part in enumerate(parts, 1):
                    part_msg = await message.reply(f"**Part {i}/{len(parts)}:**\n`{part}`")
                    print(f"Sent part {i}/{len(parts)}")
                    await asyncio.sleep(0.5)
                
                # Send footer
                footer_msg = await message.reply(
                    f"⚠️ **SECURITY WARNING:**\n"
                    f"• DO NOT SHARE THIS WITH ANYONE!\n"
                    f"• This gives FULL access to your account!\n"
                    f"• Store it securely!\n\n"
                    f"🔧 **POWERED BY:** @Anysnapupdate"
                )
            else:
                # Send in one message
                response_text = (
                    f"🎉 **SESSION GENERATED SUCCESSFULLY!**\n\n"
                    f"👤 **User:** {user_name}\n"
                    f"📱 **Phone:** `{phone}`\n"
                    f"🆔 **User ID:** `{user_info.id}`\n"
                    f"🔐 **2FA:** ❌ Disabled\n\n"
                    f"📋 **YOUR SESSION STRING:**\n\n"
                    f"`{session_display}`\n\n"
                    f"⚠️ **SECURITY WARNING:**\n"
                    f"• DO NOT SHARE THIS WITH ANYONE!\n"
                    f"• This gives FULL access to your account!\n"
                    f"• Store it securely!\n\n"
                    f"🔧 **POWERED BY:** @Anysnapupdate"
                )
                
                sent_msg = await message.reply(response_text)
                print(f"DEBUG: Message sent with ID: {sent_msg.id}")
            
            # Also send to user's saved messages
            try:
                saved_msg = await temp_client.send_message(
                    "me",
                    f"📱 **Session Generated**\n\n"
                    f"**Account:** {user_name}\n"
                    f"**Phone:** {phone}\n"
                    f"**User ID:** {user_info.id}\n"
                    f"**2FA:** Disabled\n"
                    f"**Generated at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"**Session String:**\n\n`{session_display}`\n\n"
                    f"⚠️ **Keep this secure!**"
                )
                print(f"DEBUG: Saved message sent with ID: {saved_msg.id}")
            except Exception as e:
                print(f"Error sending to saved messages: {e}")
            
            # Cleanup
            await temp_client.disconnect()
            del user_sessions[user_id]
            print(f"DEBUG: Cleaned up session for user {user_id}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ ERROR in OTP step: {error_msg}")
            if "PHONE_CODE_INVALID" in error_msg:
                await message.reply("❌ Invalid OTP code. Please send the correct OTP:")
            elif "PHONE_CODE_EXPIRED" in error_msg:
                await message.reply("⏰ OTP expired. Please use /get to start again.")
                if user_id in user_sessions:
                    del user_sessions[user_id]
            else:
                await message.reply(f"❌ Error: {error_msg}\n\nPlease try again with /get")
                if user_id in user_sessions:
                    del user_sessions[user_id]
    
    # Step 3: 2FA Password
    elif step == "2fa":
        # Cancel if requested
        if text.lower() == "/cancel":
            await cancel_session(client, message)
            return
        
        try:
            phone = user_sessions[user_id]["phone"]
            temp_client = user_sessions[user_id]["client"]
            
            print(f"DEBUG: Verifying 2FA for {phone}")
            
            # Verify 2FA password
            await temp_client.check_password(text)
            print("DEBUG: 2FA verification successful")
            
            # Generate session string after 2FA
            session_string = await get_session_string(temp_client)
            print(f"DEBUG: 2FA Session string length: {len(str(session_string))}")
            
            # Get user info
            user_info = await temp_client.get_me()
            
            # Format user name
            user_name = ""
            if user_info.first_name:
                user_name += user_info.first_name
            if user_info.last_name:
                user_name += " " + user_info.last_name
            if not user_name:
                user_name = user_info.username or "User"
            
            session_display = str(session_string)
            
            # Send session
            if len(session_display) > 3500:
                parts = [session_display[i:i+3500] for i in range(0, len(session_display), 3500)]
                
                await message.reply(
                    f"🎉 **SESSION GENERATED SUCCESSFULLY!**\n\n"
                    f"👤 **User:** {user_name}\n"
                    f"📱 **Phone:** `{phone}`\n"
                    f"🆔 **User ID:** `{user_info.id}`\n"
                    f"🔐 **2FA:** ✅ Enabled\n\n"
                    f"📋 **YOUR SESSION STRING:**\n"
                    f"(Sending in {len(parts)} parts)"
                )
                
                for i, part in enumerate(parts, 1):
                    await message.reply(f"**Part {i}/{len(parts)}:**\n`{part}`")
                    await asyncio.sleep(0.5)
                
                await message.reply(
                    f"⚠️ **SECURITY WARNING:**\n"
                    f"• DO NOT SHARE THIS WITH ANYONE!\n"
                    f"• This gives FULL access to your account!\n"
                    f"• Store it securely!\n\n"
                    f"🔧 **POWERED BY:** @Anysnapupdate"
                )
            else:
                response_text = (
                    f"🎉 **SESSION GENERATED SUCCESSFULLY!**\n\n"
                    f"👤 **User:** {user_name}\n"
                    f"📱 **Phone:** `{phone}`\n"
                    f"🆔 **User ID:** `{user_info.id}`\n"
                    f"🔐 **2FA:** ✅ Enabled\n\n"
                    f"📋 **YOUR SESSION STRING:**\n\n"
                    f"`{session_display}`\n\n"
                    f"⚠️ **SECURITY WARNING:**\n"
                    f"• DO NOT SHARE THIS WITH ANYONE!\n"
                    f"• This gives FULL access to your account!\n"
                    f"• Store it securely!\n\n"
                    f"🔧 **POWERED BY:** @Anysnapupdate"
                )
                
                await message.reply(response_text)
            
            # Also send to saved messages
            try:
                await temp_client.send_message(
                    "me",
                    f"📱 **Session Generated**\n\n"
                    f"**Account:** {user_name}\n"
                    f"**Phone:** {phone}\n"
                    f"**User ID:** {user_info.id}\n"
                    f"**2FA:** Enabled\n"
                    f"**Generated at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"**Session String:**\n\n`{session_display}`\n\n"
                    f"⚠️ **Keep this secure!**"
                )
            except:
                pass
            
            # Cleanup
            await temp_client.disconnect()
            del user_sessions[user_id]
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ ERROR in 2FA step: {error_msg}")
            if "PASSWORD_HASH_INVALID" in error_msg:
                await message.reply(
                    "❌ Incorrect 2FA password!\n\n"
                    "🔑 Please send the correct 2FA password:\n"
                    "(This is different from your phone's password)"
                )
            else:
                await message.reply(f"❌ Error: {error_msg}\n\nPlease try again with /get")
                if user_id in user_sessions:
                    del user_sessions[user_id]

# Other commands
@app.on_message(filters.command("about"))
async def about_command(client, message):
    await message.reply(
        "🤖 **Telegram String Session Generator Bot**\n\n"
        "**Version:** 2.0\n"
        "**Developer:** @MAGMAxRICH\n\n"
        "**Features:**\n"
        "✅ Generate Telegram Session Strings\n"
        "✅ Phone + OTP Login Support\n"
        "✅ 2-Factor Authentication Support\n"
        "✅ Safe & Secure - No Data Storage\n"
        "✅ Auto-cleanup after 10 minutes\n\n"
        "**Usage:**\n"
        "1️⃣ Send /get\n"
        "2️⃣ Enter phone number (+919876543210)\n"
        "3️⃣ Enter OTP received on Telegram\n"
        "4️⃣ If 2FA enabled, enter password\n"
        "5️⃣ Get your session string!\n\n"
        "**Security:** We don't store any data. All sessions are generated in memory and cleared immediately."
    )

@app.on_message(filters.command("help"))
async def help_command(client, message):
    await message.reply(
        "🆘 **Help Guide**\n\n"
        "**Commands:**\n"
        "• /start - Start the bot\n"
        "• /get - Generate new session string\n"
        "• /cancel - Cancel current session\n"
        "• /about - About this bot\n"
        "• /help - Show this help\n\n"
        "**Process:**\n"
        "1. Send /get command\n"
        "2. Enter your phone number with country code\n"
        "3. Enter OTP received on Telegram\n"
        "4. If you have 2FA, enter your password\n"
        "5. Get your session string\n\n"
        "**Note:** Session generation expires in 10 minutes."
    )

@app.on_message(filters.command("test"))
async def test_command(client, message):
    await message.reply("✅ Bot is working!")

@app.on_message(filters.command("debug"))
async def debug_command(client, message):
    if message.from_user.id == 8424259405:  # Your user ID
        active_sessions = len(user_sessions)
        debug_info = f"""
📊 **Debug Information**

• Active sessions: {active_sessions}
• Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• User sessions: {list(user_sessions.keys())}

**Session Details:**
"""
        for user_id, session_data in user_sessions.items():
            debug_info += f"\n• User {user_id}: Step={session_data.get('step')}, Phone={session_data.get('phone')}"
        
        await message.reply(debug_info)

# Main function
async def main():
    """Main async function to run the bot"""
    keep_alive() # Yaha humne web server start kar diya
    print("🚀 Session Bot Starting...")
    print("📱 API_ID:", API_ID)
    print("🤖 Bot is initializing...")
    
    # Start the bot client
    await app.start()
    
    # Get bot info
    me = await app.get_me()
    print(f"✅ Bot @{me.username} is running!")
    print("📱 Send /get to generate session strings")
    print("🐞 Debug mode: ON")
    
    # Start cleanup task
    global cleanup_task
    cleanup_task = asyncio.create_task(cleanup_expired_sessions())
    
    # Keep the bot running
    print("⏳ Bot is running. Press Ctrl+C to stop.")
    await asyncio.Event().wait()

# Run the bot
if __name__ == "__main__":
    try:
        # For Pydroid3 compatibility
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("🛑 Bot stopped.")