"""Run the lecture trainer with explicit paths and a recorded step count."""
import argparse
import json
import os
from pathlib import Path
import sys

p = argparse.ArgumentParser()
p.add_argument('--upstream', type=Path, required=True)
p.add_argument('--workspace', type=Path, required=True)
p.add_argument('--steps', type=int, default=4000)
args = p.parse_args()
upstream, workspace = args.upstream.resolve(), args.workspace.resolve()
os.environ.setdefault('WANDB_MODE', 'disabled')
sys.path.insert(0, str(upstream / 'scripts'))
sys.path.insert(0, str(upstream / 'lerobot'))
os.chdir(upstream)
import train
train.DATASET_ROOT = workspace / 'dataset/lerobot_dataset/crane_plus_wave'
train.OUTPUT_DIRECTORY = workspace / 'checkpoints/crane_plus_wave_act'
train.TRAINING_STEPS = args.steps
train.LOG_FREQ = 100
train.main()
(train.OUTPUT_DIRECTORY / 'training-run.json').write_text(json.dumps({
    'training_steps': args.steps, 'seed': 2026, 'batch_size': train.BATCH_SIZE,
    'device': str(train.DEVICE), 'source_commit': 'b4d6b5459066a80433475a83567504988875248a'
}, indent=2) + '\n')
