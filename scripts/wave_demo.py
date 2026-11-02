"""Demonstrator for the "wave" task: publishes CRANE+ V2 joint commands in the same
format as physicalai_teleop/teleop_keyboard.py (20 Hz, arm + gripper trajectories)."""
import math
import random
import sys

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

ARM_JOINT_NAMES = ['crane_plus_joint1', 'crane_plus_joint2', 'crane_plus_joint4', 'crane_plus_joint3']
GRIPPER_JOINT_NAME = 'crane_plus_joint_hand'


def point(positions):
    pt = JointTrajectoryPoint()
    pt.positions = [float(p) for p in positions]
    pt.time_from_start.sec = 0
    pt.time_from_start.nanosec = int(0.1 * 1e9)
    return pt


class WaveDemo(Node):
    """Raise the arm, wave joint4 three times while opening/closing the hand, return home."""

    def __init__(self, seed):
        super().__init__('crane_plus_wave_demo', parameter_overrides=[Parameter('use_sim_time', value=True)])
        rng = random.Random(seed)
        self.amp = rng.uniform(0.45, 0.65)     # wave amplitude [rad]
        self.period = rng.uniform(2.2, 2.5)    # peak wrist speed < URDF's 2 rad/s
        self.lift = rng.uniform(-1.0, -0.8)    # joint2 when raised [rad]
        self.yaw = rng.uniform(0.2, 0.3)       # sweep from -yaw to +yaw [rad]
        self.arm_pub = self.create_publisher(JointTrajectory, '/crane_plus_arm_controller/joint_trajectory', 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, '/crane_plus_gripper_controller/joint_trajectory', 10)
        self.t = 0.0
        self.duration = 2.0 + 3 * self.period + 2.0
        self.timer = self.create_timer(0.05, self.step)  # 20Hz, same as teleop_keyboard

    def pose(self, t):
        up = min(t / 2.0, 1.0)                          # 0-2 s: raise
        wave_t = t - 2.0
        wave_end = 3 * self.period
        if wave_t > wave_end:                          # last 2 s: lower
            up = max(1.0 - (wave_t - wave_end) / 2.0, 0.0)
        waving = 0.0 <= wave_t <= wave_end
        progress = min(max(wave_t / wave_end, 0.0), 1.0)
        j1 = self.yaw * (2 * progress - 1) * up
        j2 = self.lift * up
        j3 = -0.6 * up
        j4 = self.amp * math.sin(2 * math.pi * wave_t / self.period) if waving else 0.0
        # Continuous opening/closing, with a different phase from wrist motion.
        hand = 0.15 * (1 - math.cos(2 * math.pi * wave_t / self.period)) if waving else 0.0
        return [j1, j2, j4, j3], hand

    def step(self):
        arm, hand = self.pose(self.t)
        jt = JointTrajectory(joint_names=ARM_JOINT_NAMES, points=[point(arm)])
        jg = JointTrajectory(joint_names=[GRIPPER_JOINT_NAME], points=[point([hand])])
        self.arm_pub.publish(jt)
        self.gripper_pub.publish(jg)
        self.t += 0.05
        if self.t > self.duration + 0.5:  # hold the exact zero pose before stopping
            raise SystemExit


def main():
    rclpy.init()
    node = WaveDemo(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
