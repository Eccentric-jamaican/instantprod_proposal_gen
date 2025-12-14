"""
Helper to restore Google Cloud credentials from environment variables.
Use this in Railway/Cloud deployments where we can't store .json files.
"""
import os
import json
import base64
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def restore_credentials():
    """Restore credentials.json and token.json from env vars if needed."""
    
    # Restore credentials.json
    creds_path = PROJECT_ROOT / 'credentials.json'
    if not creds_path.exists():
        encoded_creds = os.getenv("GOOGLE_CREDENTIALS_BASE64")
        if encoded_creds:
            try:
                print("🔑 Restoring credentials.json from environment...")
                decoded = base64.b64decode(encoded_creds).decode('utf-8')
                with open(creds_path, 'w') as f:
                    f.write(decoded)
            except Exception as e:
                print(f"⚠️ Failed to restore credentials: {e}")

    # Restore token.json
    token_path = PROJECT_ROOT / 'token.json'
    if not token_path.exists():
        encoded_token = os.getenv("GOOGLE_TOKEN_BASE64")
        if encoded_token:
            try:
                print("🔑 Restoring token.json from environment...")
                decoded = base64.b64decode(encoded_token).decode('utf-8')
                with open(token_path, 'w') as f:
                    f.write(decoded)
            except Exception as e:
                print(f"⚠️ Failed to restore token: {e}")

if __name__ == "__main__":
    restore_credentials()
