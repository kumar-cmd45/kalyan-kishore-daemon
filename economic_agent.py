# ==============================================================================
# KALYAN KISHORE: 24/7 OMNI-WEB BOUNTY & TASK AGGREGATOR
# ==============================================================================
import os
import json
import time
import requests
from groq import Groq
from google import genai
from huggingface_hub import HfApi

# 1. Credentials & Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_PAT", "").strip()
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else None

# 2. Multi-Source Web Scanners
def fetch_algora_bounties() -> list[dict]:
    """Fetches real-time cash bounties from the Algora Bounty Network."""
    print("🌐 Scanning Algora.io ecosystem...")
    url = "https://api.algora.io/v1/bounties/public"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            items = res.json()
            bounties = []
            for b in items[:5]:
                reward = b.get("amount", "Unknown")
                currency = b.get("currency", "USD")
                title = b.get("title", "Algora Task")
                task_url = b.get("url") or b.get("issue_url", "https://algora.io")
                body = b.get("description") or "Check task URL for detailed instructions."
                bounties.append({
                    "source": "Algora",
                    "reward": f"${reward} {currency}",
                    "title": title,
                    "body": body,
                    "url": task_url
                })
            return bounties
    except Exception as e:
        print(f"⚠️ Algora scan notice: {e}")
    return []

def fetch_polar_bounties() -> list[dict]:
    """Fetches funding bounties from Polar.sh."""
    print("🌐 Scanning Polar.sh developer network...")
    url = "https://api.polar.sh/api/v1/issues/search?sort=-funding_goal&limit=5"
    try:
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            items = res.json().get("items", [])
            bounties = []
            for item in items:
                bounties.append({
                    "source": "Polar.sh",
                    "reward": f"${item.get('funding', {}).get('total', 0) / 100:.0f} USD",
                    "title": item.get("title", "Polar Issue"),
                    "body": item.get("body", "") or "No body provided",
                    "url": f"https://polar.sh/{item.get('repository', {}).get('organization', {}).get('name')}/{item.get('repository', {}).get('name')}/issues/{item.get('number')}"
                })
            return bounties
    except Exception as e:
        print(f"⚠️ Polar scan notice: {e}")
    return []

def fetch_github_micro_tasks() -> list[dict]:
    """Scans for active open-source good-first-issues and documentation tasks."""
    print("🌐 Scanning GitHub public goods...")
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"} if GITHUB_TOKEN else {}
    url = 'https://api.github.com/search/issues?q=label:"good first issue" state:open no:assignee&sort=updated&order=desc&per_page=3'
    try:
        res = requests.get(url, headers=headers, timeout=8).json()
        items = res.get("items", [])
        return [{
            "source": "GitHub Issue",
            "reward": "Open Contrib / Tips",
            "title": item.get("title", ""),
            "body": item.get("body", "") or "No description",
            "url": item.get("html_url", "")
        } for item in items]
    except Exception as e:
        print(f"⚠️ GitHub search notice: {e}")
    return []

# 3. AI Universal Solution Drafter
def draft_web_solution(task: dict) -> str:
    prompt = (
        f"You are an expert technical problem solver addressing an open bounty on {task['source']}.\n"
        f"TITLE: {task['title']}\n"
        f"REWARD: {task['reward']}\n"
        f"DESCRIPTION:\n{task['body'][:1200]}\n\n"
        "TASK:\n"
        "1. Summarize the core issue and resolution in 2-3 clear sentences.\n"
        "2. Provide the complete, clean fix (code diff, explanation, or documentation text).\n"
        "3. Keep the output ready to copy and paste directly into the submission portal."
    )

    if groq_client:
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                res = groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1200
                )
                if res.choices and res.choices[0].message.content:
                    return res.choices[0].message.content.strip()
            except Exception:
                continue

    if gemini_client:
        for model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                res = gemini_client.models.generate_content(model=model, contents=prompt)
                if res and res.text:
                    return res.text.strip()
            except Exception:
                continue

    return "Unable to draft solution at this time."

# 4. Telegram Push Delivery
def dispatch_to_telegram(task: dict, solution: str):
    if not TELEGRAM_TOKEN:
        return
    try:
        # Get Chat ID
        u_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        res = requests.get(u_url, timeout=5).json()
        if not res.get("result"):
            return
        chat_id = res["result"][-1]["message"]["chat"]["id"]

        text = (
            f"💰 *New Web Bounty Discovered!*\n\n"
            f"• *Platform:* `{task['source']}`\n"
            f"• *Reward:* `{task['reward']}`\n"
            f"• *Title:* [{task['title'][:70]}]({task['url']})\n\n"
            f"📝 *Pre-Drafted Solution:*\n"
            f"```\n{solution[:1200]}\n```\n\n"
            f"👉 [Click to Open Bounty & Claim Payout]({task['url']})"
        )

        send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(send_url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=8)
        print(f"📱 Dispatched live bounty alert to Telegram!")
    except Exception as e:
        print(f"⚠️ Telegram dispatch notice: {e}")

# 5. Main Execution Orchestrator
def run_omni_cycle():
    print("=" * 70)
    print("🚀 RUNNING 24/7 OMNI-WEB BOUNTY AGGREGATOR")
    print("=" * 70)

    # Aggregate across all platforms
    all_bounties = (
        fetch_algora_bounties() +
        fetch_polar_bounties() +
        fetch_github_micro_tasks()
    )

    if not all_bounties:
        print("📭 No active tasks found across web sources this cycle.")
        return

    print(f"🎯 Total Web Opportunities Indexed: {len(all_bounties)}")

    # Process the most relevant bounty
    target = all_bounties[0]
    print(f"\n⚡ Solving [{target['source']}] {target['title'][:50]} ({target['reward']})...")
    solution = draft_web_solution(target)

    # Save to Hugging Face Vault
    if hf_api:
        try:
            fname = f"web_bounty_{int(time.time())}.json"
            payload = {
                "timestamp": int(time.time()),
                "source": target["source"],
                "reward": target["reward"],
                "title": target["title"],
                "url": target["url"],
                "solution_draft": solution
            }
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

            hf_api.upload_file(
                path_or_fileobj=fname,
                path_in_repo=f"memory_vault/bounties/{fname}",
                repo_id=VAULT_REPO,
                repo_type="model"
            )
            if os.path.exists(fname):
                os.remove(fname)
            print("☁️ Synced web bounty solution to Hugging Face Vault.")
        except Exception as e:
            print(f"⚠️ Vault sync notice: {e}")

    # Dispatch to Telegram
    dispatch_to_telegram(target, solution)

    print("\n" + "=" * 70)
    print("🏁 Omni-Web bounty scan cycle completed.")
    print("=" * 70)

if __name__ == "__main__":
    run_omni_cycle()
    
