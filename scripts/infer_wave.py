"""Deploy the lecture's LeRobot ACT on live Gazebo states and record each action."""
import argparse
import csv
import math
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import torch
from lerobot.common.policies.act.modeling_act import ACTPolicy

JOINTS = ['crane_plus_joint1', 'crane_plus_joint2', 'crane_plus_joint4',
          'crane_plus_joint3', 'crane_plus_joint_hand']
# CRANE+ V2 URDF limits, reordered to match the lecture's teleop/inference.
LOW = [-2.6179, -1.8247, -1.8400, -2.5565, -0.7088]
HIGH = [2.6179, 1.7837, 1.7683, 2.4542, 0.6679]


class InferWave(Node):
    def __init__(self, args):
        super().__init__('crane_wave_act', parameter_overrides=[Parameter('use_sim_time', value=True)])
        torch.set_num_threads(2)
        self.policy = ACTPolicy.from_pretrained(str(args.model_path)).to('cpu').eval()
        self.policy.config.n_action_steps = args.action_steps
        self.policy.reset()
        self.arm = self.create_publisher(JointTrajectory, '/crane_plus_arm_controller/joint_trajectory', 10)
        self.hand = self.create_publisher(JointTrajectory, '/crane_plus_gripper_controller/joint_trajectory', 10)
        self.sub = self.create_subscription(JointState, '/joint_states', self.observe, 10)
        self.state = None
        self.start = None
        self.duration = args.duration
        self.done = False
        args.log.parent.mkdir(parents=True, exist_ok=True)
        self.log_file = args.log.open('w', newline='')
        self.writer = csv.writer(self.log_file)
        self.writer.writerow(['time', *['state_'+j for j in JOINTS], *['action_'+j for j in JOINTS], 'clipped'])
        self.timer = self.create_timer(0.05, self.step)

    def observe(self, msg):
        mapping = dict(zip(msg.name, msg.position))
        if all(j in mapping for j in JOINTS):
            self.state = [mapping[j] for j in JOINTS]

    def step(self):
        if self.state is None:
            return
        now = self.get_clock().now().nanoseconds / 1e9
        if self.start is None:
            self.start = now
        elapsed = now - self.start
        if elapsed >= self.duration:
            self.done = True
            return
        state = torch.tensor(self.state, dtype=torch.float32).unsqueeze(0)
        with torch.inference_mode():
            action = self.policy.select_action({'observation.state': state,
                                               'observation.environment_state': state}).flatten().tolist()
        if len(action) != 5 or not all(math.isfinite(x) for x in action):
            raise RuntimeError('ACT returned an invalid action')
        bounded = [min(max(x, lo), hi) for x, lo, hi in zip(action, LOW, HIGH)]
        for publisher, names, positions in [(self.arm, JOINTS[:4], bounded[:4]),
                                             (self.hand, JOINTS[4:], bounded[4:])]:
            point = JointTrajectoryPoint(positions=positions)
            point.time_from_start.nanosec = 100_000_000
            publisher.publish(JointTrajectory(joint_names=names, points=[point]))
        self.writer.writerow([elapsed, *self.state, *bounded, int(action != bounded)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-path', type=Path, required=True)
    parser.add_argument('--duration', type=float, default=15.0)
    parser.add_argument('--action-steps', type=int, default=1, choices=range(1,17))
    parser.add_argument('--log', type=Path, required=True)
    args = parser.parse_args()
    rclpy.init()
    node = InferWave(args)
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=1)
    except KeyboardInterrupt:
        pass
    finally:
        node.log_file.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
