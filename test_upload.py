import sys
import os
import requests

# Add project root to path
sys.path.append(os.getcwd())
from database import get_app_config_sync

def test_upload():
    print("--- Testing File Upload ---")
    token = get_app_config_sync("TG_Bot_Token", "")
    chat_id = get_app_config_sync("TG_Backup_Chat_ID", "")
    
    if not token or not chat_id:
        print("Missing config.")
        return

    # Create dummy file
    dummy_path = "test_upload.txt"
    with open(dummy_path, "w") as f:
        f.write("This is a test backup file content.")

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    print(f"Uploading to {chat_id}...")
    
    try:
        with open(dummy_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': chat_id, 'caption': "Test File"}
            resp = requests.post(url, files=files, data=data, timeout=30)
            print(f"Response: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)

if __name__ == "__main__":
    test_upload()
