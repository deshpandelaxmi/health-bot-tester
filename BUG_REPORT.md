# QA Defect Log

Bugs found across 10 automated test calls to the Vapi healthcare voice assistant. Timestamps are approximate, derived from call duration patterns, not embedded audio metadata.

---

### Bug 1: Identity Verification Infinite Loop

**Severity:** High  
**Transcripts:** [transcript_1.txt](transcripts/transcript_1.txt) (lines 6–15, ~0:45) and [transcript_3.txt](transcripts/transcript_3.txt) (lines 8–14, ~0:52)

The bot refuses to answer general policy questions until the caller has been fully verified, even when they're just asking something like "do you accept Blue Shield PPO?" In transcript_1, the caller provides their name and date of birth three separate times, gets it transcribed incorrectly each time ("Mya" instead of "Maya", "Lynn" instead of "Lin"), and still never gets an answer to their actual question. The bot's exact loop trigger: *"Let's confirm your details 1 more time. Please spell out your 1st and last name and confirm your date of birth."*

This is the most user-hostile failure in the set. A real patient hitting this loop would hang up within 90 seconds.

**Fix:** Gate identity verification on intent, not every call. General questions (hours, insurance network, location) should be answerable without a record lookup. Cap verification retries at 2 and fall back to "let me connect you with someone who can help" if it keeps failing.

---

### Bug 2: Scenario Persona Collapse

**Severity:** High  
**Transcripts:** [transcript_2.txt](transcripts/transcript_2.txt) (line 3, ~0:18), [transcript_4.txt](transcripts/transcript_4.txt) (line 3, ~0:15), [transcript_8.txt](transcripts/transcript_8.txt) (line 3, ~0:20)

9 out of 10 calls started with a distinct opening line -- persistent cough, billing question, new patient registration, etc. -- but by turn 2, the bot's persona had collapsed to the same response pattern: treating the caller as "Maya Lin" trying to verify Blue Shield PPO coverage. The `assistantOverrides` in `make_call.py` correctly inject a per-call system prompt, but the Vapi assistant I set up for this test suite has a static persona hardcoded in its base dashboard configuration that takes over after the first turn. To be clear: this is a bug in my test caller setup, not in the clinic bot being tested. The per-call overrides should have taken full precedence but didn't.

This is the single biggest issue with the test suite's effectiveness. In practice, I was only testing one scenario (insurance verification) 9 times instead of 10 different ones.

**Fix:** Clear the static persona from the assistant's base config in the Vapi dashboard so the per-call `assistantOverrides` can fully take hold. Alternatively, provision separate assistant IDs per scenario to eliminate the conflict entirely.

---

### Bug 3: Barge-In Cuts Off Name Spelling

**Severity:** Medium  
**Transcripts:** [transcript_5.txt](transcripts/transcript_5.txt) (lines 5–7, ~0:38) and [transcript_7.txt](transcripts/transcript_7.txt) (lines 9–11, ~0:44)

When callers spell their name letter-by-letter with natural pauses between letters, like "M... a... y... a", the bot's endpointing fires mid-sequence and interrupts them. This causes the STT to capture a partial name, leading to a mismatch that kicks off another verification round. It's a compounding problem: the barge-in creates the transcription error, which causes the loop in Bug 1.

The 300ms endpointing value in `make_call.py` works fine for normal speech but is too aggressive for spelled-out input with deliberate pauses.

**Fix:** Bump endpointing to 500-600ms. This is specifically a medical intake pattern (callers spelling names, reciting DOBs, reading policy numbers) and those all have longer natural pause cadences than conversational speech.

---

### Bug 4: Transfer Drops the Call

**Severity:** Medium  
**Transcripts:** [transcript_9.txt](transcripts/transcript_9.txt) (line 14, ~1:12) and [transcript_10.txt](transcripts/transcript_10.txt) (line 60, ~2:05)

When the bot hits a dead-end (couldn't verify identity, couldn't answer the question) it says it will connect the caller to support and then transfers to a line that immediately plays "Hello. You've reached the Pretty Good AI test line. Goodbye." The call ends with the patient's question completely unresolved. In transcript_1 the patient's literal last words are "Oh, wait." before the call drops.

This is partly a test environment issue (the transfer target is a dummy line), but the bot also doesn't announce the transfer or give the caller any warning before it happens.

**Fix:** Add an explicit hold announcement before any transfer: "I'm going to connect you with our patient support team now, please hold for just a moment." Also ensure the transfer destination in production routes to an active queue rather than a disconnected test endpoint.
