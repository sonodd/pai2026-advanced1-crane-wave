"""Summarize measured closed-loop states, without treating offline fit as success."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np


def analyze(path):
    with path.open() as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f'Empty rollout: {path}')
    keys = ['crane_plus_joint1', 'crane_plus_joint2', 'crane_plus_joint4',
            'crane_plus_joint3', 'crane_plus_joint_hand']
    states = np.array([[float(r['state_'+k]) for k in keys] for r in rows])
    times = np.array([float(r['time']) for r in rows])
    signs = []
    for angle in states[:, 2]:
        sign = 1 if angle > 0.15 else (-1 if angle < -0.15 else 0)
        if sign and (not signs or signs[-1] != sign):
            signs.append(sign)
    pairs = min(signs.count(1), signs.count(-1))
    home = bool(np.max(np.abs(states[-1])) < 0.1)
    return {'file': path.name, 'samples': len(rows), 'duration_sim_s': float(times[-1]),
            'state_min_rad': states.min(axis=0).tolist(),
            'state_max_rad': states.max(axis=0).tolist(),
            'final_state_rad': states[-1].tolist(), 'wrist_extreme_sequence': signs,
            'wrist_positive_negative_pairs': pairs, 'returned_home_within_0_1_rad': home,
            'three_waves_and_home': bool(pairs >= 3 and home),
            'clipped_commands': sum(int(r['clipped']) for r in rows)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('logs', type=Path, nargs='+')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = {'criteria': 'At least three positive/negative wrist pairs beyond +/-0.15 rad and final all-joint error <0.1 rad',
              'joint_order': ['joint1', 'joint2', 'joint4', 'joint3', 'hand'],
              'rollouts': [analyze(path) for path in args.logs]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
