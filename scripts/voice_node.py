#!/usr/bin/env python3
import rospy
import pyttsx3
import speech_recognition as sr
from std_msgs.msg import String

class VoiceNode:
    def __init__(self):
        rospy.init_node('voice_node')
        
        # Publishers and Subscribers
        self.voice_pub = rospy.Publisher('user_voice_query', String, queue_size=10)
        rospy.Subscriber('robot_speech_cmd', String, self.tts_callback)
        
        # Initialize Text-to-Speech Engine
        self.tts_engine = pyttsx3.init()
        self.configure_tts_voice()
        
        # Initialize Speech Recognition Engine
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        rospy.loginfo("Voice Node Initialized. Adjusting ambient mic noise profile...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def configure_tts_voice(self):
        """Sets up voice style from parameters."""
        gender = rospy.get_param('global/voice_gender', 'female')
        voices = self.tts_engine.getProperty('voices')
        self.tts_engine.setProperty('rate', 165) # Controlled speaking rate for clarity in lab spaces
        
        if gender == 'female' and len(voices) > 1:
            self.tts_engine.setProperty('voice', voices[1].id) # Usually index 1 is female in Linux espeak
        else:
            self.tts_engine.setProperty('voice', voices[0].id)

    def tts_callback(self, msg):
        """Triggers whenever the robot brain commands speech output."""
        text_to_speak = msg.data
        rospy.loginfo(f"Robot speaking: {text_to_speak}")
        
        # Speak text out loud (Blocks thread until speech completes to avoid self-listening)
        self.tts_engine.say(text_to_speak)
        self.tts_engine.runAndWait()
        
        # After completing its speech, instantly cycle to open mic listening thread
        self.listen_to_user()

    def listen_to_user(self):
        """Captures human vocal query and publishes to the ROS processing pipeline."""
        rospy.loginfo("Microphone status: Listening for student inquiry...")
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            # Using Google's free Web STT service endpoint
            recognized_text = self.recognizer.recognize_google(audio)
            rospy.loginfo(f"STT Recognized: {recognized_text}")
            
            # Forward text query downstream to the Brain Node
            self.voice_pub.publish(recognized_text)
            
        except sr.WaitTimeoutError:
            rospy.logdebug("Speech listening timed out waiting for human phrase input.")
        except sr.UnknownValueError:
            rospy.logwarn("Speech Recognition could not decode incoming audio signals.")
        except sr.RequestError as e:
            rospy.logerr(f"Could not request results from STT service platform; {e}")

if __name__ == '__main__':
    try:
        node = VoiceNode()
        # Keep node processing events spinning safely
        rospy.spin()
    except rospy.ROSInterruptException:
        pass