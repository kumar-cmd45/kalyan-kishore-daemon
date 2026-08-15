# ==============================================================================
# KALYAN KISHORE VAULT AUDITOR & QUALITY BENCHMARK (verify_vault.py)
# ==============================================================================
import os
import ast
import json
import tempfile
import subprocess
from huggingface_hub import HfApi, hf_hub_download

VAULT_REPO = "Kumar5674/kalyan-kishore-vault"
HF_TOKEN = os.environ.get("HF_TOKEN", "")

api = HfApi(token=HF_TOKEN) if HF_TOKEN else HfApi()

def audit_vault():
    print("🔍 Fetching vault index from Hugging Face...")
    files = api.list_repo_files(repo_id=VAULT_REPO, repo_type="model")
    target_files = [f for f in files if f.startswith("memory_vault/") and f.endswith(".json")]
    
    total = len(target_files)
    if total == 0:
        print("⚠️ No JSON trajectories found in memory_vault/")
        return

    passed_schema = 0
    passed_execution = 0
    categories = {"quant_finance": 0, "algo_systems": 0, "cyber_ast": 0, "bounties": 0}

    print(f"📊 Auditing {total} trajectories...\n")

    for file_path in target_files:
        local_path = hf_hub_download(repo_id=VAULT_REPO, filename=file_path, repo_type="model")
        with open(local_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                continue

        # 1. Schema Adherence
        has_prompt = "prompt" in data or "bounty" in data
        has_code = "solution" in data or "code" in data or "solution_patch" in data
        if has_prompt and has_code:
            passed_schema += 1

        # Track Category
        for cat in categories:
            if cat in file_path:
                categories[cat] += 1

        # 2. Sandboxed Dynamic Verification
        code_to_test = data.get("solution") or data.get("code") or ""
        if code_to_test:
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
                tmp.write(code_to_test)
                tmp_path = tmp.name

            try:
                res = subprocess.run(
                    ["python3", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if res.returncode == 0:
                    passed_execution += 1
            except Exception:
                pass
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    # 3. Quality Metrics Summary
    print("=" * 40)
    print("🏆 VAULT QUALITY AUDIT REPORT")
    print("=" * 40)
    print(f"• Total Trajectories Analyzed: {total}")
    print(f"• Valid Schema Pass Rate:      {passed_schema}/{total} ({(passed_schema/total)*100:.1f}%)")
    print(f"• Sandboxed Execution Pass Rate:{passed_execution}/{total} ({(passed_execution/total)*100:.1f}%)")
    print("\n📂 Category Distribution:")
    for cat, count in categories.items():
        print(f"  - {cat.replace('_', ' ').title()}: {count}")
    print("=" * 40)

if __name__ == "__main__":
    audit_vault()
