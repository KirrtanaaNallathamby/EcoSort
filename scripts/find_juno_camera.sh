#!/usr/bin/env bash
# Run ON the Juno robot to find the correct camera device and settings.
echo "=== EcoSort camera finder ==="
echo ""

echo "--- Video devices ---"
ls -l /dev/video* 2>/dev/null || echo "No /dev/video* found"
echo ""

if command -v v4l2-ctl >/dev/null 2>&1; then
  for dev in /dev/video*; do
    if v4l2-ctl -d "$dev" --all 2>/dev/null | grep -q "Video Capture"; then
      echo "=== $dev (Video Capture) ==="
      v4l2-ctl -d "$dev" --all 2>/dev/null | grep -E "Card type|Driver name|Bus info"
      echo "Supported formats:"
      v4l2-ctl -d "$dev" --list-formats-ext 2>/dev/null | head -20
      echo ""
    fi
  done
else
  echo "Install: sudo apt-get install v4l-utils"
fi

echo "--- Try these launches (one at a time) ---"
echo "  roslaunch ecosort usb_cam.launch"
echo "  roslaunch ecosort usb_cam.launch video_device:=/dev/video0 pixel_format:=mjpeg"
echo "  roslaunch ecosort usb_cam.launch video_device:=/dev/video1 pixel_format:=mjpeg"
echo "  roslaunch ecosort usb_cam.launch video_device:=/dev/video0 pixel_format:=yuyv io_method:=mmap"
echo ""
echo "Verify: rostopic hz /usb_cam/image_raw"
