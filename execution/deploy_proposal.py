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
@click.option('--client-slug', default='proposal', help='Client name for project (e.g. acme)')
def main(proposal: str, client_slug: str):
    """Deploy proposal to Vercel."""
    
    proposal_path = Path(proposal)
    project_name = f"proposal-{client_slug.lower().replace(' ', '-')}"[:50] # sanitize
    
    # 1. Prepare Deploy Directory
    # On Vercel (or any read-only env), use /tmp
    if os.environ.get("VERCEL"):
        deploy_root = Path("/tmp")
    else:
        deploy_root = PROJECT_ROOT

    deploy_dir = deploy_root / '.tmp' / 'deploy' / project_name
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Copy Proposal as index.html
    shutil.copy(proposal_path, deploy_dir / 'index.html')
    
    # 3. Create vercel.json configuration to force static handling and no directory listing
    vercel_config = '{"cleanUrls": true}'
    with open(deploy_dir / 'vercel.json', 'w') as f:
        f.write(vercel_config)
    
    print(f"Deploying {project_name} to Vercel...")
    
    # 4. Run Vercel
    # We use 'npx vercel --prod --yes' to deploy immediately to production without prompts
    # shell=True is CRITICAL on Windows to find npx.cmd
    try:
        # Check if logged in first (optional, but good UX)
        # subprocess.run(["npx", "vercel", "whoami"], shell=(os.name == 'nt'), check=False)

        cmd = [
            "npx", "-y", "vercel",
            "--prod",      # Production deployment
            "--yes",       # Skip confirmation prompts
            "--name", project_name, 
            "--cwd", str(deploy_dir) # Run in the deploy folder
        ]
        
        # Run command
        process = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=(os.name == 'nt'))
        
        # Extract URL from stdout (Vercel prints the url as the last line usually)
        output_lines = process.stdout.strip().split('\n')
        # Filter for url (simple heuristic: starts with https)
        deploy_url = next((line for line in reversed(output_lines) if line.startswith('https://')), None)
        
        if deploy_url:
            print("\n" + "="*50)
            print(f"[OK] DEPLOY SUCCESS: {deploy_url}")
            print("="*50)
            
            # Save the URL
            with open(deploy_root / '.tmp' / 'last_deployment_url.txt', 'w') as f:
                f.write(deploy_url)
        else:
            print("[INFO] Deploy completed but couldn't parse URL. Output below:")
            print(process.stdout)
            
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Deploy Failed. Error Code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
        print("\nNOTE: You may need to login first. Run: 'npx vercel login'")
        return 1

    return 0

if __name__ == '__main__':
    main()
