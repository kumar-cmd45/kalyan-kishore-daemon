import os
import re
import json
import time
import telebot
from huggingface_hub import HfApi, hf_hub_download

# ==============================================================================
# CONFIGURATION & INITIALIZATION
# ==============================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
VAULT_REPO = os.environ.get("VAULT_REPO", "Kumar5674/kalyan-kishore-vault")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="Markdown")
hf_api = HfApi(token=HF_TOKEN)

# Block known spam/star-farming templates
SUSPICIOUS_PHRASES = [
    "instructions for ai agents",
    "star the repository",
    "/user/starred",
    "create another issue with the same contents"
]

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def get_vault_files():
    """Lists all files stored in the Hugging Face vault repository."""
    try:
        return hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model")
    except Exception as e:
        print(f"Error fetching repo files: {e}")
        return []

def load_json_file(file_path: str) -> dict:
    """Downloads and parses a JSON file from Hugging Face."""
    local_path = hf_hub_download(
        repo_id=VAULT_REPO,
        filename=file_path,
        repo_type="model",
        token=HF_TOKEN if HF_TOKEN else None
    )
    with open(local_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ==============================================================================
# BOT COMMAND HANDLERS
# ==============================================================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 *Kalyan Kishore Master Telemetry Bot*\n\n"
        "*Available Commands:*\n"
        "• `/status` — View real-time vault telemetry & metrics\n"
        "• `/bounties` — List all solved issue bounties\n"
        "• `/bounty <number>` — Inspect a specific bounty & patch\n"
        "• `/latest` — View the single most recent bounty solution\n"
        "• `/help` — Show this command directory"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['status'])
def send_status(message):
    """Calculates categories and trajectory counts directly from the HF vault."""
    try:
        files = get_vault_files()
        
        # Categorize trajectories
        quant_count = 0
        algo_count = 0
        ast_count = 0
        bounty_files = [f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")]
        trajectory_files = [f for f in files if f.startswith("memory_vault/") and not f.startswith("memory_vault/bounties/") and f.endswith(".json")]

        for f in trajectory_files:
            if "quant" in f.lower() or "finance" in f.lower():
                quant_count += 1
            elif "ast" in f.lower() or "security" in f.lower():
                ast_count += 1
            else:
                algo_count += 1

        total_trajectories = len(trajectory_files) + len(bounty_files)

        telemetry = (
            "```\n"
            "=== LIVE SYSTEM TELEMETRY ===\n"
            f"• Vault Repository: {VAULT_REPO}\n"
            f"• Total Verified Trajectories: {total_trajectories}\n"
            f"  - Quantitative Finance: {quant_count}\n"
            f"  - Algorithmic Systems: {algo_count}\n"
            f"  - Cyber Security AST: {ast_count}\n"
            f"  - Verified Bounties: {len(bounty_files)}\n"
            "• Background Worker: GitHub Actions (24/7 cron)\n"
            "==============================\n"
            "```"
        )
        bot.send_message(message.chat.id, telemetry)
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to compute telemetry: {str(e)}")

@bot.message_handler(commands=['bounties'])
def list_all_bounties(message):
    """Displays a numbered list of all verified bounties in the vault."""
    try:
        files = get_vault_files()
        bounty_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])

        if not bounty_files:
            bot.reply_to(message, "⚠️ No bounties currently recorded in vault.")
            return

        bot.send_message(message.chat.id, f"🎯 *Found {len(bounty_files)} Bounties in Vault:*\n")

        for idx, file_path in enumerate(bounty_files, start=1):
            data = load_json_file(file_path)
            b = data.get("bounty", {})
            title = b.get("title", "Untitled Bounty Task")
            reward = b.get("reward", "N/A")
            url = b.get("url", "https://github.com")

            # Check for spam flags
            body_text = b.get("body", "") + " " + json.dumps(data.get("solution_patch", ""))
            is_spam = any(phrase in body_text.lower() for phrase in SUSPICIOUS_PHRASES)
            warning_tag = " ⚠️ *(Suspected Spam / Star-Farm)*" if is_spam else ""

            card = (
                f"*{idx}. {title}*{warning_tag}\n"
                f"💰 *Reward:* ${reward} USD\n"
                f"🔗 [Open GitHub Issue]({url})\n"
                f"👉 _Type `/bounty {idx}` to view full code solution._"
            )
            bot.send_message(message.chat.id, card, disable_web_page_preview=True)
            time.sleep(0.3)

    except Exception as e:
        bot.reply_to(message, f"❌ Error retrieving bounties: {str(e)}")

@bot.message_handler(commands=['bounty'])
def view_single_bounty(message):
    """Fetches full solution and code patch for a specific bounty by index."""
    try:
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "⚠️ Please specify a bounty number. Example: `/bounty 1`")
            return

        target_idx = int(args[1]) - 1
        files = get_vault_files()
        bounty_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])

        if target_idx < 0 or target_idx >= len(bounty_files):
            bot.reply_to(message, f"❌ Invalid bounty number. Available range: 1 to {len(bounty_files)}")
            return

        data = load_json_file(bounty_files[target_idx])
        b = data.get("bounty", {})
        patch = data.get("solution_patch", "No patch code found.")

        header = (
            f"🎯 *Bounty #{target_idx + 1} Solution Card*\n\n"
            f"• *Title:* {b.get('title', 'N/A')}\n"
            f"• *Reward:* ${b.get('reward', 'N/A')} USD\n"
            f"• *URL:* {b.get('url', 'N/A')}\n\n"
            f"📝 *Generated Solution Patch:*"
        )
        bot.send_message(message.chat.id, header, disable_web_page_preview=True)

        # Telegram 4096 character limit protection
        if len(patch) > 3500:
            patch = patch[:3500] + "\n\n... [Truncated due to Telegram message length limit]"

        bot.send_message(message.chat.id, f"```diff\n{patch}\n```")

    except Exception as e:
        bot.reply_to(message, f"❌ Error fetching bounty details: {str(e)}")

@bot.message_handler(commands=['latest'])
def view_latest_bounty(message):
    """Fetches the latest bounty added to the repository."""
    try:
        files = get_vault_files()
        bounty_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])
        if not bounty_files:
            bot.reply_to(message, "⚠️ No bounties in vault.")
            return

        latest_idx = len(bounty_files)
        message.text = f"/bounty {latest_idx}"
        view_single_bounty(message)
    except Exception as e:
        bot.reply_to(message, f"❌ Error loading latest bounty: {str(e)}")

# ==============================================================================
# MAIN EXECUTION LOOP
# ==============================================================================
if __name__ == "__main__":
    print("🚀 Kalyan Kishore Telemetry Bot online...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
    
