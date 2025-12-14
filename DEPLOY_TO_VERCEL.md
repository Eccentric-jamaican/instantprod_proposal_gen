# 🚀 Deploying to Vercel

Since Vercel is serverless, the filesystem is read-only. We've updated the code to handle this by using the `/tmp` directory.

## Step 1: Push to GitHub
Ensure all your latest changes (including `vercel.json` and `auth_helper.py` updates) are pushed.

## Step 2: Import Project in Vercel
1. Go to [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New** → **Project**.
3. Import your `instantprod_proposal_gen` repository.
4. **Framework Preset**: Select "Other" (or leave as Default/None).
5. Open the **Environment Variables** section.

## Step 3: Add Environment Variables
You need to add the same variables you generated for Railway. Open `railway_secrets.txt` to find them.

| Name | Description |
|------|-------------|
| `GOOGLE_CREDENTIALS_BASE64` | The long base64 string for credentials.json |
| `GOOGLE_TOKEN_BASE64` | The long base64 string for token.json |
| `MCP_API_KEY` | Your desired API password |
| `VERCEL` | Set to `1` (Usually automatic, but good to be safe) |

## Step 4: Deploy
Click **Deploy**.

## Step 5: Connect ChatGPT
1. Copy the Vercel deployment URL (e.g., `https://instantprod-proposal-gen.vercel.app`).
2. Go to your GPT Actions.
3. Import schema from `https://<YOUR-VERCEL-URL>/openapi.json`.
4. Update Auth to use `X-API-Key`.

✅ **That's it!** Your MCP server is now running on Vercel.
