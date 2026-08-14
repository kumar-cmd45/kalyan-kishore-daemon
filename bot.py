import os
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

bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else None

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Kalyan Kishore Bot Daemon is Online 24/7!"

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

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🤖 *Kalyan Kishore 24/7 Cloud Bot Online*\n\nSend any prompt to chat directly.", parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def check_status(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        files = hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model") if hf_api else []
        traces = [f for f in files if f.startswith("memory_vault/") and f.endswith(".json")]
        reply = f"📊 *Vault Status*\n• Trajectories: `{len(traces)}`\n• Host: `Render.com Cloud`"
    except Exception as e:
        reply = f"⚠️ Notice: {e}"
    bot.reply_to(message, reply, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_ai(message.text)
    bot.reply_to(message, reply)

def run_bot():
    print("🚀 Starting Telegram Polling Loop...")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
