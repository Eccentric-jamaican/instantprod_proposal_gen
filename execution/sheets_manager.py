#!/usr/bin/env python3
"""
Enhanced Google Sheets Integration for InstantProd Proposals.

Supports complex operations including:
- Batch updates
- Cell-level operations
- Formula support
- Advanced filtering
- Multiple sheets
- Conditional formatting
- Metadata operations

Usage:
    # Read all data from onboarding sheet
    python execution/sheets_manager.py --action read --sheet-name "Onboarding"
    
    # Read specific range
    python execution/sheets_manager.py --action read --range "Onboarding!A1:D10"
    
    # Add a new row
    python execution/sheets_manager.py --action add --data '{"name": "Acme Corp", "email": "client@acme.com"}'
    
    # Update specific cells
    python execution/sheets_manager.py --action update-cell --cell "B5" --value "New Value"
    
    # Batch update multiple cells
    python execution/sheets_manager.py --action batch-update --updates '{"B5": "Value1", "C5": "Value2"}'
    
    # Update row by matching criteria
    python execution/sheets_manager.py --action update-by-match --match-column "email" --match-value "client@acme.com" --data '{"status": "Active"}'
    
    # Find with advanced filtering
    python execution/sheets_manager.py --action find --query "Acme" --column "name"
    
    # Get sheet metadata
    python execution/sheets_manager.py --action metadata
    
    # List all sheets
    python execution/sheets_manager.py --action list-sheets
"""

import os
import sys
import json
import click
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import auth_helper
    CREDENTIALS_FILE, TOKEN_FILE = auth_helper.restore_credentials()
except ImportError:
    CREDENTIALS_FILE = PROJECT_ROOT / 'credentials.json'
    TOKEN_FILE = PROJECT_ROOT / 'token.json'

# Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Sheet ID - can be overridden via environment variable
DEFAULT_SHEET_ID = '1ZVww3zCFkyLtlj7jcUXbuh6MK0CoRViU23FegPTHOIU'
ONBOARDING_SHEET_ID = os.getenv('ONBOARDING_SHEET_ID', DEFAULT_SHEET_ID)


def get_sheets_service():
    """Authenticate and return Google Sheets service."""
    creds = None
    
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(f"credentials.json not found at: {CREDENTIALS_FILE}")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build('sheets', 'v4', credentials=creds)


def get_sheet_id(sheet_name: Optional[str] = None) -> str:
    """Get the appropriate sheet ID based on sheet name or default."""
    # If specific sheet name mapping needed, add here
    # For now, use the onboarding sheet ID
    return ONBOARDING_SHEET_ID


def get_sheet_name_from_range(range_name: str) -> str:
    """Extract sheet name from range notation (e.g., 'Sheet1!A1' -> 'Sheet1')."""
    if '!' in range_name:
        return range_name.split('!')[0]
    return 'Sheet1'


def read_sheet(service, sheet_id: str, range_name: str = None, sheet_name: str = 'Sheet1') -> List[Dict[str, Any]]:
    """Read data from the sheet and return as list of dictionaries."""
    if range_name:
        # If range includes sheet name, use it
        if '!' in range_name:
            full_range = range_name
        else:
            full_range = f"{sheet_name}!{range_name}"
    else:
        full_range = f"{sheet_name}!A:Z"
    
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=full_range
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
    except HttpError as e:
        print(f"[ERROR] Failed to read sheet: {e}")
        return []


