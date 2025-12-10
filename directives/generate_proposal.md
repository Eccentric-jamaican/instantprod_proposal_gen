# Generate Proposal from HTML Template

## Goal
Generate a customized HTML proposal for a client by populating the `proposal_template.html` with client-specific data, then optionally convert to PDF.

## Proposal Structure (Nick-style)
The proposal follows this section flow:
1. **Cover** — Title: "Website proposal for [Client Name]", date, prepared by
2. **Your Goals** — Dynamic list of client goals (3–10+ items from transcript)
3. **Problem Factors** — 4 specific problem factors getting in the way
4. **My Pitch & Proposed Solutions** — Solution summary + 4 deliverables + timeline
5. **Terms & Monthly Subscription** — Pricing, bank details, notes
6. **Signature** — Digital signature pad with smooth Bezier curves

## Inputs
- **Client Data**: JSON containing all placeholder values (see below)
- **Logo Image**: Path to logo image (will be embedded as data URI)
- **Hero Image** (optional): Path to hero image for the proposal header
- **Output Path**: Where to save the generated proposal

### Required Client Data Fields

> **Note:** `date`, `prepared_by`, and `website` are set by the backend, NOT the LLM.

```json
{
  // Header (only client_name from LLM; rest handled by backend)
  "client_name": "Acme Corp",
  
  // Goals Section (dynamic, 3–10+ items)
  "goals": [
    "Have a modern, responsive website",
    "Generate more leads from local search",
    "Make it easy to contact from any device"
  ],
  
  // Problem Section (4 equal problem factors)
  "problem": "Brief summary of the client's main pain points...",
  "problem_point_1": "First specific problem factor...",
  "problem_point_2": "Second specific problem factor...",
  "problem_point_3": "Third specific problem factor...",
  "problem_point_4": "Fourth specific problem factor...",
  
  // Solution Section
  "solution": "How we solve their problem...",
  "deliverables": "1. Responsive website<br>2. Lead capture forms<br>3. SEO basics<br>4. Mobile optimization",
  "timeline": "2-3 weeks",
  
  // Why Us
  "why_us": [
    {"title": "Speed", "body": "We deliver in days, not months."},
    {"title": "Quality", "body": "Premium design at agency level."}
  ],
  
  // Process Steps (exactly 3)
  "process_steps": [
    {"num": "01", "title": "Discovery", "what": "...", "why": "..."},
    {"num": "02", "title": "Design", "what": "...", "why": "..."},
    {"num": "03", "title": "Delivery", "what": "...", "why": "..."}
  ],
  
  // Investment (use plan strings, not raw amounts)
  "investment": "Starter subscription - flat monthly plan",
  "bank_details": "Scotiabank<br>Name: Addis Ellis<br>Account: ...",
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

### Investment Plan Strings
The `investment` field should be one of:
- `"Starter subscription - flat monthly plan"` → JMD 85,000/mo
- `"Growth subscription - flat monthly plan"` → JMD 240,000/mo
- `"Strategic Partner subscription - flat monthly plan"` → JMD 650,000/mo
- `"Flat monthly subscription - plan to be confirmed"` (fallback)

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
