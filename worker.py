# ==============================================================================
# KALYAN KISHORE: AUTONOMOUS HEADLESS CLOUD WORKER + AUTO-TRAIN TRIGGER
# ==============================================================================
import os
import sys
import json
import time
import random
import subprocess
import requests
from groq import Groq
from google import genai
from huggingface_hub import HfApi

# 1. Environment Secrets & Config
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
KAGGLE_USER = os.environ.get("KAGGLE_USERNAME", "").strip()
KAGGLE_KEY = os.environ.get("KAGGLE_KEY", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

# Initialize Clients
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else None

# 2. Resilient Inference (Groq -> Gemini Waterfall)
def generate_solution(prompt: str) -> tuple[str, str]:
    # Try Groq (Fast open-source)
    if groq_client:
        for model in ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]:
            try:
                res = groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1500
                )
                if res.choices and res.choices[0].message.content:
                    return res.choices[0].message.content, f"Groq/{model}"
            except Exception:
                continue

    # Fallback to Gemini
    if gemini_client:
        for model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                res = gemini_client.models.generate_content(model=model, contents=prompt)
                if res and res.text:
                    return res.text, f"Gemini/{model}"
            except Exception:
                continue

    raise RuntimeError("All configured upstream inference providers are currently unavailable.")

# 3. Deterministic Sandbox Executor
def run_in_sandbox(code_str: str) -> tuple[bool, str]:
    test_path = "/tmp/action_sandbox_eval.py"
    with open(test_path, "w") as f:
        f.write(code_str)
    try:
        proc = subprocess.run([sys.executable, test_path], capture_output=True, text=True, timeout=12)
        return (proc.returncode == 0), (proc.stdout.strip() if proc.returncode == 0 else proc.stderr.strip())
    except subprocess.TimeoutExpired:
        return False, "Execution timed out (>12s)."
    finally:
        if os.path.exists(test_path):
            os.remove(test_path)

# 4. Domain Challenge Suite
DOMAINS = {
    "quant_finance": {
        "title": "Quantitative Finance & Greeks",
        "prompt": (
            "Write a self-contained Python script for vectorized Black-Scholes Greeks or Monte Carlo VaR.\n"
            "STRICT RULES:\n"
            "1. Output ONLY valid executable Python code without markdown formatting.\n"
            "2. Include 4 strict assertions validating outputs against expected analytical bounds."
        )
    },
    "cyber_security": {
        "title": "Cybersecurity AST Auditor",
        "prompt": (
            "Write a self-contained Python security auditor using the 'ast' module.\n"
            "STRICT RULES:\n"
            "1. Output ONLY valid executable Python code without markdown formatting.\n"
            "2. Include 4 strict assertions evaluating safe vs. malicious AST payloads."
        )
    },
    "algo_systems": {
        "title": "Tier 4 Dynamic Programming",
        "prompt": (
            "Write a self-contained Python script solving a Tier 4 Dynamic Programming or stream optimization problem.\n"
            "STRICT RULES:\n"
            "1. ZERO HARDCODING: Do not write hardcoded matches (e.g., 'if arr == ...'). Implement general logic.\n"
            "2. Output ONLY valid executable Python code without markdown formatting.\n"
            "3. Include 4 strict assertions covering standard, edge, negative, and large boundary cases."
        )
    }
}

# 5. Telegram Notification Helper
def send_telegram_alert(text: str):
    if not TELEGRAM_TOKEN:
        return
    try:
        updates_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        res = requests.get(updates_url, timeout=5).json()
        if res.get("result"):
            chat_id = res["result"][-1]["message"]["chat"]["id"]
            send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(send_url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=5)
    except Exception:
        pass

