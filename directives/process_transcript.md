# Process Fireflies Transcript to Proposal

## Goal
Automate the extraction of structured proposal data (Goals, Problems, Solution, Pricing) from a Fireflies.ai meeting transcript using an LLM.

## Workflow

1.  **Retrieve Transcript**:
    *   Get the transcript text (via Fireflies API, Make.com webhook to Drive, or manual paste).
    *   Save as `.tmp/transcripts/client_name_transcript.txt`.

2.  **Analyze (The "Brain")**:
    *   Script: `execution/analyze_transcript.py`
    *   Action: Sends transcript to an LLM (OpenAI).
    *   Prompt: Extracts client goals, problem factors, solution, timeline, and investment plan into our JSON schema.

    *   Optional: Include research findings about the client alongside the transcript:
        *   `--additional-context "Client has no website, active on Instagram, focuses on local market..."`
        *   `--additional-context-path path/to/research_notes.txt`
        *   Use this when you've researched the client's online presence, website, social media, or industry insights

### Voice & POV Requirements (Important)
- The proposal copy should read as if **InstantProd is speaking directly to the business owner / decision maker**.
- Use **first-person plural** for InstantProd ("we", "our", "us") and **second-person** for the client ("you", "your").
- Avoid third-person narration (avoid "they" / "the client" / "InstantProd will").

3.  **Generate Output**:
    *   Script saves `<transcript_stem>_data.json` in the same folder.

4.  **Create Proposal**:
    *   Run `generate_proposal.py --client-data <path_to_json>`.

## Required JSON Structure (LLM Output)

> **Note:** The LLM does NOT set `date`, `prepared_by`, or `website` — these are handled by the backend.

The LLM must output:
- `client_name` — Inferred company name
- `goals` — Array of 3–10+ short goal statements (max 12 words each)
- `problem` — Core pain point summary (max 30 words)
- `problem_point_1` through `problem_point_4` — Four specific problem factors (max 15 words each)
- `solution` — High-level solution pitch (max 30 words)
- `deliverables` — String with items separated by `<br>` (max 4 items)
- `timeline` — E.g. "4 Weeks"
- `why_us` — Exactly 2 items: `[{title, body}, {title, body}]`
- `process_steps` — Exactly 3 items: `[{num, title, what, why}, ...]`
- `investment` — One of the plan strings:
  - `"Starter subscription - flat monthly plan"`
  - `"Growth subscription - flat monthly plan"`
  - `"Strategic Partner subscription - flat monthly plan"`
  - `"Flat monthly subscription - plan to be confirmed"` (fallback)
- `invest_notes` — Exactly 4 short bullet points

## Setup
- Requires `OPENAI_API_KEY` in `.env`.
- By default, `execution/analyze_transcript.py` uses the OpenAI `gpt-5-nano` model (override with `--model` if needed).

## Edge Cases & Learnings
- Do not hallucinate numeric pricing or budgets. Map the transcript to one of the flat monthly plan strings (or use the fallback plan when ambiguous).
- Keep text short (the HTML layout breaks if fields are too long). Follow the max word/sentence limits in the schema.

## Example Usage

```bash
# Analyze transcript
python execution/analyze_transcript.py --transcript .tmp/transcripts/acme.txt

# Analyze transcript with research findings
python execution/analyze_transcript.py --transcript .tmp/transcripts/acme.txt --additional-context "Client has no website, active on Instagram with 2k followers, targets local Jamaica market, competitors have outdated sites"

# Generate proposal from resulting JSON
python execution/generate_proposal.py --client-data .tmp/transcripts/acme_data.json --output .tmp/proposals/acme.html --open-browser
```
