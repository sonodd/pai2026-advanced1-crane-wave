#!/bin/bash
# Environment used by the lecture image, also in non-interactive docker exec.
source /opt/ros/humble/setup.bash
source /home/ubuntu/airobot_ws/install/setup.bash
source /usr/share/gazebo/setup.sh
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export DISPLAY=:0
export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_SOFTWARE=1
export QV4_FORCE_INTERPRETER=1
export QT_IM_MODULE=none
