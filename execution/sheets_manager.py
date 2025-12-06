#!/usr/bin/env python3
"""
Google Sheets Integration for InstantProd Proposals.

Usage:
    # Read all data
    python execution/sheets_manager.py --action read
    
    # Add a new client
    python execution/sheets_manager.py --action add --data '{"name": "Acme Corp", "email": "client@acme.com"}'
    
    # Update a row
    python execution/sheets_manager.py --action update --row 2 --data '{"status": "Proposal Sent"}'
    
    # Find a client
    python execution/sheets_manager.py --action find --query "Acme"
"""

import os
import sys
import json
import click
from pathlib import Path
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / 'credentials.json'
TOKEN_FILE = PROJECT_ROOT / 'token.json'

# Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Your sheet ID (extracted from URL)
SHEET_ID = '1ZVww3zCFkyLtlj7jcUXbuh6MK0CoRViU23FegPTHOIU'


def get_sheets_service():
    """Authenticate and return Google Sheets service."""
    creds = None
    
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('sheets', 'v4', credentials=creds)


def read_sheet(service, range_name='Sheet1!A:Z'):
    """Read data from the sheet."""
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=range_name
    ).execute()
    
    values = result.get('values', [])
    
    if not values:
        return []
    
    # First row is headers
    headers = values[0]
    rows = []
    
    for row in values[1:]:
        # Pad row to match header length
        while len(row) < len(headers):
            row.append('')
        
        row_dict = dict(zip(headers, row))
        rows.append(row_dict)
    
    return rows


def append_row(service, values, range_name='Sheet1!A:A'):
    """Append a new row to the sheet."""
    body = {
        'values': [values]
    }
    
    result = service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()
    
    return result


def update_row(service, row_index, values, range_name='Sheet1'):
    """Update a specific row (1-indexed, including header)."""
    cell_range = f'{range_name}!A{row_index}:Z{row_index}'
    
    body = {
        'values': [values]
    }
    
    result = service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=cell_range,
        valueInputOption='RAW',
        body=body
    ).execute()
    
    return result


def find_rows(service, query, column_index=0):
    """Find rows containing a query string in a specific column."""
    data = read_sheet(service)
    
    if not data:
        return []
    
    headers = list(data[0].keys())
    column_name = headers[column_index] if column_index < len(headers) else headers[0]
    
    matches = []
    for i, row in enumerate(data):
        if query.lower() in str(row.get(column_name, '')).lower():
            matches.append({
                'row_number': i + 2,  # +2 because: 1 for header, 1 for 1-indexing
                'data': row
            })
    
    return matches


@click.command()
@click.option('--action', type=click.Choice(['read', 'add', 'update', 'find']), required=True,
              help='Action to perform')
@click.option('--data', help='JSON data for add/update actions')
@click.option('--row', type=int, help='Row number for update action (1-indexed)')
@click.option('--query', help='Search query for find action')
@click.option('--range', default='Sheet1!A:Z', help='Sheet range (default: Sheet1!A:Z)')
def main(action, data, row, query, range):
    """Manage Google Sheets data."""
    
    print(f"[...] Connecting to Google Sheets...")
    service = get_sheets_service()
    print(f"[OK] Connected to sheet: {SHEET_ID}")
    
    if action == 'read':
        rows = read_sheet(service, range)
        print(f"\n[OK] Found {len(rows)} rows:\n")
        print(json.dumps(rows, indent=2))
    
    elif action == 'add':
        if not data:
            print("[ERROR] --data required for add action")
            return 1
        
        data_dict = json.loads(data)
        
        # Get headers to know column order
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range='Sheet1!1:1'
        ).execute()
        
        headers = result.get('values', [[]])[0]
        
        # Build row in header order
        values = [data_dict.get(h, '') for h in headers]
        
        result = append_row(service, values)
        print(f"[OK] Added row: {result.get('updates', {}).get('updatedRange')}")
    
    elif action == 'update':
        if not row or not data:
            print("[ERROR] --row and --data required for update action")
            return 1
        
        data_dict = json.loads(data)
        
        # Get current row
        current_range = f'Sheet1!A{row}:Z{row}'
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=current_range
        ).execute()
        
        current_values = result.get('values', [[]])[0]
        
        # Get headers
        headers_result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range='Sheet1!1:1'
        ).execute()
        
        headers = headers_result.get('values', [[]])[0]
        
        # Update specific columns
        for key, value in data_dict.items():
            if key in headers:
                col_index = headers.index(key)
                while len(current_values) <= col_index:
                    current_values.append('')
                current_values[col_index] = value
        
        update_row(service, row, current_values)
        print(f"[OK] Updated row {row}")
    
    elif action == 'find':
        if not query:
            print("[ERROR] --query required for find action")
            return 1
        
        matches = find_rows(service, query)
        print(f"\n[OK] Found {len(matches)} matches:\n")
        print(json.dumps(matches, indent=2))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
