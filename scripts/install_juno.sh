#!/usr/bin/env bash
set -euo pipefail

echo "=== EcoSort AI - Juno install helper ==="

if [ -z "${ROS_DISTRO:-}" ]; then
  echo "Sourcing ROS Melodic..."
  source /opt/ros/melodic/setup.bash
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CATKIN_WS="${CATKIN_WS:-$HOME/catkin_ws}"

echo "Repo: $REPO_DIR"
echo "Workspace: $CATKIN_WS"

mkdir -p "$CATKIN_WS/src"
if [ ! -e "$CATKIN_WS/src/EcoSort" ]; then
  ln -sfn "$REPO_DIR" "$CATKIN_WS/src/EcoSort"
fi

pip3 install --user -r "$REPO_DIR/requirements-juno.txt"

cd "$CATKIN_WS"
catkin_make
source devel/setup.bash

echo ""
echo "Build complete. To launch on Juno:"
echo "  export GEMINI_API_KEY=your_key"
echo "  roslaunch ecosort ecosort_juno.launch"
