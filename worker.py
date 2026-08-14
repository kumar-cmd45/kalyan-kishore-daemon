# ==============================================================================
# KALYAN KISHORE: AUTONOMOUS HEADLESS CLOUD WORKER (HIGH-YIELD RLVR)
# ==============================================================================
import os
import re
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
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

# Initialize Clients
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else None

# Helper: Extract pure Python code from any markdown/prose output
def extract_pure_code(text: str) -> str:
    # 1. Match code enclosed in ```python ... ```
    match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # 2. Match generic ``` ... ```
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 3. Fallback: filter lines
    lines = []
    for line in text.splitlines():
        if line.strip().startswith("```") or line.strip().startswith("Here is") or line.strip().startswith("Note:"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()

# 2. Resilient Inference (Groq -> Gemini Waterfall)
def generate_solution(prompt: str) -> tuple[str, str]:
    if groq_client:
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                res = groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1800
                )
                if res.choices and res.choices[0].message.content:
                    return res.choices[0].message.content, f"Groq/{model}"
            except Exception:
                continue

    if gemini_client:
        for model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                res = gemini_client.models.generate_content(model=model, contents=prompt)
                if res and res.text:
                    return res.text, f"Gemini/{model}"
            except Exception:
                continue

    raise RuntimeError("All inference endpoints are currently busy.")

# 3. Deterministic Sandbox Executor
def run_in_sandbox(code_str: str) -> tuple[bool, str]:
    test_path = "/tmp/action_sandbox_eval.py"
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(code_str)
    try:
        proc = subprocess.run([sys.executable, test_path], capture_output=True, text=True, timeout=12)
        passed = (proc.returncode == 0)
        logs = proc.stdout.strip() if passed else proc.stderr.strip()
        return passed, logs
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
            "Write a self-contained Python script implementing Black-Scholes formulas and analytical option Greeks (Delta, Gamma, Vega).\n"
            "REQUIREMENTS:\n"
            "- Use math and numpy only.\n"
            "- Include exact functions for Call/Put price and Greeks.\n"
            "- Include 4 assert statements at the bottom testing boundary conditions (e.g., deep ITM/OTM, positive Vega).\n"
            "- Output ONLY valid Python code."
        )
    },
    "cyber_security": {
        "title": "Cybersecurity AST Auditor",
        "prompt": (
            "Write a self-contained Python security auditor using the standard 'ast' module.\n"
            "REQUIREMENTS:\n"
            "- Define an AST NodeVisitor checking for dangerous calls: eval, exec, os.system, and __import__.\n"
            "- Include 4 assert statements evaluating safe vs. malicious code snippets.\n"
            "- Output ONLY valid Python code."
        )
    },
    "algo_systems": {
        "title": "Algorithmic Systems & Structures",
        "prompt": (
            "Write a self-contained Python script implementing an LRU Cache with O(1) ops or a Trie with prefix search.\n"
            "REQUIREMENTS:\n"
            "- Pure Python standard library only.\n"
            "- Include 4 assert statements verifying edge cases, eviction policies, or empty inputs.\n"
            "- Output ONLY valid Python code."
        )
    }
}

# 5. Batch Execution Logic
def execute_batch(total_cycles=6):
    print("=" * 70)
    print(f"🚀 INITIATING HIGH-YIELD RLVR WORKER ({total_cycles} CYCLES)")
    print("=" * 70)

    successful_runs = 0

    for i in range(1, total_cycles + 1):
        domain_key = random.choice(list(DOMAINS.keys()))
        spec = DOMAINS[domain_key]
        print(f"\n[Cycle {i}/{total_cycles}] Target: {spec['title']}")

        try:
            raw_code, provider = generate_solution(spec["prompt"])
            clean_code = extract_pure_code(raw_code)
            print(f"⚡ Candidate generated via {provider}")

            passed, output = run_in_sandbox(clean_code)
            attempts = 1

            # Self-Repair Loop
            if not passed:
                print(f"⚠️ Initial test failed ({output[:60]}...). Repairing...")
                repair_prompt = (
                    f"Fix this Python code. Error:\n{output}\n\nOriginal Code:\n{clean_code}\n\n"
                    "Output ONLY the corrected valid Python code."
                )
                repair_raw, _ = generate_solution(repair_prompt)
                clean_code = extract_pure_code(repair_raw)
                passed, output = run_in_sandbox(clean_code)
                attempts = 2

            if passed:
                reward = 1.0 / attempts
                successful_runs += 1
                print(f"✅ PASSED on Attempt #{attempts} (Reward: {reward:.2f})")

                # Sync to Hugging Face Vault
                if hf_api:
                    fname = f"trace_{domain_key}_{int(time.time())}.json"
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
                    with open(fname, "w", encoding="utf-8") as f:
                        json.dump(payload, f, indent=2)

                    hf_api.upload_file(
                        path_or_fileobj=fname,
                        path_in_repo=f"memory_vault/{domain_key}/{fname}",
                        repo_id=VAULT_REPO,
                        repo_type="model"
                    )
                    if os.path.exists(fname):
                        os.remove(fname)
                    print(f"☁️ Uploaded trajectory -> memory_vault/{domain_key}/{fname}")
            else:
                print(f"❌ Discarded (Failed sandbox assertions).")

        except Exception as e:
            print(f"⚠️ Cycle error: {e}")

        time.sleep(3)

    print("\n" + "=" * 70)
    print(f"📊 Summary: {successful_runs}/{total_cycles} verified trajectories uploaded to {VAULT_REPO}")
    print("=" * 70)

if __name__ == "__main__":
    execute_batch(total_cycles=6)
