#!/usr/bin/env python3
import rospy
import cv2
from ultralytics import YOLO
from ecosort_ai.msg import WasteDetection
from camera_utils import find_camera_index

def main():
    rospy.init_node('vision_node')
    pub = rospy.積極_pub = rospy.Publisher('waste_detected', WasteDetection, queue_size=10)
    
    # Dynamically find camera and load local model
    keyword = rospy.get_param('~camera_keyword', 'Jupiter')
    cam_idx = find_camera_index(keyword)
    cap = cv2.VideoCapture(cam_idx)
    
    # Path to your custom trained weights
    model = YOLO("weights/best.pt") 

    while not rospy.is_shutdown():
        ret, frame = cap.read()
        if not ret:
            continue
            
        results = model(frame, verbose=False)
        
        # Insert your model parsing and classification state logic here
        # For example, if a custom "contaminated_bottle" class is triggered:
        msg = WasteDetection()
        msg.label = "bottle"
        msg.state = "contaminated" [cite: 19]
        msg.confidence = 0.89
        
        pub.publish(msg)
        rospy.sleep(0.1) # Limit frequency to preserve CPU cycles

if __name__ == '__main__':
    main()