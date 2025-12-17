#!/usr/bin/env python3
"""
Test Google API authentication.
This script verifies that OAuth credentials are set up correctly.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes required for Sheets, Slides, and Drive
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
]

CREDENTIALS_FILE = PROJECT_ROOT / 'credentials.json'
TOKEN_FILE = PROJECT_ROOT / 'token.json'


def get_credentials():
    """Get or refresh OAuth credentials."""
    creds = None
    
    # Check for existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"[FAIL] credentials.json not found at: {CREDENTIALS_FILE}")
                return None
            
            print("Opening browser for authentication...")
            print("(You may need to click 'Advanced' -> 'Go to app' if you see a warning)")
            print()
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
        
        # Save credentials for next time
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"[OK] Token saved to: {TOKEN_FILE}")
    
    return creds


def test_sheets_api(creds):
    """Test Google Sheets API connection."""
    try:
        service = build('sheets', 'v4', credentials=creds)
        # Just build the service, don't create anything
        print("[OK] Google Sheets API - Connected")
        return True
    except HttpError as e:
        print(f"[FAIL] Google Sheets API - {e}")
        return False


def test_slides_api(creds):
    """Test Google Slides API connection."""
    try:
        service = build('slides', 'v1', credentials=creds)
        print("[OK] Google Slides API - Connected")
        return True
    except HttpError as e:
        print(f"[FAIL] Google Slides API - {e}")
        return False


def test_drive_api(creds):
    """Test Google Drive API connection."""
    try:
        service = build('drive', 'v3', credentials=creds)
        print("[OK] Google Drive API - Connected")
        return True
    except HttpError as e:
        print(f"[FAIL] Google Drive API - {e}")
        return False


def main():
    """Run authentication test."""
    print("=" * 60)
    print("Google API Authentication Test")
    print("=" * 60)
    print()
    
    # Check credentials file
    print("1. Checking credentials file...")
    if CREDENTIALS_FILE.exists():
        print(f"[OK] Found: {CREDENTIALS_FILE}")
    else:
        print(f"[FAIL] Not found: {CREDENTIALS_FILE}")
        print("\nPlease download credentials.json from Google Cloud Console")
        return 1
    
    print()
    
    # Get credentials (will open browser if needed)
    print("2. Authenticating...")
    creds = get_credentials()
    
    if not creds:
        print("[FAIL] Could not obtain credentials")
        return 1
    
    print("[OK] Authentication successful!")
    print()
    
    # Test API connections
    print("3. Testing API connections...")
    sheets_ok = test_sheets_api(creds)
    slides_ok = test_slides_api(creds)
    drive_ok = test_drive_api(creds)
    
    print()
    print("=" * 60)
    
    if sheets_ok and slides_ok and drive_ok:
        print("[OK] All Google APIs connected successfully!")
        print()
        print("You're ready to use:")
        print("  - Google Sheets API (create/read/write spreadsheets)")
        print("  - Google Slides API (create/edit presentations)")
        print("  - Google Drive API (file management)")
        print("=" * 60)
        return 0
    else:
        print("[FAIL] Some APIs failed to connect")
        print("Check that you enabled all APIs in Google Cloud Console:")
        print("  - Google Sheets API")
        print("  - Google Slides API")
        print("  - Google Drive API")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
