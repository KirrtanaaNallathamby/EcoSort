# EcoSort AI

Interactive autonomous waste classifier and educator for the **Jupiter Juno** robot.

## Architecture (ROS)

| Node | ROS name | Topic |
|------|----------|-------|
| YOLOv11 waste detection | `waste_detector` | publishes `/waste/classification` |
| Gemini reasoning | `gemini_brain` | publishes `/edu/response` |
| STT / TTS gateway | `audio_handler` | publishes `/audio/raw` |
| Patrol navigation | `patrol_nav` | publishes `/cmd_vel` |

## Quick start — Desktop (no robot)

```bash
pip install -r requirements.txt
cp .env.example .env   # add GEMINI_API_KEY
cd src
python main.py
```

## Quick start — Jupiter Juno (Python 3.8+)

### 1. Prerequisites on the robot

- ROS Melodic or **ROS Noetic** (your IO-Juno MA02 may ship with Noetic)
- `sound_play`, `cv_bridge`, `usb_cam` (or Juno camera bringup)
- Internet access for Google STT and Gemini API

### 2. Install Python dependencies

```bash
source /opt/ros/noetic/setup.bash   # or melodic
pip3 install --user -r requirements-juno.txt
```

> **Note:** `google-genai` requires Python 3.9+. On Juno (Python 3.8), Gemini uses a REST API fallback automatically while keeping model `gemini-3.1-flash-lite`.

### 3. Configure API key

```bash
export GEMINI_API_KEY="your-key-here"
export GEMINI_MODEL="gemini-3.1-flash-lite"
```

Or create `~/.env` in the project root with the same variables.

### 4. Build ROS package

**Important:** run install from inside the EcoSort repo folder.

```bash
cd ~/EcoSort          # or wherever you cloned the project
source /opt/ros/noetic/setup.bash   # or melodic
bash install_juno.sh
```

This links `ros/ecosort` → `~/catkin_ws/src/ecosort` and runs `catkin_make`.

### 5. Launch on Juno

**Terminal 1** — start ROS core and robot bringup (camera + base):

```bash
roscore
# In another terminal, start your Juno camera and base drivers, e.g.:
# roslaunch usb_cam usb_cam.launch
# roslaunch jupiterobot2_bringup jupiterobot2_bringup.launch
```

**Terminal 2** — launch EcoSort:

```bash
source /opt/ros/noetic/setup.bash   # or melodic
source ~/catkin_ws/devel/setup.bash
export GEMINI_API_KEY="your-key"
roslaunch ecosort ecosort_juno.launch
```

For **Juno2** (RealSense camera):

```bash
roslaunch ecosort ecosort_juno2.launch
```

### 6. Interaction flow

1. Robot patrols via `/cmd_vel`
2. YOLO detects a person or waste item → robot stops
3. Robot greets the user via `sound_play`
4. User asks: *"Can I recycle this cup?"*
5. Gemini analyzes the image + YOLO label → spoken educational reply
6. Robot resumes patrol after the interaction ends

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Required |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Gemini model |
| `ECOSORT_CAPTURE_DIR` | `captures` | Saved waste images |

## Project layout

```
EcoSort/
├── install_juno.sh         # Run this on Juno (from repo root)
├── src/
│   └── main.py             # Desktop entry point
├── ros/ecosort/            # ROS Melodic catkin package
│   ├── ecosort_core/       # Shared AI modules (YOLO, Gemini, voice)
│   ├── scripts/            # ROS nodes
│   ├── launch/             # Launch files
│   └── msg/                # Custom messages
├── requirements.txt        # Desktop (Python 3.10+)
└── requirements-juno.txt   # Juno robot (Python 3.8)
```

## Camera on IO-Juno MA02

**Run `roslaunch` on the Juno robot**, not on your laptop. If you run `python src/main.py` on a laptop, it will use the **laptop webcam**.

On the robot, find the correct camera:

```bash
cd ~/EcoSort
bash scripts/find_juno_camera.sh
```

Then launch with the right device (often `/dev/video1`, not `video0`):

```bash
roslaunch ecosort ecosort_io_juno.launch video_device:=/dev/video1
```

If Juno already has a camera node running, don't start usb_cam:

```bash
rostopic list | grep image
roslaunch ecosort ecosort_io_juno.launch start_usb_cam:=false camera_topic:=/your/topic/image_raw
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Uses laptop camera | Run on the **robot**, not `python main.py` on PC |
| Wrong / empty camera | `bash scripts/find_juno_camera.sh` then try `video_device:=/dev/video1` |
| `No such file or directory` on install | `cd` into the EcoSort repo first, then run `bash install_juno.sh` |
| No camera frames | Check `rostopic hz /usb_cam/image_raw` or set `camera_topic` in launch |
| No speech output | Ensure `sound_play` node is running |
| Gemini error on Juno | Verify `GEMINI_API_KEY` and internet; REST fallback is used on Python 3.8 |
| Robot does not move | Check `rostopic pub /cmd_vel` and base driver is active |

https://docs.google.com/document/d/1PWbYBl1ev9JOtkP-8UHw8B7qIUJ1jNuekc2gicWYxTs/edit?usp=sharing
