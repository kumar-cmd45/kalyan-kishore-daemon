import os
import time
import threading
import telebot
from flask import Flask
from groq import Groq
from google import genai
from huggingface_hub import HfApi

# 1. Environment Secrets
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

# Initialize Clients
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else None

app = Flask(__name__)

# Health-Check Web Endpoint (Prevents Render Sleep)
@app.route('/')
@app.route('/health')
def health():
    return "🚀 Kalyan Kishore Bot is Online & Awake 24/7!", 200

# AI Model Waterfall Engine
def ask_ai(prompt: str) -> str:
    if groq_client:
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                res = groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=1200
                )
                if res.choices and res.choices[0].message.content:
                    return res.choices[0].message.content
            except Exception:
                continue

    if gemini_client:
        for model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                res = gemini_client.models.generate_content(model=model, contents=prompt)
                if res and res.text:
                    return res.text
            except Exception:
                continue

    return "⚠️ System notice: Upstream inference endpoints are busy. Please try again shortly."

# Handlers
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "🤖 *Kalyan Kishore 24/7 Cloud Bot Online*\n\n"
        "• `/status` — View Vault metrics & cloud health\n"
        "• `/vault` — Inspect stored trajectories\n"
        "• Send any prompt to chat directly."
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def check_status(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        files = hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model") if hf_api else []
        traces = [f for f in files if f.startswith("memory_vault/") and f.endswith(".json")]
        reply = (
            "📊 *System & Vault Status*\n\n"
            f"• *Vault Repository:* `{VAULT_REPO}`\n"
            f"• *Verified Trajectories:* `{len(traces)}`\n"
            f"• *Cloud Host:* Render.com (24/7 Alive)\n"
            f"• *Worker:* GitHub Actions (`kalyan-kishore-daemon`)"
        )
    except Exception as e:
        reply = f"⚠️ Notice: {e}"
    bot.reply_to(message, reply, parse_mode="Markdown")

@bot.message_handler(commands=['vault'])
def check_vault(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        files = hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model") if hf_api else []
        traces = [f for f in files if f.startswith("memory_vault/") and f.endswith(".json")]
        if not traces:
            bot.reply_to(message, "📭 Vault is currently empty.")
            return

        vault_msg = (
            "🏛️ *Hugging Face Memory Vault*\n\n"
            f"• *Repository:* `{VAULT_REPO}`\n"
            f"• *Total Verified Solutions:* `{len(traces)}`\n"
            f"• *Latest Entry:* `{sorted(traces)[-1]}`\n\n"
            f"👉 [Open Vault on Hugging Face](https://huggingface.co/{VAULT_REPO}/tree/main/memory_vault)"
        )
        bot.reply_to(message, vault_msg, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(func=lambda msg: True)
def handle_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_ai(message.text)
    bot.reply_to(message, reply)

# Resilient Polling Worker
def start_bot():
    print("🚀 Telegram polling loop initialized.")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"⚠️ Polling reconnecting: {e}")
            time.sleep(3)

if __name__ == "__main__":
    # Start bot listener in background thread
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()
    
    # Run web server for keepalive pings on port assigned by Render
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
