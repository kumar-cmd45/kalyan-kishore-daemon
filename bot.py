import os
import re
import json
import time
import telebot
import requests
from huggingface_hub import HfApi, hf_hub_download

# ==============================================================================
# CONFIGURATION & INITIALIZATION
# ==============================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
VAULT_REPO = os.environ.get("VAULT_REPO", "Kumar5674/kalyan-kishore-vault").strip()

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="Markdown")
hf_api = HfApi(token=HF_TOKEN if HF_TOKEN else None)

SUSPICIOUS_PHRASES = [
    "instructions for ai agents",
    "star the repository",
    "/user/starred",
    "create another issue with the same contents"
]

# ==============================================================================
# VAULT UTILITIES & PAYLOAD PARSER
# ==============================================================================
def get_vault_files():
    try:
        return hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model")
    except Exception as e:
        print(f"Repo list error: {e}")
        return []

def load_json_file(file_path: str) -> dict:
    local_path = hf_hub_download(
        repo_id=VAULT_REPO,
        filename=file_path,
        repo_type="model",
        token=HF_TOKEN if HF_TOKEN else None
    )
    with open(local_path, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_bounty_payload(data: dict) -> dict:
    """Universal parser supporting flat schemas and nested dictionary structures."""
    nested = {}
    if isinstance(data.get("task"), dict):
        nested = data.get("task")
    elif isinstance(data.get("bounty"), dict):
        nested = data.get("bounty")

    # 1. Clean Title Extraction
    raw_title = data.get("title") or nested.get("title")
    if not raw_title and isinstance(data.get("task"), str):
        raw_title = data.get("task")
    title = str(raw_title or "Bounty Task").strip()

    # 2. Clean Reward Extraction
    raw_reward = (
        data.get("reward")
        or nested.get("reward")
        or data.get("bounty_amount")
        or data.get("payout")
        or data.get("amount")
    )
    reward = str(raw_reward or "Escrow / Unlisted").replace("$", "").strip()

    # 3. Clean URL Extraction
    raw_url = (
        data.get("url")
        or nested.get("url")
        or data.get("issue_url")
        or data.get("html_url")
        or data.get("link")
    )
    url = str(raw_url or "https://github.com").strip()

    # 4. Patch / Solution Extraction
    patch = (
        data.get("solution_patch")
        or data.get("solution")
        or nested.get("solution_patch")
        or nested.get("solution")
        or data.get("patch")
        or data.get("diff")
        or "No patch code found."
    )

    return {
        "title": title[:100],
        "reward": reward,
        "url": url,
        "patch": str(patch).strip()
    }

# ==============================================================================
# MULTI-TIER CONVERSATIONAL LLM ROUTER (GROQ -> GEMINI)
# ==============================================================================
def ask_conversational_llm(prompt: str) -> str:
    """Answers general questions via Groq with automatic Gemini fallback."""
    # Tier 1: Groq API
    if GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are Kalyan Kishore Master, an expert assistant in quantitative finance, cyber security, and Python engineering."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.4
            }
            res = requests.post(url, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Groq routing error: {e}")

    # Tier 2: Google Gemini Direct API
    if GEMINI_API_KEY:
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "gemini-1.5-flash",
                "messages": [
                    {"role": "system", "content": "You are Kalyan Kishore Master, an expert assistant in quantitative finance, cyber security, and Python engineering."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.4
            }
            res = requests.post(url, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Gemini routing error: {e}")

    return "⚠️ AI Gateway Unavailable: Please configure either `GROQ_API_KEY` or `GEMINI_API_KEY` in your environment variables."

# ==============================================================================
# TELEGRAM BOT HANDLERS
# ==============================================================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🤖 *Kalyan Kishore Master AI Online*\n\n"
        "*Commands:*\n"
        "• `/status` — View vault trajectory telemetry\n"
        "• `/bounties` — List all verified bounties\n"
        "• `/bounty <id>` — View unified git patch solution\n"
        "• `/cleanup` — Auto-delete duplicate tasks & spam from HF\n"
        "• `/raw_bounty <id>` — Debug raw JSON in vault\n\n"
        "💬 *General Questions:* Send any text or coding question directly."
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['status'])
def send_status(message):
    try:
        files = get_vault_files()
        bounty_files = [f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")]
        trajectory_files = [f for f in files if f.startswith("memory_vault/") and not f.startswith("memory_vault/bounties/") and f.endswith(".json")]

        quant, algo, ast = 0, 0, 0
        for f in trajectory_files:
            f_l = f.lower()
            if "quant" in f_l or "finance" in f_l:
                quant += 1
            elif "ast" in f_l or "security" in f_l:
                ast += 1
            else:
                algo += 1

        total = len(trajectory_files) + len(bounty_files)
        telemetry = (
            "```\n"
            "=== LIVE SYSTEM TELEMETRY ===\n"
            f"• Vault: {VAULT_REPO}\n"
            f"• Total Verified Trajectories: {total}\n"
            f"  - Quantitative Finance: {quant}\n"
            f"  - Algorithmic Systems: {algo}\n"
            f"  - Cyber Security AST: {ast}\n"
            f"  - Verified Bounties: {len(bounty_files)}\n"
            "• Background Worker: GitHub Actions (24/7 cron)\n"
            "==============================\n"
            "```"
        )
        bot.send_message(message.chat.id, telemetry)
    except Exception as e:
        bot.reply_to(message, f"❌ Status calculation error: {str(e)}")

@bot.message_handler(commands=['bounties'])
def list_bounties(message):
    try:
        files = get_vault_files()
        b_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])

        if not b_files:
            bot.reply_to(message, "⚠️ No bounty records currently indexed in vault.")
            return

        bot.send_message(message.chat.id, f"🎯 *Found {len(b_files)} Bounties in Vault:*")
        for idx, fpath in enumerate(b_files, start=1):
            data = load_json_file(fpath)
            item = parse_bounty_payload(data)

            is_spam = any(phrase in json.dumps(data).lower() for phrase in SUSPICIOUS_PHRASES)
            warning = " ⚠️ *(Suspected Star-Farm)*" if is_spam else ""

            card = (
                f"*{idx}. {item['title']}*{warning}\n"
                f"💰 *Reward:* ${item['reward']} USD\n"
                f"🔗 [Open Link]({item['url']})\n"
                f"👉 View patch: `/bounty {idx}`"
            )
            bot.send_message(message.chat.id, card, disable_web_page_preview=True)
            time.sleep(0.2)
    except Exception as e:
        bot.reply_to(message, f"❌ Bounties retrieval error: {str(e)}")

@bot.message_handler(commands=['bounty'])
def view_bounty(message):
    try:
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "⚠️ Specify a task number. Example: `/bounty 1`")
            return

        idx = int(args[1]) - 1
        files = get_vault_files()
        b_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])

        if idx < 0 or idx >= len(b_files):
            bot.reply_to(message, f"❌ Out of range. Available bounds: 1 to {len(b_files)}")
            return

        data = load_json_file(b_files[idx])
        item = parse_bounty_payload(data)

        header = (
            f"🎯 *Bounty #{idx+1} Solution Card*\n"
            f"• *Task:* {item['title']}\n"
            f"• *Reward:* ${item['reward']} USD\n"
            f"• *URL:* {item['url']}\n\n"
            f"📝 *Generated Pull Request Diff:*"
        )
        bot.send_message(message.chat.id, header, disable_web_page_preview=True)

        patch = item["patch"]
        if len(patch) > 3500:
            patch = patch[:3500] + "\n\n... [Truncated for Telegram payload limits]"

        bot.send_message(message.chat.id, f"```diff\n{patch}\n```")
    except Exception as e:
        bot.reply_to(message, f"❌ Bounty view error: {str(e)}")

