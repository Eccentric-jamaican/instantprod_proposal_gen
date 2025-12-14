#!/usr/bin/env python3
"""
InstantProd Proposal Generator - HTTP API Server

This wraps the MCP server functionality in a REST API that can be accessed
by ChatGPT Custom GPT Actions or any HTTP client.

Usage:
    python api_server.py

Endpoints:
    POST /tools/{tool_name}  - Execute a tool
    GET  /tools              - List available tools
    GET  /resources          - List available resources
    GET  /resources/{uri}    - Read a resource
    GET  /health            - Health check
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import from MCP server
sys.path.insert(0, str(Path(__file__).parent))
from mcp_server import (
    handle_analyze_transcript,
    handle_generate_proposal,
    handle_deploy_proposal,
    handle_send_email,
    handle_quick_proposal,
    handle_read_sheet,
    handle_find_client,
    handle_list_proposals,
    handle_list_transcripts,
    handle_get_last_url,
    handle_sync_to_drive,
    handle_list_drive_files,
    handle_download_from_drive,
    list_tools,
    list_resources,
    read_resource,
    PROJECT_ROOT,
    DIRECTIVES_DIR,
)

# Initialize FastAPI
app = FastAPI(
    title="InstantProd Proposal Generator API",
    description="REST API for the proposal generation workflow. Connect this to ChatGPT via Custom GPT Actions.",
    version="1.0.0",
)

# Enable CORS for ChatGPT and other clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# MODELS
# =============================================================================

class ToolRequest(BaseModel):
    """Request body for tool execution."""
    arguments: dict = {}


class AnalyzeTranscriptRequest(BaseModel):
    """Request for analyze_transcript tool."""
    transcript_text: str
    client_name: str


class GenerateProposalRequest(BaseModel):
    """Request for generate_proposal tool."""
    client_data_path: Optional[str] = None
    client_name: Optional[str] = None
    website: Optional[str] = None


class DeployProposalRequest(BaseModel):
    """Request for deploy_proposal tool."""
    proposal_path: Optional[str] = None
    client_slug: str = "proposal"


class SendEmailRequest(BaseModel):
    """Request for send_proposal_email tool."""
    to_email: str
    client_name: str
    proposal_link: str
    subject: Optional[str] = None


class QuickProposalRequest(BaseModel):
    """Request for quick_proposal tool."""
    client_name: str
    transcript_text: str


class ReadSheetRequest(BaseModel):
    """Request for read_sheet tool."""
    action: str = "read"
    range: Optional[str] = None
    sheet_name: Optional[str] = "Sheet1"


class FindClientRequest(BaseModel):
    """Request for find_client tool."""
    query: str
    column: Optional[str] = None
    exact_match: bool = False


class ListRequest(BaseModel):
    """Request for list tools."""
    limit: int = 10


class ListDriveFilesRequest(BaseModel):
    """Request for list_drive_files tool."""
    folder: str = "proposals"


class DownloadFromDriveRequest(BaseModel):
    """Request for download_from_drive tool."""
    file_id: str
    output_name: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """API root - returns basic info."""
    return {
        "name": "InstantProd Proposal Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/tools")
async def get_tools():
    """List all available tools."""
    tools = await list_tools()
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema
            }
            for t in tools
        ]
    }


@app.get("/resources")
async def get_resources():
    """List all available resources."""
    resources = await list_resources()
    return {
        "resources": [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
                "mime_type": r.mimeType
            }
            for r in resources
        ]
    }


@app.get("/resources/{uri:path}")
async def get_resource(uri: str):
    """Read a specific resource."""
    content = await read_resource(uri)
    return {"uri": uri, "content": content}


# Tool-specific endpoints for better OpenAPI schema generation

@app.post("/tools/analyze_transcript")
async def analyze_transcript(request: AnalyzeTranscriptRequest):
    """Analyze a call transcript using AI to extract structured proposal data."""
    result = await handle_analyze_transcript(request.model_dump())
    return {"result": result[0].text}


@app.post("/tools/generate_proposal")
async def generate_proposal(request: GenerateProposalRequest):
    """Generate an HTML proposal from client data."""
    result = await handle_generate_proposal(request.model_dump())
    return {"result": result[0].text}


@app.post("/tools/deploy_proposal")
async def deploy_proposal(request: DeployProposalRequest):
    """Deploy a generated proposal to Vercel."""
    result = await handle_deploy_proposal(request.model_dump())
    return {"result": result[0].text}


@app.post("/tools/send_proposal_email")
async def send_proposal_email(request: SendEmailRequest):
    """Send a branded email with the proposal link via Gmail."""
    result = await handle_send_email({
        "to_email": request.to_email,
        "client_name": request.client_name,
        "proposal_link": request.proposal_link,
        "subject": request.subject
    })
    return {"result": result[0].text}


@app.post("/tools/quick_proposal")
async def quick_proposal(request: QuickProposalRequest):
    """Run the full proposal pipeline (analyze → generate → deploy)."""
    result = await handle_quick_proposal(request.model_dump())
    return {"result": result[0].text}


@app.post("/tools/read_sheet")
async def read_sheet(request: ReadSheetRequest):
    """Read data from the Google Sheets database."""
    result = await handle_read_sheet(request.model_dump())
    return {"result": result[0].text}


@app.post("/tools/find_client")
async def find_client(request: FindClientRequest):
    """Search for a client in the database."""
    result = await handle_find_client(request.model_dump())
    return {"result": result[0].text}


@app.post("/tools/list_proposals")
async def list_proposals_endpoint(request: ListRequest = ListRequest()):
    """List all generated proposals."""
    result = await handle_list_proposals(request.model_dump())
    return {"result": result[0].text}


@app.post("/tools/list_transcripts")
async def list_transcripts_endpoint(request: ListRequest = ListRequest()):
    """List all saved transcripts."""
    result = await handle_list_transcripts(request.model_dump())
    return {"result": result[0].text}


@app.get("/tools/last_deployment_url")
async def get_last_deployment_url():
    """Get the URL of the most recently deployed proposal."""
    result = await handle_get_last_url({})
    return {"result": result[0].text}


@app.post("/tools/sync_to_drive")
async def sync_to_drive():
    """Sync all local proposal files to Google Drive."""
    result = await handle_sync_to_drive({})
    return {"result": result[0].text}


@app.post("/tools/list_drive_files")
async def list_drive_files(request: ListDriveFilesRequest = ListDriveFilesRequest()):
    """List files stored in Google Drive."""
    result = await handle_list_drive_files(request.model_dump())
    return {"result": result[0].text}


@app.post("/tools/download_from_drive")
async def download_from_drive(request: DownloadFromDriveRequest):
    """Download a file from Google Drive to local storage."""
    result = await handle_download_from_drive(request.model_dump())
    return {"result": result[0].text}


# Generic tool endpoint (for flexibility)
@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, request: ToolRequest):
    """Execute any tool by name with arbitrary arguments."""
    handlers = {
        "analyze_transcript": handle_analyze_transcript,
        "generate_proposal": handle_generate_proposal,
        "deploy_proposal": handle_deploy_proposal,
        "send_proposal_email": handle_send_email,
        "quick_proposal": handle_quick_proposal,
        "read_sheet": handle_read_sheet,
        "find_client": handle_find_client,
        "list_proposals": handle_list_proposals,
        "list_transcripts": handle_list_transcripts,
        "get_last_deployment_url": handle_get_last_url,
        "sync_to_drive": handle_sync_to_drive,
        "list_drive_files": handle_list_drive_files,
        "download_from_drive": handle_download_from_drive,
    }
    
    handler = handlers.get(tool_name)
    if not handler:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    result = await handler(request.arguments)
    return {"result": result[0].text}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║     InstantProd Proposal Generator - API Server           ║
╠═══════════════════════════════════════════════════════════╣
║  Local:    http://localhost:{port}                          ║
║  Docs:     http://localhost:{port}/docs                     ║
║  OpenAPI:  http://localhost:{port}/openapi.json             ║
╚═══════════════════════════════════════════════════════════╝

To connect ChatGPT:
1. Go to chat.openai.com → Explore GPTs → Create a GPT
2. In the Configure tab, add an Action
3. Use the OpenAPI schema from http://localhost:{port}/openapi.json
4. For production, deploy this to a public URL (Vercel, Railway, etc.)
""")
    uvicorn.run(app, host="0.0.0.0", port=port)
