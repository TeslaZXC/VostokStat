import os
import shutil
import zipfile
import datetime
import requests
import asyncio
from typing import Optional

# Constants
DB_PATH = "vostokstat.db"
BACKUP_DIR = "backups"

def create_backup_zip() -> str:
    """
    Creates a ZIP backup of the database.
    Returns the absolute path to the created ZIP file.
    """
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"vostokstat_backup_{timestamp}.zip"
    zip_path = os.path.join(BACKUP_DIR, backup_name)

    # Use a temporary file for the DB copy to avoid locking issues if possible,
    # though with SQLite shutil.copy is usually fine for read-only copy.
    # For extra safety, we might want to wal_checkpoint if we were doing this perfectly,
    # but for this scale, direct copy zipping is standard.
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.exists(DB_PATH):
            zipf.write(DB_PATH, arcname="vostokstat.db")
        else:
            raise FileNotFoundError(f"Database file {DB_PATH} not found.")

    return os.path.abspath(zip_path)

import httpx
import datetime

# Logging helper
def log_debug(msg):
    with open("backup_debug.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()}: {msg}\n")

async def send_to_telegram(file_path: str, bot_token: str, chat_id: str) -> bool:
    """
    Sends the specified file to Telegram (Async).
    """
    if not bot_token or not chat_id:
        log_debug("Telegram Bot Token or Chat ID not configured.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    try:
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': chat_id, 'caption': f"Backup: {os.path.basename(file_path)}"}
                # 300s timeout (5 mins)
                log_debug(f"Sending POST to {url} with 300s timeout...")
                response = await client.post(url, data=data, files=files, timeout=300.0)
                
                if response.status_code == 200:
                    log_debug(f"Successfully sent {file_path} to Telegram.")
                    return True
                else:
                    log_debug(f"Failed to send to Telegram: {response.text}")
                    return False
    except Exception as e:
        log_debug(f"Error sending to Telegram: {e}")
        return False

# Logging helper
def log_debug(msg):
    with open("backup_debug.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()}: {msg}\n")

async def run_backup_task(get_config_func):
    """
    Main task to be run by scheduler.
    """
    log_debug("=== Starting Backup Task (Async HTTPX) ===")
    print("=== Starting Backup Task ===")
    try:
        # Create Zip
        log_debug("Creating zip...")
        # Run zip creation in thread to avoid blocking loop
        zip_path = await asyncio.to_thread(create_backup_zip)
        log_debug(f"Backup created at: {zip_path}")
        print(f"Backup created at: {zip_path}")
        
        # Get Config
        log_debug("Fetching config...")
        try:
            bot_token = get_config_func("TG_Bot_Token", "")
            chat_id = get_config_func("TG_Backup_Chat_ID", "")
            log_debug(f"Config Retrieved. Token: {'Yes' if bot_token else 'No'}, ChatID: {chat_id}")
        except Exception as e:
            log_debug(f"Config Fetch Failed: {e}")
            return

        if bot_token and chat_id:
            log_debug("Starting upload to Telegram (HTTPX)...")
            # Directly await the async function, no to_thread needed for IO
            success = await send_to_telegram(zip_path, bot_token, chat_id)
            log_debug(f"Upload Result: {success}")
        else:
            log_debug("Telegram not configured. Skipping upload.")
            print("Telegram not configured. Skipping upload.")

    except Exception as e:
        log_debug(f"Backup task CRITICAL FAIL: {e}")
        print(f"Backup task failed: {e}")
    print("=== Backup Task Finished ===")
