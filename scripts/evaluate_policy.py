"""Offline ACT evaluation on recorded states; this does not prove task success."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import torch
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from lerobot.common.policies.act.modeling_act import ACTPolicy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-root', type=Path, required=True)
    parser.add_argument('--model-path', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    dataset = LeRobotDataset('crane_plus_wave', root=args.dataset_root)
    policy = ACTPolicy.from_pretrained(str(args.model_path)).to('cpu').eval()
    results = []
    first = None
    for episode in range(dataset.num_episodes):
        policy.reset()
        start = int(dataset.episode_data_index['from'][episode])
        end = int(dataset.episode_data_index['to'][episode])
        truth, pred = [], []
        for index in range(start, end):
            sample = dataset[index]
            obs = {key: sample[key].float().unsqueeze(0) for key in
                   ['observation.state', 'observation.environment_state']}
            with torch.inference_mode():
                pred.append(policy.select_action(obs).squeeze(0).numpy())
            truth.append(sample['action'].numpy())
        truth, pred = np.array(truth), np.array(pred)
        if not np.isfinite(pred).all():
            raise ValueError('Policy returned nonfinite actions')
        error = pred - truth
        results.append({'episode': episode, 'frames': end-start,
                        'rmse_rad': float(np.sqrt(np.mean(error**2))),
                        'joint_rmse_rad': np.sqrt(np.mean(error**2, axis=0)).tolist()})
        if first is None:
            first = truth, pred
    payload = {'evaluation': 'offline recorded-state action prediction',
               'does_not_establish_closed_loop_success': True,
               'episodes': results, 'joint_order': ['joint1', 'joint2', 'joint4', 'joint3', 'hand']}
    (args.output_dir / 'offline-evaluation.json').write_text(json.dumps(payload, indent=2) + '\n')
    truth, pred = first
    fig, axes = plt.subplots(5, 1, figsize=(10, 9), sharex=True)
    times = np.arange(len(truth)) / dataset.fps
    for j, ax in enumerate(axes):
        ax.plot(times, truth[:, j], label='Demonstrator command', linewidth=1.5)
        ax.plot(times, pred[:, j], label='ACT prediction', linewidth=1.2)
        ax.set_ylabel(payload['joint_order'][j] + ' [rad]')
        ax.grid(alpha=0.25)
    axes[0].legend(loc='upper right')
    axes[0].set_title('Offline prediction on recorded states (episode 0)')
    axes[-1].set_xlabel('Simulation time from start [s]')
    fig.tight_layout()
    fig.savefig(args.output_dir / 'offline-prediction.png', dpi=140)
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