@bot.message_handler(commands=['cleanup'])
def cleanup_vault(message):
    """Deletes all duplicate issue URLs and spam honeypots directly from Hugging Face."""
    bot.reply_to(message, "🧹 Scanning Hugging Face Vault for duplicates and spam...")
    try:
        files = get_vault_files()
        b_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])

        seen_urls = set()
        deleted_count = 0

        for fpath in b_files:
            data = load_json_file(fpath)
            item = parse_bounty_payload(data)
            url_key = item["url"].strip().lower()

            is_spam = any(phrase in json.dumps(data).lower() for phrase in SUSPICIOUS_PHRASES)
            is_duplicate = url_key in seen_urls and url_key not in ["", "https://github.com"]

            if is_spam or is_duplicate:
                hf_api.delete_file(
                    path_in_repo=fpath,
                    repo_id=VAULT_REPO,
                    repo_type="model"
                )
                deleted_count += 1
            else:
                seen_urls.add(url_key)

        bot.send_message(
            message.chat.id,
            f"✅ *Vault Cleaned Successfully!*\n• Deleted `{deleted_count}` duplicate/spam records.\n• Unique tasks retained."
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Vault cleanup notice: {str(e)}")

@bot.message_handler(commands=['raw_bounty'])
def debug_raw_bounty(message):
    try:
        args = message.text.split()
        idx = int(args[1]) - 1 if len(args) > 1 and args[1].isdigit() else 0
        files = get_vault_files()
        b_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])

        if not b_files:
            bot.reply_to(message, "⚠️ No records in vault.")
            return

        data = load_json_file(b_files[idx])
        raw_str = json.dumps(data, indent=2)[:3500]
        bot.send_message(message.chat.id, f"```json\n{raw_str}\n```")
    except Exception as e:
        bot.reply_to(message, f"❌ Debug dump notice: {str(e)}")

# ==============================================================================
# GENERAL CONVERSATION HANDLER (FOR ALL REGULAR TEXT MESSAGES)
# ==============================================================================
@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_general_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    response = ask_conversational_llm(message.text)
    bot.reply_to(message, response)

# ==============================================================================
# MAIN EXECUTION LOOP
# ==============================================================================
if __name__ == "__main__":
    print("🚀 Kalyan Kishore Master Daemon online...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
    
