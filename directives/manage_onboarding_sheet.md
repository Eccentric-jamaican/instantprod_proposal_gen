# Manage Onboarding Google Sheet

## Goal
Read from and write to the onboarding Google Sheet to track client progress, update statuses, add new entries, and query existing data.

**Privacy-Conscious Approach**: This system uses OAuth authentication and supports targeted queries that only read the specific data needed, avoiding exposing entire sheet contents in context.

## Inputs
- **Sheet ID**: Can be set via `ONBOARDING_SHEET_ID` environment variable, or passed via `--sheet-id` flag
- **Sheet Name**: Name of the specific sheet/tab within the spreadsheet (default: "Sheet1")
- **Action**: What operation to perform (read, add, update, find, etc.)
- **Data**: JSON data for add/update operations
- **Query Parameters**: For finding and filtering rows

## Tools/Scripts to Use
- `execution/sheets_manager.py` - Enhanced Google Sheets manager with complex operations

## Available Actions

### 1. Get Sheet Structure (Privacy-Conscious)
Get column headers and row count without reading any data.

```bash
# Get headers and structure info only
python execution/sheets_manager.py --action get-headers --sheet-name "Onboarding"

# With custom sheet ID
python execution/sheets_manager.py --action get-headers --sheet-id "YOUR_SHEET_ID" --sheet-name "Onboarding"
```

**Output**: JSON with headers, row count, and column count (no actual data)

### 2. Query Specific Range (Privacy-Conscious)
Read only a specific range of cells.

```bash
# Query specific range (e.g., first 10 rows, columns A-D)
python execution/sheets_manager.py --action query-range --range "Onboarding!A1:D10"

# Query with sheet name in range
python execution/sheets_manager.py --action query-range --range "Onboarding!A1:D10" --sheet-id "YOUR_SHEET_ID"
```

**Output**: Raw values from the specified range only

### 3. Query by Column Value (Privacy-Conscious)
Find rows matching a column value, return only specified columns.

```bash
# Find by email, return only name and status
python execution/sheets_manager.py --action query-by-column \
  --column "Email" \
  --query "client@acme.com" \
  --return-columns "Client Name,Status,Notes" \
  --sheet-name "Onboarding"

# Find by name, return all columns
python execution/sheets_manager.py --action query-by-column \
  --column "Client Name" \
  --query "Acme Corp" \
  --sheet-name "Onboarding"
```

**Output**: Only matching rows with requested columns (privacy-conscious)

### 4. Read Data (Full Read)
Read all or specific ranges from the sheet. **Use sparingly for large sheets.**

```bash
# Read entire sheet (use with caution - reads all data)
python execution/sheets_manager.py --action read --sheet-name "Onboarding"

# Read specific range
python execution/sheets_manager.py --action read --range "Onboarding!A1:D10"

# Read with custom sheet ID
python execution/sheets_manager.py --action read --sheet-id "YOUR_SHEET_ID" --sheet-name "Onboarding"
```

**Output**: JSON array of rows as dictionaries (first row is headers, subsequent rows are data)

**Note**: For privacy, prefer `query-range` or `query-by-column` instead of full reads.

### 5. Add New Row
Add a new entry to the onboarding sheet.

```bash
python execution/sheets_manager.py --action add \
  --sheet-name "Onboarding" \
  --data '{"Client Name": "Acme Corp", "Email": "contact@acme.com", "Status": "New", "Date": "2025-01-15"}'
```

**Note**: Column names must match the headers in your sheet. The script automatically orders values based on header positions.

### 6. Update Row by Row Number
Update an existing row by its row number (1-indexed, including header).

```bash
python execution/sheets_manager.py --action update \
  --row 5 \
  --sheet-name "Onboarding" \
  --data '{"Status": "In Progress", "Notes": "Started onboarding process"}'
```

### 7. Update Single Cell
Update a specific cell directly.

```bash
# Update cell A5
python execution/sheets_manager.py --action update-cell \
  --cell "A5" \
  --value "New Value" \
  --sheet-name "Onboarding"

# Update with formula
python execution/sheets_manager.py --action update-cell \
  --cell "B5" \
  --value "=SUM(A1:A4)" \
  --use-formula \
  --sheet-name "Onboarding"
```

### 8. Batch Update Multiple Cells
Update multiple cells in a single operation (more efficient than multiple single updates).

```bash
python execution/sheets_manager.py --action batch-update \
  --sheet-name "Onboarding" \
  --updates '{"A5": "Value1", "B5": "Value2", "C5": "=SUM(A1:A4)"}'
```

### 9. Update by Matching Criteria
Find rows matching a specific column value and update them.

```bash
# Update all rows where email matches
python execution/sheets_manager.py --action update-by-match \
  --match-column "Email" \
  --match-value "client@acme.com" \
  --data '{"Status": "Completed", "Completion Date": "2025-01-20"}' \
  --sheet-name "Onboarding"
```

**Use Case**: Update status for a specific client without knowing their row number.

### 10. Find Rows (Privacy-Conscious with Limits)
Search for rows containing specific text.

```bash
# Search in all columns (with row limit for privacy)
python execution/sheets_manager.py --action find \
  --query "Acme" \
  --sheet-name "Onboarding" \
  --limit-rows 10

# Search in specific column (more privacy-conscious)
python execution/sheets_manager.py --action find \
  --query "client@acme.com" \
  --column "Email" \
  --exact-match \
  --sheet-name "Onboarding"
```

