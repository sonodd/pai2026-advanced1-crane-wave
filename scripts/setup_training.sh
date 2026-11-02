#!/bin/bash
# Run inside the lecture image. Reuses its torch/torchvision CPU-capable build.
set -eo pipefail
PAI_ROOT=${PAI_ROOT:-/home/ubuntu/pai_training}
RUNTIME=${RUNTIME:-/home/ubuntu/pai_runtime}
if [ ! -d "$PAI_ROOT/.git" ]; then
  git clone --recursive https://github.com/matsuolab/pai_training.git "$PAI_ROOT"
  git -C "$PAI_ROOT" checkout b4d6b5459066a80433475a83567504988875248a
  git -C "$PAI_ROOT" submodule update --init --recursive
fi
python3 -m pip install --target "$RUNTIME" \
  'numpy<1.25' 'datasets==3.6.0' 'huggingface-hub==0.31.2' \
  'draccus==0.10.0' 'wandb==0.19.11' 'diffusers==0.33.1' \
  'rosbags==0.10.10' einops safetensors jsonlines deepdiff termcolor \
  'gymnasium==0.29.1' omegaconf imageio av pyserial
export PYTHONPATH="$RUNTIME:$PAI_ROOT/lerobot:${PYTHONPATH:-}"
python3 /workspace/scripts/configure_training.py --upstream "$PAI_ROOT" --workspace /workspace
echo "Ready: cd $PAI_ROOT"
echo "PYTHONPATH=$RUNTIME:$PAI_ROOT/lerobot python3 scripts/rosbag2lerobot.py"
echo "PYTHONPATH=$RUNTIME:$PAI_ROOT/lerobot WANDB_MODE=disabled python3 /workspace/scripts/train_wave.py --upstream $PAI_ROOT --workspace /workspace --steps 4000"
