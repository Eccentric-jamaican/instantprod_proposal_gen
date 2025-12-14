import os
import sys
import shutil
import subprocess
from pathlib import Path
import click

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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

    # Add optional IDs if present (needed specific team context)
    # params = {}
    # if os.environ.get('VERCEL_TEAM_ID'):
    #     params['teamId'] = os.environ.get('VERCEL_TEAM_ID')

    print(f"Deploying {project_name} to Vercel API...")
    
    try:
        import requests
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"[FAIL] API Error {response.status_code}: {response.text}")
            return 1
            
        data = response.json()
        deploy_url = f"https://{data['url']}" # The preview URL
        
        # Check alias/production
        # For instantprod, the random URL is usually fine, or we can look at alias
        # but instant deployment returns the deployment url immediately
        
        print("\n" + "="*50)
        print(f"[OK] DEPLOY SUCCESS: {deploy_url}")
        print("="*50)
        
        # Save URL for other tools
        # Use /tmp on Vercel
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
