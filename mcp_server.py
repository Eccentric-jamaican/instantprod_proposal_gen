#!/usr/bin/env python3
"""
InstantProd Proposal Generator - MCP Server

This MCP server exposes the proposal generation workflow as tools that can be
invoked by AI assistants like ChatGPT, Claude, or any MCP-compatible client.

Usage:
    python mcp_server.py

Tools Available:
    - analyze_transcript: Analyze a call transcript and extract proposal data
    - generate_proposal: Create an HTML proposal from client data
    - deploy_proposal: Deploy a proposal to Vercel
    - send_proposal_email: Send the proposal via email
    - quick_proposal: Full pipeline (analyze → generate → deploy)
    - read_sheet: Read data from Google Sheets
    - find_client: Search for a client in the database
    - list_proposals: List all generated proposals
    - list_transcripts: List all saved transcripts
    - sync_to_drive: Sync all local files to Google Drive
    - list_drive_files: List files stored in Google Drive
    - download_from_drive: Download a file from Google Drive

Resources Available:
    - proposal://template - The HTML proposal template
    - proposal://email-template - The email template
    - directive://generate_proposal - SOP for generating proposals
    - directive://send_proposal - SOP for sending proposals

ChatGPT Connector Tools:
    - search: Search for documents/items (returns JSON-encoded results)
    - fetch: Get full content of an item (returns JSON-encoded content)
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    ResourceTemplate,
)

# Setup paths
PROJECT_ROOT = Path(__file__).parent
EXECUTION_DIR = PROJECT_ROOT / "execution"
DIRECTIVES_DIR = PROJECT_ROOT / "directives"
TMP_DIR = PROJECT_ROOT / ".tmp"
TRANSCRIPTS_DIR = TMP_DIR / "transcripts"
PROPOSALS_DIR = TMP_DIR / "proposals"

# Ensure directories exist
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize MCP server
server = Server("instantprod-proposal-generator")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:50]


def run_script(script_name: str, args: list) -> tuple[bool, str]:
    """Run a Python script and return success status and output."""
    script_path = EXECUTION_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            shell=(os.name == 'nt'),  # Windows compatibility
            timeout=120  # 2 minute timeout
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 120 seconds"
    except Exception as e:
        return False, str(e)


def get_file_list(directory: Path, extension: str = "*") -> list[dict]:
    """Get list of files in a directory with metadata."""
    files = []
    if directory.exists():
        pattern = f"*.{extension}" if extension != "*" else "*"
        for f in directory.glob(pattern):
            if f.is_file():
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "size_bytes": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
    return sorted(files, key=lambda x: x["modified"], reverse=True)


def sync_file_to_drive(file_path: Path, folder_type: str = "proposals") -> Optional[str]:
    """Sync a single file to Google Drive. Returns the Drive view URL or None on failure."""
    try:
        success, output = run_script('drive_storage.py', [
            '--action', 'upload',
            '--file', str(file_path),
            '--folder', folder_type
        ])
        if success:
            # Try to extract the view URL from output
            import re
            url_match = re.search(r'View: (https://[^\s]+)', output)
            return url_match.group(1) if url_match else "Uploaded (URL not captured)"
        return None
    except Exception:
        return None


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="analyze_transcript",
            description="""Analyze a call transcript using AI to extract structured proposal data.
            
            This uses OpenAI to parse the transcript and identify:
            - Client name and company
            - Goals and pain points
            - Proposed solution and deliverables
            - Recommended pricing tier (Starter/Growth/Strategic Partner)
            
            The output is saved as a JSON file that can be used to generate a proposal.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "transcript_text": {
                        "type": "string",
                        "description": "The full transcript text from the call (e.g., from Fireflies.ai)"
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client or company name (used for file naming)"
                    }
                },
                "required": ["transcript_text", "client_name"]
            }
        ),
        Tool(
            name="generate_proposal",
            description="""Generate an HTML proposal from client data.
            
            Can accept either:
            1. A path to a JSON file with client data (from analyze_transcript)
            2. Direct client data as a dictionary
            
            The generated proposal uses the InstantProd branded template with:
            - Hero section with client name
            - Goals and problem statement
            - Solution and deliverables
            - Process steps
            - Investment/pricing section
            - Signature area""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_data_path": {
                        "type": "string",
                        "description": "Path to JSON file with client data (from analyze_transcript)"
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name (required if not using client_data_path)"
                    },
                    "website": {
                        "type": "string",
                        "description": "Client website URL (optional)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="deploy_proposal",
            description="""Deploy a generated proposal to Vercel for instant web access.
            
            This creates a live URL that can be shared with the client.
            No attachments needed - the client views the proposal in their browser.
            
            Returns the live Vercel URL (e.g., https://proposal-acme-corp.vercel.app)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "proposal_path": {
                        "type": "string",
                        "description": "Path to the HTML proposal file"
                    },
                    "client_slug": {
                        "type": "string",
                        "description": "URL-safe client identifier (e.g., 'acme-corp')"
                    }
                },
                "required": ["proposal_path", "client_slug"]
            }
        ),
        Tool(
            name="send_proposal_email",
            description="""Send a branded email with the proposal link via Gmail.
            
            Uses the InstantProd dark-mode email template.
            Requires Gmail API authentication (credentials.json must be set up).""",
            inputSchema={
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client name for personalization"
                    },
                    "proposal_link": {
                        "type": "string",
                        "description": "URL to the deployed proposal"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject (optional, defaults to 'Your Proposal from InstantProd')"
                    }
                },
                "required": ["to_email", "client_name", "proposal_link"]
            }
        ),
        Tool(
            name="quick_proposal",
            description="""Run the full proposal pipeline in one step.
            
            This combines:
            1. Analyze transcript with AI
            2. Generate HTML proposal
            3. Deploy to Vercel
            
            Returns the live proposal URL ready to share with the client.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_name": {
                        "type": "string",
                        "description": "Client or company name"
                    },
                    "transcript_text": {
                        "type": "string",
                        "description": "The full transcript text from the call"
                    }
                },
                "required": ["client_name", "transcript_text"]
            }
        ),
        Tool(
            name="read_sheet",
            description="""Read data from the Google Sheets onboarding database.
            
            Can read:
            - All rows (be careful with large datasets)
            - Specific range (e.g., 'A1:D10')
            - Headers only (for understanding structure)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read", "headers", "metadata"],
                        "description": "What to read: 'read' for data, 'headers' for column names, 'metadata' for sheet info"
                    },
                    "range": {
                        "type": "string",
                        "description": "Optional range to read (e.g., 'A1:D10')"
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "Sheet name (defaults to 'Sheet1')"
                    }
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="find_client",
            description="""Search for a client in the Google Sheets database.
            
            Searches across all columns for matching text.
            Returns matching rows with all their data.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (client name, email, etc.)"
                    },
                    "column": {
                        "type": "string",
                        "description": "Optional: limit search to specific column"
                    },
                    "exact_match": {
                        "type": "boolean",
                        "description": "If true, requires exact match (default: false)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_proposals",
            description="""List all generated proposals.
            
            Returns a list of proposal files with their names, paths, and modification dates.
            Useful for finding recently generated proposals.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of proposals to return (default: 10)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="list_transcripts",
            description="""List all saved transcripts.
            
            Returns a list of transcript files with their names, paths, and modification dates.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of transcripts to return (default: 10)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_last_deployment_url",
            description="""Get the URL of the most recently deployed proposal.
            
            Useful after running quick_proposal or deploy_proposal to retrieve the URL.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="sync_to_drive",
            description="""Sync all local proposal files to Google Drive.
            
            This uploads all transcripts, proposals, and deployment data to Google Drive,
            maintaining the same folder structure:
            
            InstantProd Proposals/
            ├── transcripts/   (call transcripts)
            ├── proposals/     (HTML proposals)
            ├── deployments/   (deployment URLs)
            └── exports/       (other files)
            
            Files are automatically synced after quick_proposal runs.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_drive_files",
            description="""List files stored in Google Drive.
            
            Shows files in the InstantProd Proposals folder on Google Drive.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder": {
                        "type": "string",
                        "enum": ["transcripts", "proposals", "deployments", "exports"],
                        "description": "Which folder to list (default: proposals)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="download_from_drive",
            description="""Download a file from Google Drive to local storage.
            
            Use list_drive_files to get the file ID first.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "Google Drive file ID"
                    },
                    "output_name": {
                        "type": "string",
                        "description": "Name for the downloaded file"
                    }
                },
                "required": ["file_id", "output_name"]
            }
        ),
        # ChatGPT Connector Tools
        Tool(
            name="search",
            description="""Search for documents in the InstantProd system.
            
            Searches across:
            1. Saved Transcripts (Files)
            2. Generated Proposals (Files)
            
            Returns a strict JSON-encoded string with results for ChatGPT Connectors.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="fetch",
            description="""Retrieve the full content of a document by ID.
            
            Returns a strict JSON-encoded string for ChatGPT Connectors.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique ID of the document to fetch"
                    }
                },
                "required": ["id"]
            }
        )
    ]


# =============================================================================
# TOOL HANDLERS
# =============================================================================

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    
    try:
        if name == "analyze_transcript":
            return await handle_analyze_transcript(arguments)
        elif name == "generate_proposal":
            return await handle_generate_proposal(arguments)
        elif name == "deploy_proposal":
            return await handle_deploy_proposal(arguments)
        elif name == "send_proposal_email":
            return await handle_send_email(arguments)
        elif name == "quick_proposal":
            return await handle_quick_proposal(arguments)
        elif name == "read_sheet":
            return await handle_read_sheet(arguments)
        elif name == "find_client":
            return await handle_find_client(arguments)
        elif name == "list_proposals":
            return await handle_list_proposals(arguments)
        elif name == "list_transcripts":
            return await handle_list_transcripts(arguments)
        elif name == "get_last_deployment_url":
            return await handle_get_last_url(arguments)
        elif name == "sync_to_drive":
            return await handle_sync_to_drive(arguments)
        elif name == "list_drive_files":
            return await handle_list_drive_files(arguments)
        elif name == "list_drive_files":
            return await handle_list_drive_files(arguments)
        elif name == "download_from_drive":
            return await handle_download_from_drive(arguments)
        elif name == "search":
            return await handle_search(arguments)
        elif name == "fetch":
            return await handle_fetch(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_analyze_transcript(args: dict) -> list[TextContent]:
    """Analyze a transcript and extract proposal data."""
    transcript_text = args.get("transcript_text", "")
    client_name = args.get("client_name", "client")
    
    if not transcript_text:
        return [TextContent(type="text", text="Error: transcript_text is required")]
    
    # Save transcript to file
    client_slug = slugify(client_name)
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    transcript_file = TRANSCRIPTS_DIR / f"{client_slug}_{date_str}.txt"
    
    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(transcript_text)
    
    # Run analysis
    success, output = run_script('analyze_transcript.py', [
        '--transcript', str(transcript_file)
    ])
    
    if not success:
        return [TextContent(type="text", text=f"Analysis failed:\n{output}")]
    
    # Find the generated JSON file
    json_file = transcript_file.parent / f"{transcript_file.stem}_data.json"
    
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [TextContent(
            type="text",
            text=f"""✅ Transcript analyzed successfully!

