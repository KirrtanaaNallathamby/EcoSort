#!/usr/bin/env bash
set -euo pipefail

echo "=== EcoSort AI - Juno install ==="
echo "Current dir: $(pwd)"

# Find repo root from this script (works no matter where you run it from)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CATKIN_WS="${CATKIN_WS:-${HOME}/catkin_ws}"
PKG_SRC="${REPO_DIR}/ros/ecosort"
PKG_LINK="${CATKIN_WS}/src/ecosort"

echo "Repo:      ${REPO_DIR}"
echo "Workspace: ${CATKIN_WS}"
echo "Package:   ${PKG_SRC}"

if [ ! -f "${SCRIPT_DIR}/install_juno.sh" ]; then
  echo "ERROR: install script not found at ${SCRIPT_DIR}/install_juno.sh"
  exit 1
fi

# Verify required files exist
MISSING=0
for REQUIRED in \
  "${REPO_DIR}/requirements-juno.txt" \
  "${PKG_SRC}/package.xml" \
  "${PKG_SRC}/CMakeLists.txt" \
  "${PKG_SRC}/scripts/waste_detector_node.py"
do
  if [ ! -e "${REQUIRED}" ]; then
    echo "ERROR: Missing file: ${REQUIRED}"
    MISSING=1
  fi
done

if [ "${MISSING}" -eq 1 ]; then
  echo ""
  echo "The EcoSort repo is incomplete on this machine."
  echo "Copy or git clone the FULL project to the robot, then run:"
  echo "  cd ${REPO_DIR}"
  echo "  bash scripts/install_juno.sh"
  exit 1
fi

# Source ROS (Melodic or Noetic)
if [ -n "${ROS_DISTRO:-}" ]; then
  echo "ROS already sourced: ${ROS_DISTRO}"
elif [ -f /opt/ros/noetic/setup.bash ]; then
  # shellcheck disable=SC1091
  source /opt/ros/noetic/setup.bash
  echo "Sourced ROS Noetic"
elif [ -f /opt/ros/melodic/setup.bash ]; then
  # shellcheck disable=SC1091
  source /opt/ros/melodic/setup.bash
  echo "Sourced ROS Melodic"
else
  echo "ERROR: ROS not found. Install Melodic or Noetic, or run:"
  echo "  source /opt/ros/noetic/setup.bash"
  exit 1
fi

# Link catkin package
mkdir -p "${CATKIN_WS}/src"
ln -sfn "${PKG_SRC}" "${PKG_LINK}"
echo "Linked: ${PKG_LINK} -> ${PKG_SRC}"

# Python deps for Juno (Python 3.8)
pip3 install --user -r "${REPO_DIR}/requirements-juno.txt"

# Build catkin workspace
cd "${CATKIN_WS}"
catkin_make
# shellcheck disable=SC1091
source devel/setup.bash

echo ""
echo "=== Install complete ==="
echo ""
echo "Next steps:"
echo "  export GEMINI_API_KEY=your_key"
echo "  export GEMINI_MODEL=gemini-3.1-flash-lite"
echo "  roscore"
echo "  roslaunch ecosort ecosort_juno.launch"
