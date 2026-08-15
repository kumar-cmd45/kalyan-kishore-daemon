import os
import json
import requests
import telebot
from flask import Flask
import threading

# Configuration
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Kalyan Kishore Master Daemon is Live!"

def get_vault_files():
    """Fetches list of all files inside memory_vault/."""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    url = f"https://huggingface.co/api/models/{VAULT_REPO}/tree/main/memory_vault?recursive=true"
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            return [f["path"] for f in res.json()]
    except Exception as e:
        print(f"Vault fetch notice: {e}")
    return []

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 <b>Kalyan Kishore Master Daemon</b>\n\n"
        "Commands:\n"
        "• <code>/status</code> - View live telemetry & counts\n"
        "• <code>/bounties</code> - Get latest verified bounty code & submission URL\n"
        "• <code>/vault</code> - Hugging Face storage direct link",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['status', 'vault'])
def send_status(message):
    files = get_vault_files()
    bounties = [f for f in files if "bounties/" in f]
    quant = [f for f in files if "quant_finance/" in f]
    algo = [f for f in files if "algo_systems/" in f]
    cyber = [f for f in files if "cyber_ast/" in f]

    status_msg = (
        f"=== LIVE SYSTEM TELEMETRY ===\n"
        f"• Vault Repository: {VAULT_REPO}\n"
        f"• Total Verified Trajectories: {len(files)}\n"
        f"  - Quantitative Finance: {len(quant)}\n"
        f"  - Algorithmic Systems: {len(algo)}\n"
        f"  - Cyber Security AST: {len(cyber)}\n"
        f"  - Verified Bounties: {len(bounties)}\n"
        f"• Background Worker: GitHub Actions (24/7 cron)\n"
        f"=============================="
    )
    bot.reply_to(message, f"```\n{status_msg}\n```", parse_mode="Markdown")

@bot.message_handler(commands=['bounties', 'latest_bounty'])
def send_bounties(message):
    files = get_vault_files()
    bounty_files = sorted([f for f in files if "bounties/" in f])
    
    if not bounty_files:
        bot.reply_to(message, "📭 No verified bounty solutions found in vault yet.")
        return

    # Pull the latest verified bounty JSON
    latest_file = bounty_files[-1]
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    raw_url = f"https://huggingface.co/{VAULT_REPO}/raw/main/{latest_file}"
    
    try:
        data = requests.get(raw_url, headers=headers, timeout=10).json()
        task = data.get("task", {})
        solution = data.get("solution", "No solution payload.")
        badge = data.get("badge", "Triple Consensus Verified")

        title = task.get("title", "Open Source / Web3 Bounty")
        platform = task.get("platform", "Bounty Network")
        reward = task.get("reward", "Reward Specified on Portal")
        url = task.get("url", "https://github.com")

        import html
        clean_solution = html.escape(solution[:1400])
        clean_title = html.escape(title[:75])

        msg = (
            f"🎯 <b>Latest Verified Bounty ({len(bounty_files)} Total in Vault)</b>\n\n"
            f"• <b>Platform:</b> {platform}\n"
            f"• <b>Reward:</b> <code>{reward}</code>\n"
            f"• <b>Status:</b> <code>{badge}</code>\n"
            f"• <b>Task:</b> <a href='{url}'>{clean_title}</a>\n\n"
            f"📝 <b>Pre-Verified Solution (Ready to Paste):</b>\n"
            f"<pre>{clean_solution}</pre>\n\n"
            f"👉 <a href='{url}'><b>[Click Here to Open Task & Submit]</b></a>"
        )
        bot.send_message(message.chat.id, msg, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error parsing bounty file: {str(e)}")

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(timeout=20, long_polling_timeout=10), daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
    
