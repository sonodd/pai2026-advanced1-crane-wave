#!/bin/bash
# 1エピソード＝1 bag（Day5 講義の収集方法）。デモ動作を episodes 回記録する
set -eo pipefail
exec 9>/tmp/crane-wave-collection.lock
flock -n 9 || { echo 'Another wave collection is already running' >&2; exit 1; }
source /workspace/scripts/ros_env.sh
OUT=${OUT:-/workspace/dataset/rosbags/wave}
EPISODES=${1:-12}
START_EPISODE=${START_EPISODE:-0}
mkdir -p "$OUT" /workspace/logs
BAG=
cleanup() {
  if [ -n "$BAG" ]; then
    kill -INT "$BAG" 2>/dev/null || true
    wait "$BAG" || true
    BAG=
  fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM
timeout 30 ros2 topic echo --once /joint_states >/dev/null
for ((n=START_EPISODE; n<START_EPISODE+EPISODES; n++)); do
  printf -v i '%02d' "$n"
  if [ -e "$OUT/episode_$i" ]; then
    echo "Refusing to overwrite existing episode: $OUT/episode_$i" >&2
    exit 1
  fi
  ros2 bag record --use-sim-time -o "$OUT/episode_$i" /clock /joint_states /crane_plus_arm_controller/joint_trajectory /crane_plus_gripper_controller/joint_trajectory >"/workspace/logs/record_$i.log" 2>&1 &
  BAG=$!
  sleep 2
  kill -0 "$BAG"
  python3 /workspace/scripts/wave_demo.py "$n"
  sleep 1
  cleanup
  ros2 bag info "$OUT/episode_$i"
  sleep 1
done
ls "$OUT"
