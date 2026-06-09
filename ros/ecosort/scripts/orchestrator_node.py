#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import Bool, String

from ecosort.msg import EduResponse, PatrolStatus, WasteDetection


class OrchestratorNode(object):
    def __init__(self):
        rospy.init_node("ecosort_orchestrator", anonymous=False)

        self.greeting = rospy.get_param(
            "~greeting",
            "Hello, I am EcoSort AI. Show me your waste item and ask me about recycling.",
        )
        self.state = "patrol"
        self.greeted = False
        self.latest_waste = None

        self.engage_pub = rospy.Publisher("/ecosort/engage", Bool, queue_size=1)
        self.resume_pub = rospy.Publisher("/ecosort/resume_patrol", Bool, queue_size=1)
        self.prompt_pub = rospy.Publisher("/edu/response", EduResponse, queue_size=1)

        rospy.Subscriber(
            "/patrol_nav/status",
            PatrolStatus,
            self._patrol_status_callback,
            queue_size=1,
        )
        rospy.Subscriber(
            "/waste/classification",
            WasteDetection,
            self._waste_callback,
            queue_size=1,
        )
        rospy.Subscriber("/audio/raw", String, self._speech_callback, queue_size=1)
        rospy.Subscriber("/edu/response", EduResponse, self._edu_callback, queue_size=1)

        rospy.loginfo("ecosort orchestrator ready")

    def _patrol_status_callback(self, msg):
        if msg.engaging and self.state == "patrol":
            self.state = "engage"
            self.greeted = False
            self.engage_pub.publish(Bool(data=True))

        if self.state == "engage" and not self.greeted:
            self._speak_prompt(self.greeting)
            self.greeted = True

    def _waste_callback(self, msg):
        if msg.broad_class:
            self.latest_waste = msg.broad_class

    def _speech_callback(self, msg):
        if self.state != "engage":
            return

        text = (msg.data or "").lower()
        if any(word in text for word in ["done", "thank you", "thanks", "goodbye", "bye"]):
            self._end_interaction()

    def _edu_callback(self, msg):
        if self.state != "engage":
            return
        if msg.response_type == "final_advice":
            rospy.Timer(
                rospy.Duration(8.0),
                self._schedule_resume,
                oneshot=True,
            )

    def _schedule_resume(self, _event):
        self._end_interaction()

    def _end_interaction(self):
        self.state = "patrol"
        self.greeted = False
        self.latest_waste = None
        self.resume_pub.publish(Bool(data=True))
        self._speak_prompt("Thank you. I will continue patrolling. Have a great day.")
        rospy.loginfo("Interaction complete, resuming patrol.")

    def _speak_prompt(self, text):
        msg = EduResponse()
        msg.header.stamp = rospy.Time.now()
        msg.response_type = "general"
        msg.text = text
        self.prompt_pub.publish(msg)


if __name__ == "__main__":
    try:
        OrchestratorNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
