import os
import sys
import time
import subprocess

print("🚀 Initializing Kalyan Kishore Kaggle Closed Loop Daemon...")

# 1. Install required packages in Kaggle container
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyTelegramBotAPI", "flask", "requests", "huggingface_hub"])

# 2. Cycle configuration (Runs for 3.8 hours before handoff)
INTERVAL_SECONDS = 210  # 3.5 minutes
MAX_DURATION_SECONDS = 3.8 * 3600  # 3.8 hours
start_time = time.time()
cycle_num = 1

while (time.time() - start_time) < MAX_DURATION_SECONDS:
    print(f"\n========================================================")
    print(f"🔄 KAGGLE CYCLE #{cycle_num} | Elapsed: {int((time.time() - start_time)/60)}m")
    print(f"========================================================")
    
    # Run worker (RLVR trajectories)
    print("⚡ Executing RLVR worker cycles...")
    subprocess.run([sys.executable, "worker.py"])
    
    # Run paid bounty engine
    print("💰 Scanning and solving paid bounties (>= $10)...")
    subprocess.run([sys.executable, "economic_agent.py"])
    
    print(f"⏳ Sleeping {INTERVAL_SECONDS}s before next cycle...")
    time.sleep(INTERVAL_SECONDS)
    cycle_num += 1

print("🏁 Cycle window completed cleanly. Ready for next automated trigger.")
