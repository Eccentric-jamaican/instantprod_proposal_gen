#!/usr/bin/env python3
"""
Generate HTML proposals from template.

This script populates the proposal_template.html with client-specific data
and outputs a customized proposal ready for delivery.
"""

import os
import sys
import json
import base64
import html
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_FILE = PROJECT_ROOT / 'proposal_template.html'
HERO_IMAGE = PROJECT_ROOT / 'hero_image.jpg'
LOGO_FILE = PROJECT_ROOT / 'Dark-mode.svg'
TMP_DIR = PROJECT_ROOT / '.tmp'
PROPOSALS_DIR = TMP_DIR / 'proposals'


def encode_image_to_data_uri(image_path: Path) -> str:
    """
    Encode an image file to a base64 data URI.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Data URI string (e.g., "data:image/png;base64,...")
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Determine MIME type
    suffix = image_path.suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
    }
    
    mime_type = mime_types.get(suffix, 'image/png')
    
    # Read and encode
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    base64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:{mime_type};base64,{base64_data}"


def load_client_data(json_path: Path) -> Dict[str, Any]:
    """Load client data from a JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def escape_html(text: str) -> str:
    """Escape HTML special characters in text."""
    if not text:
        return ""
    return html.escape(str(text))


def build_placeholder_map(data: Dict[str, Any], logo_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Build a mapping of template placeholders to their values.
    
    Args:
        data: Client data dictionary
        logo_path: Optional path to logo image
        
    Returns:
        Dictionary mapping placeholder names to values
    """
    placeholders = {}
    
    # Header fields
    placeholders['COMPANY'] = escape_html(data.get('company', 'Company'))
    placeholders['CLIENT_NAME'] = escape_html(data.get('client_name', 'Client'))
    placeholders['WEBSITE'] = escape_html(data.get('website', ''))
    placeholders['PREPARED_BY'] = escape_html(data.get('prepared_by', 'InstantProd'))
    placeholders['DATE'] = escape_html(data.get('date', datetime.now().strftime('%B %d, %Y')))
    
    # Logo
    if logo_path and logo_path.exists():
        try:
            placeholders['LOGO_DATA_URI'] = encode_image_to_data_uri(logo_path)
        except Exception as e:
            print(f"[WARN] Could not encode logo: {e}")
            placeholders['LOGO_DATA_URI'] = ''
    else:
        placeholders['LOGO_DATA_URI'] = data.get('logo_data_uri', '')
    
    # Problem section
    placeholders['PROBLEM'] = escape_html(data.get('problem', ''))
    placeholders['PROBLEM_COST'] = escape_html(data.get('problem_cost', ''))
    placeholders['OPPORTUNITY'] = escape_html(data.get('opportunity', ''))
    placeholders['PROBLEM_POINT_3'] = escape_html(data.get('problem_point_3', ''))
    placeholders['PROBLEM_POINT_4'] = escape_html(data.get('problem_point_4', ''))
    
    # Solution section
    placeholders['SOLUTION'] = escape_html(data.get('solution', ''))
    deliverables_raw = str(data.get('deliverables', ''))
    placeholders['DELIVERABLES'] = deliverables_raw
    deliverables_items = [
        re.sub(r'^\d+[).\-\s]*', '', item).strip()
        for item in re.split(r'<br\s*/?>', deliverables_raw)
        if item and item.strip()
    ]

    for idx in range(4):
        placeholders[f'SOLUTION_POINT_{idx + 1}'] = (
            deliverables_items[idx] if idx < len(deliverables_items) else ''
        )

    placeholders['TIMELINE'] = escape_html(data.get('timeline', ''))
    
    # Why Us section
    why_us = data.get('why_us', [])
    if len(why_us) >= 1:
        placeholders['WHY_US_TITLE_1'] = escape_html(why_us[0].get('title', ''))
        placeholders['WHY_US_BODY_1'] = escape_html(why_us[0].get('body', ''))
    else:
        placeholders['WHY_US_TITLE_1'] = ''
        placeholders['WHY_US_BODY_1'] = ''
    
    if len(why_us) >= 2:
        placeholders['WHY_US_TITLE_2'] = escape_html(why_us[1].get('title', ''))
        placeholders['WHY_US_BODY_2'] = escape_html(why_us[1].get('body', ''))
    else:
        placeholders['WHY_US_TITLE_2'] = ''
        placeholders['WHY_US_BODY_2'] = ''
    
    # Process steps
    process_steps = data.get('process_steps', [])
    for i in range(3):
        step_num = i + 1
        if i < len(process_steps):
            step = process_steps[i]
            placeholders[f'STEP_{step_num}_NUM'] = escape_html(step.get('num', f'0{step_num}'))
            placeholders[f'STEP_{step_num}_TITLE'] = escape_html(step.get('title', ''))
            placeholders[f'STEP_{step_num}_WHAT'] = escape_html(step.get('what', ''))
            placeholders[f'STEP_{step_num}_WHY'] = escape_html(step.get('why', ''))
        else:
            placeholders[f'STEP_{step_num}_NUM'] = f'0{step_num}'
            placeholders[f'STEP_{step_num}_TITLE'] = ''
            placeholders[f'STEP_{step_num}_WHAT'] = ''
            placeholders[f'STEP_{step_num}_WHY'] = ''
    
    # Investment section
    investment_raw = str(data.get('investment', '')).strip()
    plan_details = {
        "Starter subscription - flat monthly plan": ("Starter", "JMD 85,000 / month"),
        "Growth subscription - flat monthly plan": ("Growth", "JMD 240,000 / month"),
        "Strategic Partner subscription - flat monthly plan": ("Strategic Partner", "JMD 650,000 / month"),
        "Flat monthly subscription - plan to be confirmed": ("Flat monthly subscription - plan to be confirmed", ""),
    }
    plan_label, plan_price = plan_details.get(investment_raw, (investment_raw, ""))
    placeholders['INVESTMENT'] = escape_html(investment_raw)
    placeholders['INVESTMENT_PLAN'] = escape_html(plan_label)
    placeholders['INVESTMENT_PRICE'] = escape_html(plan_price)
    # Don't escape - intentionally contains HTML like <br>
    placeholders['BANK_DETAILS'] = str(data.get('bank_details', ''))
    placeholders['MIN_TERM_LABEL'] = escape_html(data.get('min_term_label', 'Minimum Term'))
    placeholders['MIN_TERM_VALUE'] = escape_html(data.get('min_term_value', ''))
    
    # Investment notes
    invest_notes = data.get('invest_notes', [])
    for i in range(4):
        if i < len(invest_notes):
            # Don't escape HTML here to allow formatting tags like <strong>
            placeholders[f'INVEST_NOTE_{i+1}'] = str(invest_notes[i])
        else:
            placeholders[f'INVEST_NOTE_{i+1}'] = ''
    
    # Signature
    placeholders['SIGNATURE_INSTRUCTION'] = escape_html(
        data.get('signature_instruction', 'Please sign below to accept this proposal.')
    )
    
    return placeholders


def generate_proposal(
    template_path: Path,
    placeholders: Dict[str, str],
    output_path: Path,
    hero_image_path: Optional[Path] = None
) -> Path:
    """
    Generate a proposal by replacing placeholders in the template.
    
    Args:
        template_path: Path to the HTML template
        placeholders: Dictionary of placeholder values
        output_path: Path to save the generated proposal
        hero_image_path: Optional path to hero image (will be embedded as data URI)
        
    Returns:
        Path to the generated proposal file
    """
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Replace placeholders
    result = template_content
    replaced_count = 0
    missing = []
    
    for key, value in placeholders.items():
        placeholder = f'{{{{{key}}}}}'
        if placeholder in result:
            result = result.replace(placeholder, value)
            replaced_count += 1
    
    # Embed hero image as data URI for portability
    if hero_image_path and hero_image_path.exists():
        try:
            hero_data_uri = encode_image_to_data_uri(hero_image_path)
            # Replace the CSS background-image reference
            result = result.replace("url('./hero_image.jpg')", f"url('{hero_data_uri}')")
            print(f"[OK] Embedded hero image: {hero_image_path.name}")
        except Exception as e:
            print(f"[WARN] Could not embed hero image: {e}")
    
    # Check for any remaining placeholders
    remaining = re.findall(r'\{\{([A-Z_0-9]+)\}\}', result)
    if remaining:
        print(f"[WARN] Unreplaced placeholders: {remaining}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"[OK] Generated proposal: {output_path}")
    print(f"     Replaced {replaced_count} placeholders")
    
    return output_path


@click.command()
@click.option('--client-data', '-d', type=click.Path(exists=True), 
              help='Path to JSON file with client data')
@click.option('--logo', '-l', type=click.Path(exists=True),
              help='Path to logo image (default: Dark-mode.svg)')
@click.option('--hero', '-h', type=click.Path(exists=True),
              help='Path to hero image (default: hero_image.jpg)')
@click.option('--output', '-o', type=click.Path(),
              help='Output path for generated proposal')
@click.option('--client-name', help='Client name (if not using JSON)')
@click.option('--company', default='InstantProd', help='Your company name')
@click.option('--website', help='Client website')
@click.option('--open-browser', is_flag=True, help='Open the proposal in browser after generating')
def main(
    client_data: Optional[str],
    logo: Optional[str],
    hero: Optional[str],
    output: Optional[str],
    client_name: Optional[str],
    company: str,
    website: Optional[str],
    open_browser: bool
):
    """
    Generate an HTML proposal from the template.
    
    Either provide a --client-data JSON file, or use individual options
    like --client-name, --website, etc.
    
    Default logo: Dark-mode.svg
    Default hero: hero_image.jpg
    """
    # Load client data
    if client_data:
        data = load_client_data(Path(client_data))
    else:
        # Build minimal data from CLI options
        data = {
            'company': company,
            'client_name': client_name or 'Client',
            'website': website or '',
            'date': datetime.now().strftime('%B %d, %Y'),
        }
    
    # Set up logo path (use default if not specified)
    if logo:
        logo_path = Path(logo)
    elif LOGO_FILE.exists():
        logo_path = LOGO_FILE
        print(f"[OK] Using default logo: {LOGO_FILE.name}")
    else:
        logo_path = None
    
    # Set up hero image path (use default if not specified)
    if hero:
        hero_path = Path(hero)
    elif HERO_IMAGE.exists():
        hero_path = HERO_IMAGE
        print(f"[OK] Using default hero: {HERO_IMAGE.name}")
    else:
        hero_path = None
    
    # Build placeholders
    placeholders = build_placeholder_map(data, logo_path)
    
    # Determine output path
    if output:
        output_path = Path(output)
    else:
        # Generate a filename based on client name
        safe_name = re.sub(r'[^\w\-]', '_', data.get('client_name', 'client').lower())
        date_str = datetime.now().strftime('%Y%m%d')
        output_path = PROPOSALS_DIR / f'{safe_name}_{date_str}.html'
    
    # Generate the proposal
    result_path = generate_proposal(TEMPLATE_FILE, placeholders, output_path, hero_path)
    
    # Open in browser if requested
    if open_browser:
        import webbrowser
        webbrowser.open(f'file://{result_path.absolute()}')
        print("[OK] Opened in browser")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

