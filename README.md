
<div align="center">

<img src="https://i.ibb.co/wFFyNCLK/x.jpg" alt="Magma Header" width="100%">

# 🤖 MAGMA SESSION GENERATOR

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=25&duration=3000&pause=1000&color=F7F7F7&center=true&vCenter=true&width=800&height=60&lines=Ultra+Fast+Telegram+Session+Generator;Lightning+Fast+Async+Generation;Secure+In-Memory+Session+Storage;Built+For+Performance;Modern+Force-Subscribe+System;Easy+Deployment+On+Cloud;24%2F7+Uptime+With+Flask;Developer+Friendly+Architecture" alt="Typing SVG" />
</p>

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-v2.0+-red.svg?logo=telegram&logoColor=white)](https://docs.pyrogram.org/)
[![Flask](https://img.shields.io/badge/Flask-KeepAlive-lightgrey.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<br>

<div align="center">
  <img src="https://i.ibb.co/b5g28nD1/x.jpg" alt="Project Preview" width="800">
</div>

</div>

---

## 🔗 The Magma Ecosystem
This project is an essential part of the **Magma Ecosystem**. While this tool handles secure **Session Generation**, it is designed to seamlessly work with [Snapbot](https://github.com/themagmalord333-oss/Magmasnapbot). 

> **Workflow:** Use this tool to generate your secure Pyrogram String Session, then input that session into **Snapbot** to unlock the full power of the Magma Userbot suite.

---

## ✨ About
**Magma Session Generator** is a high-performance, asynchronous Telegram session string generator bot. It provides a secure, streamlined environment for users to generate Pyrogram-compatible session strings without exposing their API credentials. Featuring a built-in Force-Subscribe system and 24/7 uptime monitoring via Flask, it ensures reliable access management.

---

## 🚀 Key Features
* **Async/Await Engine:** Built on Pyrogram for ultra-fast performance.
* **In-Memory Sessions:** Uses `in_memory=True` for security, ensuring no session files touch the local disk.
* **Smart Force-Subscribe:** Advanced membership verification for multiple channels/groups.
* **24/7 Keep-Alive:** Integrated Flask server for seamless cloud deployment (Render, Heroku, etc.).
* **Safe Authentication:** Handles OTP and 2FA password verification securely.
* **Magma Ready:** Perfectly compatible with [Snapbot](https://github.com/themagmalord333-oss/Magmasnapbot).

---

## 🏗 Architecture
* **Web Layer:** A Flask-based keep-alive monitor running on `0.0.0.0`.
* **Bot Layer:** A centralized Pyrogram client handling commands and stateful conversation flows.
* **Session Layer:** Dynamic, temporary `in_memory` Pyrogram clients spawned per-user for session generation.

---

## 📁 Folder Structure
```text
MAGMA-SESSION/
├── .env                  # Environment Variables
├── main.py               # Core Bot & Flask logic
└── requirements.txt      # Project Dependencies

```
## 🛠 Installation
 1. **Clone the repository:**
   ```bash
   git clone [https://github.com/themagmalord333-oss/magma-session](https://github.com/themagmalord333-oss/magma-session)
   cd magma-session
   
   ```
 2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   
   ```
 3. **Configure:**
   Fill in your details in the .env file.
 4. **Start:**
   ```bash
   python main.py
   
   ```
## 🔑 Environment Variables
| Variable | Description |
|---|---|
| API_ID | Telegram API ID |
| API_HASH | Telegram API Hash |
| BOT_TOKEN | BotFather Token |
| CHANNEL_X_ID | Numeric Channel IDs for Force-Sub |
| CHANNEL_X_URL | Invite links for channels |
| PORT | Web server port |
## 📚 Commands Reference
### General Commands
| Command | Description |
|---|---|
| /start | Welcome and access check. |
| /get | Initiates the session generation flow. |
| /cancel | Aborts the current session generation process. |
## 🛡 Security
 * **Memory Isolation:** Temporary session clients are explicitly disconnected and deleted after completion.
 * **State Expiry:** User session state automatically expires after 10 minutes of inactivity.
 * **No Disk Persistence:** All generation happens in RAM.
## ❤️ Credits
Built with precision by **MAGMA**.
Connected Ecosystem: Snapbot
## 📜 License
This project is licensed under the MIT License.
