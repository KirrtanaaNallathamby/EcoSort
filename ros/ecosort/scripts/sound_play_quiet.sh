#!/usr/bin/env bash
# sound_play without harmless ALSA stderr spam on robot hardware
ROS_DISTRO="${ROS_DISTRO:-noetic}"
exec python3 "/opt/ros/${ROS_DISTRO}/lib/sound_play/soundplay_node.py" "$@" 2>/dev/null
