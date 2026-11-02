#!/bin/bash
set -eo pipefail
source /workspace/scripts/ros_env.sh
export PYTHONPATH="/home/ubuntu/pai_runtime:/home/ubuntu/pai_training/lerobot:/home/ubuntu/pai_wave_training:${PYTHONPATH:-}"
exec python3 /workspace/scripts/infer_wave.py "$@"
