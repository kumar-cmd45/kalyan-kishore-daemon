import os
import time
import json
import threading
import telebot
from flask import Flask
from groq import Groq
from google import genai
from huggingface_hub import HfApi

# 1. Environment Secrets & Config
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else None
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "🚀 Kalyan Kishore Bot is Online & Awake 24/7!", 200

# 2. Live Vault & Telemetry Reader
def get_live_system_context() -> tuple[dict, str]:
    if not hf_api:
        return {}, "Hugging Face API uninitialized (missing HF_TOKEN)."
    
    repo_type = "model"
    files = []
    try:
        files = hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model")
    except Exception:
        try:
            files = hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="dataset")
            repo_type = "dataset"
        except Exception as e:
            return {}, f"Vault connection notice: {e}"

    traces = [f for f in files if f.startswith("memory_vault/") and f.endswith(".json")]
    quant_traces = [f for f in traces if "quant_finance" in f]
    algo_traces = [f for f in traces if "algo_systems" in f]
    cyber_traces = [f for f in traces if "cyber_security" in f]
    bounty_traces = [f for f in traces if "bount" in f]

    stats = {
        "total_trajectories": len(traces),
        "quant_count": len(quant_traces),
        "algo_count": len(algo_traces),
        "cyber_count": len(cyber_traces),
        "bounty_count": len(bounty_traces),
        "repo_type": repo_type,
        "latest_file": sorted(traces)[-1] if traces else "None"
    }

    summary = (
        f"=== LIVE SYSTEM TELEMETRY ===\n"
        f"• Vault Repository: {VAULT_REPO} ({repo_type})\n"
        f"• Total Verified Trajectories: {len(traces)}\n"
        f"  - Quantitative Finance: {len(quant_traces)}\n"
        f"  - Algorithmic Systems: {len(algo_traces)}\n"
        f"  - Cyber Security AST: {len(cyber_traces)}\n"
        f"  - Verified Bounties: {len(bounty_traces)}\n"
        f"• Latest Stored Trace: {stats['latest_file']}\n"
        f"• Background Worker: GitHub Actions (24/7 cron)\n"
        f"=============================="
    )
    return stats, summary

# 3. Context-Aware AI Chat Waterfall
def ask_ai_with_telemetry(user_query: str) -> str:
    _, telemetry = get_live_system_context()

    system_prompt = (
        "You are Kalyan Kishore (Isikai), an autonomous RLVR reasoning agent.\n"
        "You run autonomous background cycles solving complex code challenges, validating them in deterministic sandboxes, and syncing them to your Hugging Face vault.\n\n"
        f"{telemetry}\n\n"
        "STRICT INSTRUCTIONS:\n"
        "- When the user asks about trajectories, background work, bounties, self-training, or status, always use the real metrics above.\n"
        "- Be concise, direct, and factual."
    )

    if groq_client:
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                res = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                if res.choices and res.choices[0].message.content:
                    return res.choices[0].message.content
            except Exception:
                continue

    if gemini_client:
        for model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                full_prompt = f"{system_prompt}\n\nUser: {user_query}"
                res = gemini_client.models.generate_content(model=model, contents=full_prompt)
                if res and res.text:
                    return res.text
            except Exception:
                continue

    return "⚠️ System notice: Inference endpoints are busy. Please try again shortly."

# 4. Telegram Command Handlers
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "🤖 *Kalyan Kishore 24/7 Autonomous Agent*\n\n"
        "• `/status` — View real-time Vault & system stats\n"
        "• `/vault` — Inspect stored trajectories & categories\n"
        "• Ask me anything about what I'm executing in the background!"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def show_status(message):
    bot.send_chat_action(message.chat.id, 'typing')
    _, summary = get_live_system_context()
    bot.reply_to(message, f"```\n{summary}\n```", parse_mode="Markdown")

@bot.message_handler(commands=['vault'])
def show_vault(message):
    bot.send_chat_action(message.chat.id, 'typing')
    stats, _ = get_live_system_context()
    if not stats or stats.get("total_trajectories", 0) == 0:
        bot.reply_to(message, "📭 Vault is currently empty or indexing.")
        return

    text = (
        "🏛️ *Hugging Face Memory Vault*\n\n"
        f"• *Total Verified Trajectories:* `{stats['total_trajectories']}`\n"
        f"• *Quant Finance:* `{stats['quant_count']}`\n"
        f"• *Algo Systems:* `{stats['algo_count']}`\n"
        f"• *Cyber AST:* `{stats['cyber_count']}`\n"
        f"• *Bounty Patches:* `{stats['bounty_count']}`\n\n"
        f"• *Latest Entry:* `{stats['latest_file']}`\n\n"
        f"👉 [Open Hugging Face Vault](https://huggingface.co/{VAULT_REPO}/tree/main/memory_vault)"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_ai_with_telemetry(message.text)
    bot.reply_to(message, reply)

# 5. Execution Entry Point
def start_bot():
    print("🚀 Telegram polling loop initialized.")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"⚠️ Polling notice: {e}")
            time.sleep(3)

if __name__ == "__main__":
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    
