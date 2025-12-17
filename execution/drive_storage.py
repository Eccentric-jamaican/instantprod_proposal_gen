#!/usr/bin/env python3
"""
Google Drive Cloud Storage Manager for InstantProd Proposals.

This module syncs local proposal files to Google Drive, maintaining
the same folder structure. It supports:
- Automatic upload on file creation
- Folder structure mirroring
- File versioning (Google Drive handles this automatically)
- Download from Drive to local

Folder Structure in Google Drive:
    InstantProd Proposals/
    ├── transcripts/        # Call transcripts (.txt, .json)
    ├── proposals/          # Generated HTML proposals
    ├── deployments/        # Deployment logs and URLs
    └── exports/            # Any exported files

Usage:
    # Upload a file
    python execution/drive_storage.py --action upload --file .tmp/proposals/acme.html
    
    # Sync all local files to Drive
    python execution/drive_storage.py --action sync
    
    # List files in Drive
    python execution/drive_storage.py --action list
    
    # Download a file from Drive
    python execution/drive_storage.py --action download --file-id <ID> --output local/path.html
"""

import os
import sys
import json
import click
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Scopes - using drive.file which allows file creation/access for files created by this app
# This is more secure and should match the existing token scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive.file',  # Access to files created by this app
    'https://www.googleapis.com/auth/gmail.send',
]

# Use auth_helper to get correct paths (handles Vercel /tmp)
try:
    import auth_helper
    CREDENTIALS_FILE, TOKEN_FILE = auth_helper.restore_credentials()
except ImportError:
    # Fallback for local dev if auth_helper not found in path
    CREDENTIALS_FILE = PROJECT_ROOT / 'credentials.json'
    TOKEN_FILE = PROJECT_ROOT / 'token.json'

# Local directories to sync
# On Vercel, we must write to /tmp
if os.environ.get("VERCEL"):
    TMP_DIR = Path("/tmp") / '.tmp'
else:
    TMP_DIR = PROJECT_ROOT / '.tmp'

TRANSCRIPTS_DIR = TMP_DIR / 'transcripts'
PROPOSALS_DIR = TMP_DIR / 'proposals'
DEPLOY_DIR = TMP_DIR / 'deploy'

# Drive folder structure
DRIVE_ROOT_FOLDER = "InstantProd Proposals"
DRIVE_FOLDERS = {
    "transcripts": "transcripts",
    "proposals": "proposals", 
    "deployments": "deployments",
    "exports": "exports",
}

# Cache for folder IDs
_folder_cache: Dict[str, str] = {}


def get_drive_service():
    """Get authenticated Google Drive service."""
    creds = None
    
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            # Token file exists but may have different scopes, will re-auth
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # Refresh failed, need to re-authenticate
                creds = None
        
        if not creds:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError("credentials.json not found. Please set up Google API credentials.")
            
            print("🔐 Opening browser for Google authentication...")
            print("   (You may need to click 'Advanced' → 'Go to app' if you see a warning)")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
        
        # Save credentials for next time
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print("✅ Authentication successful!")
    
    return build('drive', 'v3', credentials=creds)


def get_or_create_folder(service, folder_name: str, parent_id: str = None) -> str:
    """Get or create a folder in Google Drive. Returns folder ID."""
    cache_key = f"{parent_id or 'root'}:{folder_name}"
    
    if cache_key in _folder_cache:
        return _folder_cache[cache_key]
    
    # Search for existing folder
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    
    if files:
        folder_id = files[0]['id']
    else:
        # Create new folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
        print(f"  📁 Created folder: {folder_name}")
    
    _folder_cache[cache_key] = folder_id
    return folder_id


