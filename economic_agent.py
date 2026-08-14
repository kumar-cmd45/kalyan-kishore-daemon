# ==============================================================================
# KALYAN KISHORE: SELF-CONTAINED ECONOMIC & ALGORITHMIC AGENT
# ==============================================================================
import os
import sys
import json
import time
import random
import subprocess
from groq import Groq
from google import genai
from huggingface_hub import HfApi

# 1. Configuration & Secrets
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else None

# High-value algorithmic & quantitative domains
TASK_DOMAINS = [
    "algorithmic_order_routing_and_slippage_optimization",
    "black_scholes_implied_volatility_newton_raphson",
    "merkle_tree_cryptographic_state_verifier",
    "asynchronous_rate_limiter_token_bucket",
    "sparse_matrix_graph_laplacian_eigenvalues",
    "monte_carlo_var_portfolio_risk_engine",
    "fast_fourier_transform_signal_denoising"
]

def generate_and_solve_challenge():
    domain = random.choice(TASK_DOMAINS)
    print(f"⚡ Target Domain: {domain}")

    prompt = (
        f"Generate an expert-level, self-contained Python problem and complete solution for domain: {domain}.\n\n"
        "STRICT REQUIREMENTS:\n"
        "1. Standard Python libraries only (numpy, math, typing, collections, hashlib, scipy).\n"
        "2. The code must contain the complete working implementation.\n"
        "3. Include at least 4 strict assert statements at the bottom that test edge cases.\n"
        "4. Output ONLY valid executable Python code without markdown tags."
    )

    code = None
    if groq_client:
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                res = groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=2200
                )
                if res.choices and res.choices[0].message.content:
                    code = res.choices[0].message.content
                    break
            except Exception:
                continue

    if not code and gemini_client:
        for model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                res = gemini_client.models.generate_content(model=model, contents=prompt)
                if res and res.text:
                    code = res.text
                    break
            except Exception:
                continue

    if not code:
        raise RuntimeError("Failed to generate solution from inference providers.")

    return domain, code.replace("```python", "").replace("```", "").strip()

def evaluate_sandbox(code_str: str) -> tuple[bool, str]:
    test_path = "/tmp/sandbox_eval.py"
    with open(test_path, "w") as f:
        f.write(code_str)
    try:
        proc = subprocess.run([sys.executable, test_path], capture_output=True, text=True, timeout=12)
        passed = (proc.returncode == 0)
        logs = proc.stdout if passed else proc.stderr
        return passed, logs
    except subprocess.TimeoutExpired:
        return False, "Timed out (>12s)"
    finally:
        if os.path.exists(test_path):
            os.remove(test_path)

def run_cycle():
    print("=" * 70)
    print("🚀 RUNNING AUTONOMOUS REASONING & VAULT INGESTION")
    print("=" * 70)

    for attempt in range(1, 4):
        print(f"\n--- Batch Attempt {attempt}/3 ---")
        try:
            domain, clean_code = generate_and_solve_challenge()
            passed, logs = evaluate_sandbox(clean_code)

            if passed:
                print(f"✅ Code verified 100% against all unit assertions!")
                if hf_api:
                    timestamp = int(time.time())
                    fname = f"trace_{domain}_{timestamp}.json"
                    payload = {
                        "timestamp": timestamp,
                        "domain": domain,
                        "verified": True,
                        "solution_code": clean_code
                    }
                    with open(fname, "w") as f:
                        json.dump(payload, f, indent=2)

                    # Determine repo type (default: model)
                    hf_api.upload_file(
                        path_or_fileobj=fname,
                        path_in_repo=f"memory_vault/{domain}/{fname}",
                        repo_id=VAULT_REPO,
                        repo_type="model"
                    )
                    if os.path.exists(fname):
                        os.remove(fname)
                    print(f"☁️ Uploaded trajectory to Hugging Face Vault: memory_vault/{domain}/{fname}")
                break
            else:
                print(f"❌ Sandbox assertions failed:\n{logs[:180]}")
        except Exception as e:
            print(f"⚠️ Cycle error: {e}")

    print("\n" + "=" * 70)
    print("🏁 Cycle completed.")
    print("=" * 70)

if __name__ == "__main__":
    run_cycle()
