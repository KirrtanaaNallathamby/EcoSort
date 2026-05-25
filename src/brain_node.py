import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types


class BrainNode:
    def __init__(self):
        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY in .env")

        self.client = genai.Client(api_key=api_key)
        self.current_detection = None
        self.cached_analysis = None

    def receive_detection(self, detection):
        self.current_detection = detection
        self.cached_analysis = None

    def analyze_once_with_gemini(self):
        if self.cached_analysis:
            return self.cached_analysis

        if not self.current_detection:
            return None

        d = self.current_detection

        prompt = f"""
You are EcoSort AI, a recycling assistant robot.

YOLO detected:
YOLO label: {d["yolo_label"]}
Broad waste class: {d["broad_class"]}
Confidence: {d["confidence"]}

Use the attached image and YOLO result together.

Return ONLY one valid JSON object.
Do not return a list.
Do not use markdown.
Do not ask the user questions.

The JSON object must follow this exact format:

{{
  "broad_class": "plastic/paper/metal/glass/e-waste/general",
  "specific_object": "specific item name",
  "material_type": "material type",
  "condition": "clean/dirty/has liquid/greasy/mixed material/unknown",
  "can_recycle_now": true,
  "can_be_made_recyclable": true,
  "beyond_saving": false,
  "recycling_bin": "which bin it should go into",
  "reason": "short reason",
  "action_steps": "what user should do",
  "identification_reply": "short robot answer for: what is this?",
  "recyclability_reply": "short robot answer for: can it be recycled?",
  "final_advice_reply": "short robot answer for: where to throw it or what should be done?"
}}
"""

        uploaded_image = self.client.files.upload(file=d["image_path"])

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[uploaded_image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        print("\n========== GEMINI RAW ==========")
        print(response.text)
        print("================================\n")

        data = json.loads(response.text)

        if isinstance(data, list):
            raise ValueError("Gemini returned a list instead of one JSON object.")

        self.cached_analysis = data
        return self.cached_analysis

    def answer_identification(self):
        analysis = self.analyze_once_with_gemini()
        if not analysis:
            return "Please show me a waste item first."
        return analysis["identification_reply"]

    def answer_recyclability(self):
        analysis = self.analyze_once_with_gemini()
        if not analysis:
            return "Please show me a waste item first."
        return analysis["recyclability_reply"]

    def answer_final_advice(self):
        analysis = self.analyze_once_with_gemini()
        if not analysis:
            return "Please show me a waste item first."
        return analysis["final_advice_reply"]
    
    def answer_user_question(self, user_question):
        analysis = self.analyze_once_with_gemini()

        if not analysis:
            return "Please show me a waste item first."

        question = user_question.lower()

        if any(word in question for word in ["what is", "what kind", "what waste", "identify"]):
            return analysis["identification_reply"]

        if any(word in question for word in ["recycle", "recyclable", "can it", "can this"]):
            return analysis["recyclability_reply"]

        if any(word in question for word in ["where", "bin", "throw", "dispose"]):
            return f"Put it in the {analysis['recycling_bin']}."

        if any(word in question for word in ["what should", "what can", "how", "clean", "wash"]):
            return analysis["final_advice_reply"]

        if any(word in question for word in ["why"]):
            return analysis["reason"]

        return (
            f"This is {analysis['specific_object']}. "
            f"{analysis['recyclability_reply']} "
            f"{analysis['final_advice_reply']}"
        )
    
    def receive_detection(self, detection):
        if self.current_detection != detection:
            self.current_detection = detection
            self.cached_analysis = None

    def answer_user_question(self, user_question):
        analysis = self.analyze_once_with_gemini()

        if not analysis:
            return "Please show me a waste item first."

        q = user_question.lower()

        if any(x in q for x in ["what is", "what kind", "identify", "what waste"]):
            return analysis["identification_reply"]

        if any(x in q for x in ["recycle", "recyclable", "can it", "can this"]):
            return analysis["recyclability_reply"]

        if any(x in q for x in ["where", "bin", "throw", "dispose"]):
            return f"Put it in the {analysis['recycling_bin']}."

        if any(x in q for x in ["what should", "what can", "how", "clean", "wash"]):
            return analysis["final_advice_reply"]

        if "why" in q:
            return analysis["reason"]

        return (
            f"This is {analysis['specific_object']}. "
            f"{analysis['recyclability_reply']} "
            f"{analysis['final_advice_reply']}"
        )