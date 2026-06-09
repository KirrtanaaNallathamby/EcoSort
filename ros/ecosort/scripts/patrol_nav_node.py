#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

from ecosort.msg import PatrolStatus, WasteDetection


class PatrolNavNode(object):
    STATES = ("patrolling", "engaging", "idle")

    def __init__(self):
        rospy.init_node("patrol_nav", anonymous=False)

        self.cmd_vel_topic = rospy.get_param("~cmd_vel_topic", "/cmd_vel")
        self.linear_speed = rospy.get_param("~linear_speed", 0.08)
        self.angular_speed = rospy.get_param("~angular_speed", 0.25)
        self.patrol_duration = rospy.get_param("~patrol_duration_sec", 4.0)
        self.turn_duration = rospy.get_param("~turn_duration_sec", 2.0)
        self.engage_on_person = rospy.get_param("~engage_on_person", True)
        self.engage_on_waste = rospy.get_param("~engage_on_waste", True)

        self.state = "patrolling"
        self.person_detected = False
        self.waste_detected = False
        self.phase = "forward"
        self.phase_start = rospy.Time.now()

        self.cmd_pub = rospy.Publisher(self.cmd_vel_topic, Twist, queue_size=1)
        self.status_pub = rospy.Publisher("/patrol_nav/status", PatrolStatus, queue_size=1)

        rospy.Subscriber(
            "/waste/classification",
            WasteDetection,
            self._detection_callback,
            queue_size=1,
        )
        rospy.Subscriber(
            "/ecosort/engage",
            Bool,
            self._engage_callback,
            queue_size=1,
        )
        rospy.Subscriber(
            "/ecosort/resume_patrol",
            Bool,
            self._resume_callback,
            queue_size=1,
        )

        rospy.Timer(rospy.Duration(0.1), self._control_loop)
        rospy.Timer(rospy.Duration(0.5), self._publish_status)

        rospy.on_shutdown(self._stop_robot)
        rospy.loginfo("patrol_nav ready on %s", self.cmd_vel_topic)

    def _detection_callback(self, msg):
        self.person_detected = bool(msg.person_detected)
        self.waste_detected = bool(msg.broad_class)

        should_engage = False
        if self.engage_on_person and self.person_detected:
            should_engage = True
        if self.engage_on_waste and self.waste_detected:
            should_engage = True

        if should_engage and self.state == "patrolling":
            self.state = "engaging"
            self._stop_robot()
            rospy.loginfo("Engaging user: person=%s waste=%s", self.person_detected, self.waste_detected)

    def _engage_callback(self, msg):
        if msg.data:
            self.state = "engaging"
            self._stop_robot()

    def _resume_callback(self, msg):
        if msg.data:
            self.state = "patrolling"
            self.phase = "forward"
            self.phase_start = rospy.Time.now()
            rospy.loginfo("Resuming patrol.")

    def _control_loop(self, _event):
        if self.state != "patrolling":
            self._stop_robot()
            return

        twist = Twist()
        elapsed = (rospy.Time.now() - self.phase_start).to_sec()

        if self.phase == "forward":
            twist.linear.x = self.linear_speed
            if elapsed >= self.patrol_duration:
                self.phase = "turn"
                self.phase_start = rospy.Time.now()
        else:
            twist.angular.z = self.angular_speed
            if elapsed >= self.turn_duration:
                self.phase = "forward"
                self.phase_start = rospy.Time.now()

        self.cmd_pub.publish(twist)

    def _publish_status(self, _event):
        msg = PatrolStatus()
        msg.header.stamp = rospy.Time.now()
        msg.state = self.state
        msg.person_detected = self.person_detected
        msg.waste_detected = self.waste_detected
        msg.engaging = self.state == "engaging"
        self.status_pub.publish(msg)

    def _stop_robot(self):
        self.cmd_pub.publish(Twist())


if __name__ == "__main__":
    try:
        PatrolNavNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
