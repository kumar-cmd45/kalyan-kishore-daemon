# ==============================================================================
# KALYAN KISHORE - HIGH-YIELD RLVR WORKER DAEMON (worker.py)
# Domains: Quantitative Finance & Greeks, Algorithmic Systems, Cybersecurity AST
# Architecture: Task Generation -> Inference -> Sandbox Eval -> Self-Repair -> HF Vault Upload
# ==============================================================================
import os
import sys
import time
import json
import random
import subprocess
import requests
from huggingface_hub import HfApi

# 1. Environment Variables & Hugging Face Vault Setup
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

hf_api = HfApi(token=HF_TOKEN) if HF_TOKEN else HfApi()

# ==============================================================================
# 2. MULTI-MODEL INFERENCE WATERFALL (Groq 70B -> Groq 8B -> Gemini 1.5)
# ==============================================================================
def call_llm(prompt, system_prompt="You are an expert autonomous software engineer and quantitative scientist."):
    """Waterfall LLM inference engine."""
    # 1. Try Groq (Llama-3.3-70B then Llama-3.1-8B)
    if GROQ_API_KEY:
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2
                }
                res = requests.post(url, headers=headers, json=payload, timeout=25)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"].strip(), f"Groq/{model}"
            except Exception:
                pass
            time.sleep(1)

    # 2. Try Gemini via OpenAI-Compatible Gateway
    if GEMINI_API_KEY:
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            headers = {
                "Authorization": f"Bearer {GEMINI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gemini-1.5-flash",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            res = requests.post(url, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"].strip(), "Gemini/1.5-flash"
        except Exception:
            pass

    return None, "None"

def clean_python_code(raw_text):
    """Extracts pure executable Python code from markdown blocks."""
    if not raw_text:
        return ""
    if "```python" in raw_text:
        return raw_text.split("```python")[1].split("```")[0].strip()
    elif "```" in raw_text:
        return raw_text.split("```")[1].split("```")[0].strip()
    return raw_text.strip()

# ==============================================================================
# 3. TASK GENERATORS FOR ALL 3 DOMAINS
# ==============================================================================

def get_quant_task():
    """Generates Quantitative Finance & Option Greeks tasks."""
    tasks = [
        {
            "domain": "quant_finance",
            "title": "Black-Scholes European Option Pricing & Greeks Calculator",
            "prompt": (
                "Write a Python function `calculate_black_scholes(S, K, T, r, sigma, option_type='call') -> dict` "
                "that computes theoretical price, Delta, and Gamma for a European option.\n"
                "Return a dict with keys: 'price', 'delta', 'gamma'. Use math or scipy.stats.norm."
            ),
            "test_code": """
import math

res_call = calculate_black_scholes(100, 100, 1.0, 0.05, 0.2, option_type='call')
assert abs(res_call['price'] - 10.45) < 0.6, f"Call price inaccurate: {res_call['price']}"
assert 0.5 < res_call['delta'] < 0.7, f"Call Delta inaccurate: {res_call['delta']}"
assert res_call['gamma'] > 0, f"Gamma should be positive: {res_call['gamma']}"

res_put = calculate_black_scholes(100, 100, 1.0, 0.05, 0.2, option_type='put')
assert abs(res_put['price'] - 5.57) < 0.6, f"Put price inaccurate: {res_put['price']}"
assert -0.5 < res_put['delta'] < -0.3, f"Put Delta inaccurate: {res_put['delta']}"
print("✅ Quant assertions passed.")
"""
        },
        {
            "domain": "quant_finance",
            "title": "Cash-and-Carry Arbitrage Spread Calculator",
            "prompt": (
                "Write a Python function `arbitrage_spread(spot_price, futures_price, r, T, storage_cost=0.0) -> dict` "
                "that computes the theoretical forward price, theoretical basis/spread, and returns an arbitrage recommendation "
                "('CASH_AND_CARRY', 'REVERSE_CASH_AND_CARRY', or 'NO_ARBITRAGE').\n"
                "Return a dict with keys: 'forward_price', 'spread', 'action'."
            ),
            "test_code": """
res1 = arbitrage_spread(1000, 1060, 0.05, 1.0)
assert res1['forward_price'] > 1050 and res1['forward_price'] < 1052
assert res1['spread'] > 0
assert res1['action'] == 'CASH_AND_CARRY'

res2 = arbitrage_spread(1000, 1000, 0.05, 1.0)
assert res2['action'] == 'REVERSE_CASH_AND_CARRY'
print("✅ Arbitrage assertions passed.")
"""
        }
    ]
    return random.choice(tasks)

def get_algo_task():
    """Generates Algorithmic Systems & Data Structures tasks."""
    tasks = [
        {
            "domain": "algo_systems",
            "title": "O(1) Least Recently Used (LRU) Cache Implementation",
            "prompt": (
                "Write a complete `LRUCache` class in Python supporting `get(key)` and `put(key, value)` in O(1) time complexity.\n"
                "The constructor accepts `capacity: int`."
            ),
            "test_code": """
lru = LRUCache(2)
lru.put(1, 10)
lru.put(2, 20)
assert lru.get(1) == 10
lru.put(3, 30) # evicts key 2
assert lru.get(2) == -1 or lru.get(2) is None
assert lru.get(3) == 30
lru.put(4, 40) # evicts key 1
assert lru.get(1) == -1 or lru.get(1) is None
assert lru.get(4) == 40
print("✅ LRU Cache assertions passed.")
"""
        },
        {
            "domain": "algo_systems",
            "title": "Dijkstra Shortest Path with Priority Queue",
            "prompt": (
                "Write a Python function `dijkstra(graph: dict, start_node: str) -> dict` "
                "that computes the shortest distance from `start_node` to all reachable nodes using `heapq`.\n"
                "The graph is formatted as { 'A': [('B', 1), ('C', 4)], ... }."
            ),
            "test_code": """
graph = {
    'A': [('B', 1), ('C', 4)],
    'B': [('C', 2), ('D', 5)],
    'C': [('D', 1)],
    'D': []
}
dist = dijkstra(graph, 'A')
assert dist['A'] == 0
assert dist['B'] == 1
assert dist['C'] == 3
assert dist['D'] == 4
print("✅ Dijkstra assertions passed.")
"""
        }
    ]
    return random.choice(tasks)

def get_cyber_ast_task():
    """Generates Cybersecurity AST Static Analysis tasks with standardized visitor signatures."""
    tasks = [
        {
            "domain": "cyber_ast",
            "title": "AST Static Vulnerability & Dangerous Sink Detection",
            "prompt": (
                "Write a Python function `audit_code_ast(source_code: str) -> list` using Python's built-in `ast` module.\n"
                "The function should inspect the Abstract Syntax Tree (AST) of the input code and detect dangerous sinks:\n"
                "- Calls to `eval()` or `exec()`\n"
                "- Calls to `os.system()` or `subprocess.Popen()` / `subprocess.run()` with `shell=True`\n"
                "Return a list of strings describing any detected vulnerabilities (empty list if safe)."
            ),
            "test_code": """
import ast

safe_sample = "def add(a, b):\\n    return a + b\\nprint(add(2, 3))"
eval_sample = "user_input = '__import__(\\'os\\').system(\\'ls\\')'\\neval(user_input)"
exec_sample = "exec('import sys')"
system_sample = "import os\\nos.system('rm -rf /')"

safe_res = audit_code_ast(safe_sample)
eval_res = audit_code_ast(eval_sample)
exec_res = audit_code_ast(exec_sample)
system_res = audit_code_ast(system_sample)

assert len(safe_res) == 0, f"False positive on safe code: {safe_res}"
assert any("eval" in str(r).lower() for r in eval_res), f"Missed eval sink: {eval_res}"
assert any("exec" in str(r).lower() for r in exec_res), f"Missed exec sink: {exec_res}"
assert any("system" in str(r).lower() or "os" in str(r).lower() for r in system_res), f"Missed os.system sink: {system_res}"
print("✅ Cyber AST assertions passed.")
"""
        },
        {
            "domain": "cyber_ast",
            "title": "AST Static Detection of Hardcoded High-Entropy Secrets",
            "prompt": (
                "Write a Python function `audit_secrets_ast(source_code: str) -> list` using Python's `ast` module.\n"
                "The function should inspect all string assignments (`ast.Assign`) where the variable name contains "
                "keywords like `api_key`, `secret`, `password`, `token` (case-insensitive) and the assigned value is a non-empty string literal.\n"
                "Return a list of detected variable names."
            ),
            "test_code": """
import ast

code_clean = "x = 10\\nusername = 'admin'"
code_leak = "API_KEY = 'sk-live-99384918239'\\ndb_password = 'SuperSecret123!'\\nnormal_var = 'hello'"

assert len(audit_secrets_ast(code_clean)) == 0, "False positive on clean code"
detected = [str(x).upper() for x in audit_secrets_ast(code_leak)]
assert any("API_KEY" in d for d in detected), "Failed to detect API_KEY"
assert any("DB_PASSWORD" in d for d in detected), "Failed to detect db_password"
print("✅ AST Secret Detection assertions passed.")
"""
        }
    ]
    return random.choice(tasks)

# ==============================================================================
# 4. DETERMINISTIC SANDBOX EXECUTION & SELF-REPAIR
# ==============================================================================

def execute_in_sandbox(candidate_code, test_harness):
    """Executes the candidate code combined with unit assertions in an isolated process."""
    combined_script = f"{candidate_code}\n\n{test_harness}"
    temp_path = "/tmp/action_sandbox_eval.py"
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(combined_script)

    try:
        res = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode == 0:
            return True, "All assertions passed"
        else:
            return False, (res.stderr or res.stdout).strip()
    except subprocess.TimeoutExpired:
        return False, "Execution timed out (>10s)"
    except Exception as e:
        return False, str(e)

def run_reasoning_cycle(cycle_num, total_cycles, target_domain):
    """Runs a single RLVR cycle with automated self-repair."""
    # Pick domain generator
    if target_domain == "quant_finance":
        task = get_quant_task()
        domain_label = "Quantitative Finance & Greeks"
    elif target_domain == "cyber_ast":
        task = get_cyber_ast_task()
        domain_label = "Cybersecurity AST Auditor"
    else:
        task = get_algo_task()
        domain_label = "Algorithmic Systems & Structures"

    print(f"\n[Cycle {cycle_num}/{total_cycles}] Target: {domain_label}")
    
    # 1. Initial Generation
    gen_prompt = f"{task['prompt']}\n\nProvide only valid, complete, and bug-free Python code."
    raw_response, model_name = call_llm(gen_prompt)
    if not raw_response:
        print("  ⚠️ Inference endpoints busy/rate-limited.")
        return False

    code = clean_python_code(raw_response)
    print(f"  ⚡ Candidate generated via {model_name}")

    # 2. First Sandbox Evaluation
    passed, logs = execute_in_sandbox(code, task["test_code"])
    
    # 3. Automated Self-Repair Loop if initial test failed
    if not passed:
        print(f"  ⚠️ Initial test failed ({logs[:80]}...). Repairing...")
        repair_prompt = f"""
The following Python implementation failed unit test verification.
Original Task:
{task['prompt']}

Your Code:
{code}

Error / Traceback:
{logs}

Fix all errors and return the complete corrected Python code.
"""
        repaired_raw, _ = call_llm(repair_prompt)
        if repaired_raw:
            code = clean_python_code(repaired_raw)
            passed, logs = execute_in_sandbox(code, task["test_code"])

    # 4. Vault Upload upon passing verification
    if passed:
        print("  ✅ PASSED on Verification (Reward: 1.00)")
        timestamp = int(time.time())
        filename = f"trace_{task['domain']}_{timestamp}.json"
        vault_path = f"memory_vault/{task['domain']}/{filename}"

        payload = {
            "timestamp": timestamp,
            "domain": task["domain"],
            "title": task["title"],
            "prompt": task["prompt"],
            "code": code,
            "test_harness": task["test_code"],
            "reward": 1.00,
            "status": "VERIFIED_PASS",
            "model": model_name
        }

        if HF_TOKEN:
            try:
                local_file = f"/tmp/{filename}"
                with open(local_file, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)

                hf_api.upload_file(
                    path_or_fileobj=local_file,
                    path_in_repo=vault_path,
                    repo_id=VAULT_REPO,
                    repo_type="model"
                )
                print(f"  ☁️ Uploaded trajectory -> {vault_path}")
                return True
            except Exception as e:
                print(f"  ⚠️ Vault upload notice: {e}")
        return True
    else:
        print(f"  ❌ Discarded (Failed sandbox assertions: {logs[:100]}).")
        return False

# ==============================================================================
# 5. MAIN BATCH CONTROLLER
# ==============================================================================
def main():
    print("==================================================================")
    print("🚀 INITIATING HIGH-YIELD RLVR WORKER (6 CYCLES)")
    print("==================================================================")

    # 6 balanced cycles: 2 Quant Finance, 2 Algo Systems, 2 Cybersecurity AST
    domains = [
        "quant_finance",
        "algo_systems",
        "cyber_ast",
        "quant_finance",
        "algo_systems",
        "cyber_ast"
    ]

    successes = 0
    for idx, domain in enumerate(domains, 1):
        if run_reasoning_cycle(idx, len(domains), domain):
            successes += 1
        time.sleep(2)  # Prevent rate limits

    print("==================================================================")
    print(f"📊 Summary: {successes}/{len(domains)} verified trajectories uploaded to {VAULT_REPO}")
    print("==================================================================")

if __name__ == "__main__":
    main()
    
