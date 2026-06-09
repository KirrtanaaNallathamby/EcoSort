import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

print("API Key Found:", bool(api_key))

url = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + model
    + ":generateContent?key="
    + api_key
)
payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": (
                        "A plastic bottle contains some liquid. "
                        "Can it be recycled? Give a short explanation."
                    )
                }
            ]
        }
    ]
}
response = requests.post(url, json=payload, timeout=60)
response.raise_for_status()
text = response.json()["candidates"][0]["content"]["parts"][0]["text"]

print("\nGemini Response:")
print(text)