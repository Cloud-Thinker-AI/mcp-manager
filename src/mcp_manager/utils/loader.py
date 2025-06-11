import os
import secrets

def load_api_key(API_KEY_FILE: str):
    if not os.path.exists(API_KEY_FILE):
        api_key = secrets.token_urlsafe(32)
        with open(API_KEY_FILE, "w") as f:
            f.write(api_key)
        return api_key
    
    with open(API_KEY_FILE, "r") as f:
        return f.read().strip()