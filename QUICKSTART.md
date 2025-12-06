# Quick Start Guide

## What You Have Now

Your environment is fully initialized with the **3-layer architecture**:

### ✅ Layer 1: Directives
- **Location**: `directives/`
- **Purpose**: Natural language SOPs that define workflows
- **Example**: `directives/example_directive.md`

### ✅ Layer 2: Orchestration
- **Who**: AI Agent (me!)
- **Purpose**: Read directives, make decisions, call execution scripts
- **How**: I route tasks intelligently and handle errors

### ✅ Layer 3: Execution
- **Location**: `execution/`
- **Purpose**: Deterministic Python scripts that do the actual work
- **Example**: `execution/example_script.py`

## Environment Status

✅ Python 3.13.9 installed
✅ Virtual environment created (`venv/`)
✅ All dependencies installed
✅ `.env` file created
✅ Directory structure ready
✅ Example files created

## Next Steps

### 1. Configure API Keys

Edit your `.env` file and add your API keys:

```bash
# Open .env in your editor
notepad .env  # Windows
# or
code .env     # VS Code
```

Add your keys:
```env
# Google API (for Sheets, Slides, etc.)
GOOGLE_APPLICATION_CREDENTIALS=credentials.json

# OpenAI API (if needed)
OPENAI_API_KEY=your_key_here
```

### 2. Set Up Google OAuth

Follow the README instructions to:
1. Create a Google Cloud project
2. Enable required APIs (Sheets, Slides, Drive)
3. Download `credentials.json`
4. Place it in the project root

### 3. Create Your First Directive

Create a new file in `directives/` for your workflow:

```bash
# Example: directives/generate_proposal.md
```

Use the template in `directives/example_directive.md` as a guide.

### 4. Create Execution Scripts

Build deterministic Python scripts in `execution/`:

```bash
# Example: execution/create_google_sheet.py
```

Use `execution/example_script.py` as a template.

## How to Work with the Agent

### Tell Me What You Want

Just describe your goal naturally:
- "Create a directive for scraping competitor websites"
- "Build a script to generate a Google Slides presentation"
- "Help me automate proposal generation"

### I Will:

1. **Read** the relevant directive (or help you create one)
2. **Decide** which execution scripts to run
3. **Execute** the scripts in the right order
4. **Handle** errors and update directives with learnings
5. **Deliver** results to the cloud (Google Sheets, Slides, etc.)

## Key Concepts

### Deliverables vs Intermediates

- **Deliverables**: Live in the cloud (Google Sheets, Slides)
  - These are what you actually use and share
  - Persistent and accessible anywhere

- **Intermediates**: Live in `.tmp/`
  - Temporary processing files
  - Can be deleted and regenerated
  - Never committed to git

### Self-Annealing

When something breaks:
1. I fix the script
2. Test it again
3. Update the directive with what I learned
4. System gets stronger

This means the system **improves over time** automatically.

## Common Commands

### Activate Virtual Environment

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

### Run Verification

```bash
python verify_setup.py
```

### Test Example Script

```bash
python execution/example_script.py --input "test" --verbose
```

### Deactivate Virtual Environment

```bash
deactivate
```

## File Organization

```
instantprod_proposal_gen/
├── directives/              # Your SOPs (what to do)
│   └── example_directive.md
├── execution/               # Your tools (how to do it)
│   └── example_script.py
├── .tmp/                    # Temporary files (auto-generated)
├── venv/                    # Python virtual environment
├── .env                     # Your API keys (keep secret!)
├── verify_setup.py          # Environment checker
├── AGENTS.md               # How I operate
└── README.md               # Full documentation
```

## Tips

1. **Always activate the virtual environment** before running scripts
2. **Keep .env and credentials.json secret** (they're gitignored)
3. **Update directives** when you discover new patterns
4. **Use .tmp/** for all intermediate files
5. **Deliver to the cloud** for final outputs

## Need Help?

Just ask me! I can:
- Create new directives
- Build execution scripts
- Debug errors
- Update documentation
- Explain the architecture

Let's build something great! 🚀
