#!/bin/bash
set -eo pipefail
source /workspace/scripts/ros_env.sh
mkdir -p /workspace/logs
exec ros2 launch crane_plus_gazebo crane_plus_with_table.launch.py "$@"