def read_raw_values(service, sheet_id: str, range_name: str) -> List[List[Any]]:
    """Read raw values from sheet (no header processing)."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        return result.get('values', [])
    except HttpError as e:
        print(f"[ERROR] Failed to read values: {e}")
        return []


def append_row(service, sheet_id: str, values: List[Any], sheet_name: str = 'Sheet1', range_name: str = None):
    """Append a new row to the sheet."""
    if range_name:
        full_range = range_name
    else:
        full_range = f"{sheet_name}!A:A"
    
    body = {
        'values': [values]
    }
    
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=full_range,
            valueInputOption='USER_ENTERED',  # Allows formulas
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        return result
    except HttpError as e:
        print(f"[ERROR] Failed to append row: {e}")
        return None


def update_row(service, sheet_id: str, row_index: int, values: List[Any], sheet_name: str = 'Sheet1'):
    """Update a specific row (1-indexed, including header)."""
    cell_range = f'{sheet_name}!A{row_index}:Z{row_index}'
    
    body = {
        'values': [values]
    }
    
    try:
        result = service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=cell_range,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        return result
    except HttpError as e:
        print(f"[ERROR] Failed to update row: {e}")
        return None


def update_cell(service, sheet_id: str, cell: str, value: Any, sheet_name: str = 'Sheet1', use_formula: bool = False):
    """Update a single cell. Cell can be 'A1' or 'Sheet1!A1' format."""
    if '!' in cell:
        full_range = cell
    else:
        full_range = f"{sheet_name}!{cell}"
    
    # If value starts with '=', treat as formula
    if isinstance(value, str) and value.startswith('='):
        use_formula = True
    
    body = {
        'values': [[value]]
    }
    
    try:
        result = service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=full_range,
            valueInputOption='USER_ENTERED' if use_formula else 'RAW',
            body=body
        ).execute()
        return result
    except HttpError as e:
        print(f"[ERROR] Failed to update cell: {e}")
        return None


def batch_update_cells(service, sheet_id: str, updates: Dict[str, Any], sheet_name: str = 'Sheet1'):
    """Batch update multiple cells. Updates is dict of {'A1': value, 'B2': value}."""
    data = []
    
    for cell, value in updates.items():
        if '!' in cell:
            full_range = cell
        else:
            full_range = f"{sheet_name}!{cell}"
        
        # Check if value is a formula
        use_formula = isinstance(value, str) and value.startswith('=')
        
        data.append({
            'range': full_range,
            'values': [[value]]
        })
    
    body = {
        'valueInputOption': 'USER_ENTERED',
        'data': data
    }
    
    try:
        result = service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()
        return result
    except HttpError as e:
        print(f"[ERROR] Failed to batch update: {e}")
        return None


def get_headers(service, sheet_id: str, sheet_name: str = 'Sheet1') -> List[str]:
    """Get column headers without reading entire sheet (privacy-conscious)."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f'{sheet_name}!A1:Z1'
        ).execute()
        values = result.get('values', [[]])
        if values and len(values) > 0:
            return values[0]
        return []
    except HttpError as e:
        print(f"[ERROR] Failed to get headers: {e}")
        return []


def get_row_count(service, sheet_id: str, sheet_name: str = 'Sheet1') -> int:
    """Get approximate row count without reading data (privacy-conscious)."""
    try:
        # Get metadata which includes row count
        result = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        for sheet in result.get('sheets', []):
            if sheet.get('properties', {}).get('title') == sheet_name:
                return sheet.get('properties', {}).get('gridProperties', {}).get('rowCount', 0)
        return 0
    except HttpError as e:
        print(f"[ERROR] Failed to get row count: {e}")
        return 0


