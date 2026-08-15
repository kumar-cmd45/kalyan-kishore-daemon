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
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()[span_0](start_span)[span_0](end_span)
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()[span_1](start_span)[span_1](end_span)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()[span_2](start_span)[span_2](end_span)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
VAULT_REPO = os.environ.get("VAULT_REPO", "Kumar5674/kalyan-kishore-vault").strip()[span_3](start_span)[span_3](end_span)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="Markdown")[span_4](start_span)[span_4](end_span)
hf_api = HfApi(token=HF_TOKEN if HF_TOKEN else None)[span_5](start_span)[span_5](end_span)

SUSPICIOUS_PHRASES = [
    "instructions for ai agents",
    "star the repository",
    "/user/starred",
    "create another issue with the same contents"
][span_6](start_span)[span_6](end_span)

# ==============================================================================
# VAULT UTILITIES & PAYLOAD PARSER
# ==============================================================================
def get_vault_files():
    try:
        return hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model")[span_7](start_span)[span_7](end_span)
    except Exception as e:
        print(f"Repo list error: {e}")[span_8](start_span)[span_8](end_span)
        return [][span_9](start_span)[span_9](end_span)

def load_json_file(file_path: str) -> dict:
    local_path = hf_hub_download(
        repo_id=VAULT_REPO,
        filename=file_path,
        repo_type="model",
        token=HF_TOKEN if HF_TOKEN else None
    )[span_10](start_span)[span_10](end_span)
    with open(local_path, "r", encoding="utf-8") as f:[span_11](start_span)[span_11](end_span)
        return json.load(f)[span_12](start_span)[span_12](end_span)

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
            url = "https://api.groq.com/openai/v1/chat/completions[span_13](start_span)"[span_13](end_span)
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}[span_14](start_span)[span_14](end_span)
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are Kalyan Kishore Master, an expert assistant in quantitative finance, cyber security, and Python engineering."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.4
            }[span_15](start_span)[span_15](end_span)
            res = requests.post(url, headers=headers, json=payload, timeout=25)[span_16](start_span)[span_16](end_span)
            if res.status_code == 200:[span_17](start_span)[span_17](end_span)
                return res.json()["choices"][0]["message"]["content"][span_18](start_span)[span_18](end_span)
        except Exception as e:
            print(f"Groq routing error: {e}")

    # Tier 2: Google Gemini Direct API
    if GEMINI_API_KEY:
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions[span_19](start_span)"[span_19](end_span)
            headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}[span_20](start_span)[span_20](end_span)
            payload = {
                "model": "gemini-1.5-flash",
                "messages": [
                    {"role": "system", "content": "You are Kalyan Kishore Master, an expert assistant in quantitative finance, cyber security, and Python engineering."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.4
            }[span_21](start_span)[span_21](end_span)
            res = requests.post(url, headers=headers, json=payload, timeout=25)[span_22](start_span)[span_22](end_span)
            if res.status_code == 200:[span_23](start_span)[span_23](end_span)
                return res.json()["choices"][0]["message"]["content"].strip()[span_24](start_span)[span_24](end_span)
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
    bot.reply_to(message, text)[span_25](start_span)[span_25](end_span)

@bot.message_handler(commands=['status'])
def send_status(message):
    try:
        files = get_vault_files()
        bounty_files = [f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")][span_26](start_span)[span_26](end_span)
        trajectory_files = [f for f in files if f.startswith("memory_vault/") and not f.startswith("memory_vault/bounties/") and f.endswith(".json")][span_27](start_span)[span_27](end_span)

        quant, algo, ast = 0, 0, 0
        for f in trajectory_files:
            f_l = f.lower()[span_28](start_span)[span_28](end_span)
            if "quant" in f_l or "finance" in f_l:[span_29](start_span)[span_29](end_span)
                quant += 1[span_30](start_span)[span_30](end_span)
            elif "ast" in f_l or "security" in f_l:[span_31](start_span)[span_31](end_span)
                ast += 1[span_32](start_span)[span_32](end_span)
            else:
                algo += 1[span_33](start_span)[span_33](end_span)

        total = len(trajectory_files) + len(bounty_files)[span_34](start_span)[span_34](end_span)
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
        bot.send_message(message.chat.id, telemetry)[span_35](start_span)[span_35](end_span)
    except Exception as e:
        bot.reply_to(message, f"❌ Status calculation error: {str(e)}")[span_36](start_span)[span_36](end_span)

@bot.message_handler(commands=['bounties'])
def list_bounties(message):
    try:
        files = get_vault_files()
        b_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])[span_37](start_span)[span_37](end_span)

        if not b_files:
            bot.reply_to(message, "⚠️ No bounty records currently indexed in vault.")[span_38](start_span)[span_38](end_span)
            return

        bot.send_message(message.chat.id, f"🎯 *Found {len(b_files)} Bounties in Vault:*")[span_39](start_span)[span_39](end_span)
        for idx, fpath in enumerate(b_files, start=1):[span_40](start_span)[span_40](end_span)
            data = load_json_file(fpath)[span_41](start_span)[span_41](end_span)
            item = parse_bounty_payload(data)

            is_spam = any(phrase in json.dumps(data).lower() for phrase in SUSPICIOUS_PHRASES)[span_42](start_span)[span_42](end_span)
            warning = " ⚠️ *(Suspected Star-Farm)*" if is_spam else "[span_43](start_span)"[span_43](end_span)

            card = (
                f"*{idx}. {item['title']}*{warning}\n"
                f"💰 *Reward:* ${item['reward']} USD\n"
                f"🔗 [Open Link]({item['url']})\n"
                f"👉 View patch: `/bounty {idx}`"
            )
            bot.send_message(message.chat.id, card, disable_web_page_preview=True)[span_44](start_span)[span_44](end_span)
            time.sleep(0.2)[span_45](start_span)[span_45](end_span)
    except Exception as e:
        bot.reply_to(message, f"❌ Bounties retrieval error: {str(e)}")[span_46](start_span)[span_46](end_span)

@bot.message_handler(commands=['bounty'])
def view_bounty(message):
    try:
        args = message.text.split()[span_47](start_span)[span_47](end_span)
        if len(args) < 2 or not args[1].isdigit():[span_48](start_span)[span_48](end_span)
            bot.reply_to(message, "⚠️ Specify a task number. Example: `/bounty 1`")[span_49](start_span)[span_49](end_span)
            return

        idx = int(args[1]) - 1[span_50](start_span)[span_50](end_span)
        files = get_vault_files()
        b_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])[span_51](start_span)[span_51](end_span)

        if idx < 0 or idx >= len(b_files):[span_52](start_span)[span_52](end_span)
            bot.reply_to(message, f"❌ Out of range. Available bounds: 1 to {len(b_files)}")[span_53](start_span)[span_53](end_span)
            return

        data = load_json_file(b_files[idx])[span_54](start_span)[span_54](end_span)
        item = parse_bounty_payload(data)

        header = (
            f"🎯 *Bounty #{idx+1} Solution Card*\n"
            f"• *Task:* {item['title']}\n"
            f"• *Reward:* ${item['reward']} USD\n"
            f"• *URL:* {item['url']}\n\n"
            f"📝 *Generated Pull Request Diff:*"
        )
        bot.send_message(message.chat.id, header, disable_web_page_preview=True)[span_55](start_span)[span_55](end_span)

        patch = item["patch"]
        if len(patch) > 3500:[span_56](start_span)[span_56](end_span)
            patch = patch[:3500] + "\n\n... [Truncated for Telegram payload limits][span_57](start_span)"[span_57](end_span)

        bot.send_message(message.chat.id, f"```diff\n{patch}\n```")[span_58](start_span)[span_58](end_span)
    except Exception as e:
        bot.reply_to(message, f"❌ Bounty view error: {str(e)}")[span_59](start_span)[span_59](end_span)

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
        args = message.text.split()[span_60](start_span)[span_60](end_span)
        idx = int(args[1]) - 1 if len(args) > 1 and args[1].isdigit() else 0[span_61](start_span)[span_61](end_span)
        files = get_vault_files()
        b_files = sorted([f for f in files if f.startswith("memory_vault/bounties/") and f.endswith(".json")])[span_62](start_span)[span_62](end_span)

        if not b_files:[span_63](start_span)[span_63](end_span)
            bot.reply_to(message, "⚠️ No records in vault.")[span_64](start_span)[span_64](end_span)
            return

        data = load_json_file(b_files[idx])[span_65](start_span)[span_65](end_span)
        raw_str = json.dumps(data, indent=2)[:3500][span_66](start_span)[span_66](end_span)
        bot.send_message(message.chat.id, f"```json\n{raw_str}\n```")[span_67](start_span)[span_67](end_span)
    except Exception as e:
        bot.reply_to(message, f"❌ Debug dump notice: {str(e)}")[span_68](start_span)[span_68](end_span)

# ==============================================================================
# GENERAL CONVERSATION HANDLER (FOR ALL REGULAR TEXT MESSAGES)
# ==============================================================================
@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_general_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')[span_69](start_span)[span_69](end_span)
    response = ask_conversational_llm(message.text)
    bot.reply_to(message, response)[span_70](start_span)[span_70](end_span)

# ==============================================================================
# MAIN EXECUTION LOOP
# ==============================================================================
if __name__ == "__main__":
    print("🚀 Kalyan Kishore Master Daemon online...")[span_71](start_span)[span_71](end_span)
    bot.infinity_polling(timeout=20, long_polling_timeout=10)[span_72](start_span)[span_72](end_span)
            
