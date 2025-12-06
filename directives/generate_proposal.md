# Generate Proposal from HTML Template

## Goal
Generate a customized HTML proposal for a client by populating the `proposal_template.html` with client-specific data, then optionally convert to PDF.

## Inputs
- **Client Data**: JSON or dictionary containing all placeholder values
- **Logo Image**: Path to logo image (will be embedded as data URI)
- **Hero Image** (optional): Path to hero image for the proposal header
- **Output Path**: Where to save the generated proposal

### Required Client Data Fields

```json
{
  // Header
  "company": "InstantProd",
  "client_name": "Acme Corp",
  "website": "acmecorp.com",
  "prepared_by": "InstantProd",
  "date": "December 6, 2025",
  
  // Problem Section
  "problem": "Brief description of the client's main problem...",
  "problem_cost": "Description of what this problem is costing them...",
  "opportunity": "What they're missing out on...",
  "problem_point_3": "Additional pain point...",
  "problem_point_4": "Another pain point...",
  
  // Solution Section
  "solution": "How we solve their problem...",
  "deliverables": "What they get: Website, Branding, etc.",
  "timeline": "2-3 weeks",
  
  // Why Us
  "why_us": [
    {"title": "Speed", "body": "We deliver in days, not months."},
    {"title": "Quality", "body": "Premium design at agency level."}
  ],
  
  // Process Steps
  "process_steps": [
    {"num": "01", "title": "Discovery", "what": "...", "why": "..."},
    {"num": "02", "title": "Design", "what": "...", "why": "..."},
    {"num": "03", "title": "Delivery", "what": "...", "why": "..."}
  ],
  
  // Investment
  "investment": "$2,500/mo",
  "bank_details": "Account details...",
  "min_term_label": "Minimum Term",
  "min_term_value": "3 months",
  "invest_notes": [
    "Note about payment terms...",
    "Note about what's included...",
    "Note about support...",
    "Note about cancellation..."
  ],
  
  // Signature
  "signature_instruction": "Please sign below to accept this proposal..."
}
```

## Tools/Scripts to Use
- `execution/generate_proposal.py` - Main script to generate proposals
- Logo image should be in the project root or specified path

## Process

1. **Load client data** from JSON file or direct input
2. **Load and encode logo** as base64 data URI
3. **Read HTML template** from `proposal_template.html`
4. **Replace all placeholders** with client data
5. **Save generated HTML** to output path
6. **Optionally convert to PDF** using browser print or wkhtmltopdf

## Outputs
- **Primary Output**: Generated HTML file in `.tmp/proposals/`
- **Optional**: PDF version of the proposal

## Edge Cases & Learnings
- **Missing placeholders**: Script should warn if any required fields are missing
- **Logo encoding**: Must be proper base64 data URI format
- **Special characters**: HTML-escape any user content to prevent XSS
- **Long content**: Some fields may overflow; consider character limits

## Example Usage

```bash
# Generate proposal from JSON file
python execution/generate_proposal.py \
  --client-data .tmp/client_acme.json \
  --logo assets/logo.png \
  --output .tmp/proposals/acme_proposal.html

# Generate with inline data
python execution/generate_proposal.py \
  --client-name "Acme Corp" \
  --website "acmecorp.com" \
  --output .tmp/proposals/acme_proposal.html
```

## Success Criteria
- [ ] HTML file generated with all placeholders replaced
- [ ] Logo properly embedded as data URI
- [ ] No broken placeholders (all `{{...}}` replaced)
- [ ] File opens correctly in browser
- [ ] PDF export works via browser print
