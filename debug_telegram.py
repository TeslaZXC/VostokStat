import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from database import init_db, get_app_config_sync
import requests

def test_telegram():
    print("--- Debugging Telegram Config ---")
    
    # Check Config
    token = get_app_config_sync("TG_Bot_Token", "")
    chat_id = get_app_config_sync("TG_Backup_Chat_ID", "")
    
    print(f"Token Found: {'Yes' if token else 'No'} ({token[:5]}... via DB)")
    print(f"Chat ID Found: {'Yes' if chat_id else 'No'} ({chat_id})")
    
    if not token or not chat_id:
        print("ERROR: Token or Chat ID is missing in database.")
        print("Please go to Admin -> Tools -> Telegram Backups and save settings.")
        return

    # Test Message
    print("\n--- Sending Test Message ---")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "ðŸ”§ VostokStat Debug Message: Connection verified!"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 200:
            print("\nSUCCESS: Message sent successfully!")
        elif resp.status_code == 401:
            print("\nERROR: Unauthorized. Check your Bot Token.")
        elif resp.status_code == 400:
            print("\nERROR: Bad Request. Check your Chat ID or if bot is blocked.")
            print("Did you press /start in your bot?")
        else:
            print(f"\nERROR: Unknown error.")
            
    except Exception as e:
        print(f"\nEXCEPTION: {e}")

if __name__ == "__main__":
    test_telegram()
