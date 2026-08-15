# ==============================================================================
# KALYAN KISHORE MASTER BOT & PUBLIC MICRO-API GATEWAY (bot.py)
# Zero-Capital / Zero-Client / Stateless HTTP Engine
# ==============================================================================
import os
import ast
import math
import json
import requests
import telebot
from flask import Flask, request, jsonify
from huggingface_hub import HfApi

# 1. Environment & Telegram Setup
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL", "").strip()
RAPIDAPI_SECRET = os.environ.get("RAPIDAPI_PROXY_SECRET", "").strip()
VAULT_REPO = "Kumar5674/kalyan-kishore-vault"

bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
app = Flask(__name__)
hf_api = HfApi()

# ==============================================================================
# DETERMINISTIC MICRO-API ENDPOINTS (Render Hosted / RapidAPI Compatible)
# ==============================================================================

def verify_api_request():
    """Optional security check for RapidAPI proxy secret."""
    if not RAPIDAPI_SECRET:
        return True
    proxy_secret = request.headers.get("X-RapidAPI-Proxy-Secret", "")
    return proxy_secret == RAPIDAPI_SECRET

@app.route('/api/v1/quant/pricing', methods=['POST'])
def quant_pricing_api():
    """Calculates Black-Scholes Greeks and Cash-and-Carry theoretical futures basis."""
    if not verify_api_request():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True, silent=True) or {}
    try:
        S = float(data.get("spot_price", 100.0))
        K = float(data.get("strike_price", 100.0))
        T = float(data.get("time_to_expiry_years", 1.0))
        r = float(data.get("risk_free_rate", 0.05))
        sigma = float(data.get("volatility", 0.20))
        div_yield = float(data.get("dividend_yield", 0.0))

        # Black-Scholes Calculation
        d1 = (math.log(S / K) + (r - div_yield + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        call_delta = math.exp(-div_yield * T) * 0.5 * (1.0 + math.erf(d1 / math.sqrt(2.0)))
        put_delta = call_delta - math.exp(-div_yield * T)
        gamma = (math.exp(-div_yield * T) / (S * sigma * math.sqrt(T))) * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2)
        vega = S * math.exp(-div_yield * T) * math.sqrt(T) * (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2) / 100.0
        
        # Cash and Carry Basis
        theoretical_futures = S * math.exp((r - div_yield) * T)
        basis_spread = theoretical_futures - S

        return jsonify({
            "status": "success",
            "model": "Black-Scholes-Merton (1973)",
            "metrics": {
                "call_delta": round(call_delta, 6),
                "put_delta": round(put_delta, 6),
                "gamma": round(gamma, 6),
                "vega_1pct": round(vega, 6),
                "theoretical_futures_price": round(theoretical_futures, 4),
                "basis_spread": round(basis_spread, 4)
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/v1/security/ast-audit', methods=['POST'])
def ast_security_audit_api():
    """Performs deterministic AST static vulnerability analysis on submitted Python code."""
    if not verify_api_request():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True, silent=True) or {}
    code_snippet = data.get("code", "")
    if not code_snippet:
        return jsonify({"status": "error", "message": "Field 'code' is required."}), 400

    vulnerabilities = []
    try:
        parsed_tree = ast.parse(code_snippet)
        for node in ast.walk(parsed_tree):
            # Check for OS Command Injection Sinks
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr in ["system", "popen"]:
                    vulnerabilities.append({
                        "type": "CWE-78: OS Command Injection",
                        "severity": "CRITICAL",
                        "line": node.lineno,
                        "sink": f"os.{node.func.attr}",
                        "recommendation": "Use subprocess.run(..., shell=False) with parameterized arguments."
                    })
                elif isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec"]:
                    vulnerabilities.append({
                        "type": "CWE-95: Improper Code Evaluation",
                        "severity": "HIGH",
                        "line": node.lineno,
                        "sink": node.func.id,
                        "recommendation": "Avoid dynamic code execution; use ast.literal_eval() if deserializing data."
                    })

        return jsonify({
            "status": "vulnerabilities_detected" if vulnerabilities else "clean",
            "findings_count": len(vulnerabilities),
            "findings": vulnerabilities
        }), 200
    except SyntaxError as syn_err:
        return jsonify({"status": "syntax_error", "message": str(syn_err)}), 400

# ==============================================================================
# TELEGRAM BOT CONTROLLER & WEBHOOK
# ==============================================================================

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid', 403

@bot.message_handler(commands=['status'])
def send_status(message):
    try:
        files = hf_api.list_repo_files(repo_id=VAULT_REPO, repo_type="model")
        quant_count = len([f for f in files if f.startswith("memory_vault/quant_finance/")])
        algo_count = len([f for f in files if f.startswith("memory_vault/algo_systems/")])
        cyber_count = len([f for f in files if f.startswith("memory_vault/cyber_ast/")])
        bounty_count = len([f for f in files if f.startswith("memory_vault/bounties/")])
        total_count = quant_count + algo_count + cyber_count

        telemetry = (
            "=== LIVE SYSTEM TELEMETRY ===\n"
            f"• Vault Repository: {VAULT_REPO}\n"
            f"• Total Verified Trajectories: {total_count}\n"
            f"  - Quantitative Finance: {quant_count}\n"
            f"  - Algorithmic Systems: {algo_count}\n"
            f"  - Cyber Security AST: {cyber_count}\n"
            f"  - Verified Bounties: {bounty_count}\n"
            "• Public APIs: /api/v1/quant/pricing | /api/v1/security/ast-audit\n"
            "• Background Worker: GitHub Actions (Hourly Batch)\n"
            "============================="
        )
        bot.reply_to(message, telemetry)
    except Exception as e:
        bot.reply_to(message, f"Telemetry Error: {str(e)}")

@app.route('/', methods=['GET'])
def health():
    return "Kalyan Kishore Engine Active (APIs & Webhooks Online)", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
