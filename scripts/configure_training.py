"""Configure a separate checkout of the lecture's pai_training for this task.

Run with the same Python environment used for conversion/training (requires yaml).
Upstream code is fetched from its source, not copied into the public submission.
"""
import argparse
from pathlib import Path
import yaml


def replace_once(path, old, new):
    text = path.read_text()
    if new in text:
        return
    if text.count(old) != 1:
        raise RuntimeError(f'Unexpected upstream source: {path}, {old!r}')
    path.write_text(text.replace(old, new, 1))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--upstream', type=Path, required=True)
    p.add_argument('--workspace', type=Path, required=True)
    args = p.parse_args()
    upstream, workspace = args.upstream.resolve(), args.workspace.resolve()
    configs = upstream / 'configs'
    data = str(workspace / 'dataset/lerobot_dataset/crane_plus_wave')
    cfg = yaml.safe_load((configs / 'conversion_config.yaml').read_text())
    cfg.update(bag_dir=str(workspace / 'dataset/rosbags/wave'), output_dir=data)
    (configs / 'conversion_config.yaml').write_text(yaml.safe_dump(cfg))
    cfg = yaml.safe_load((configs / 'train_config.yaml').read_text())
    cfg.update(dataset_root=data, repo_id='crane_plus_wave',
               output_directory=str(workspace / 'checkpoints/crane_plus_wave_act'),
               num_workers=0)
    # At 20 Hz, action k is k*0.05 seconds ahead, starting at the present.
    # The lecture config starts at -0.1 seconds and uses 0.1-second spacing.
    cfg['delta_timestamps']['action'] = [round(i / 20, 3) for i in range(cfg['chunk_size'])]
    (configs / 'train_config.yaml').write_text(yaml.safe_dump(cfg, sort_keys=False))
    f = configs / 'crane_features.py'
    text = f.read_text().replace('crane_plus_pekori', 'crane_plus_wave')
    text = text.replace('"pekori"', '"wave"')
    text = text.replace('"joint3", "joint4"', '"joint4", "joint3"')
    lines = [f'root = {data!r}' if line.startswith('root =') else line for line in text.splitlines()]
    f.write_text('\n'.join(lines) + '\n')
    # Match the observation ordering used by the lecture's inference node.
    replace_once(upstream / 'scripts/rosbag2lerobot.py',
                 'j_pos = np.array([msg.position for msg, _ in joint_states])',
                 "joint_order = ['crane_plus_joint1', 'crane_plus_joint2', 'crane_plus_joint4', 'crane_plus_joint3', 'crane_plus_joint_hand']\n                j_pos = np.array([[dict(zip(msg.name, msg.position))[name] for name in joint_order] for msg, _ in joint_states])")
    # Exact 20 Hz timestamps instead of stretching a linspace to the endpoint.
    replace_once(upstream / 'scripts/rosbag2lerobot.py',
                 'target_times = np.linspace(start_time, end_time, num_frames)',
                 'target_times = start_time + np.arange(num_frames) * (1e9 / target_freq)')
    replace_once(upstream / 'scripts/train.py',
                 '    # Create a directory to store the training checkpoint.',
                 '    torch.manual_seed(2026)\n    torch.set_num_threads(4)\n    # Create a directory to store the training checkpoint.')
    replace_once(upstream / 'scripts/train.py',
                 '            step += 1\n',
                 '            step += 1\n            if step in (1000, 2000, 3000):\n                policy.save_pretrained(OUTPUT_DIRECTORY / f"step-{step}")\n')
    print(f'Configured {upstream} for {workspace}')


if __name__ == '__main__':
    main()
