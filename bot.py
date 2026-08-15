import os
import json
import requests
import telebot
from flask import Flask

# 1. Config
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running live!"

# Helper to fetch vault stats & latest bounty
def fetch_vault_info():
    url = f"https://huggingface.co/api/models/{VAULT_REPO}/tree/main/memory_vault?recursive=true"
    res = requests.get(url, timeout=10)
    files = [f["path"] for f in res.json()] if res.status_code == 200 else []
    
    bounties = [f for f in files if "bounties/" in f]
    return len(files), len(bounties), bounties

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 **Kalyan Kishore Master Daemon is Active**\n\n"
        "Commands:\n"
        "• `/vault` - View Hugging Face vault metrics\n"
        "• `/status` - Live telemetry status\n"
        "• `/bounties` - View and submit the latest verified bounty fix"
    )

@bot.message_handler(commands=['status', 'vault'])
def send_status(message):
    total, bounty_count, _ = fetch_vault_info()
    status_msg = (
        f"=== LIVE SYSTEM TELEMETRY ===\n"
        f"• Vault Repository: {VAULT_REPO}\n"
        f"• Total Verified Trajectories: {total}\n"
        f"• Verified Bounties: {bounty_count}\n"
        f"• Background Worker: GitHub Actions (24/7 cron)\n"
        f"=============================="
    )
    bot.reply_to(message, f"```\n{status_msg}\n```", parse_mode="Markdown")

@bot.message_handler(commands=['bounties', 'latest_bounty'])
def send_bounty(message):
    try:
        _, bounty_count, bounties = fetch_vault_info()
        if not bounties:
            bot.reply_to(message, "📭 No verified bounties generated yet.")
            return

        # Fetch latest bounty JSON
        latest_file = sorted(bounties)[-1]
        raw_url = f"https://huggingface.co/{VAULT_REPO}/raw/main/{latest_file}"
        data = requests.get(raw_url, timeout=10).json()

        task = data.get("task", {})
        solution = data.get("solution", "No solution text")
        title = task.get("title", "Bounty Task")
        url = task.get("url", "https://github.com")
        reward = task.get("reward", "Bounty")
        platform = task.get("platform", "Web Platform")

        msg = (
            f"🎯 <b>Latest Verified Bounty ({bounty_count} in Vault)</b>\n\n"
            f"• <b>Platform:</b> {platform}\n"
            f"• <b>Reward:</b> {reward}\n"
            f"• <b>Task:</b> <a href='{url}'>{title}</a>\n\n"
            f"📝 <b>Pre-Verified Solution:</b>\n"
            f"<pre>{solution[:1500]}</pre>\n\n"
            f"👉 <a href='{url}'>Click here to open and submit fix</a>"
        )
        bot.send_message(message.chat.id, msg, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error fetching bounty: {str(e)}")

# Fallback generic message
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Send `/bounties` to view the latest ready-to-paste solution, or `/status` for live telemetry.")

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: bot.infinity_polling(timeout=20, long_polling_timeout=10), daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
    
