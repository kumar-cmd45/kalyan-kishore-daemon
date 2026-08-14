# ==============================================================================
# TELEGRAM HANDLER: TRACK KAGGLE COMPUTE & STATUS
# ==============================================================================
import os
import subprocess

# Set Kaggle credentials from your environment or secrets
# os.environ["KAGGLE_USERNAME"] = "your_kaggle_username"
# os.environ["KAGGLE_KEY"] = "your_kaggle_key"

@bot.message_handler(commands=['kaggle'])
def check_kaggle_status(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Replace with your Kaggle username and notebook slug
    kernel_slug = "kumar5674/kalyan-kishore-worker"
    
    try:
        # Check kernel status via Kaggle CLI
        res = subprocess.run(
            ["kaggle", "kernels", "status", kernel_slug],
            capture_output=True,
            text=True,
            timeout=10
        )
        kernel_status = res.stdout.strip() if res.returncode == 0 else "Kernel not found or API key unset."
        
        status_msg = (
            "⚙️ *Kaggle Background Compute Telemetry*\n\n"
            f"• *Kernel Target:* `{kernel_slug}`\n"
            f"• *Execution State:* `{kernel_status}`\n"
            f"• *Weekly Free Quota:* `30.0 GPU Hours`\n"
            "• *Tip:* When running with `Accelerator: None (CPU)`, GPU quota remains `100% untouched`."
        )
        bot.reply_to(message, status_msg, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Kaggle tracking notice: {e}")