**Files Created:**
- Transcript: `{transcript_file.name}`
- Data JSON: `{json_file.name}`

**Extracted Data:**
```json
{json.dumps(data, indent=2)}
```

**Next Step:** Use `generate_proposal` with client_data_path="{json_file}" to create the HTML proposal."""
        )]
    else:
        return [TextContent(type="text", text=f"Analysis completed but JSON not found.\nOutput: {output}")]


async def handle_generate_proposal(args: dict) -> list[TextContent]:
    """Generate an HTML proposal."""
    client_data_path = args.get("client_data_path")
    client_name = args.get("client_name")
    website = args.get("website")
    
    cmd_args = []
    
    if client_data_path:
        cmd_args.extend(['--client-data', client_data_path])
    elif client_name:
        cmd_args.extend(['--client-name', client_name])
        if website:
            cmd_args.extend(['--website', website])
    else:
        return [TextContent(type="text", text="Error: Either client_data_path or client_name is required")]
    
    # Generate output path
    slug = slugify(client_name or "proposal")
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = PROPOSALS_DIR / f"{slug}_{date_str}.html"
    cmd_args.extend(['--output', str(output_file)])
    
    success, output = run_script('generate_proposal.py', cmd_args)
    
    if not success:
        return [TextContent(type="text", text=f"Generation failed:\n{output}")]
    
    return [TextContent(
        type="text",
        text=f"""✅ Proposal generated successfully!

