import os
import json
import time
import telebot
import requests
from huggingface_hub import HfApi, hf_hub_download

# ==============================================================================
# CONFIGURATION
# ==============================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
VAULT_REPO = os.environ.get("VAULT_REPO", "Kumar5674/kalyan-kishore-vault")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="Markdown")
hf_api = HfApi(token=HF_TOKEN if HF_TOKEN else None)

SUSPICIOUS_PHRASES = [
    "instructions for ai agents",
    "star the repository",
    "/user/starred",
    "create another issue with the same contents"
]

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
    """Universal parser searching across flat and nested dictionary structures."""
    # Check if nested under 'task' or 'bounty'
    nested = {}
    if isinstance(data.get("task"), dict):
        nested = data.get("task")
    elif isinstance(data.get("bounty"), dict):
        nested = data.get("bounty")

    # 1. Title
    title = (
        data.get("title") or nested.get("title")
        or (data.get("task") if isinstance(data.get("task"), str) else None)
        or "Bounty Task"
    )

    # 2. Reward
    reward = (
        data.get("reward") or nested.get("reward")
        or data.get("bounty_amount") or data.get("payout")
        or "Escrow / Unlisted"
    )

    # 3. URL
    url = (
        data.get("url") or nested.get("url")
        or data.get("issue_url") or data.get("html_url")
        or "https://github.com"
    )

    # 4. Patch / Solution
    patch = (
        data.get("solution_patch") or data.get("solution")
        or nested.get("solution_patch") or nested.get("solution")
        or data.get("patch") or data.get("diff")
        or "No patch code found."
    )

    return {
        "title": str(title)[:120],
        "reward": str(reward).replace("$", ""),
        "url": str(url),
        "patch": str(patch)
    }

def ask_groq_llm(prompt: str) -> str:
    """Answers general questions via Groq."""
    if not GROQ_API_KEY:
        return "⚠️ Set `GROQ_API_KEY` in environment variables to enable general conversational AI."
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are Kalyan Kishore Master, a quantitative finance and systems automation AI assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.5
        }
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        return f"⚠️ LLM Response Error (HTTP {res.status_code})"
    except Exception as e:
        return f"⚠️ Connection error: {str(e)}"

# ==============================================================================
# BOT COMMANDS
# ==============================================================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🤖 *Kalyan Kishore Master AI Online*\n\n"
        "*Commands:*\n"
        "• `/status` — View telemetry & trajectory counts\n"
        "• `/bounties` — List all verified bounties\n"
        "• `/bounty <num>` — View solution code for bounty\n"
        "• `/raw_bounty <num>` — View raw JSON debug dump\n\n"
        "💬 *General Questions:* Send any question directly to chat."
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
            f"• Total Trajectories: {total}\n"
            f"  - Quantitative Finance: {quant}\n"
            f"  - Algorithmic Systems: {algo}\n"
            f"  - Cyber Security AST: {ast}\n"
            f"  - Verified Bounties: {len(bounty_files)}\n"
            "• Worker: GitHub Actions (24/7 cron)\n"
            "==============================\n"
            "```"
        )
        bot.send_message(message.chat.id, telemetry)
    except Exception as e:
        bot.reply_to(message, f"❌ Status error: {str(e)}")

@bot.message_handler(commands=['bounties'])
def list_bounties(message):
    try:
        files = get_vault_files()
        b_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])

        if not b_files:
            bot.reply_to(message, "⚠️ No bounty files found in `memory_vault/bounties/`.")
            return

        bot.send_message(message.chat.id, f"🎯 *Found {len(b_files)} Bounties:*")
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
        bot.reply_to(message, f"❌ Retrieval error: {str(e)}")

@bot.message_handler(commands=['bounty'])
def view_bounty(message):
    try:
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "⚠️ Specify a number: `/bounty 1`")
            return

        idx = int(args[1]) - 1
        files = get_vault_files()
        b_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])

        if idx < 0 or idx >= len(b_files):
            bot.reply_to(message, f"❌ Invalid index. Max available: {len(b_files)}")
            return

        data = load_json_file(b_files[idx])
        item = parse_bounty_payload(data)
        
        header = f"🎯 *Bounty #{idx+1} Solution*\n• *Task:* {item['title']}\n• *Reward:* ${item['reward']}\n• *URL:* {item['url']}\n\n📝 *Patch:*"
        bot.send_message(message.chat.id, header, disable_web_page_preview=True)

        patch = item["patch"]
        if len(patch) > 3500:
            patch = patch[:3500] + "\n\n...[Truncated]"
        bot.send_message(message.chat.id, f"```diff\n{patch}\n```")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['raw_bounty'])
def debug_raw_bounty(message):
    try:
        args = message.text.split()
        idx = int(args[1]) - 1 if len(args) > 1 and args[1].isdigit() else 0
        files = get_vault_files()
        b_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])
        
        if not b_files:
            bot.reply_to(message, "No bounties in vault.")
            return

        data = load_json_file(b_files[idx])
        raw_str = json.dumps(data, indent=2)[:3500]
        bot.send_message(message.chat.id, f"```json\n{raw_str}\n```")
    except Exception as e:
        bot.reply_to(message, f"Debug error: {str(e)}")

@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_general_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    response = ask_groq_llm(message.text)
    bot.reply_to(message, response)

if __name__ == "__main__":
    print("🚀 Bot initialized with conversational LLM & universal vault parser...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
    
