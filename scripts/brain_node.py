#!/usr/bin/env python3
import rospy
import json
import os
from std_msgs.msg import String
from ecosort_ai.msg import WasteDetection
from google import genai
from google.genai import types

class BrainNode:
    def __init__(self):
        rospy.init_node('brain_node')
        
        # ROS Publishers & Subscribers
        self.speech_pub = rospy.Publisher('robot_speech_cmd', String, queue_size=10)
        rospy.Subscriber('waste_detected', WasteDetection, self.vision_callback)
        rospy.Subscriber('user_voice_query', String, self.voice_callback)
        
        # Local state cache to match your flowchart logic
        self.current_item = None
        self.cached_json_data = None
        
        # Initialize Gemini Client (Reads GEMINI_API_KEY from your local shell/.env environment)
        # Note: In production, ensure you run 'export GEMINI_API_KEY="your_key"' or load it in your launch sequence
        self.client = genai.Client()

    def vision_callback(self, msg):
        """Triggers when YOLOv11 detects an item."""
        # Only process if it's a new detection to avoid looping identical frames
        if self.current_item != msg.label:
            self.current_item = msg.label
            self.cached_json_data = None # Clear old cache
            
            # Match flowchart 1.jpeg: Immediately announce the detected waste group
            initial_announcement = f"I see a {msg.label}. Let me know if you want to recycle it!"
            rospy.loginfo(initial_announcement)
            self.speech_pub.publish(initial_announcement)

    def voice_callback(self, msg):
        """Triggers when the user asks a verbal question."""
        user_query = msg.data.lower()
        rospy.loginfo(f"User asked: {user_query}")
        
        if not self.current_item:
            self.speech_pub.publish("Please show me an item first.")
            return

        # FLOWCHART 2.jpeg: User asks "Can this be recycled?" -> Send to Gemini
        if "recycle" in user_query and ("can i" in user_query or "is this" in user_query):
            self.speech_pub.publish("Analyzing the item, please hold on...")
            self.call_gemini_api()
            
        # FLOWCHART 3.jpeg: User asks "What can I do to make it recyclable?" -> Read from Cache!
        elif "how" in user_query or "make it" in user_query or "clean" in user_query:
            self.handle_follow_up_query()
        else:
            self.speech_pub.publish("I didn't quite catch that. You can ask if this can be recycled, or how to clean it.")

    def call_gemini_api(self):
        """Sends context to Gemini 1.5 Flash and enforces a structured JSON schema."""
        prompt = f"""
        The robot camera has detected a waste item labeled as '{self.current_item}' in a campus environment.
        Analyze if this item can typically be recycled, what challenges it presents (such as contamination or mixed materials like bubble tea cups or greasy snack boxes), and provide instructions.
        """
        
        # Enforce your precise flowchart schema 
        class RecyclingAnalysis(types.BaseModel):
            type: str
            can_or_not: bool
            cleanable_to_recycle: bool
            steps_to_clean: str
            reasoning: str

        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RecyclingAnalysis,
                    temperature=0.2
                ),
            )
            
            # Parse response and store in local cache
            self.cached_json_data = json.loads(response.text)
            rospy.loginfo(f"Gemini Structured Output: {self.cached_json_data}")
            
            # Execute Decision Tree based on 'can_or_not' 
            if self.cached_json_data['can_or_not']:
                reply = f"Yes! This {self.cached_json_data['type']} can be recycled. {self.cached_json_data['reasoning']}"
            else:
                reply = f"No, it cannot be recycled directly. Why? {self.cached_json_data['reasoning']}"
                
            self.speech_pub.publish(reply)
            
        except Exception as e:
            rospy.logerr(f"Gemini API Error: {e}")
            self.speech_pub.publish("Sorry, I encountered an error checking my brain database.")

    def handle_follow_up_query(self):
        """Instant follow-up response executing flowchart 3.jpeg using local memory cache."""
        if not self.cached_json_data:
            self.speech_pub.publish("Please ask me if the item can be recycled first so I can analyze it.")
            return
            
        # Check if item can be saved [cite: 3]
        if self.cached_json_data['cleanable_to_recycle']:
            reply = f"Here is what you can do: {self.cached_json_data['steps_to_clean']}"
        else:
            reply = "Unfortunately, this item is beyond saving for standard recycling bins. Please dispose of it in general waste." [cite: 3]
            
        self.speech_pub.publish(reply)

if __name__ == '__main__':
    try:
        node = BrainNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass