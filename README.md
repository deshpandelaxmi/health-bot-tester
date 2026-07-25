# Health Bot Tester

An automated QA framework for testing a healthcare voice bot built on Vapi. It places outbound test calls simulating different patient scenarios, saves the transcripts and recordings, then runs them through Gemini to score each conversation.

---

## How it works

The system has two stages.

**Stage 1 - `make_call.py`** triggers outbound calls via Vapi's phone call API, one per scenario. Each call injects a per-scenario opening line and a corrective system prompt via `assistantOverrides`. The script polls the Vapi call status endpoint every 10 seconds until the call ends, then pulls the message log and saves it as a transcript. Audio is downloaded from Vapi's presigned mono recording URL.

I used status polling rather than webhooks to keep the setup self-contained. No public endpoint required, no ngrok, no infra. The tradeoff is a ~10s lag before the transcript is captured after a call ends, which is fine for an offline QA run.

For the caller model, I used a single Vapi assistant with per-call `assistantOverrides` rather than provisioning 10 separate assistant IDs. This keeps credential management simple but means any static persona baked into the base assistant config on the Vapi dashboard can partially override the injected prompt after turn 1. That turned out to be a real issue. See Bug 2 in `BUG_REPORT.md`.

**Stage 2 - `evaluate_transcripts.py`** reads each saved transcript and sends it to Gemini (`gemini-3.5-flash`) for scoring across four criteria: accuracy, workflow adherence, safety guardrails, and professionalism. Results are written to `evaluation_report.json`. Gemini was the right call here over GPT-4o for this task since it's cheaper at scale and the structured JSON output via `response_mime_type` is cleaner to parse without postprocessing.

---

## Project structure

```
make_call.py           # Places outbound calls, monitors status, saves transcripts + audio
evaluate_transcripts.py  # Scores saved transcripts with Gemini, outputs evaluation_report.json
requirements.txt       # Python dependencies
.env.example           # Required environment variable template
BUG_REPORT.md          # Issues found across the 10 test calls
evaluation_report.json # Per-transcript scores and feedback
transcripts/           # transcript_1.txt through transcript_10.txt
recordings/            # recording_1.mp3 through recording_10.mp3
```

---

## Setup

Clone the repo and install dependencies:

```bash
git clone <your-repo-url>
cd health-bot-tester
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```env
VAPI_API_KEY="your-vapi-api-key"
ASSISTANT_ID="your-vapi-assistant-id"
GEMINI_API_KEY="your-gemini-api-key"
```

---

## Running the test suite

**Step 1 - Place the calls:**

```bash
python3 make_call.py
```

This runs through all 10 scenarios interactively. Press Enter to trigger each call, or type `exit` to stop early. Transcripts are saved to `transcripts/` and recordings to `recordings/` automatically once each call ends.

**Step 2 - Evaluate the transcripts:**

```bash
python3 evaluate_transcripts.py
```

Scores all transcripts in `transcripts/` and writes results to `evaluation_report.json`.

---

## Results summary

9 of 10 calls failed. The dominant issues were an identity verification loop that prevented callers from getting answers to simple policy questions, and a persona collapse where the Vapi assistant's base dashboard config overrode the per-call prompts after turn 1, effectively collapsing 9 different scenarios into the same insurance verification flow. Full details and transcript citations in `BUG_REPORT.md`.
