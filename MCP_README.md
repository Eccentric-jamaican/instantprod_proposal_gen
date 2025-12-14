# InstantProd Proposal Generator - MCP Server

This MCP (Model Context Protocol) server exposes the proposal generation workflow as tools that can be invoked by AI assistants like **ChatGPT**, **Claude**, or any MCP-compatible client.

## 🚀 Quick Start

### Option 1: HTTP API (For ChatGPT)

```bash
# Start the HTTP API server
python api_server.py
```

Then:
1. Go to [chat.openai.com](https://chat.openai.com) → Explore GPTs → Create a GPT
2. In the **Configure** tab, click **Create new action**
3. Import the OpenAPI schema from: `http://localhost:8000/openapi.json`
4. Test the tools in your custom GPT!

### Option 2: MCP Protocol (For Claude Desktop)

Add to your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "instantprod-proposals": {
      "command": "python",
      "args": ["c:/Users/Addis/py/instantprod_proposal_gen/mcp_server.py"]
    }
  }
}
```

---

## 🛠️ Available Tools

| Tool | Description |
|------|-------------|
| `analyze_transcript` | Analyze a Fireflies.ai transcript with AI to extract proposal data |
| `generate_proposal` | Create an HTML proposal from client data |
| `deploy_proposal` | Deploy a proposal to Vercel and get a live URL |
| `send_proposal_email` | Send the proposal via Gmail with branded template |
| `quick_proposal` | Full pipeline: analyze → generate → deploy → **sync to Drive** (one command!) |
| `read_sheet` | Read data from Google Sheets onboarding database |
| `find_client` | Search for a client in the database |
| `list_proposals` | List all generated proposals |
| `list_transcripts` | List all saved transcripts |
| `get_last_deployment_url` | Get the most recent Vercel deployment URL |
| **`sync_to_drive`** | ☁️ Sync all local files to Google Drive |
| **`list_drive_files`** | ☁️ List files stored in Google Drive |
| **`download_from_drive`** | ☁️ Download a file from Google Drive |

---

## 📚 Available Resources

| Resource URI | Description |
|--------------|-------------|
| `proposal://template` | The HTML proposal template |
| `proposal://email-template` | The email template |
| `directive://generate_proposal` | SOP for generating proposals |
| `directive://send_proposal` | SOP for sending proposals |

---

## 💬 Example ChatGPT Conversation

```
User: I just had a call with Acme Corp. Here's the transcript from Fireflies:
[pastes transcript]

ChatGPT: I'll analyze this transcript and create a proposal for Acme Corp.
[calls quick_proposal tool]

✅ Proposal created and deployed!
Live URL: https://proposal-acme-corp.vercel.app

Would you like me to send this to the client via email?

User: Yes, send it to john@acme.com

ChatGPT: [calls send_proposal_email tool]
✅ Email sent to john@acme.com!
```

---

## 🔧 Development

### Test the MCP Server

```bash
python mcp_server.py
```

### Test the HTTP API

```bash
python api_server.py
# Visit http://localhost:8000/docs for interactive API docs
```

### API Endpoints

```
GET  /                          - API info
GET  /health                    - Health check
GET  /tools                     - List all tools
GET  /resources                 - List all resources
GET  /resources/{uri}           - Read a resource

POST /tools/analyze_transcript  - Analyze transcript
POST /tools/generate_proposal   - Generate proposal
POST /tools/deploy_proposal     - Deploy to Vercel
POST /tools/send_proposal_email - Send email
POST /tools/quick_proposal      - Full pipeline
POST /tools/read_sheet          - Read Google Sheet
POST /tools/find_client         - Search for client
POST /tools/list_proposals      - List proposals
POST /tools/list_transcripts    - List transcripts
GET  /tools/last_deployment_url - Get last URL
```

---

## 🌐 Production Deployment

For ChatGPT to access your API, it needs a public URL. Options:

### 1. ngrok (Quick testing)
```bash
ngrok http 8000
# Use the ngrok URL in your GPT action
```

### 2. Railway/Render (Production)
Deploy the `api_server.py` to a cloud platform and use that URL.

### 3. Vercel (Serverless)
Convert to serverless functions if needed.

---

## 📁 Files

```
instantprod_proposal_gen/
├── mcp_server.py       # MCP protocol server
├── api_server.py       # HTTP REST API wrapper
├── mcp_config.json     # Claude Desktop config
└── MCP_README.md       # This file
```
