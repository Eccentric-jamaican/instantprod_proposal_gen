import os
import sys
import json
import click
from pathlib import Path
from dotenv import load_dotenv
import openai

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

SYSTEM_PROMPT = """
You are an expert sales engineer. Your goal is to extract structured data from a transcript to populate a high-design HTML proposal for Instantprod, a B2B subscription web design and development studio.

Business context (for consistency only; do not restate full legal text):
- Instantprod works with founders and small teams on a flat monthly subscription.
- Clients own their code, repos, and infrastructure; there is no vendor lock-in.
- Work is delivered on the client's stack as an independent contractor.
- Client and lead data is handled under our Privacy Policy and Data Processing terms; we do not sell personal data.

CRITICAL: You must output PURE JSON. No markdown. No `json` wrappers.

Guardrails for UI Integrity:
1. **Brevity is King**: The UI breaks if text is too long. Keep "problem" and "solution" to MAX 2 sentences.
2. **Exact Counts**: 
   - `goals`: Return at least 3 items and include all distinct goals mentioned in the transcript. There is no maximum, but keep each goal short.
   - `process_steps`: MUST have exactly 3 items.
   - `why_us`: MUST have exactly 2 items.
   - `invest_notes`: MUST have exactly 4 short bullet points.
3. **Cleaning**: Do NOT use markdown bolding (e.g. `**text**`). Use HTML `<strong>` if absolutely necessary, but prefer plain text.
4. **Defaults & Pricing**:
   - Never hallucinate numeric prices or budgets.
   - Always map the call to one flat monthly plan where possible by setting `investment` to **one** of:
       * "Starter subscription - flat monthly plan"
       * "Growth subscription - flat monthly plan"
       * "Strategic Partner subscription - flat monthly plan"
   - Use these heuristics:
       * Starter: small team, single brand, mainly marketing site or simple product site, light forms, no multi-portal or heavy integrations.
       * Growth: growing team or multiple stakeholders, ongoing backlog/experiments, multiple brands/seats, or recurring CRO/feature work on an existing product site.
       * Strategic Partner: complex build such as multi-portal or multi-tenant apps, enterprise RFPs, logistics/operations portals, significant back-end work, or multiple deep integrations (e.g. CRM/ERP, real-time tracking, vendor/carrier portals).
   - Only if the transcript is genuinely too ambiguous to decide, set `investment` to "Flat monthly subscription - plan to be confirmed".

SCHEMA & CONSTRAINTS (backend or other inputs will set `date`, `prepared_by`, and `website`; do NOT include those fields):
{
  "client_name": "Inferred Company Name",
  
  "goals": [
    "Short goal 1 (Max 12 words)",
    "Short goal 2 (Max 12 words)"
  ],
  
  "problem": "MAX 30 words. Core pain point summary.",
  "problem_point_1": "MAX 15 words. First specific problem factor.",
  "problem_point_2": "MAX 15 words. Second specific problem factor.",
  "problem_point_3": "MAX 15 words. Third specific problem factor.",
  "problem_point_4": "MAX 15 words. Fourth specific problem factor.",
  
  "solution": "MAX 30 words. High-level solution pitch.",
  "deliverables": "A single string with items separated by <br>. Example: '1. Dashboard<br>2. API Integration'. MAX 4 items.",
  "timeline": "MAX 5 words. E.g. '4 Weeks'.",
  
  "why_us": [
    {"title": "Constraint: Max 3 words", "body": "Constraint: Max 15 words"},
    {"title": "Constraint: Max 3 words", "body": "Constraint: Max 15 words"}
  ],
  
  "process_steps": [
    {"num": "01", "title": "Max 3 words", "what": "Max 5 words", "why": "Max 10 words"},
    {"num": "02", "title": "Max 3 words", "what": "Max 5 words", "why": "Max 10 words"},
    {"num": "03", "title": "Max 3 words", "what": "Max 5 words", "why": "Max 10 words"}
  ],
  
  "investment": "One of the plan strings above (Starter/Growth/Strategic Partner) or 'Flat monthly subscription - plan to be confirmed' (no numeric amounts).",
  "bank_details": "Scotiabank<br>Name: Addis Ellis<br>Account: 90175 000853932<br>Transit: 90175",
  "min_term_label": "Timeline",
  "min_term_value": "Duration",
  
  "invest_notes": [
    "Short note 1 (Max 10 words)",
    "Short note 2 (Max 10 words)",
    "Short note 3 (Max 10 words)",
    "Short note 4 (Max 10 words)"
  ],
  
  "signature_instruction": "Please sign below to execute this agreement."
}
"""

@click.command()
@click.option('--transcript', required=True, type=click.Path(exists=True), help='Path to transcript text file')
@click.option('--model', default='gpt-5-nano', help='OpenAI model to use')
@click.option('--output', default=None, help='Output JSON path')
def main(transcript, model, output):
    """Analyze transcript and generate proposal data JSON."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found in .env")
        return 1

    client = openai.OpenAI(api_key=api_key)
    
    transcript_path = Path(transcript)
    if not output:
        output = transcript_path.parent / f"{transcript_path.stem}_data.json"
        
    print(f"Reading transcript: {transcript_path}")
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()

    print(f"Analyzing with {model}...")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Here is the transcript:\n\n{transcript_text}"}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean markdown wrappers if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        data = json.loads(content)
        
        # Save JSON
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"[SUCCESS] Data extracted to: {output}")
        print("Next Step: Run 'python execution/generate_proposal.py --client-data ...'")
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        return 1

if __name__ == '__main__':
    main()