def ensure_folder_structure(service) -> Dict[str, str]:
    """Ensure the folder structure exists in Google Drive. Returns folder IDs."""
    print("📂 Ensuring folder structure in Google Drive...")
    
    # Create or get root folder
    root_id = get_or_create_folder(service, DRIVE_ROOT_FOLDER)
    folder_ids = {"root": root_id}
    
    # Create subfolders
    for key, name in DRIVE_FOLDERS.items():
        folder_ids[key] = get_or_create_folder(service, name, root_id)
    
    print(f"  ✅ Folder structure ready!")
    return folder_ids


def get_mime_type(file_path: Path) -> str:
    """Get MIME type for a file."""
    extension = file_path.suffix.lower()
    mime_types = {
        '.html': 'text/html',
        '.txt': 'text/plain',
        '.json': 'application/json',
        '.md': 'text/markdown',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.pdf': 'application/pdf',
        '.zip': 'application/zip',
    }
    return mime_types.get(extension, 'application/octet-stream')


def upload_file(service, local_path: Path, folder_id: str, update_existing: bool = True) -> Dict[str, Any]:
    """
    Upload a file to Google Drive.
    
    Args:
        service: Drive API service
        local_path: Path to local file
        folder_id: ID of target folder in Drive
        update_existing: If True, update existing file instead of creating duplicate
        
    Returns:
        Dict with file info (id, name, webViewLink)
    """
    if not local_path.exists():
        raise FileNotFoundError(f"File not found: {local_path}")
    
    file_name = local_path.name
    mime_type = get_mime_type(local_path)
    
    # Check if file already exists
    query = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    existing_files = results.get('files', [])
    
    media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)
    
    if existing_files and update_existing:
        # Update existing file
        file_id = existing_files[0]['id']
        file = service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id, name, webViewLink, modifiedTime'
        ).execute()
        action = "Updated"
    else:
        # Create new file
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, modifiedTime'
        ).execute()
        action = "Uploaded"
    
    print(f"  ☁️  {action}: {file_name}")
    return file


def download_file(service, file_id: str, output_path: Path) -> Path:
    """Download a file from Google Drive."""
    request = service.files().get_media(fileId=file_id)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    with open(output_path, 'wb') as f:
        fh.seek(0)
        f.write(fh.read())
    
    print(f"  ⬇️  Downloaded: {output_path.name}")
    return output_path


def list_files_in_folder(service, folder_id: str, file_type: str = None) -> List[Dict[str, Any]]:
    """List files in a Drive folder."""
    query = f"'{folder_id}' in parents and trashed = false"
    if file_type:
        query += f" and mimeType = '{file_type}'"
    
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, mimeType, size, modifiedTime, webViewLink)',
        orderBy='modifiedTime desc'
    ).execute()
    
    return results.get('files', [])


def sync_directory(service, local_dir: Path, folder_id: str, extensions: List[str] = None) -> int:
    """
    Sync a local directory to a Drive folder.
    
    Args:
        service: Drive API service
        local_dir: Local directory path
        folder_id: Target Drive folder ID
        extensions: List of file extensions to sync (e.g., ['.html', '.txt'])
        
    Returns:
        Number of files synced
    """
    if not local_dir.exists():
        return 0
    
    count = 0
    for file_path in local_dir.iterdir():
        if file_path.is_file():
            if extensions and file_path.suffix.lower() not in extensions:
                continue
            try:
                upload_file(service, file_path, folder_id)
                count += 1
            except Exception as e:
                print(f"  ⚠️  Failed to upload {file_path.name}: {e}")
    
    return count


def sync_all(service = None) -> Dict[str, int]:
    """
    Sync all local proposal files to Google Drive.
    
    Returns dict with sync counts per folder.
    """
    if service is None:
        service = get_drive_service()
    
    folder_ids = ensure_folder_structure(service)
    
    results = {}
    
    # Sync transcripts
    print("\n📄 Syncing transcripts...")
    results['transcripts'] = sync_directory(
        service, TRANSCRIPTS_DIR, folder_ids['transcripts'],
        extensions=['.txt', '.json']
    )
    
    # Sync proposals
    print("\n📑 Syncing proposals...")
    results['proposals'] = sync_directory(
        service, PROPOSALS_DIR, folder_ids['proposals'],
        extensions=['.html']
    )
    
    # Sync deployment info
    print("\n🚀 Syncing deployment data...")
    last_url_file = TMP_DIR / 'last_deployment_url.txt'
    if last_url_file.exists():
        upload_file(service, last_url_file, folder_ids['deployments'])
        results['deployments'] = 1
    else:
        results['deployments'] = 0
    
    return results


