"""Reset between experiments; do not run concurrently with a demonstrator or ACT."""
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

JOINTS = ['crane_plus_joint1', 'crane_plus_joint2', 'crane_plus_joint4',
          'crane_plus_joint3', 'crane_plus_joint_hand']


def main():
    rclpy.init()
    node = Node('crane_wave_reset', parameter_overrides=[Parameter('use_sim_time', value=True)])
    pubs = [node.create_publisher(JointTrajectory, '/crane_plus_arm_controller/joint_trajectory', 10),
            node.create_publisher(JointTrajectory, '/crane_plus_gripper_controller/joint_trajectory', 10)]
    initial = []
    def observe(msg):
        if not initial:
            m = dict(zip(msg.name, msg.position))
            if all(j in m for j in JOINTS):
                initial.extend(m[j] for j in JOINTS)
    sub = node.create_subscription(JointState, '/joint_states', observe, 10)
    while not initial:
        rclpy.spin_once(node, timeout_sec=1)
    start = node.get_clock().now().nanoseconds / 1e9
    done = False
    def step():
        nonlocal done
        elapsed = node.get_clock().now().nanoseconds / 1e9 - start
        scale = max(1 - elapsed / 2, 0)
        values = [x * scale for x in initial]
        for pub, names, angles in [(pubs[0], JOINTS[:4], values[:4]), (pubs[1], JOINTS[4:], values[4:])]:
            point = JointTrajectoryPoint(positions=angles)
            point.time_from_start.nanosec = 100_000_000
            pub.publish(JointTrajectory(joint_names=names, points=[point]))
        done = elapsed >= 3
    timer = node.create_timer(0.05, step)
    while not done:
        rclpy.spin_once(node, timeout_sec=1)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