# 6. Auto-Training Trigger Check
def check_and_trigger_fine_tuning(threshold=50):
    if not hf_api or not KAGGLE_USER or not KAGGLE_KEY:
        return

    try:
        files = hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model")
        verified_traces = [f for f in files if f.startswith("memory_vault/") and f.endswith(".json")]
        total_vault_count = len(verified_traces)

        last_trained_count = 0
        if "training_watermark.json" in files:
            p = hf_api.hf_hub_download(repo_id=VAULT_REPO, filename="training_watermark.json", repo_type="model")
            with open(p, "r") as f:
                mark = json.load(f)
                last_trained_count = mark.get("total_trained_samples", 0)

        un_trained_count = total_vault_count - last_trained_count
        print(f"\n📊 Auto-Train Check: {total_vault_count} total traces ({un_trained_count} new, threshold: {threshold})")

        if un_trained_count >= threshold:
            print(f"🎯 Milestone reached ({un_trained_count} new traces)! Triggering remote Kaggle training...")
            send_telegram_alert(
                f"🚀 *Auto-Training Trigger Activated!*\n"
                f"• Vault Milestones: `{total_vault_count}` verified traces\n"
                f"• Dispatching Kaggle GPU fine-tuning worker..."
            )
            # Push kernel to Kaggle
            subprocess.run(["kaggle", "kernels", "push", "-p", "."], check=False)

    except Exception as e:
        print(f"⚠️ Auto-train watcher notice: {e}")

# 7. Batch Execution Logic
def execute_batch(total_cycles=3):
    print("=" * 70)
    print(f"🚀 INITIATING KALYAN KISHORE AUTONOMOUS BATCH ({total_cycles} CYCLES)")
    print("=" * 70)

    successful_runs = 0

    for i in range(1, total_cycles + 1):
        domain_key = random.choice(list(DOMAINS.keys()))
        spec = DOMAINS[domain_key]
        print(f"\n[Cycle {i}/{total_cycles}] Domain: {spec['title']}")

        try:
            raw_code, provider = generate_solution(spec["prompt"])
            clean_code = raw_code.replace("```python", "").replace("```", "").strip()
            print(f"⚡ Generated candidate code via {provider}")

            passed, output = run_in_sandbox(clean_code)
            attempts = 1

            # Auto-Repair on Failure
            if not passed:
                print("⚠️ Initial test failed. Triggering self-repair loop...")
                repair_prompt = f"Fix this Python code that failed with error:\n{output}\n\nCode:\n{clean_code}\nOutput ONLY valid Python."
                repair_code, _ = generate_solution(repair_prompt)
                clean_code = repair_code.replace("```python", "").replace("```", "").strip()
                passed, output = run_in_sandbox(clean_code)
                attempts = 2

            if passed:
                reward = 1.0 / attempts
                successful_runs += 1
                print(f"✅ PASSED on Attempt #{attempts} (Reward: {reward:.2f})")

                # Push to Hugging Face Vault
                if hf_api:
                    fname = f"action_{domain_key}_{int(time.time())}.json"
                    payload = {
                        "timestamp": int(time.time()),
                        "domain": domain_key,
                        "domain_title": spec["title"],
                        "provider": provider,
                        "attempts": attempts,
                        "reward": reward,
                        "verified": True,
                        "solution_code": clean_code
                    }
                    with open(fname, "w") as f:
                        json.dump(payload, f, indent=2)

                    hf_api.upload_file(
                        path_or_fileobj=fname,
                        path_in_repo=f"memory_vault/{domain_key}/{fname}",
                        repo_id=VAULT_REPO,
                        repo_type="model"
                    )
                    if os.path.exists(fname):
                        os.remove(fname)
                    print(f"☁️ Synced verified trace to {VAULT_REPO}")
            else:
                print(f"❌ Failed after {attempts} attempts. Skipped vault upload.")

        except Exception as e:
            print(f"⚠️ Batch Cycle Notice: {e}")

        time.sleep(5)

    print("\n" + "=" * 70)
    summary_msg = f"📊 *GitHub Cloud Worker Summary*\n• Verified Runs: `{successful_runs}/{total_cycles}`\n• Vault: `{VAULT_REPO}`"
    print(summary_msg.replace("*", "").replace("`", ""))
    print("=" * 70)
    
    send_telegram_alert(summary_msg)
    
    # Check if threshold reached to trigger model fine-tuning
    check_and_trigger_fine_tuning(threshold=50)

if __name__ == "__main__":
    execute_batch(total_cycles=3)
