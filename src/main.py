import os
import sys
import time

import cv2

# Use shared core modules from the ROS package
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO_ROOT, "ros", "ecosort"))

from ecosort_core.brain_node import BrainNode
from ecosort_core.camera_utils import get_camera
from ecosort_core.vision_node import VisionNode
from ecosort_core.voice_node import VoiceNode


def is_identification_question(text):
    return any(keyword in text for keyword in [
        "what is this",
        "what is it",
        "what waste",
        "is this plastic",
        "is this paper",
        "is this metal",
        "what kind",
    ])


def is_recycle_question(text):
    return any(keyword in text for keyword in [
        "can it be recycled",
        "can this be recycled",
        "is it recyclable",
        "recycle",
        "recycled",
        "recyclable",
    ])


def is_final_advice_question(text):
    return any(keyword in text for keyword in [
        "where",
        "throw",
        "dispose",
        "what should i do",
        "what can i do",
        "make it recyclable",
        "clean",
        "wash",
        "which bin",
    ])


def main():
    vision = VisionNode()
    brain = BrainNode()
    voice = VoiceNode(backend="desktop")

    cap = get_camera(0)
    voice.speak("EcoSort AI is ready. Show me a waste item and ask what is this.")
    time.sleep(1)

    latest_detection = None
    state = "waiting_for_identification"

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        detection = vision.detect_waste(frame)
        if detection:
            latest_detection = detection
            cv2.putText(
                frame,
                "{label} detected".format(label=detection["broad_class"]),
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

        cv2.imshow("EcoSort AI - Press Q to quit", frame)
        speech = voice.get_latest_speech()

        if speech:
            print("[STATE]:", state)

            if latest_detection is None:
                voice.speak("Please show me a waste item clearly.")
                time.sleep(1)
                continue

            if state == "waiting_for_identification":
                if is_identification_question(speech):
                    brain.receive_detection(latest_detection)
                    voice.speak(brain.answer_identification())
                    time.sleep(1)
                    state = "waiting_for_recycle_question"

            elif state == "waiting_for_recycle_question":
                if is_recycle_question(speech):
                    voice.speak(brain.answer_recyclability())
                    time.sleep(1)
                    state = "waiting_for_final_question"

            elif state == "waiting_for_final_question":
                if is_final_advice_question(speech):
                    voice.speak(brain.answer_final_advice())
                    time.sleep(1)
                    voice.speak("Interaction complete. Show me another item.")
                    time.sleep(1)
                    brain.reset_session()
                    state = "waiting_for_identification"

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    voice.stop()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
