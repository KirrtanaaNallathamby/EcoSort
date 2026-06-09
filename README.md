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

## Quick start — Jupiter Juno (Python 3.8)

### 1. Prerequisites on the robot

- ROS Melodic
- `sound_play`, `cv_bridge`, `usb_cam` (or Juno camera bringup)
- Internet access for Google STT and Gemini API

### 2. Install Python dependencies

```bash
source /opt/ros/melodic/setup.bash
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

```bash
cd ~/catkin_ws/src
# copy or symlink this repo
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

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
source /opt/ros/melodic/setup.bash
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
├── src/                    # Core AI logic (shared)
│   ├── vision_node.py      # YOLOv11 detection
│   ├── brain_node.py       # Gemini reasoning
│   ├── voice_node.py       # STT/TTS (desktop)
│   ├── gemini_client.py    # Python 3.8 REST fallback
│   └── main.py             # Desktop entry point
├── ros/ecosort/            # ROS Melodic catkin package
│   ├── scripts/            # ROS nodes
│   ├── launch/             # Launch files
│   └── msg/                # Custom messages
├── requirements.txt        # Desktop (Python 3.10+)
└── requirements-juno.txt   # Juno robot (Python 3.8)
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No camera frames | Check `rostopic echo /usb_cam/image_raw` or set `camera_topic` in launch |
| No speech output | Ensure `sound_play` node is running |
| Gemini error on Juno | Verify `GEMINI_API_KEY` and internet; REST fallback is used on Python 3.8 |
| Robot does not move | Check `rostopic pub /cmd_vel` and base driver is active |
