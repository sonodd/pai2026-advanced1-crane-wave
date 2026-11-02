#!/bin/bash
# Day5 講義資料 p.9 の run_pai_container.sh。macOS 向けに --platform linux/amd64 を付ける（講義資料の注記どおり）
set -euo pipefail
cd "$(dirname "$0")"
if docker container inspect pai_ros2 >/dev/null 2>&1; then
  docker start pai_ros2
  exit 0
fi
docker run -d --name pai_ros2 \
  --platform linux/amd64 \
  -p 127.0.0.1:6080:80 --shm-size=512m \
  -p 127.0.0.1:9090:9090 -p 127.0.0.1:9876:9876 \
  -e RESOLUTION=1280x720 \
  -v "$(pwd)":/workspace \
  airobotbook/ros2-desktop-ai-robot-book-humble:latest
