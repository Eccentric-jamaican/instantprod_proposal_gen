# Send Proposal for Signature

## Goal
Send the generated HTML proposal to the client in a way that ensures they can open it, sign it, and return a legally binding PDF copy.

## The Challenge
- HTML files contain code, so email providers like Gmail often block them as attachments.
- The signature pad is interactive; it must be signed in a browser *before* becoming a PDF.

## The Workflow

1.  **Package**: Zip the generated HTML file.
2.  **Send**: Email the ZIP file to the client.
3.  **Sign**: Client opens HTML, signs, and "Prints to PDF".
4.  **Return**: Client replies with the signed PDF.

## Instructions for the Client
*Include this text in your email so they know exactly what to do.*

> **Subject**: Proposal for {{CLIENT_NAME}} - Review & Signature Required
>
> Hi {{FIRST_NAME}},
>
> Please find our proposal attached. This is an interactive digital document designed to be viewed in your web browser.
>
> **Instructions to Sign:**
> 1. **Download** and unzip the attached file.
> 2. **Double-click** the `.html` file to open it in your browser (Chrome/Safari/Edge).
> 3. Scroll to the bottom and **draw your signature** in the box.
> 4. Click the **"Download as PDF"** button (or press Ctrl+P).
> 5. **Save** the PDF to your computer.
> 6. **Reply** to this email and attach the signed PDF.
>
> Let me know if you have any questions!
>
> Best,
> {{YOUR_NAME}}

## Automation

### 1. Hosted Workflow (Recommended)
This method deploys the proposal to Vercel and emails a shareable link. No unzipping required.

1.  **Deploy**:
    ```bash
    python execution/deploy_proposal.py --proposal .tmp/proposals/client.html --client-slug client-name
    ```
2.  **Send Email**:
    ```bash
    python execution/send_email.py \
      --to "client@example.com" \
      --subject "Proposal" \
      --body "View online" \
      --client-name "Client Name" \
      --link "https://..."
    ```

#### Notes
- The email uses an HTML template by default (`email_template.html`).
- The CTA button text is controlled by the template placeholder `{{BUTTON_TEXT}}`.

### 2. Attachment Workflow (Legacy)
Use this if the client requires a physical file.

```bash
python execution/send_email.py \
  --to "client@example.com" \
  --subject "Proposal" \
  --body "View attached" \
  --attachment .tmp/proposals/client.zip \
  --client-name "Client Name"
```

### Features
*   **HTML Template**: Automatically loads `email_template.html`.
*   **Branding**: Uses your hosted logo URL.
*   **Smart Content**: Automatically switches between "Click to View" (Link) and "Download" (Attachment) instructions.

## Plain Text Email (Utility)
Use this for normal emails that should NOT use the HTML template.

### Send (CLI)
```bash
python execution/send_email.py \
  --to "client@example.com" \
  --subject "Quick follow-up" \
  --body "Hey — quick follow up on our last message." \
  --plain
```

### Optional Attachment (CLI)
```bash
python execution/send_email.py \
  --to "client@example.com" \
  --subject "File attached" \
  --body "See attached." \
  --attachment .tmp/some_file.pdf \
  --plain
```

## Trello Board Invite Email
Use this when you want to invite the client into their Trello board with branded email.

### Send (CLI)
```bash
python execution/send_email.py \
  --to "client@example.com" \
  --subject "Your Trello Board - InstantProd" \
  --body "Your Trello board is ready" \
  --client-name "Client Name" \
  --link "https://trello.com/invite/..." \
  --template trello_invite_email_template.html \
  --button-text "ACCESS YOUR BOARD" \
  --instruction-text "Click the button below to access your Trello board."
```
