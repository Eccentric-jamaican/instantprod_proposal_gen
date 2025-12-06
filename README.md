# InstantProd Proposal Generator

A 3-layer architecture system for automated proposal generation with Google Sheets/Slides integration.

## Architecture

This project uses a 3-layer architecture to separate concerns:

1. **Directives** (`directives/`) - Natural language SOPs defining what to do
2. **Orchestration** - AI agent decision-making and routing
3. **Execution** (`execution/`) - Deterministic Python scripts that do the work

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.\venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
```

### 5. Google API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Sheets API
   - Google Slides API
   - Google Drive API
4. Create OAuth 2.0 credentials
5. Download the credentials and save as `credentials.json` in the project root

### 6. Verify Setup

Run the verification script to ensure everything is configured correctly:

```bash
python verify_setup.py
```

This will check:
- Python version (3.8+)
- All required dependencies
- Directory structure
- Configuration files

## Directory Structure

```
instantprod_proposal_gen/
├── directives/          # SOPs and instructions (Markdown)
├── execution/           # Python scripts (deterministic tools)
├── .tmp/               # Temporary/intermediate files (gitignored)
├── .env                # Environment variables (gitignored)
├── credentials.json    # Google OAuth credentials (gitignored)
├── token.json          # Google OAuth token (gitignored)
├── requirements.txt    # Python dependencies
└── AGENTS.md          # Agent operating instructions
```

## Usage: Proposal Workflow

The system is designed for a seamless 3-step workflow: **Generate -> Deploy -> Email**.

### 1. Generate Proposal
Create a customized HTML proposal from the template.
```bash
python execution/generate_proposal.py --client-name "Acme Corp" --output .tmp/proposals/acme.html
```

### 2. Deploy to Cloud (Recommended)
Deploy the proposal to **Vercel** for instant mobile/desktop access without attachments.
```bash
python execution/deploy_proposal.py --proposal .tmp/proposals/acme.html --client-slug acme-corp
# Returns: https://proposal-acme-corp-xyz.vercel.app
```

### 3. Send Branded Email
Send a "Tesla-style" dark mode email with the link.
```bash
python execution/send_email.py \
  --to "client@example.com" \
  --subject "Proposal for Acme Corp" \
  --body "View online" \
  --client-name "Acme Corp" \
  --link "https://proposal-acme-corp-xyz.vercel.app"
```

See individual directives in `directives/` for advanced details.

## Key Principles

- **Deliverables** live in the cloud (Google Sheets, Slides)
- **Intermediates** live in `.tmp/` and can be regenerated
- **Scripts** are deterministic and well-tested
- **Directives** are living documents that improve over time
