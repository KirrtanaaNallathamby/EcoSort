#!/usr/bin/env bash
# Run ON the Juno robot to find the correct camera device and ROS topic.
echo "=== EcoSort camera finder (run on Juno robot) ==="
echo ""

echo "--- USB video devices ---"
if ls /dev/video* 1>/dev/null 2>&1; then
  ls -l /dev/video*
else
  echo "No /dev/video* devices found."
fi
echo ""

if command -v v4l2-ctl >/dev/null 2>&1; then
  echo "--- Devices with Video Capture (use one of these for video_device) ---"
  for dev in /dev/video*; do
    if v4l2-ctl -d "$dev" --all 2>/dev/null | grep -q "Video Capture"; then
      name=$(v4l2-ctl -d "$dev" --all 2>/dev/null | grep "Card type" | head -1)
      echo "  $dev  $name"
    fi
  done
else
  echo "Install v4l2-utils for details: sudo apt-get install v4l-utils"
  echo "Try each device: roslaunch ecosort ecosort_io_juno.launch video_device:=/dev/video1"
fi
echo ""

echo "--- ROS image topics (start camera driver first, then check) ---"
source /opt/ros/noetic/setup.bash 2>/dev/null || source /opt/ros/melodic/setup.bash 2>/dev/null
if rostopic list 2>/dev/null | grep -i image; then
  rostopic list 2>/dev/null | grep -i image
else
  echo "  (no image topics yet — start a camera node first)"
fi
echo ""
echo "Launch examples:"
echo "  # Juno already has camera running on a topic:"
echo "  roslaunch ecosort ecosort_io_juno.launch start_usb_cam:=false camera_topic:=/YOUR_TOPIC/image_raw"
echo ""
echo "  # Start usb_cam on correct device:"
echo "  roslaunch ecosort ecosort_io_juno.launch start_usb_cam:=true video_device:=/dev/video1"
