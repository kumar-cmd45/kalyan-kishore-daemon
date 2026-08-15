def update_bounty_ledger(attempted_item: dict, status: str, details: str):
    """Logs background execution stats to Hugging Face for the bot to read."""
    if not hf_api:
        return
    ledger_file = "bounty_ledger.json"
    ledger_path = f"telemetry/{ledger_file}"
    
    # 1. Download existing ledger or create fresh
    ledger = {
        "total_scanned": 0,
        "total_attempts": 0,
        "total_passed": 0,
        "recent_logs": []
    }
    try:
        local_p = hf_api.hf_hub_download(repo_id=VAULT_REPO, filename=ledger_path, repo_type="model")
        with open(local_p, "r", encoding="utf-8") as f:
            ledger = json.load(f)
    except Exception:
        pass

    # 2. Update metrics
    ledger["total_attempts"] += 1
    if status == "VERIFIED":
        ledger["total_passed"] += 1

    entry = {
        "timestamp": int(time.time()),
        "repo": attempted_item.get("repo", "unknown"),
        "issue_number": attempted_item.get("number", 0),
        "title": attempted_item.get("title", "")[:60],
        "status": status,
        "details": details[:100]
    }
    ledger["recent_logs"] = [entry] + ledger["recent_logs"][:15]  # Keep last 15 attempts

    # 3. Upload back to Hugging Face
    with open(ledger_file, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)
    try:
        hf_api.upload_file(
            path_or_fileobj=ledger_file,
            path_in_repo=ledger_path,
            repo_id=VAULT_REPO,
            repo_type="model"
        )
        if os.path.exists(ledger_file):
            os.remove(ledger_file)
    except Exception as e:
        print(f"⚠️ Failed to sync telemetry ledger: {e}")
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
