#!/bin/bash
# Records only the simulation display inside the task's container.
# Coordinates match the verified 936x976 VNC desktop / maximized wave.rviz view.
set -eo pipefail
source /workspace/scripts/ros_env.sh
MODE=${1:?teacher or act}
NAME=${2:?output stem}
MODEL=${3:-/workspace/checkpoints/crane_plus_wave_act}
ACTION_STEPS=${4:-1}
mkdir -p /workspace/outputs /workspace/logs
python3 /workspace/scripts/reset_pose.py
ffmpeg -hide_banner -loglevel warning -f x11grab -framerate 25 \
  -video_size 886x782 -i :0.0+25,130 -an -c:v libx264 -preset ultrafast \
  -crf 18 -pix_fmt yuv420p "/workspace/outputs/${NAME}-raw.mp4" \
  >"/workspace/logs/${NAME}-record.log" 2>&1 &
RECORDER=$!
cleanup() { kill -INT "$RECORDER" 2>/dev/null || true; wait "$RECORDER" || true; }
trap cleanup EXIT
sleep 1
if [ "$MODE" = teacher ]; then
  python3 /workspace/scripts/wave_demo.py 0
elif [ "$MODE" = act ]; then
  bash /workspace/scripts/run_infer.sh --model-path "$MODEL" --duration 25 --action-steps "$ACTION_STEPS" \
    --log "/workspace/outputs/${NAME}.csv"
else
  echo 'mode must be teacher or act' >&2
  exit 1
fi
sleep 1
