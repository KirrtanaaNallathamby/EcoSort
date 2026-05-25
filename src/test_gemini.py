import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("API Key Found:", bool(api_key))

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents="""
A plastic bottle contains some liquid.
Can it be recycled?
Give a short explanation.
"""
)

print("\nGemini Response:")
print(response.text)