**File:** `{output_file.name}`
**Path:** `{output_file}`

**Next Step:** Use `deploy_proposal` to get a live URL, or open the HTML file locally to preview."""
    )]


async def handle_deploy_proposal(args: dict) -> list[TextContent]:
    """Deploy a proposal to Vercel."""
    proposal_path = args.get("proposal_path")
    client_slug = args.get("client_slug", "proposal")
    
    if not proposal_path:
        # Try to find the most recent proposal
        proposals = get_file_list(PROPOSALS_DIR, "html")
        if proposals:
            proposal_path = proposals[0]["path"]
        else:
            return [TextContent(type="text", text="Error: No proposal_path provided and no proposals found")]
    
    success, output = run_script('deploy_proposal.py', [
        '--proposal', proposal_path,
        '--client-slug', client_slug
    ])
    
    if not success:
        return [TextContent(type="text", text=f"Deployment failed:\n{output}")]
    
    # Extract URL
    url_match = re.search(r'https://[^\s]+\.vercel\.app', output)
    url = url_match.group(0) if url_match else "(Check Vercel dashboard)"
    
    return [TextContent(
        type="text",
        text=f"""✅ Proposal deployed to Vercel!

**Live URL:** {url}

**Next Step:** Use `send_proposal_email` to send this link to the client."""
    )]


async def handle_send_email(args: dict) -> list[TextContent]:
    """Send proposal email."""
    to_email = args.get("to_email")
    client_name = args.get("client_name")
    proposal_link = args.get("proposal_link")
    subject = args.get("subject", f"Your Proposal from InstantProd")
    
    if not all([to_email, client_name, proposal_link]):
        return [TextContent(type="text", text="Error: to_email, client_name, and proposal_link are required")]
    
    success, output = run_script('send_email.py', [
        '--to', to_email,
        '--subject', subject,
        '--body', f"Your proposal is ready: {proposal_link}",
        '--client-name', client_name,
        '--link', proposal_link
    ])
    
    if not success:
        return [TextContent(type="text", text=f"Email failed:\n{output}")]
    
    return [TextContent(
        type="text",
        text=f"""✅ Proposal email sent!

