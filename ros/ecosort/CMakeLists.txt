cmake_minimum_required(VERSION 3.0.2)
project(ecosort)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  sensor_msgs
  message_generation
)

add_message_files(
  FILES
  WasteDetection.msg
  EduResponse.msg
  PatrolStatus.msg
)

generate_messages(
  DEPENDENCIES
  std_msgs
)

catkin_package(
  CATKIN_DEPENDS message_runtime std_msgs geometry_msgs sensor_msgs rospy
)

catkin_install_python(PROGRAMS
  scripts/waste_detector_node.py
  scripts/gemini_brain_node.py
  scripts/audio_handler_node.py
  scripts/patrol_nav_node.py
  scripts/orchestrator_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
