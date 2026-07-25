# 🐛 QA Defect Log & Conversational Failure Analysis

The following structured log captures the critical behavioral defects and conversational anomalies identified across the 10-call testing lifecycle of the Vapi healthcare voice assistant.

---

### 🚨 Defect 1: Turn-Taking Race Condition (Interruption Handling)
* **Severity:** High
* **Description:** When a user takes a brief breath or hesitates mid-sentence (common during stressful medical triage), the assistant prematurely cuts in, breaking the user's stream of speech. 
* **Impact:** Distorts context gathering. Important medical updates are clipped because the bot begins speaking over the patient.
* **Remediation:** Implementation of the **300 ms absolute max endpointing buffer** was required to balance fast responsiveness with patient conversational pacing.

---

### 🔄 Defect 2: Medical Records Intake Verification Loop
* **Severity:** Medium
* **Description:** During user confirmation of date of birth or policy numbers, the bot occasionally enters an infinite confirmation loop. Even after the user clearly states *"Yes, that is correct,"* the bot repeats the verification prompt.
* **Impact:** High user frustration; prevents the call from advancing to the actual clinical triage phase.
* **Remediation:** Refine the prompt guardrails to explicitly track state machine changes so confirmation phrases break the intake cycle cleanly.

---

### ⏳ Defect 3: Latency Spikes on Complex Multi-Turn Responses
* **Severity:** Medium
* **Description:** Whenever the patient asks a non-linear question (e.g., *"Wait, will my insurance cover this before you ask about my symptoms?"*), the assistant experiences a localized latency spike exceeding 1.8 seconds.
* **Impact:** Breaks conversational realism, causing the patient to think the call dropped or prompting them to say *"Hello?"*, which further confuses the LLM.
* **Remediation:** Implement a low-latency "thinking" token filler phrase or lean on a faster upstream model router for non-clinical workflow detours.