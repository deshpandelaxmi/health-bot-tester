# Health Bot Tester - Automated Voice QA Framework

This repository contains an automated test runner designed to evaluate the conversational performance, latency, and guardrails of our automated healthcare voice bot built on Vapi.

## 🛠️ Project Structure
* `make_call.py` - The core Python script that dynamically triggers outbound test calls using the Vapi API.
* `requirements.txt` - Required external dependencies for network requests and environment variables.
* `.env.example` - Template showing the required configuration keys.
* `BUG_REPORT.md` - Structured QA bug tracking document detailing conversational edge cases and failures.
* `📁 transcripts/` - Contains raw text conversational logs from 10 unique test iterations.
* `📁 recordings/` - Contains downloaded call recordings (.mp3/.ogg) used for conversational rhythm analysis.

## 🚀 Setup & Installation

1. **Clone the repository and navigate to your workspace:**
   ```bash
   cd /Users/vikasdeshpande/health-bot-tester/