**To:** {to_email}
**Subject:** {subject}
**Link:** {proposal_link}"""
    )]


async def handle_quick_proposal(args: dict) -> list[TextContent]:
    """Run the full proposal pipeline."""
    client_name = args.get("client_name")
    transcript_text = args.get("transcript_text")
    
    if not client_name or not transcript_text:
        return [TextContent(type="text", text="Error: client_name and transcript_text are required")]
    
    results = []
    
    # Step 1: Analyze
    results.append("📝 **Step 1: Analyzing transcript...**")
    analyze_result = await handle_analyze_transcript({
        "transcript_text": transcript_text,
        "client_name": client_name
    })
    
    if "failed" in analyze_result[0].text.lower():
        return [TextContent(type="text", text=f"Pipeline failed at analysis:\n{analyze_result[0].text}")]
    
    # Find the JSON file
    client_slug = slugify(client_name)
    json_files = list(TRANSCRIPTS_DIR.glob(f"{client_slug}_*_data.json"))
    if not json_files:
        return [TextContent(type="text", text="Pipeline failed: Could not find generated JSON")]
    
    json_file = max(json_files, key=lambda x: x.stat().st_mtime)
    results.append("✅ Transcript analyzed")
    
    # Step 2: Generate
    results.append("\n🎨 **Step 2: Generating proposal...**")
    generate_result = await handle_generate_proposal({
        "client_data_path": str(json_file),
        "client_name": client_name
    })
    
    if "failed" in generate_result[0].text.lower():
        return [TextContent(type="text", text=f"Pipeline failed at generation:\n{generate_result[0].text}")]
    
    # Find the HTML file
    html_files = list(PROPOSALS_DIR.glob(f"{client_slug}_*.html"))
    if not html_files:
        return [TextContent(type="text", text="Pipeline failed: Could not find generated HTML")]
    
    html_file = max(html_files, key=lambda x: x.stat().st_mtime)
    results.append("✅ Proposal generated")
    
    # Step 3: Deploy
    results.append("\n🚀 **Step 3: Deploying to Vercel...**")
    deploy_result = await handle_deploy_proposal({
        "proposal_path": str(html_file),
        "client_slug": client_slug
    })
    
    if "failed" in deploy_result[0].text.lower():
        return [TextContent(type="text", text=f"Pipeline failed at deployment:\n{deploy_result[0].text}")]
    
    # Extract URL
    url_match = re.search(r'https://[^\s]+\.vercel\.app', deploy_result[0].text)
    url = url_match.group(0) if url_match else "(Check Vercel dashboard)"
    results.append("✅ Deployed to Vercel")
    
    # Step 4: Sync to Google Drive
    results.append("\n☁️ **Step 4: Syncing to Google Drive...**")
    sync_result = await handle_sync_to_drive({})
    if "failed" not in sync_result[0].text.lower():
        results.append("✅ Synced to Google Drive")
    else:
        results.append("⚠️ Drive sync skipped (check credentials)")
    
    # Final summary
    results.append(f"""

