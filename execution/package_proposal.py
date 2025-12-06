#!/usr/bin/env python3
"""
Package a proposal for sending.

1. Zips the HTML file (to bypass email filters)
2. Generates the email body text for the client
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
import click
# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Try to import from execution script to reuse logic if needed, 
# but mostly we just need file ops here.

def create_zip(html_path: Path) -> Path:
    """Create a zip file containing the proposal."""
    zip_path = html_path.with_suffix('.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # ARCNAME is the name inside the zip. We use just the filename.
        zf.write(html_path, arcname=html_path.name)
        
    return zip_path

def generate_email_text(client_name: str, filename: str) -> str:
    """Generate the email text template."""
    return f"""
=================================================================
             EMAIL TEMPLATE (Copy & Paste)
=================================================================

SUBJECT: Proposal for {client_name} - Review & Signature Required

Hi {client_name.split(' ')[0]},

Please find our proposal attached. This is an interactive digital document designed to be viewed in your web browser.

INSTRUCTIONS TO SIGN:
1. Download and unzip the attached file ({filename}).
2. Double-click the file to open it in your browser (Chrome/Safari/Edge).
3. Scroll to the bottom and draw your signature in the box.
4. Click the "Download as PDF" button.
5. Save the PDF to your computer.
6. Reply to this email with the signed PDF attached.

Let me know if you have any questions!

Best,
InstantProd Team
=================================================================
"""

@click.command()
@click.option('--proposal', '-p', required=True, type=click.Path(exists=True), 
              help='Path to the generated HTML proposal')
def main(proposal: str):
    """
    Package an HTML proposal for sending.
    
    Zips the file and prints the recommended email text.
    """
    html_path = Path(proposal)
    
    # 1. Create Zip
    print(f"Packaging {html_path.name}...")
    zip_path = create_zip(html_path)
    print(f"[OK] Created: {zip_path}")
    
    # 2. Extract Client Name from filename (rough guess) or prompt
    # Filename format is usually name_date.html
    # We'll just be generic or try to clean it up
    clean_name = html_path.stem.split('_20')[0].replace('_', ' ').title()
    
    # 3. Print Email Text
    email_text = generate_email_text(clean_name, zip_path.name)
    print(email_text)
    
    # 4. Open folder
    if sys.platform == 'win32':
        os.startfile(zip_path.parent)
    elif sys.platform == 'darwin':
        os.system(f'open "{zip_path.parent}"')
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
