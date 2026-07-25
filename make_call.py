import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("VAPI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

CALL_URL = "https://api.vapi.ai/call/phone"
STATUS_URL = "https://api.vapi.ai/call"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# These overrides push corrected behavior rules into the assistant at call time.
# They're meant to counteract a static persona baked into the Vapi dashboard config
# (the "Maya Lin / Blue Shield PPO" persona that collapses 9/10 scenarios).
# Note: if the Vapi assistant's base config hasn't been cleared on the dashboard side,
# these overrides may still be partially overridden at turn 2+. See BUG_REPORT.md Bug 2.
ASSISTANT_SYSTEM_PROMPT = """
You are a helpful Voice AI Quality Assurance assistant for a healthcare clinic system.

CRITICAL BEHAVIOR RULES:
1. ANSWER GENERAL QUESTIONS FIRST: If the patient asks a general question (such as whether the clinic accepts Blue Shield PPO, office hours, or general policies), answer their question IMMEDIATELY. Do NOT force them to provide their Name, Date of Birth, or look up their record before answering standard questions.
2. NEW PATIENTS: If the caller explicitly states they are a new patient or does not have an existing record, acknowledge this immediately and stop searching for an existing account.
3. VERIFICATION SCOPE: Only request identification details (Name, DOB) if the patient explicitly wants to schedule an appointment, access personal health records, or process billing details.
4. GRACEFUL TRANSFERS: If you need to transfer the patient or escalate to human support, explicitly announce: "I am connecting you with our patient support team now. Please hold for just a moment." Never end the call abruptly.
"""

SCENARIOS = [
    {
        "name": "Insurance Verification (Blue Shield PPO)",
        "first_message": "Hello! I am a new patient switching to a Blue Shield PPO plan next month, and I wanted to check if your clinic accepts it?"
    },
    {
        "name": "Appointment Scheduling",
        "first_message": "Hi, I've been having a persistent cough for three days and I'd like to schedule an appointment with a doctor this week."
    },
    {
        "name": "Prescription Refill Request",
        "first_message": "Hello, I am calling to request a prescription refill for my blood pressure medication. Can someone help me with that?"
    },
    {
        "name": "Clinic Hours and Location",
        "first_message": "Hi there! Could you tell me your weekend clinic hours and whether walk-in visits are allowed?"
    },
    {
        "name": "Billing & Payment Inquiry",
        "first_message": "Hello, I received a bill in the mail for my recent visit, and I have a question about one of the charges."
    },
    {
        "name": "Specialist Referral Request",
        "first_message": "Hi, my primary doctor suggested I see a dermatologist. Do I need a formal referral from your clinic first?"
    },
    {
        "name": "Lab Results Status",
        "first_message": "Hello! I had blood work done last Tuesday and was calling to see if my lab results are available yet?"
    },
    {
        "name": "After-Hours & Emergency Policy",
        "first_message": "Hi, I wanted to know what the process is if I have an urgent medical issue outside of normal office hours?"
    },
    {
        "name": "New Patient Intake & Registration",
        "first_message": "Hello! I just moved to the area and would like to register as a new patient at your practice. What forms do I need?"
    },
    {
        "name": "Post-Visit Follow-Up Consultation",
        "first_message": "Hi, I was seen by the doctor two days ago for flu symptoms and wanted to leave a quick update for the nurse."
    }
]


def monitor_and_save_call(call_id, file_index):
    """Poll call status every 10s and save transcript + recording once the call ends."""
    print(f"Monitoring call {call_id}...")

    while True:
        time.sleep(10)
        res = requests.get(f"{STATUS_URL}/{call_id}", headers={"Authorization": f"Bearer {API_KEY}"})

        if res.status_code == 200:
            call_data = res.json()
            status = call_data.get("status")
            print(f"   Status: {status}")

            if status in ["ended", "completed", "failed"]:
                messages = call_data.get("messages", [])
                filename = f"transcripts/transcript_{file_index}.txt"
                os.makedirs("transcripts", exist_ok=True)

                with open(filename, "w") as f:
                    if not messages:
                        f.write("No dialogue transcript found for this call.\n")
                    for msg in messages:
                        role = msg.get("role")
                        text = msg.get("message") or msg.get("content") or msg.get("originalMessage")
                        # Skip system-role messages; they're not part of the spoken dialogue
                        if role and role != "system" and text and text.strip():
                            speaker = "Bot" if role == "assistant" else "Patient"
                            f.write(f"{speaker}: {text.strip()}\n")

                print(f"Transcript saved: {filename}")

                # Download the mono recording from Vapi's presigned URL
                artifact = call_data.get("artifact", {})
                rec_url = artifact.get("presignedMonoUrl") or call_data.get("recordingUrl")
                if rec_url:
                    audio_res = requests.get(rec_url, stream=True)
                    if audio_res.status_code == 200:
                        rec_filename = f"recordings/recording_{file_index}.mp3"
                        os.makedirs("recordings", exist_ok=True)
                        with open(rec_filename, "wb") as f:
                            for chunk in audio_res.iter_content(chunk_size=16384):
                                f.write(chunk)
                        print(f"Recording saved: {rec_filename}\n")
                break
        else:
            print(f"Error checking call status: {res.status_code}")
            break


if __name__ == "__main__":
    for i in range(1, 11):
        scenario = SCENARIOS[i - 1]
        print(f"\n--- Call {i}/10: {scenario['name']} ---")
        print(f"Opening line: \"{scenario['first_message']}\"")

        user_input = input(f"Press Enter to trigger call {i} (or type 'exit' to quit): ").strip().lower()
        if user_input == 'exit':
            print("Exiting.")
            break

        payload = {
            "assistantId": ASSISTANT_ID,
            "assistantOverrides": {
                "firstMessage": scenario["first_message"],
                "model": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "system",
                            "content": ASSISTANT_SYSTEM_PROMPT
                        }
                    ]
                },
                # 300ms endpointing, chosen as a middle ground between responsiveness and
                # giving callers time to finish a thought. May need bumping to 500-600ms
                # if barge-in on name-spelling turns out to be a consistent issue.
                "transcriber": {
                    "provider": "deepgram",
                    "model": "nova-2",
                    "endpointing": 300
                }
            },
            "phoneNumberId": "7c11cea8-1c74-42a8-9763-fb8ce6aff698",
            "customer": {
                "number": "+18054398008"
            }
        }

        print(f"Placing call {i}...")
        response = requests.post(CALL_URL, json=payload, headers=headers)

        if response.status_code in [200, 201]:
            call_info = response.json()
            call_id = call_info.get("id")
            print(f"Call placed successfully (ID: {call_id})")
            monitor_and_save_call(call_id, i)
        else:
            print(f"Failed to place call {i}. Status: {response.status_code}")
            print("Response:", response.text)

    print("\nAll 10 scenario calls completed.")