═══════════════════════════════════════════════════════
                    🎉 SUCCESS!
═══════════════════════════════════════════════════════

**Client:** {client_name}
**Proposal:** {html_file.name}

**🔗 LIVE URL:** {url}

**☁️ Cloud Backup:** Google Drive (InstantProd Proposals folder)

═══════════════════════════════════════════════════════

**Next Step:** Use `send_proposal_email` to email this to the client.""")
    
    return [TextContent(type="text", text="\n".join(results))]


async def handle_read_sheet(args: dict) -> list[TextContent]:
    """Read data from Google Sheets."""
    action = args.get("action", "read")
    range_name = args.get("range")
    sheet_name = args.get("sheet_name", "Sheet1")
    
    cmd_args = ['--action', action]
    if sheet_name:
        cmd_args.extend(['--sheet-name', sheet_name])
    if range_name:
        cmd_args.extend(['--range', range_name])
    
    success, output = run_script('sheets_manager.py', cmd_args)
    
    if not success:
        return [TextContent(type="text", text=f"Sheet read failed:\n{output}")]
    
    return [TextContent(type="text", text=f"Sheet data:\n{output}")]


async def handle_find_client(args: dict) -> list[TextContent]:
    """Find a client in the sheets database."""
    query = args.get("query")
    column = args.get("column")
    exact_match = args.get("exact_match", False)
    
    if not query:
        return [TextContent(type="text", text="Error: query is required")]
    
    cmd_args = ['--action', 'find', '--query', query]
    if column:
        cmd_args.extend(['--column', column])
    if exact_match:
        cmd_args.append('--exact-match')
    
    success, output = run_script('sheets_manager.py', cmd_args)
    
    if not success:
        return [TextContent(type="text", text=f"Search failed:\n{output}")]
    
    return [TextContent(type="text", text=f"Search results for '{query}':\n{output}")]


async def handle_list_proposals(args: dict) -> list[TextContent]:
    """List generated proposals."""
    limit = args.get("limit", 10)
    proposals = get_file_list(PROPOSALS_DIR, "html")[:limit]
    
    if not proposals:
        return [TextContent(type="text", text="No proposals found.")]
    
    lines = ["**Generated Proposals:**\n"]
    for p in proposals:
        lines.append(f"- `{p['name']}` ({p['modified'][:10]})")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_list_transcripts(args: dict) -> list[TextContent]:
    """List saved transcripts."""
    limit = args.get("limit", 10)
    transcripts = get_file_list(TRANSCRIPTS_DIR, "txt")[:limit]
    
    if not transcripts:
        return [TextContent(type="text", text="No transcripts found.")]
    
    lines = ["**Saved Transcripts:**\n"]
    for t in transcripts:
        lines.append(f"- `{t['name']}` ({t['modified'][:10]})")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_get_last_url(args: dict) -> list[TextContent]:
    """Get the last deployment URL."""
    url_file = TMP_DIR / "last_deployment_url.txt"
    
    if url_file.exists():
        url = url_file.read_text().strip()
        return [TextContent(type="text", text=f"**Last Deployed URL:** {url}")]
    else:
        return [TextContent(type="text", text="No deployment URL found. Run `deploy_proposal` first.")]


async def handle_sync_to_drive(args: dict) -> list[TextContent]:
    """Sync all local files to Google Drive."""
    success, output = run_script('drive_storage.py', ['--action', 'sync'])
    
    if not success:
        return [TextContent(type="text", text=f"Drive sync failed:\n{output}")]
    
    return [TextContent(
        type="text",
        text=f"""✅ Files synced to Google Drive!

