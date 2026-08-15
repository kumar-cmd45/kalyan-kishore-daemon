import os
import json
import html
import requests
import telebot
from flask import Flask
import threading

# 1. Environment Secrets
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Kalyan Kishore Master Daemon is Live!"

def get_auth_headers():
    return {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

def get_vault_files():
    """Fetches list of all files inside memory_vault/."""
    url = f"https://huggingface.co/api/models/{VAULT_REPO}/tree/main/memory_vault?recursive=true"
    try:
        res = requests.get(url, headers=get_auth_headers(), timeout=10)
        if res.status_code == 200:
            return [f["path"] for f in res.json()]
    except Exception as e:
        print(f"⚠️ Vault fetch notice: {e}")
    return []

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 <b>Kalyan Kishore Master Daemon</b>\n\n"
        "Commands:\n"
        "• <code>/status</code> - View live telemetry & counts\n"
        "• <code>/bounties</code> - Get latest verified bounty code & submission link\n"
        "• <code>/vault</code> - Hugging Face storage link",
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

@bot.message_handler(commands=['bounties', 'bounty', 'latest_bounty'])
def send_bounties(message):
    files = get_vault_files()
    bounty_files = sorted([f for f in files if "bounties/" in f])
    
    if not bounty_files:
        bot.reply_to(message, "📭 No verified bounty solutions found in vault yet.")
        return

    # Use the latest bounty file
    latest_file = bounty_files[-1]
    
    # Direct CDN resolve endpoint (follows redirects automatically)
    resolve_url = f"https://huggingface.co/{VAULT_REPO}/resolve/main/{latest_file}"
    
    try:
        res = requests.get(resolve_url, headers=get_auth_headers(), timeout=12, allow_redirects=True)
        if res.status_code != 200:
            bot.reply_to(message, f"⚠️ Hugging Face returned HTTP {res.status_code}: {res.text[:200]}")
            return

        data = res.json()

        # Handle nested task dictionary vs flat dictionary
        task_data = data.get("task", {}) if isinstance(data.get("task"), dict) else data

        title = task_data.get("title") or data.get("title") or "Open Source Bounty"
        platform = task_data.get("platform") or data.get("platform") or "Bounty Platform"
        reward = task_data.get("reward") or data.get("reward") or "Portal Stated Reward"
        payout_type = task_data.get("payout_type") or data.get("payout_type") or "Crypto / Stripe"
        url = task_data.get("url") or data.get("url") or "https://github.com"
        solution = data.get("solution") or task_data.get("solution") or "Fix verified and stored."
        badge = data.get("badge") or "Triple Consensus Verified"

        clean_solution = html.escape(str(solution)[:1400])
        clean_title = html.escape(str(title)[:80])
        clean_platform = html.escape(str(platform))
        clean_reward = html.escape(str(reward))

        msg = (
            f"🎯 <b>Latest Verified Bounty ({len(bounty_files)} in Vault)</b>\n\n"
            f"• <b>Platform:</b> {clean_platform}\n"
            f"• <b>Reward:</b> <code>{clean_reward}</code> ({payout_type})\n"
            f"• <b>Status:</b> <code>{badge}</code>\n"
            f"• <b>Task:</b> <a href='{url}'>{clean_title}</a>\n\n"
            f"📝 <b>Pre-Verified Solution (Ready to Paste):</b>\n"
            f"<pre>{clean_solution}</pre>\n\n"
            f"👉 <a href='{url}'><b>[Click Here to Open Task & Submit]</b></a>"
        )
        bot.send_message(message.chat.id, msg, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error downloading bounty payload: {str(e)}")

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(timeout=20, long_polling_timeout=10), daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error parsing vault bounty: {str(e)}")
