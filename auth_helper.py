"""
Helper to restore Google Cloud credentials from environment variables.
Use this in Railway/Cloud deployments where we can't store .json files.
"""
import os
import json
import base64
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def get_writable_path(filename: str) -> Path:
    """Get a writable path for the file (uses /tmp on Vercel)."""
    if os.environ.get("VERCEL"):
        return Path("/tmp") / filename
    return PROJECT_ROOT / filename

def restore_credentials():
    """Restore credentials.json and token.json from env vars if needed."""
    
    # Restore credentials.json
    creds_path = get_writable_path('credentials.json')
    
    # Only try to restore if file doesn't exist
    if not creds_path.exists():
        encoded_creds = os.getenv("GOOGLE_CREDENTIALS_BASE64")
        if encoded_creds:
            try:
                print(f"🔑 Restoring credentials.json to {creds_path}...")
                decoded = base64.b64decode(encoded_creds).decode('utf-8')
                with open(creds_path, 'w') as f:
                    f.write(decoded)
            except Exception as e:
                print(f"⚠️ Failed to restore credentials: {e}")

    # Restore token.json
    token_path = get_writable_path('token.json')
    if not token_path.exists():
        encoded_token = os.getenv("GOOGLE_TOKEN_BASE64")
        if encoded_token:
            try:
                print(f"🔑 Restoring token.json to {token_path}...")
                decoded = base64.b64decode(encoded_token).decode('utf-8')
                with open(token_path, 'w') as f:
                    f.write(decoded)
            except Exception as e:
                print(f"⚠️ Failed to restore token: {e}")
                
    # Set standard env var so Google libraries find the credentials
    # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(creds_path) 
    # (Optional, but our scripts usually look for the file specifically)
    return creds_path, token_path

if __name__ == "__main__":
    restore_credentials()
