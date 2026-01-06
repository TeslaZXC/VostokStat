import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database import get_app_config_sync
from logic.backup import run_backup_task

async def manual_trigger():
    print("--- 1. Starting Manual Trigger of Backup Task ---")
    try:
        # Assuming run_backup_task is async
        await run_backup_task(get_app_config_sync)
        print("--- 2. Task Completed (Check for previous output lines) ---")
    except Exception as e:
        print(f"--- ERROR: Task Crashed: {e} ---")

if __name__ == "__main__":
    asyncio.run(manual_trigger())
