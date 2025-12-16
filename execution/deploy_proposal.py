import os
import sys
import shutil
import subprocess
import time
import random
from pathlib import Path
import click
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(override=True)

@click.command()
@click.option('--proposal', required=True, type=click.Path(exists=True), help='Path to HTML proposal file')
@click.option('--client-slug', default='proposal', help='Client name for project')
def main(proposal: str, client_slug: str):
    """Deploy proposal to Vercel via REST API (No CLI required)."""
    
    # 1. Configuration
    token = os.environ.get('VERCEL_TOKEN')
    if not token:
        print("[FAIL] VERCEL_TOKEN environment variable is required.")
        return 1

    # Project setup
    project_name = f"proposal-{client_slug.lower().replace(' ', '-')}"[:50]
    proposal_path = Path(proposal)
    
    # Read HTML content
    with open(proposal_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 2. Construct API Payload
    # Vercel API v13 allows direct file structure
    url = "https://api.vercel.com/v13/deployments"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": project_name,
        "public": True,
        "target": "production",
        "alias": [],
        "files": [
            {
                "file": "index.html",
                "data": html_content,
                "encoding": "utf-8"
            },
            {
                "file": "vercel.json",
                "data": '{"cleanUrls": true}',
                "encoding": "utf-8"
            }
        ],
        "projectSettings": {
            "framework": None
        }
    }

    params = {}
    team_id = os.environ.get('VERCEL_TEAM_ID')
    team_slug = os.environ.get('VERCEL_TEAM_SLUG')
    if team_id:
        params['teamId'] = team_id
    if team_slug:
        params['slug'] = team_slug

    if team_slug:
        payload['alias'] = [f"{project_name}-{team_slug}.vercel.app"]
    else:
        payload['alias'] = [f"{project_name}.vercel.app"]

    if team_slug or team_id:
        scope_bits = []
        if team_slug:
            scope_bits.append(f"slug={team_slug}")
        if team_id:
            scope_bits.append(f"teamId={team_id}")
        print(f"Deploy scope: team ({', '.join(scope_bits)})")
    else:
        print("Deploy scope: personal (no VERCEL_TEAM_SLUG / VERCEL_TEAM_ID set)")

    print(f"Deploying {project_name} to Vercel API...")
    
    try:
        import requests
        max_attempts = int(os.environ.get("VERCEL_DEPLOY_MAX_ATTEMPTS", "4"))
        connect_timeout = float(os.environ.get("VERCEL_DEPLOY_CONNECT_TIMEOUT", "10"))
        read_timeout = float(os.environ.get("VERCEL_DEPLOY_READ_TIMEOUT", "120"))
        timeout = (connect_timeout, read_timeout)
        backoff_base = float(os.environ.get("VERCEL_DEPLOY_BACKOFF_BASE", "1"))

        attempt = 1
        response = None
        last_error = None
        while attempt <= max_attempts:
            try:
                response = requests.post(
                    url,
                    params=params if params else None,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                )
                if response.status_code == 200:
                    last_error = None
                    break

                if response.status_code not in (408, 429) and not (500 <= response.status_code <= 599):
                    print(f"[FAIL] API Error {response.status_code}: {response.text}")
                    return 1

                last_error = f"HTTP {response.status_code}: {response.text}"
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = str(e)

            if attempt >= max_attempts:
                break

            sleep_s = backoff_base * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
            print(f"[WARN] Deploy attempt {attempt} failed ({last_error}). Retrying in {sleep_s:.2f}s...")
            time.sleep(sleep_s)
            attempt += 1

        if last_error:
            status_part = f" (status={response.status_code})" if response is not None else ""
            print(f"[FAIL] Deployment request failed after {max_attempts} attempts{status_part}: {last_error}")
            return 1
        
        data = response.json()
        alias_final = data.get('aliasFinal')
        aliases = data.get('alias') or []
        deploy_url = (
            f"https://{alias_final}"
            if alias_final
            else (f"https://{aliases[0]}" if len(aliases) > 0 else f"https://{data['url']}")
        )
        
        print("\n" + "="*50)
        print(f"[OK] DEPLOY SUCCESS: {deploy_url}")
        print("="*50)
        
        if os.environ.get("VERCEL"):
            tmp = Path("/tmp")
        else:
            tmp = PROJECT_ROOT
            
        save_dir = tmp / '.tmp'
        save_dir.mkdir(parents=True, exist_ok=True)
            
        with open(save_dir / 'last_deployment_url.txt', 'w') as f:
            f.write(deploy_url)
            
    except ImportError:
        print("requests library missing. Please install requests.")
        return 1
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return 1

    return 0

if __name__ == '__main__':
    main()