**Options**:
- `--column`: Search only in a specific column
- `--exact-match`: Require exact match (case-insensitive)

### 11. Get Sheet Metadata
Get information about the spreadsheet structure.

```bash
python execution/sheets_manager.py --action metadata --sheet-id "YOUR_SHEET_ID"
```

**Output**: Spreadsheet title, list of sheets with their properties (row count, column count, etc.)

### 12. List All Sheets
List all sheets/tabs in the spreadsheet.

```bash
python execution/sheets_manager.py --action list-sheets --sheet-id "YOUR_SHEET_ID"
```

## Privacy-Conscious Best Practices

1. **Use `get-headers` first** to see structure without reading data
2. **Use `query-range`** for specific ranges instead of full reads
3. **Use `query-by-column`** to find specific rows and return only needed columns
4. **Use `--limit-rows`** when using `find` to limit data exposure
5. **Use `--return-columns`** with `query-by-column` to return only relevant data
6. **Avoid full `read`** operations on large sheets unless necessary

## Common Workflows

### Workflow 1: Add New Client to Onboarding (Privacy-Conscious)
```bash
# Step 1: Get headers to see structure (no data read)
python execution/sheets_manager.py --action get-headers --sheet-name "Onboarding"

# Step 2: Add new client
python execution/sheets_manager.py --action add \
  --sheet-name "Onboarding" \
  --data '{
    "Client Name": "New Corp",
    "Email": "contact@newcorp.com",
    "Status": "New",
    "Date Added": "2025-01-15",
    "Notes": "Initial contact"
  }'
```

### Workflow 2: Update Client Status (Privacy-Conscious)
```bash
# Find the client first (only reads matching rows)
python execution/sheets_manager.py --action query-by-column \
  --column "Email" \
  --query "contact@newcorp.com" \
  --return-columns "Client Name,Status" \
  --sheet-name "Onboarding"

# Then update by matching email (no need to read full sheet)
python execution/sheets_manager.py --action update-by-match \
  --match-column "Email" \
  --match-value "contact@newcorp.com" \
  --data '{"Status": "In Progress", "Last Updated": "2025-01-16"}' \
  --sheet-name "Onboarding"
```

### Workflow 3: Bulk Status Update
```bash
# Update multiple cells at once
python execution/sheets_manager.py --action batch-update \
  --sheet-name "Onboarding" \
  --updates '{
    "E5": "Completed",
    "F5": "2025-01-20",
    "E6": "In Progress",
    "F6": "2025-01-20"
  }'
```

## Outputs
- **Read Operations**: JSON output to stdout (can be redirected to `.tmp/` for processing)
- **Write Operations**: Success messages with updated ranges
- **Find Operations**: JSON array of matching rows with row numbers

## OAuth Authentication

The system uses OAuth 2.0 authentication via `credentials.json`. This means:
- **No hardcoded sheet IDs needed** - You can access any sheet you have permission to
- **Dynamic sheet access** - Just pass `--sheet-id` for any sheet
- **Secure** - Credentials are stored locally and not exposed
- **Token refresh** - Automatically refreshes expired tokens

To authenticate for the first time:
```bash
python execution/test_google_auth.py
```

This will open a browser for OAuth consent. After that, `token.json` is saved and reused.

## Edge Cases & Learnings

### Column Names
- Column names are case-sensitive and must match exactly
- Use `--action read` first to see the exact column names
- Spaces in column names are preserved

### Row Numbers
- Row numbers are 1-indexed
- Row 1 is the header row
- Data starts at row 2

### Formulas
- Values starting with `=` are automatically treated as formulas
- Use `--use-formula` flag to explicitly mark as formula
- Formulas are evaluated by Google Sheets

### Batch Operations
- Batch updates are more efficient than multiple single updates
- All updates in a batch happen atomically
- Use batch-update when updating multiple cells

### Matching
- `update-by-match` updates ALL rows that match (not just the first)
- Use `exact-match` flag for precise matching
- Matching is case-insensitive by default

### Sheet Names
- Sheet names are case-sensitive
- If sheet name contains spaces, use quotes: `--sheet-name "My Sheet"`
- Default sheet name is "Sheet1" if not specified

### Environment Variables
- Set `ONBOARDING_SHEET_ID` in `.env` to avoid passing `--sheet-id` every time
- Format: `ONBOARDING_SHEET_ID=your_sheet_id_here`

### Error Handling
- Script returns exit code 1 on errors
- Check error messages for authentication issues
- Verify sheet ID and sheet name are correct

## API Limits
- Google Sheets API has rate limits (typically 100 requests per 100 seconds per user)
- Batch operations count as 1 request regardless of number of cells
- Use batch operations when possible to stay within limits

## Success Criteria
- [ ] Can read data from onboarding sheet
- [ ] Can add new rows with correct column mapping
- [ ] Can update existing rows by row number
- [ ] Can update rows by matching criteria
- [ ] Can find rows using search queries
- [ ] Can update individual cells
- [ ] Can perform batch updates
- [ ] Formulas are properly evaluated
- [ ] All operations complete without errors

