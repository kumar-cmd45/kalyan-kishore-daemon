import os
import time
import json
import threading
import telebot
from flask import Flask
from groq import Groq
from google import genai
from huggingface_hub import HfApi

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

def get_live_system_context() -> str:
    """Reads live vault data and telemetry ledger from Hugging Face."""
    if not hf_api:
        return "No telemetry connection available."
    try:
        files = hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model")
        traces = [f for f in files if f.startswith("memory_vault/") and f.endswith(".json")]
        
        ledger_info = "No bounty runs logged yet."
        if "telemetry/bounty_ledger.json" in files:
            p = hf_api.hf_hub_download(repo_id=VAULT_REPO, filename="telemetry/bounty_ledger.json", repo_type="model")
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                recent = "\n".join([f"- [{log['status']}] {log['repo']} #{log['issue_number']}: {log['title']}" for log in data.get("recent_logs", [])[:5]])
                ledger_info = (
                    f"Total Attempts: {data.get('total_attempts', 0)}\n"
                    f"Total Verified: {data.get('total_passed', 0)}\n"
                    f"Recent Targets:\n{recent}"
                )

        return (
            f"=== LIVE AGENT TELEMETRY & STATE ===\n"
            f"Vault Repo: {VAULT_REPO}\n"
            f"Total Verified Trajectories: {len(traces)}\n"
            f"Bounty Operations:\n{ledger_info}\n"
            f"====================================="
        )
    except Exception as e:
        return f"Telemetry read error: {e}"

def ask_ai_with_context(user_query: str) -> str:
    telemetry = get_live_system_context()
    
    system_prompt = (
        "You are Kalyan Kishore, an autonomous reasoning AI agent with active background workflows.\n"
        "You run continuous RLVR loops, deterministic sandbox tests, and GitHub bounty scanners.\n\n"
        f"{telemetry}\n\n"
        "INSTRUCTIONS:\n"
        "- When asked about bounties, trajectories, background tasks, or self-training, reference the exact live metrics above.\n"
        "- Be precise, candid, and direct about real numbers. If an attempt failed unit tests, state that accurately."
    )

    # Groq Waterfall
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
                    max_tokens=1200
                )
                if res.choices and res.choices[0].message.content:
                    return res.choices[0].message.content
            except Exception:
                continue

    # Gemini Fallback
    if gemini_client:
        for model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                full_prompt = f"{system_prompt}\n\nUser Question: {user_query}"
                res = gemini_client.models.generate_content(model=model, contents=full_prompt)
                if res and res.text:
                    return res.text
            except Exception:
                continue

    return "⚠️ System notice: Upstream inference endpoints are busy. Please try again shortly."

@bot.message_handler(commands=['bounties'])
def show_bounties(message):
    bot.send_chat_action(message.chat.id, 'typing')
    context = get_live_system_context()
    bot.reply_to(message, f"```\n{context}\n```", parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def show_status(message):
    bot.send_chat_action(message.chat.id, 'typing')
    context = get_live_system_context()
    bot.reply_to(message, f"```\n{context}\n```", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = ask_ai_with_context(message.text)
    bot.reply_to(message, reply)

def start_bot():
    print("🚀 Telegram polling loop initialized.")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"⚠️ Polling reconnecting: {e}")
            time.sleep(3)

if __name__ == "__main__":
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    reply = ask_ai(message.text)
    bot.reply_to(message, reply)

# Resilient Polling Worker
def start_bot():
    print("🚀 Telegram polling loop initialized.")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"⚠️ Polling reconnecting: {e}")
            time.sleep(3)

if __name__ == "__main__":
    # Start bot listener in background thread
    t = threading.Thread(target=start_bot, daemon=True)
    t.start()
    
    # Run web server for keepalive pings on port assigned by Render
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
