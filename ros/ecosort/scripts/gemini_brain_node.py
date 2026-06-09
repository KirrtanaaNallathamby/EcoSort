#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import rospy
from std_msgs.msg import String

from ecosort.msg import EduResponse, WasteDetection


def _setup_ecosort_path():
    try:
        import rospkg
        pkg_path = rospkg.RosPack().get_path("ecosort")
    except Exception:
        pkg_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pkg_path not in sys.path:
        sys.path.insert(0, pkg_path)


_setup_ecosort_path()
from ecosort_core.brain_node import BrainNode


class GeminiBrainNode(object):
    def __init__(self):
        rospy.init_node("gemini_brain", anonymous=False)

        self.brain = BrainNode()
        self.latest_detection = None
        self.latest_detection_msg = None

        self.edu_pub = rospy.Publisher("/edu/response", EduResponse, queue_size=1)

        rospy.Subscriber(
            "/waste/classification",
            WasteDetection,
            self._detection_callback,
            queue_size=1,
        )
        rospy.Subscriber("/audio/raw", String, self._speech_callback, queue_size=1)

        rospy.loginfo("gemini_brain ready on /edu/response")

    def _detection_callback(self, msg):
        if not msg.broad_class:
            self.latest_detection_msg = msg
            return

        detection = {
            "yolo_label": msg.yolo_label,
            "broad_class": msg.broad_class,
            "confidence": msg.confidence,
            "image_path": msg.image_path,
        }
        self.latest_detection = detection
        self.latest_detection_msg = msg
        self.brain.receive_detection(detection)

    def _speech_callback(self, msg):
        user_text = (msg.data or "").strip().lower()
        if not user_text:
            return

        if self.latest_detection is None:
            if (
                self.latest_detection_msg is not None
                and self.latest_detection_msg.person_detected
                and self.latest_detection_msg.image_path
            ):
                self.latest_detection = {
                    "yolo_label": "unknown",
                    "broad_class": "general",
                    "confidence": 0.0,
                    "image_path": self.latest_detection_msg.image_path,
                }
                self.brain.receive_detection(self.latest_detection)
            else:
                self._publish_response(
                    "general",
                    "Please show me a waste item clearly before asking.",
                )
                return

        self.brain.receive_detection(self.latest_detection)
        answer = self.brain.answer_user_question(user_text)
        response_type = self._classify_question(user_text)
        analysis = self.brain.cached_analysis or {}

        self._publish_response(
            response_type=response_type,
            text=answer,
            recycling_bin=analysis.get("recycling_bin", ""),
            can_recycle_now=bool(analysis.get("can_recycle_now", False)),
            reason=analysis.get("reason", ""),
        )

    def _classify_question(self, text):
        if any(word in text for word in ["what is", "what kind", "identify", "what waste"]):
            return "identification"
        if any(word in text for word in ["recycle", "recyclable", "can it", "can this"]):
            return "recyclability"
        if any(word in text for word in ["where", "bin", "throw", "dispose", "clean", "wash"]):
            return "final_advice"
        if "why" in text:
            return "reason"
        return "general"

    def _publish_response(
        self,
        response_type,
        text,
        recycling_bin="",
        can_recycle_now=False,
        reason="",
    ):
        msg = EduResponse()
        msg.header.stamp = rospy.Time.now()
        msg.response_type = response_type
        msg.text = text
        msg.recycling_bin = recycling_bin
        msg.can_recycle_now = can_recycle_now
        msg.reason = reason
        self.edu_pub.publish(msg)
        rospy.loginfo("Published edu response [%s]: %s", response_type, text)


if __name__ == "__main__":
    try:
        GeminiBrainNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