def query_specific_range(service, sheet_id: str, range_name: str) -> List[List[Any]]:
    """Query a specific range without reading entire sheet (privacy-conscious)."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        return result.get('values', [])
    except HttpError as e:
        print(f"[ERROR] Failed to query range: {e}")
        return []


def find_rows(service, sheet_id: str, query: str, column: Optional[str] = None, sheet_name: str = 'Sheet1', exact_match: bool = False, limit_rows: Optional[int] = None):
    """Find rows containing a query string. Can limit rows read for privacy."""
    # If column is specified, we can be more efficient
    if column:
        headers = get_headers(service, sheet_id, sheet_name)
        if column not in headers:
            return []
        
        col_index = headers.index(column)
        # Convert column index to letter (A=0, B=1, ..., Z=25, AA=26, etc.)
        if col_index < 26:
            col_letter = chr(65 + col_index)
        else:
            first_letter = chr(65 + (col_index // 26) - 1)
            second_letter = chr(65 + (col_index % 26))
            col_letter = first_letter + second_letter
        
        # Read only the specific column (more privacy-conscious)
        col_range = f'{sheet_name}!{col_letter}:{col_letter}'
        col_values = query_specific_range(service, sheet_id, col_range)
        
        # Find matching rows
        matches = []
        query_lower = query.lower()
        
        for i, row in enumerate(col_values[1:], start=2):  # Skip header
            if not row:
                continue
            cell_value = str(row[0] if row else '').lower()
            
            if exact_match:
                match_found = cell_value == query_lower
            else:
                match_found = query_lower in cell_value
            
            if match_found:
                # Only read the specific row that matches
                row_range = f'{sheet_name}!A{i}:Z{i}'
                row_data = query_specific_range(service, sheet_id, row_range)
                if row_data:
                    headers = get_headers(service, sheet_id, sheet_name)
                    row_values = row_data[0]
                    while len(row_values) < len(headers):
                        row_values.append('')
                    row_dict = dict(zip(headers, row_values))
                    matches.append({
                        'row_number': i,
                        'data': row_dict
                    })
                    
                    if limit_rows and len(matches) >= limit_rows:
                        break
        
        return matches
    
    # Fallback: read all data if column not specified (less efficient)
    data = read_sheet(service, sheet_id, sheet_name=sheet_name)
    
    if not data:
        return []
    
    matches = []
    query_lower = query.lower()
    
    for i, row in enumerate(data):
        match_found = False
        
        # Search in all columns
        for value in row.values():
            cell_value = str(value).lower()
            if exact_match:
                if cell_value == query_lower:
                    match_found = True
                    break
            else:
                if query_lower in cell_value:
                    match_found = True
                    break
        
        if match_found:
            matches.append({
                'row_number': i + 2,  # +2 because: 1 for header, 1 for 1-indexing
                'data': row
            })
            
            if limit_rows and len(matches) >= limit_rows:
                break
    
    return matches


def update_by_match(service, sheet_id: str, match_column: str, match_value: str, updates: Dict[str, Any], sheet_name: str = 'Sheet1'):
    """Update rows that match a specific column value."""
    matches = find_rows(service, sheet_id, match_value, column=match_column, sheet_name=sheet_name, exact_match=True)
    
    if not matches:
        return {'updated': 0, 'message': 'No matching rows found'}
    
    # Get headers to know column order
    headers_result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f'{sheet_name}!1:1'
    ).execute()
    
    headers = headers_result.get('values', [[]])[0]
    
    updated_count = 0
    for match in matches:
        row_num = match['row_number']
        
        # Get current row
        current_range = f'{sheet_name}!A{row_num}:Z{row_num}'
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=current_range
        ).execute()
        
        current_values = result.get('values', [[]])[0]
        
        # Update specific columns
        for key, value in updates.items():
            if key in headers:
                col_index = headers.index(key)
                while len(current_values) <= col_index:
                    current_values.append('')
                current_values[col_index] = value
        
        update_row(service, sheet_id, row_num, current_values, sheet_name)
        updated_count += 1
    
    return {'updated': updated_count, 'message': f'Updated {updated_count} row(s)'}


def get_sheet_metadata(service, sheet_id: str):
    """Get metadata about the spreadsheet (sheets, properties, etc.)."""
    try:
        result = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        return {
            'title': result.get('properties', {}).get('title', ''),
            'sheets': [
                {
                    'id': sheet.get('properties', {}).get('sheetId'),
                    'title': sheet.get('properties', {}).get('title'),
                    'rowCount': sheet.get('properties', {}).get('gridProperties', {}).get('rowCount'),
                    'columnCount': sheet.get('properties', {}).get('gridProperties', {}).get('columnCount'),
                }
                for sheet in result.get('sheets', [])
            ]
        }
    except HttpError as e:
        print(f"[ERROR] Failed to get metadata: {e}")
        return None


def list_sheets(service, sheet_id: str):
    """List all sheets in the spreadsheet."""
    metadata = get_sheet_metadata(service, sheet_id)
    if metadata:
        return metadata.get('sheets', [])
    return []


def delete_column(service, sheet_id: str, column_index: int, sheet_name: str = 'Sheet1'):
    """Delete a column by index (0-based, where A=0, B=1, etc.)."""
    try:
        # Get sheet ID (not the spreadsheet ID, but the sheet's internal ID)
        metadata = get_sheet_metadata(service, sheet_id)
        sheet_id_internal = None
        for sheet in metadata.get('sheets', []):
            if sheet.get('title') == sheet_name:
                sheet_id_internal = sheet.get('id')
                break
        
        if sheet_id_internal is None:
            print(f"[ERROR] Sheet '{sheet_name}' not found")
            return None
        
        # Delete the column using batchUpdate
        body = {
            'requests': [{
                'deleteDimension': {
                    'range': {
                        'sheetId': sheet_id_internal,
                        'dimension': 'COLUMNS',
                        'startIndex': column_index,
                        'endIndex': column_index + 1
                    }
                }
            }]
        }
        
        result = service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()
        
        return result
    except HttpError as e:
        print(f"[ERROR] Failed to delete column: {e}")
        return None


def delete_column_by_name(service, sheet_id: str, column_name: str, sheet_name: str = 'Sheet1'):
    """Delete a column by its header name."""
    headers = get_headers(service, sheet_id, sheet_name)
    if column_name not in headers:
        print(f"[ERROR] Column '{column_name}' not found in headers")
        return None
    
    column_index = headers.index(column_name)
    return delete_column(service, sheet_id, column_index, sheet_name)


def rename_column(service, sheet_id: str, old_name: str, new_name: str, sheet_name: str = 'Sheet1'):
    """Rename a column header."""
    headers = get_headers(service, sheet_id, sheet_name)
    if old_name not in headers:
        print(f"[ERROR] Column '{old_name}' not found in headers")
        return None
    
    column_index = headers.index(old_name)
    # Convert column index to letter (A=0, B=1, etc.)
    if column_index < 26:
        col_letter = chr(65 + column_index)
    else:
        first_letter = chr(65 + (column_index // 26) - 1)
        second_letter = chr(65 + (column_index % 26))
        col_letter = first_letter + second_letter
    
    # Update the header cell
    cell_range = f'{sheet_name}!{col_letter}1'
    return update_cell(service, sheet_id, cell_range, new_name, sheet_name='', use_formula=False)


def get_headers_only(service, sheet_id: str, sheet_name: str = 'Sheet1') -> Dict[str, Any]:
    """Get only column headers without reading data (privacy-conscious)."""
    headers = get_headers(service, sheet_id, sheet_name)
    row_count = get_row_count(service, sheet_id, sheet_name)
    return {
        'sheet_name': sheet_name,
        'headers': headers,
        'row_count': row_count,
        'column_count': len(headers)
    }


def query_by_column_value(service, sheet_id: str, column: str, value: str, sheet_name: str = 'Sheet1', return_columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Query specific rows by column value, return only specified columns (privacy-conscious)."""
    headers = get_headers(service, sheet_id, sheet_name)
    if column not in headers:
        return []
    
    col_index = headers.index(column)
    col_letter = chr(65 + col_index) if col_index < 26 else f"A{chr(65 + (col_index - 26))}"
    
    # Read only the specific column
    col_range = f'{sheet_name}!{col_letter}:{col_letter}'
    col_values = query_specific_range(service, sheet_id, col_range)
    
    matches = []
    value_lower = value.lower()
    
    for i, row in enumerate(col_values[1:], start=2):  # Skip header
        if not row:
            continue
        cell_value = str(row[0] if row else '').lower()
        
        if cell_value == value_lower:
            # Determine which columns to return
            if return_columns:
                # Build range for specific columns only
                col_indices = []
                for ret_col in return_columns:
                    if ret_col in headers:
                        col_indices.append(headers.index(ret_col))
                
                if col_indices:
                    def index_to_letter(idx):
                        if idx < 26:
                            return chr(65 + idx)
                        else:
                            first = chr(65 + (idx // 26) - 1)
                            second = chr(65 + (idx % 26))
                            return first + second
                    start_col = index_to_letter(min(col_indices))
                    end_col = index_to_letter(max(col_indices))
                    row_range = f'{sheet_name}!{start_col}{i}:{end_col}{i}'
                else:
                    row_range = f'{sheet_name}!A{i}:Z{i}'
            else:
                row_range = f'{sheet_name}!A{i}:Z{i}'
            
            row_data = query_specific_range(service, sheet_id, row_range)
            if row_data:
                row_values = row_data[0]
                if return_columns:
                    # Filter to only requested columns
                    row_dict = {}
                    for ret_col in return_columns:
                        if ret_col in headers:
                            col_idx = headers.index(ret_col)
                            row_dict[ret_col] = row_values[col_idx] if col_idx < len(row_values) else ''
                else:
                    # Return all columns
                    while len(row_values) < len(headers):
                        row_values.append('')
                    row_dict = dict(zip(headers, row_values))
                
                matches.append({
                    'row_number': i,
                    'data': row_dict
                })
    
    return matches


@click.command()
@click.option('--action', type=click.Choice([
    'read', 'add', 'update', 'update-cell', 'batch-update', 
    'update-by-match', 'find', 'metadata', 'list-sheets',
    'get-headers', 'query-range', 'query-by-column',
    'delete-column', 'rename-column'
]), required=True, help='Action to perform')
@click.option('--sheet-id', help='Sheet ID (overrides default/ONBOARDING_SHEET_ID)')
@click.option('--sheet-name', default='Sheet1', help='Sheet name within spreadsheet')
@click.option('--data', help='JSON data for add/update actions')
@click.option('--row', type=int, help='Row number for update action (1-indexed)')
@click.option('--cell', help='Cell reference (e.g., "A1" or "Sheet1!A1")')
@click.option('--value', help='Value to set for cell update')
@click.option('--updates', help='JSON dict of cell:value pairs for batch-update')
@click.option('--query', help='Search query for find action')
@click.option('--column', help='Column name to search in (for find)')
@click.option('--range', help='Sheet range (e.g., "A1:D10" or "Sheet1!A1:D10")')
@click.option('--match-column', help='Column name to match for update-by-match')
@click.option('--match-value', help='Value to match for update-by-match')
@click.option('--exact-match', is_flag=True, help='Use exact match for find')
@click.option('--use-formula', is_flag=True, help='Treat value as formula')
@click.option('--limit-rows', type=int, help='Limit number of rows to read (privacy-conscious)')
@click.option('--return-columns', help='Comma-separated list of columns to return (for query-by-column)')
@click.option('--new-name', help='New column name for rename-column action')
def main(action, sheet_id, sheet_name, data, row, cell, value, updates, query, column, range, 
         match_column, match_value, exact_match, use_formula, limit_rows, return_columns, new_name):
    """Enhanced Google Sheets management with complex operations."""
    
    # Determine which sheet ID to use
    target_sheet_id = sheet_id or get_sheet_id(sheet_name)
    
    print(f"[...] Connecting to Google Sheets...")
    service = get_sheets_service()
    print(f"[OK] Connected to sheet: {target_sheet_id}")

    if action not in {'metadata', 'list-sheets'}:
        if range and '!' in range:
            sheet_name = get_sheet_name_from_range(range)
        else:
            sheets = list_sheets(service, target_sheet_id)
            sheet_titles = [s.get('title') for s in sheets if s.get('title')]
            if sheet_titles and (not sheet_name or sheet_name == 'Sheet1'):
                sheet_name = sheet_titles[0]
    
    if action == 'read':
        rows = read_sheet(service, target_sheet_id, range_name=range, sheet_name=sheet_name)
        print(f"\n[OK] Found {len(rows)} rows:\n")
        print(json.dumps(rows, indent=2, default=str))
    
    elif action == 'add':
        if not data:
            print("[ERROR] --data required for add action")
            return 1
        
        data_dict = json.loads(data)
        
        # Get headers to know column order
        headers_result = service.spreadsheets().values().get(
            spreadsheetId=target_sheet_id,
            range=f'{sheet_name}!1:1'
        ).execute()
        
        headers = headers_result.get('values', [[]])[0]
        
        # Build row in header order
        values = [data_dict.get(h, '') for h in headers]
        
        result = append_row(service, target_sheet_id, values, sheet_name)
        if result:
            print(f"[OK] Added row: {result.get('updates', {}).get('updatedRange')}")
        else:
            return 1
    
    elif action == 'update':
        if not row or not data:
            print("[ERROR] --row and --data required for update action")
            return 1
        
        data_dict = json.loads(data)
        
        # Get current row
        current_range = f'{sheet_name}!A{row}:Z{row}'
        result = service.spreadsheets().values().get(
            spreadsheetId=target_sheet_id,
            range=current_range
        ).execute()
        
        current_values = result.get('values', [[]])[0]
        
        # Get headers
        headers_result = service.spreadsheets().values().get(
            spreadsheetId=target_sheet_id,
            range=f'{sheet_name}!1:1'
        ).execute()
        
        headers = headers_result.get('values', [[]])[0]
        
        # Update specific columns
        for key, value in data_dict.items():
            if key in headers:
                col_index = headers.index(key)
                while len(current_values) <= col_index:
                    current_values.append('')
                current_values[col_index] = value
        
        result = update_row(service, target_sheet_id, row, current_values, sheet_name)
        if result:
            print(f"[OK] Updated row {row}")
        else:
            return 1
    
    elif action == 'update-cell':
        if not cell or value is None:
            print("[ERROR] --cell and --value required for update-cell action")
            return 1
        
        result = update_cell(service, target_sheet_id, cell, value, sheet_name, use_formula)
        if result:
            print(f"[OK] Updated cell {cell}")
        else:
            return 1
    
    elif action == 'batch-update':
        if not updates:
            print("[ERROR] --updates required for batch-update action")
            return 1
        
        updates_dict = json.loads(updates)
        result = batch_update_cells(service, target_sheet_id, updates_dict, sheet_name)
        if result:
            updated = result.get('responses', [])
            print(f"[OK] Batch updated {len(updated)} cell(s)")
        else:
            return 1
    
    elif action == 'update-by-match':
        if not match_column or not match_value or not data:
            print("[ERROR] --match-column, --match-value, and --data required for update-by-match")
            return 1
        
        updates_dict = json.loads(data)
        result = update_by_match(service, target_sheet_id, match_column, match_value, updates_dict, sheet_name)
        print(f"[OK] {result['message']}")
    
    elif action == 'find':
        if not query:
            print("[ERROR] --query required for find action")
            return 1
        
        matches = find_rows(service, target_sheet_id, query, column=column, sheet_name=sheet_name, exact_match=exact_match, limit_rows=limit_rows)
        print(f"\n[OK] Found {len(matches)} matches:\n")
        print(json.dumps(matches, indent=2, default=str))
    
    elif action == 'get-headers':
        headers_info = get_headers_only(service, target_sheet_id, sheet_name)
        print("\n[OK] Sheet Structure:\n")
        print(json.dumps(headers_info, indent=2, default=str))
    
    elif action == 'query-range':
        if not range:
            print("[ERROR] --range required for query-range action")
            return 1
        
        values = query_specific_range(service, target_sheet_id, range)
        print(f"\n[OK] Query Results ({len(values)} rows):\n")
        print(json.dumps(values, indent=2, default=str))
    
    elif action == 'query-by-column':
        if not column or not query:
            print("[ERROR] --column and --query required for query-by-column action")
            return 1
        
        return_cols = return_columns.split(',') if return_columns else None
        if return_cols:
            return_cols = [col.strip() for col in return_cols]
        
        matches = query_by_column_value(service, target_sheet_id, column, query, sheet_name, return_cols)
        print(f"\n[OK] Found {len(matches)} matches:\n")
        print(json.dumps(matches, indent=2, default=str))
    
    elif action == 'metadata':
        metadata = get_sheet_metadata(service, target_sheet_id)
        if metadata:
            print("\n[OK] Sheet Metadata:\n")
            print(json.dumps(metadata, indent=2, default=str))
        else:
            return 1
    
    elif action == 'list-sheets':
        sheets = list_sheets(service, target_sheet_id)
        print(f"\n[OK] Found {len(sheets)} sheet(s):\n")
        print(json.dumps(sheets, indent=2, default=str))
    
    elif action == 'delete-column':
        if not column:
            print("[ERROR] --column required for delete-column action")
            return 1
        
        result = delete_column_by_name(service, target_sheet_id, column, sheet_name)
        if result:
            print(f"[OK] Deleted column '{column}' from sheet '{sheet_name}'")
        else:
            return 1
    
    elif action == 'rename-column':
        if not column or not new_name:
            print("[ERROR] --column and --new-name required for rename-column action")
            return 1
        
        result = rename_column(service, target_sheet_id, column, new_name, sheet_name)
        if result:
            print(f"[OK] Renamed column '{column}' to '{new_name}' in sheet '{sheet_name}'")
        else:
            return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
