#!/usr/bin/env python3
"""
Send an email with attachment using the Gmail API.
"""

import os
import sys
import base64
import mimetypes
from pathlib import Path
from email.message import EmailMessage
from typing import Optional, List

import click
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import auth_helper

# Same scopes as test_google_auth.py
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
]

def get_gmail_service():
    """Get authenticated Gmail service."""
    
    # Restore credentials to standard paths (or /tmp)
    creds_path, token_path = auth_helper.restore_credentials() # This handles Vercel /tmp logic
    
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(f"credentials.json not found at {creds_path}")
            
            # Interactive flow (only works locally)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save refreshed token
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
    return build('gmail', 'v1', credentials=creds)

def create_message_with_attachment(
    sender: str,
    to: str,
    subject: str,
    message_text: str,
    attachment_path: Optional[Path] = None,
    html_content: Optional[str] = None,
    logo_path: Optional[Path] = None
):
    """Create an email message with an attachment and inline logo."""
    message = EmailMessage()
    message['To'] = to
    message['From'] = sender
    message['Subject'] = subject

    # Set the plain text body first
    message.set_content(message_text)

    # If HTML is provided, add it as an alternative
    if html_content:
        # We use 'related' to bundle HTML + Inline Images together
        message.add_alternative(html_content, subtype='html')
        
        # If logo is provided, attach it as an inline image to the HTML part
        if logo_path and logo_path.exists():
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                # Link the image to the 'cid:logo' in the HTML
                message.get_payload()[1].add_related(
                    logo_data, 
                    maintype='image', 
                    subtype='svg+xml', 
                    cid='<logo>'
                )

    # Attach the main file (proposal ZIP) if provided
    if attachment_path and attachment_path.exists():
        ctype, encoding = mimetypes.guess_type(attachment_path)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        
        maintype, subtype = ctype.split('/', 1)
        
        with open(attachment_path, 'rb') as f:
            file_data = f.read()
            message.add_attachment(
                file_data,
                maintype=maintype,
                subtype=subtype,
                filename=attachment_path.name
            )

    # Encode the message (base64url)
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': encoded_message}

def send_message(service, user_id, message):
    """Send an email message."""
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"[OK] Message Id: {message['id']}")
        return message
    except HttpError as error:
        print(f"[FAIL] An error occurred: {error}")
        return None

def render_template(template_path: Path, replacements: dict) -> str:
    """Load HTML template and replace placeholders."""
    if not template_path.exists():
        return ""
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for key, value in replacements.items():
        content = content.replace(f'{{{{{key}}}}}', str(value))
        
    return content

@click.command()
@click.option('--to', required=True, help='Recipient email address')
@click.option('--subject', required=True, help='Email subject')
@click.option('--body', required=True, help='Email body text (fallback)')
@click.option('--attachment', type=click.Path(exists=True), help='Path to attachment file')
@click.option('--client-name', default='Client', help='Client Name for HTML template')
@click.option('--logo', type=click.Path(exists=True), help='Path to logo file')
@click.option('--link', help='URL link to the proposal (replaces attachment)')
def main(to: str, subject: str, body: str, attachment: Optional[str], client_name: str, logo: Optional[str], link: Optional[str]):
    """Send an email via Gmail API with HTML template support."""
    try:
        print(f"Authenticating...")
        service = get_gmail_service()
        
        # Skip fetching profile to avoid scope issues.
        sender_email = 'me' 
        print(f"Sending as: Authenticated User")
        
        # Prepare HTML content
        template_file = PROJECT_ROOT / 'email_template.html'
        html_content = None
        if template_file.exists():
            print("Using HTML Email Template...")
            
            # Use provided link or fallback to '#' if likely sending an attachment
            if link:
                proposal_link = link
                instruction_text = "Click the button below to view and sign your proposal instantly."
            else:
                proposal_link = "#"
                instruction_text = "Please download the attached file to review your proposal."
            
            html_content = render_template(template_file, {
                'CLIENT_NAME': client_name,
                'FIRST_NAME': client_name.split(' ')[0],
                'PROPOSAL_LINK': proposal_link,
                'INSTRUCTION_TEXT': instruction_text
            })
        
        print(f"Preparing email to: {to}...")
        attachment_path = Path(attachment) if attachment else None
        
        # Determine logo path (CLI arg only)
        logo_path = Path(logo) if logo else None
        if logo_path:
            if not logo_path.exists():
                print(f"[WARN] Logo not found at {logo_path}, skipping inline attachment.")
                logo_path = None
            else:
                print(f"Attaching inline logo: {logo_path.name}")
        
        message = create_message_with_attachment(
            sender=sender_email,
            to=to,
            subject=subject,
            message_text=body,
            attachment_path=attachment_path,
            html_content=html_content,
            logo_path=logo_path
        )
        
        print("Sending...")
        send_message(service, 'me', message)
        print("[OK] Email sent successfully!")
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
