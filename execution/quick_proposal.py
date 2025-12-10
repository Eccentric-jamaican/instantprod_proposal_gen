#!/usr/bin/env python3
"""
Quick Proposal Generator - All-in-one workflow.

Usage:
    python execution/quick_proposal.py

This script will:
1. Prompt for client name
2. Prompt for transcript (paste from Fireflies)
3. Analyze transcript with AI
4. Generate HTML proposal
5. Deploy to Vercel
6. Output the live URL
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
TRANSCRIPTS_DIR = PROJECT_ROOT / '.tmp' / 'transcripts'
PROPOSALS_DIR = PROJECT_ROOT / '.tmp' / 'proposals'

# Ensure directories exist
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:50]  # Limit length


def get_multiline_input(prompt: str) -> str:
    """Get multi-line input from user. End with empty line or Ctrl+Z (Windows)."""
    print(prompt)
    print("(Paste your transcript, then press Enter twice to finish)")
    print("-" * 50)
    
    lines = []
    empty_count = 0
    
    while True:
        try:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append(line)
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break
    
    return "\n".join(lines).strip()


def run_script(script_name: str, args: list) -> tuple[bool, str]:
    """Run a Python script and return success status and output."""
    cmd = [sys.executable, str(PROJECT_ROOT / 'execution' / script_name)] + args
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            shell=(os.name == 'nt')  # Windows compatibility
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except Exception as e:
        return False, str(e)


def main():
    print("\n" + "=" * 60)
    print("   INSTANTPROD QUICK PROPOSAL GENERATOR")
    print("=" * 60 + "\n")
    
    # Step 1: Get client name
    client_name = input("Client Name: ").strip()
    if not client_name:
        print("[ERROR] Client name is required.")
        return 1
    
    client_slug = slugify(client_name)
    date_str = datetime.now().strftime('%Y%m%d')
    
    # Step 2: Get transcript
    print()
    transcript = get_multiline_input("Paste Fireflies Transcript:")
    
    if len(transcript) < 50:
        print("[ERROR] Transcript seems too short. Please paste the full call.")
        return 1
    
    # Step 3: Save transcript
    transcript_file = TRANSCRIPTS_DIR / f"{client_slug}_{date_str}.txt"
    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(transcript)
    print(f"\n[OK] Saved transcript: {transcript_file.name}")
    
    # Step 4: Analyze with AI
    print("\n[...] Analyzing transcript with AI...")
    success, output = run_script('analyze_transcript.py', [
        '--transcript', str(transcript_file)
    ])
    
    if not success:
        print(f"[ERROR] Analysis failed:\n{output}")
        return 1
    
    # The JSON file is saved next to the transcript as `<stem>_data.json`
    json_file = transcript_file.parent / f"{transcript_file.stem}_data.json"
    
    if not json_file.exists():
        print(f"[ERROR] Expected JSON not found: {json_file}")
        return 1
    
    print(f"[OK] AI analysis complete: {json_file.name}")
    
    # Step 5: Generate HTML proposal
    print("\n[...] Generating HTML proposal...")
    proposal_file = PROPOSALS_DIR / f"{client_slug}_{date_str}.html"
    
    success, output = run_script('generate_proposal.py', [
        '--client-data', str(json_file),
        '--output', str(proposal_file)
    ])
    
    if not success:
        print(f"[ERROR] Generation failed:\n{output}")
        return 1
    
    print(f"[OK] Proposal generated: {proposal_file.name}")
    
    # Step 6: Deploy to Vercel
    print("\n[...] Deploying to Vercel...")
    success, output = run_script('deploy_proposal.py', [
        '--proposal', str(proposal_file),
        '--client-slug', client_slug
    ])
    
    if not success:
        print(f"[ERROR] Deployment failed:\n{output}")
        return 1
    
    # Extract URL from output
    url_match = re.search(r'https://[^\s]+\.vercel\.app', output)
    if url_match:
        live_url = url_match.group(0)
    else:
        live_url = "(Check Vercel dashboard)"
    
    # Final output
    print("\n" + "=" * 60)
    print("   SUCCESS!")
    print("=" * 60)
    print(f"\n   Client:    {client_name}")
    print(f"   Proposal:  {proposal_file.name}")
    print(f"\n   LIVE URL:  {live_url}")
    print("\n" + "=" * 60)
    
    # Copy to clipboard (Windows)
    if os.name == 'nt':
        try:
            subprocess.run(['clip'], input=live_url.encode(), check=True)
            print("   (URL copied to clipboard!)")
        except:
            pass
    
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