{output}

**Google Drive Location:** InstantProd Proposals/

You can access these files from any device via Google Drive."""
    )]


async def handle_list_drive_files(args: dict) -> list[TextContent]:
    """List files in Google Drive."""
    folder = args.get("folder", "proposals")
    
    success, output = run_script('drive_storage.py', [
        '--action', 'list',
        '--folder', folder
    ])
    
    if not success:
        return [TextContent(type="text", text=f"Failed to list Drive files:\n{output}")]
    
    return [TextContent(type="text", text=f"**Google Drive - {folder}/**\n\n{output}")]


async def handle_download_from_drive(args: dict) -> list[TextContent]:
    """Download a file from Google Drive."""
    file_id = args.get("file_id")
    output_name = args.get("output_name")
    
    if not file_id or not output_name:
        return [TextContent(type="text", text="Error: file_id and output_name are required")]
    
    output_path = TMP_DIR / "downloads" / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    success, output = run_script('drive_storage.py', [
        '--action', 'download',
        '--file-id', file_id,
        '--output', str(output_path)
    ])
    
    if not success:
        return [TextContent(type="text", text=f"Download failed:\n{output}")]
    
    return [TextContent(
        type="text",
        text=f"""✅ Downloaded from Google Drive!

**File:** {output_name}
**Saved to:** {output_path}"""
    )]


# =============================================================================
# RESOURCE DEFINITIONS
# =============================================================================

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    resources = [
        Resource(
            uri="proposal://template",
            name="Proposal HTML Template",
            description="The main HTML template used for generating proposals",
            mimeType="text/html"
        ),
        Resource(
            uri="proposal://email-template",
            name="Email Template",
            description="The HTML email template for sending proposals",
            mimeType="text/html"
        ),
    ]
    
    # Add directives
    if DIRECTIVES_DIR.exists():
        for f in DIRECTIVES_DIR.glob("*.md"):
            resources.append(Resource(
                uri=f"directive://{f.stem}",
                name=f"Directive: {f.stem.replace('_', ' ').title()}",
                description=f"SOP for {f.stem.replace('_', ' ')}",
                mimeType="text/markdown"
            ))
    
    return resources


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if uri == "proposal://template":
        template_file = PROJECT_ROOT / "proposal_template.html"
        if template_file.exists():
            return template_file.read_text(encoding='utf-8')
        return "Template not found"
    
    elif uri == "proposal://email-template":
        template_file = PROJECT_ROOT / "email_template.html"
        if template_file.exists():
            return template_file.read_text(encoding='utf-8')
        return "Email template not found"
    
    elif uri.startswith("directive://"):
        directive_name = uri.replace("directive://", "")
        directive_file = DIRECTIVES_DIR / f"{directive_name}.md"
        if directive_file.exists():
            return directive_file.read_text(encoding='utf-8')
        return f"Directive '{directive_name}' not found"
    
    return f"Unknown resource: {uri}"


# =============================================================================
# CHATGPT CONNECTOR HANDLERS (Search/Fetch)
# =============================================================================

async def handle_search(args: dict) -> list[TextContent]:
    """
    Search tool for ChatGPT Connectors.
    Returns JSON-encoded string in strict format: {"results": [{"id":..., "title":..., "url":...}]}
    """
    query = args.get("query", "").lower()
    results = []
    
    # 1. Search Files (Transcripts & Proposals)
    if TRANSCRIPTS_DIR.exists():
        for f in TRANSCRIPTS_DIR.glob(f"*{query}*"):
            if f.suffix in ['.txt', '.json']:
                results.append({
                    "id": f"file://transcripts/{f.name}",
                    "title": f"Transcript: {f.name}",
                    "url": str(f.absolute())
                })

    if PROPOSALS_DIR.exists():
        for f in PROPOSALS_DIR.glob(f"*{query}*"):
            if f.suffix == '.html':
                results.append({
                    "id": f"file://proposals/{f.name}",
                    "title": f"Proposal: {f.name}",
                    "url": str(f.absolute())
                })

    # 2. Search Sheets (Clients)
    # We'll do a quick partial match if possible, or just skip if too heavy.
    # For now, let's keep it lightweight and search files primarily.
    # Real implementation would call sheets_manager.py here.
    
    response_obj = {"results": results}
    return [TextContent(type="text", text=json.dumps(response_obj))]


async def handle_fetch(args: dict) -> list[TextContent]:
    """
    Fetch tool for ChatGPT Connectors.
    Returns JSON-encoded strict format: {"id":..., "title":..., "text":..., "url":...}
    """
    doc_id = args.get("id", "")
    content_obj = {}
    
    try:
        if doc_id.startswith("file://"):
            # Handle file path
            rel_path = doc_id.replace("file://", "")
            if rel_path.startswith("transcripts/"):
                path = TRANSCRIPTS_DIR / rel_path.replace("transcripts/", "")
            elif rel_path.startswith("proposals/"):
                path = PROPOSALS_DIR / rel_path.replace("proposals/", "")
            else:
                path = None
            
            if path and path.exists():
                text = path.read_text(encoding='utf-8')
                content_obj = {
                    "id": doc_id,
                    "title": path.name,
                    "text": text,
                    "url": str(path.absolute()),
                    "metadata": {
                        "size": path.stat().st_size,
                        "modified": str(datetime.fromtimestamp(path.stat().st_mtime))
                    }
                }
            else:
                 content_obj = {"id": doc_id, "error": "File not found"}
        else:
             content_obj = {"id": doc_id, "error": "Invalid ID format"}
             
    except Exception as e:
        content_obj = {"id": doc_id, "error": str(e)}

    return [TextContent(type="text", text=json.dumps(content_obj))]


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