def upload_single_file(file_path: Path, folder_type: str = "proposals") -> Dict[str, Any]:
    """
    Upload a single file to the appropriate Drive folder.
    
    Args:
        file_path: Path to the file
        folder_type: One of 'transcripts', 'proposals', 'deployments', 'exports'
        
    Returns:
        Dict with file info including webViewLink
    """
    service = get_drive_service()
    folder_ids = ensure_folder_structure(service)
    
    if folder_type not in folder_ids:
        folder_type = "exports"
    
    return upload_file(service, file_path, folder_ids[folder_type])


# =============================================================================
# CLI
# =============================================================================

@click.command()
@click.option('--action', type=click.Choice(['upload', 'sync', 'list', 'download']), 
              required=True, help='Action to perform')
@click.option('--file', 'file_path', type=click.Path(), help='Local file path for upload')
@click.option('--folder', type=click.Choice(['transcripts', 'proposals', 'deployments', 'exports']),
              default='proposals', help='Target folder in Drive')
@click.option('--file-id', help='Google Drive file ID for download')
@click.option('--output', type=click.Path(), help='Output path for download')
def main(action: str, file_path: Optional[str], folder: str, file_id: Optional[str], output: Optional[str]):
    """Google Drive storage manager for InstantProd proposals."""
    
    try:
        service = get_drive_service()
        folder_ids = ensure_folder_structure(service)
        
        if action == 'upload':
            if not file_path:
                print("[ERROR] --file is required for upload")
                return 1
            
            path = Path(file_path)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            
            result = upload_file(service, path, folder_ids[folder])
            print(f"\n✅ Uploaded successfully!")
            print(f"   View: {result.get('webViewLink', 'N/A')}")
            
        elif action == 'sync':
            print("🔄 Starting full sync to Google Drive...")
            results = sync_all(service)
            
            print("\n" + "=" * 50)
            print("✅ Sync Complete!")
            print("=" * 50)
            for folder_name, count in results.items():
                print(f"   {folder_name}: {count} files")
            
        elif action == 'list':
            print(f"\n📂 Files in {folder}:")
            files = list_files_in_folder(service, folder_ids[folder])
            
            if not files:
                print("   (empty)")
            else:
                for f in files:
                    size = int(f.get('size', 0)) / 1024
                    print(f"   • {f['name']} ({size:.1f} KB)")
                    print(f"     ID: {f['id']}")
            
        elif action == 'download':
            target_id = file_id
            
            # If file_id looks like a filename, try to find it
            if file_id and '.' in file_id:
                 print(f"Searching for file '{file_id}' in Drive...")
                 found_files = []
                 # Search in all known folders
                 for f_id in folder_ids.values():
                     q = f"'{f_id}' in parents and name = '{file_id}' and trashed = false"
                     res = service.files().list(q=q, fields="files(id, name)").execute()
                     found_files.extend(res.get('files', []))
                 
                 if found_files:
                     target_id = found_files[0]['id']
                     print(f"✅ Found file: {target_id}")
                 else:
                     print(f"[ERROR] Could not find file named '{file_id}' in Drive.")
                     return 1

            if not target_id or not output:
                print("[ERROR] --file-id (or filename) and --output are required for download")
                return 1
            
            output_path = Path(output)
            if not output_path.is_absolute():
                output_path = PROJECT_ROOT / output_path
            
            # Ensure parent dir exists (important for Vercel /tmp)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            download_file(service, target_id, output_path)
            print(f"\n✅ Downloaded to: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
