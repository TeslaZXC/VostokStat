try:
    from api.main import app
    print("Success: App imported correctly")
except ImportError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Exception: {e}")
