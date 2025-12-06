# Process Fireflies Transcript to Proposal

## Goal
Automate the extraction of structured proposal data (Problem, Solution, Pricing) from a Fireflies.ai meeting transcript using an LLM.

## Workflow

1.  **Retrieve Transcript**:
    *   Get the transcript text (via Fireflies API, Make.com webhook to Drive, or manual paste).
    *   Save as `.tmp/transcripts/client_name_transcript.txt`.

2.  **Analyze (The "Brain")**:
    *   Script: `execution/analyze_transcript.py`
    *   Action: Sends transcript to an LLM (OpenAI/Gemini).
    *   Prompt: "Extract client pain points, proposed solution, timeline, and budget into our specific JSON schema."

3.  **Generate Output**:
    *   Script saves `client_data.json`.

4.  **Create Proposal**:
    *   Run `generate_proposal.py` using this new JSON.

## Required JSON Structure
The LLM must output data matching our template fields:
- `problem`
- `problem_cost` (Infer if mentioned)
- `solution`
- `deliverables` (Bullet points)
- `investment` (Budget mentioned)
- `timeline`

## Setup
- Requires `OPENAI_API_KEY` or `GEMINI_API_KEY` in `.env`.
