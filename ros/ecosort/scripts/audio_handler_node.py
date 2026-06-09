#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time

import rospy
import speech_recognition as sr
from std_msgs.msg import String

from ecosort.msg import EduResponse


class AudioHandlerNode(object):
    def __init__(self):
        rospy.init_node("audio_handler", anonymous=False)

        self.backend = rospy.get_param("~backend", "robot")
        self.listen_timeout = rospy.get_param("~listen_timeout", 5.0)
        self.phrase_time_limit = rospy.get_param("~phrase_time_limit", 6.0)

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.running = True
        self.is_speaking = False
        self._sound_client = None

        if self.backend == "robot":
            self._init_robot_tts()

        self.audio_pub = rospy.Publisher("/audio/raw", String, queue_size=1)
        rospy.Subscriber("/edu/response", EduResponse, self._response_callback, queue_size=1)

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

        rospy.loginfo("audio_handler ready on /audio/raw")

    def _init_robot_tts(self):
        try:
            from sound_play.libsoundplay import SoundClient

            self._sound_client = SoundClient()
            time.sleep(1)
            rospy.loginfo("Using sound_play for robot TTS.")
        except ImportError:
            rospy.logwarn("sound_play not available, TTS will be text-only.")
            self.backend = "text"

    def _listen_loop(self):
        while self.running and not rospy.is_shutdown():
            if self.is_speaking:
                time.sleep(0.1)
                continue

            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=self.listen_timeout,
                        phrase_time_limit=self.phrase_time_limit,
                    )
                text = self.recognizer.recognize_google(audio).lower()
                rospy.loginfo("Heard: %s", text)
                self.audio_pub.publish(String(data=text))
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as error:
                rospy.logwarn("Speech recognition error: %s", error)

    def _response_callback(self, msg):
        if not msg.text:
            return
        self._speak(msg.text)

    def _speak(self, text):
        rospy.loginfo("Speaking: %s", text)
        self.is_speaking = True
        try:
            if self.backend == "robot" and self._sound_client is not None:
                self._sound_client.stopAll()
                self._sound_client.say(text)
                time.sleep(max(2.0, len(text) * 0.06))
            else:
                rospy.loginfo("[TTS]: %s", text)
        except Exception as error:
            rospy.logwarn("TTS error: %s", error)
        finally:
            time.sleep(0.3)
            self.is_speaking = False


if __name__ == "__main__":
    try:
        node = AudioHandlerNode()
        rospy.spin()
        node.running = False
    except rospy.ROSInterruptException:
        pass
