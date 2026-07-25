import os
import requests
from dotenv import load_dotenv

# Load credentials from the .env file
load_dotenv()

API_KEY = os.getenv("VAPI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Vapi outbound calling API endpoint
url = "https://api.vapi.ai/call/phone"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# TODO: Replace the placeholder with your own phone number to test it!

payload = {
    "assistantId": ASSISTANT_ID,
    "assistantOverrides": {
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "endpointing": 300  # Set to the absolute maximum allowable limit
        }
    },
    "phoneNumberId": "7c11cea8-1c74-42a8-9763-fb8ce6aff698",
    "customer": {
        "number": "+18054398008"
    }
}

print("Triggering outbound voice call...")
response = requests.post(url, json=payload, headers=headers)

print(f"Status Code: {response.status_code}")
try:
    print("Response Data:", response.json())
except Exception:
    print("Response Text:", response.text)