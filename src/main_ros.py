#!/usr/bin/env python3
import os
import sys
import time
import cv2
import rospy # ADDED: The ROS Python library

# Keep your friend's path setup
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO_ROOT, "ros", "ecosort"))

# Import your friend's core modules
from ecosort_core.brain_node import BrainNode
from ecosort_core.camera_utils import get_camera
from ecosort_core.vision_node import VisionNode
from ecosort_core.voice_node import VoiceNode

# Helper functions for the State Machine
def is_identification_question(text):
    return any(keyword in text for keyword in ["what is this", "what is it", "what waste", "what kind"])

def is_recycle_question(text):
    return any(keyword in text for keyword in ["can it be recycled", "can this be recycled", "recycle", "recyclable"])

def is_final_advice_question(text):
    return any(keyword in text for keyword in ["where", "throw", "dispose", "what should i do", "clean", "which bin"])

def main():
    # 1. INITIALIZE THE ROS NODE (Crucial for marks!)
    rospy.init_node('ecosort_main_brain', anonymous=True)
    rospy.loginfo("Starting EcoSort AI ROS Node...")

    # 2. Initialize AI Components
    vision = VisionNode()
    brain = BrainNode()
    # Changed backend to desktop for Linux compatibility without extra ROS sound setups
    voice = VoiceNode(backend="desktop") 

    # 3. Open Camera (Using laptop webcam /dev/video0)
    cap = get_camera(0)
    voice.speak("EcoSort AI is ready. Show me a waste item and ask what is this.")
    rospy.sleep(1) # Replaced time.sleep with ROS sleep

    latest_detection = None
    state = "waiting_for_identification"
    
    rate = rospy.Rate(30) # Run at 30 frames per second

    # 4. THE ROS LOOP (Replaces 'while True:')
    while not rospy.is_shutdown():
        ret, frame = cap.read()
        if not ret:
            rospy.logwarn("Failed to grab camera frame. Retrying...")
            rate.sleep()
            continue

        # Run YOLO Vision
        detection = vision.detect_waste(frame)
        if detection:
            latest_detection = detection
            cv2.putText(
                frame,
                f"{detection['broad_class']} detected",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,
            )

        cv2.imshow("EcoSort AI - Press Q to quit", frame)
        speech = voice.get_latest_speech()

        if speech:
            rospy.loginfo(f"[STATE]: {state} | User said: {speech}")

            if latest_detection is None:
                voice.speak("Please show me a waste item clearly.")
                rospy.sleep(1)
                continue

            # --- STATE MACHINE LOGIC ---
            if state == "waiting_for_identification":
                if is_identification_question(speech):
                    brain.receive_detection(latest_detection)
                    voice.speak(brain.answer_identification())
                    rospy.sleep(1)
                    state = "waiting_for_recycle_question"

            elif state == "waiting_for_recycle_question":
                if is_recycle_question(speech):
                    voice.speak(brain.answer_recyclability())
                    rospy.sleep(1)
                    state = "waiting_for_final_question"

            elif state == "waiting_for_final_question":
                if is_final_advice_question(speech):
                    voice.speak(brain.answer_final_advice())
                    rospy.sleep(1)
                    voice.speak("Interaction complete. Show me another item.")
                    rospy.sleep(1)
                    brain.reset_session()
                    state = "waiting_for_identification"

        # Safe exit using 'q' or Ctrl+C
        if cv2.waitKey(1) & 0xFF == ord("q"):
            rospy.loginfo("Shutting down EcoSort AI...")
            break
            
        rate.sleep() # Keeps the ROS node running efficiently

    # Clean up hardware
    voice.stop()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass