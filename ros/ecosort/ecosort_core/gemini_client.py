import base64
import json
import os

import requests

DEFAULT_MODEL = "gemini-3.1-flash-lite"


def _image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _generate_with_sdk(api_key, model_name, image_path, prompt):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    uploaded_image = client.files.upload(file=image_path)
    response = client.models.generate_content(
        model=model_name,
        contents=[uploaded_image, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    return response.text


def _generate_with_rest(api_key, model_name, image_path, prompt):
    image_b64 = _image_to_base64(image_path)
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + model_name
        + ":generateContent?key="
        + api_key
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_b64,
                        }
                    },
                    {"text": prompt},
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2,
        },
    }
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini REST API returned no candidates.")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError("Gemini REST API returned empty content.")
    return parts[0].get("text", "")


def generate_json_from_image(image_path, prompt, api_key=None, model_name=None):
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    model_name = model_name or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in environment or .env")

    try:
        text = _generate_with_sdk(api_key, model_name, image_path, prompt)
    except ImportError:
        text = _generate_with_rest(api_key, model_name, image_path, prompt)
    except Exception as sdk_error:
        print("[GEMINI] SDK failed, falling back to REST:", sdk_error)
        text = _generate_with_rest(api_key, model_name, image_path, prompt)

    data = json.loads(text)
    if isinstance(data, list):
        raise ValueError("Gemini returned a list instead of one JSON object.")
    return data
