# 🚀 Deploying to Railway

This guide covers how to deploy your InstantProd Proposal System to Railway, making it accessible to ChatGPT and other AI tools.

## Prerequisites
- A GitHub account (repo pushed)
- A [Railway](https://railway.app/) account
- Your Google Cloud `credentials.json` and `token.json` files

## Step 1: Encode Your Credentials
Railway (and most cloud providers) handles secrets as environment variables, but your Google authentication uses JSON files. We will encoded them to Base64 to store them as secrets.

**Run this command in your local terminal:**
```bash
# On Windows PowerShell
$creds = [Convert]::ToBase64String([IO.File]::ReadAllBytes("credentials.json"))
$token = [Convert]::ToBase64String([IO.File]::ReadAllBytes("token.json"))

echo "GOOGLE_CREDENTIALS_BASE64=$creds"
echo "GOOGLE_TOKEN_BASE64=$token"
```
*Copy the output values for the next step.*

## Step 2: Create Railway Project
1. Log in to [Railway](https://railway.app/).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select your `instantprod_proposal_gen` repo.
4. Click **Deploy Now**.

## Step 3: Configure Environment Variables
1. Go to your project dashboard in Railway.
2. Click on the service card.
3. Go to the **Variables** tab.
4. Add the following variables:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `GOOGLE_CREDENTIALS_BASE64` | *(Paste value from Step 1)* | Your encoded credentials |
| `GOOGLE_TOKEN_BASE64` | *(Paste value from Step 1)* | Your encoded token |
| `MCP_API_KEY` | `your-secret-password-here` | Set a strong password to secure your API |
| `PORT` | `8000` | (Optional, Railway usually detects it) |

5. Railway will automatically redeploy when you save variables.

## Step 4: Get Your Public URL
1. Go to the **Settings** tab.
2. Under **Networking**, ensure a public domain is generated (e.g., `instantprod-production.up.railway.app`).

## Step 5: Connect to ChatGPT
1. Go to [ChatGPT](https://chat.openai.com) → **Explore GPTs** → **Create**.
2. **Configure Tab** → **Create new action**.
3. **Import from URL**: `https://<your-railway-url>/openapi.json`.
4. **Authentication**: 
   - Type: `API Key`
   - Auth Type: `Custom` (Header Name: `X-API-Key`)
   - Key: *(The password you set in MCP_API_KEY)*

## ✅ Success!
Your custom GPT can now:
- Analyze transcripts
- Generate and deploy proposals
- Send emails
- **Function as a Search Connector** to find past proposals!
