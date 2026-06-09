#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import cv2
import rospy
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image

from ecosort.msg import WasteDetection


def _setup_ecosort_path():
    try:
        import rospkg
        pkg_path = rospkg.RosPack().get_path("ecosort")
    except Exception:
        pkg_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pkg_path not in sys.path:
        sys.path.insert(0, pkg_path)


_setup_ecosort_path()
from ecosort_core.vision_node import VisionNode


class WasteDetectorNode(object):
    def __init__(self):
        rospy.init_node("waste_detector", anonymous=False)

        self.camera_topic = rospy.get_param("~camera_topic", "/usb_cam/image_raw")
        self.confidence_threshold = rospy.get_param("~confidence_threshold", 0.45)
        self.yolo_model = rospy.get_param("~yolo_model", "yolo11n.pt")
        self.publish_rate_hz = rospy.get_param("~publish_rate_hz", 5.0)

        self.capture_dir = rospy.get_param("~capture_dir", os.path.expanduser("~/ecosort_captures"))
        os.makedirs(self.capture_dir, exist_ok=True)
        self.image_path = os.path.join(self.capture_dir, "latest_waste.jpg")

        self.bridge = CvBridge()
        self.latest_frame = None
        self.vision = VisionNode(
            model_path=self.yolo_model,
            image_path=self.image_path,
            confidence_threshold=self.confidence_threshold,
        )

        self.classification_pub = rospy.Publisher(
            "/waste/classification",
            WasteDetection,
            queue_size=1,
        )

        rospy.Subscriber(self.camera_topic, Image, self._image_callback, queue_size=1)
        rospy.Timer(rospy.Duration(1.0 / self.publish_rate_hz), self._process_frame)

        rospy.loginfo(
            "waste_detector ready. Camera topic: %s", self.camera_topic
        )

    def _image_callback(self, msg):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as error:
            rospy.logwarn("cv_bridge error: %s", error)

    def _process_frame(self, _event):
        if self.latest_frame is None:
            return

        frame = self.latest_frame.copy()
        detection = self.vision.detect_waste(frame)
        person = self.vision.detect_person(frame)

        if detection is None and person is None:
            return

        cv2.imwrite(self.image_path, frame)

        msg = WasteDetection()
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = "camera"
        msg.image_path = self.image_path

        if detection:
            msg.yolo_label = detection["yolo_label"]
            msg.broad_class = detection["broad_class"]
            msg.confidence = detection["confidence"]
        else:
            msg.yolo_label = ""
            msg.broad_class = ""
            msg.confidence = 0.0

        if person:
            msg.person_detected = True
            msg.person_confidence = person["confidence"]
        else:
            msg.person_detected = False
            msg.person_confidence = 0.0

        self.classification_pub.publish(msg)


if __name__ == "__main__":
    try:
        WasteDetectorNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
