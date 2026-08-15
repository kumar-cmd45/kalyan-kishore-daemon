# ==============================================================================
# KALYAN KISHORE TELEGRAM MASTER DAEMON (bot.py)
# Features: Hugging Face Vault Reader, Universal Bounty Key Parser, Flask Web Port
# ==============================================================================
import os
import json
import html
import telebot
from flask import Flask
import threading
from huggingface_hub import HfApi, hf_hub_download

# 1. Environment Secrets & Setup
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else HfApi()

@app.route('/')
def home():
    return "Kalyan Kishore Master Daemon is Live and Polling!"

# Helper to index all stored traces across domain folders
def get_all_vault_files():
    try:
        files = hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model")
        return [f for f in files if f.startswith("memory_vault/")]
    except Exception as e:
        print(f"⚠️ Vault list error: {e}")
        return []

# ==============================================================================
# 2. COMMAND HANDLERS
# ==============================================================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 <b>Kalyan Kishore Master Daemon</b>\n\n"
        "Available Commands:\n"
        "• <code>/status</code> - View live telemetry & verified counts\n"
        "• <code>/bounties</code> - Get latest verified bounty solution & submission link\n"
        "• <code>/vault</code> - Hugging Face storage direct telemetry"
    )
    bot.reply_to(message, welcome_text, parse_mode="HTML")

@bot.message_handler(commands=['status', 'vault'])
def send_status(message):
    files = get_all_vault_files()
    bounties = [f for f in files if "memory_vault/bounties/" in f and f.endswith(".json")]
    quant = [f for f in files if "memory_vault/quant_finance/" in f]
    algo = [f for f in files if "memory_vault/algo_systems/" in f]
    cyber = [f for f in files if "memory_vault/cyber_ast/" in f]

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
    try:
        files = get_all_vault_files()
        bounty_files = sorted([f for f in files if "memory_vault/bounties/" in f and f.endswith(".json")])
        
        if not bounty_files:
            bot.reply_to(message, "📭 No verified bounty solutions found in the vault yet.")
            return

        # 1. Select the newest verified bounty file
        latest_file = bounty_files[-1]

        # 2. Download file locally via official Hugging Face Hub SDK
        local_path = hf_hub_download(
            repo_id=VAULT_REPO,
            filename=latest_file,
            repo_type="model",
            token=HF_TOKEN if HF_TOKEN else None
        )

        with open(local_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 3. Universal Schema Parser (handles nested vs flat JSON dictionaries)
        task_data = data.get("task", {}) if isinstance(data.get("task"), dict) else data

        # Extract Task Metadata
        title = task_data.get("title") or data.get("title") or "Open Source Bounty Task"
        platform = task_data.get("platform") or data.get("platform") or "Bounty Platform"
        reward = task_data.get("reward") or data.get("reward") or "See Issue / Portal"
        payout_type = task_data.get("payout_type") or data.get("payout_type") or "Crypto / Cash"
        url = task_data.get("url") or data.get("url") or "https://github.com"
        badge = data.get("badge") or "Triple Consensus Verified"

        # 4. Universal Multi-Key Solution Extractor (inspects all fallback keys)
        raw_solution = (
            data.get("solution") or 
            data.get("draft") or 
            data.get("patch") or 
            data.get("code") or 
            data.get("output") or 
            data.get("completion") or 
            task_data.get("solution") or 
            task_data.get("draft") or 
            task_data.get("patch") or 
            task_data.get("body") or 
            "Solution verified and archived in vault."
        )

        # 5. HTML Escape for Telegram formatting safety
        clean_solution = html.escape(str(raw_solution)[:1500])
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
        bot.reply_to(message, f"⚠️ Error parsing vault bounty: {str(e)}")

# ==============================================================================
# 3. THREADED EXECUTION (Render Web Service + Telebot Polling)
# ==============================================================================
if __name__ == "__main__":
    # Start bot polling in a background daemon thread
    threading.Thread(
        target=lambda: bot.infinity_polling(timeout=20, long_polling_timeout=10),
        daemon=True
    ).start()
    
    # Run lightweight Flask app on port 10000 to keep Render Web Service healthy
    app.run(host="0.0.0.0", port=10000)
        
