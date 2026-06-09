import os

from dotenv import load_dotenv

from ecosort_core.gemini_client import DEFAULT_MODEL, generate_json_from_image


class BrainNode:
    def __init__(self):
        load_dotenv()
        self.model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.current_detection = None
        self.cached_analysis = None

        if not self.api_key:
            raise RuntimeError("Missing GEMINI_API_KEY in .env")

    def receive_detection(self, detection):
        if self.current_detection != detection:
            self.current_detection = detection
            self.cached_analysis = None

    def analyze_once_with_gemini(self):
        if self.cached_analysis:
            return self.cached_analysis

        if not self.current_detection:
            return None

        detection = self.current_detection
        prompt = """
You are EcoSort AI, a recycling assistant robot.

YOLO detected:
YOLO label: {yolo_label}
Broad waste class: {broad_class}
Confidence: {confidence}

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
""".format(
            yolo_label=detection["yolo_label"],
            broad_class=detection["broad_class"],
            confidence=detection["confidence"],
        )

        data = generate_json_from_image(
            image_path=detection["image_path"],
            prompt=prompt,
            api_key=self.api_key,
            model_name=self.model_name,
        )

        print("\n========== GEMINI RAW ==========")
        print(data)
        print("================================\n")

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
            return "Put it in the {bin}.".format(bin=analysis["recycling_bin"])

        if any(word in question for word in ["what should", "what can", "how", "clean", "wash"]):
            return analysis["final_advice_reply"]

        if "why" in question:
            return analysis["reason"]

        return (
            "This is {object_name}. {recyclability} {advice}".format(
                object_name=analysis["specific_object"],
                recyclability=analysis["recyclability_reply"],
                advice=analysis["final_advice_reply"],
            )
        )

    def reset_session(self):
        self.current_detection = None
        self.cached_analysis = None
