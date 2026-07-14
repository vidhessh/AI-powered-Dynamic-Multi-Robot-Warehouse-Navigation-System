#!/usr/bin/env python3
"""
lot_navigator_node.py — pure Nav2, single-threaded, multi-bot.

BasicNavigator IS the node — it also owns the /target_lot subscription
directly, so there's only ever one node being spun, on one thread, using
nav2_simple_commander's own blocking calls exactly as designed.

Mid-navigation target switching works because isTaskComplete() internally
processes pending callbacks (including target_lot) each time it's polled —
so a new command is seen within one poll cycle and the current goal is
canceled immediately.

Shared lots: multiple bots CAN be sent to the same lot color at once, and
both are sent the exact same goal coordinate — no manual offset. Collision
avoidance is handled the normal Nav2 way: each bot's own laser scan marks
any other robot it sees as a live obstacle in its local costmap (same as
it would any moving crate), so whichever bot arrives second stops short
of the first instead of driving into it.
"""

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from std_msgs.msg import String

from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

LOT_POSITIONS = {
    'red':    (5.0, 2.0),
    'green':  (5.0, -2.0),
    'blue':   (8.0, 2.0),
    'yellow': (8.0, -2.0),
    'origin': (-7.0, 0.0),
}

# per-bot (x, y) offset added to any lot's center, in meters. Forward is
# +x, so right-of-center is -y and left-of-center is +y. Bot1 always
# parks on the right, bot3 always on the left, both centered on the lot's
# width (lot is 1.5m x 1.5m, so 0.4m off-center keeps them well inside the
# pad, not at a corner) and 0.8m apart — safely more than the combined
# 0.6m footprint of two 0.3m-radius robots.
LOT_OFFSETS = {
    'bot1': (0.0, -0.4),  # right of center
    'bot3': (0.0, 0.4),   # left of center
}


class LotNavigator(BasicNavigator):
    def __init__(self):
        super().__init__()
        self.ns = self.get_namespace()  # e.g. '/bot1', or '/' if unnamespaced
        if self.ns in ('', '/'):
            self.ns = self.get_name()
        self.ns = self.ns.lstrip('/')

        self._pending_target = None

        self.status_pub = self.create_publisher(String, 'lot_status', 10)
        self.create_subscription(String, 'target_lot', self._target_cb, 10)

        self._cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)

    def _target_cb(self, msg):
        color = msg.data.strip().lower()
        self.get_logger().info(f"target_lot message received: raw='{color}'")
        if color not in LOT_POSITIONS:
            self.get_logger().warn(f"Unknown target '{color}'")
            self.status_pub.publish(String(data=f"unknown_lot:{color}"))
            return
        self._pending_target = color

    def _stop(self):
        # single hard-stop publish; the real hold now comes from the
        # continuous idle-hold in run() below, which keeps re-asserting
        # zero velocity every loop cycle for as long as there's no active
        # target — so nothing trailing from Nav2 can out-race it.
        self._cmd_vel_pub.publish(Twist())

    def _make_pose(self, color):
        x, y = LOT_POSITIONS[color]
        ox, oy = LOT_OFFSETS.get(self.ns, (0.0, 0.0))
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x + ox
        pose.pose.position.y = y + oy
        pose.pose.orientation.w = 1.0
        return pose

    def run(self):
        self.get_logger().info("Waiting for Nav2 to become active...")
        self.waitUntilNav2Active()
        self.get_logger().info(
            "Nav2 active. Send a /target_lot command: " +
            ", ".join(f"{k}={v}" for k, v in LOT_POSITIONS.items())
        )

        current_target = None

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.2)

            # continuous idle-hold: as long as we're not actively navigating
            # (no current target), keep re-asserting zero velocity every
            # cycle. This is what actually stops any post-arrival wander —
            # a one-time stop can lose a race against a trailing command
            # from controller_server; this can't, since it never stops
            # reasserting.
            if current_target is None:
                self._cmd_vel_pub.publish(Twist())

            if self._pending_target is None or self._pending_target == current_target:
                continue

            current_target = self._pending_target
            self._pending_target = None

            self.get_logger().info(f"Sending Nav2 goal: '{current_target}'")
            self.status_pub.publish(String(data=f"heading_to:{current_target}"))
            self.goToPose(self._make_pose(current_target))

            switched = False
            while not self.isTaskComplete():
                if self._pending_target is not None and self._pending_target != current_target:
                    self.get_logger().info(
                        f"New target '{self._pending_target}' received — canceling '{current_target}'."
                    )
                    self.cancelTask()
                    while not self.isTaskComplete():
                        rclpy.spin_once(self, timeout_sec=0.1)
                    switched = True
                    break

            if switched:
                current_target = None
                continue

            result = self.getResult()
            if result == TaskResult.SUCCEEDED:
                self.get_logger().info(f"Goal reached: {current_target}")
                self._stop()
                self.status_pub.publish(String(data=f"reached:{current_target}"))
            elif result == TaskResult.CANCELED:
                self.get_logger().info(f"Goal to {current_target} canceled.")
            else:
                self.get_logger().warn(f"Goal to {current_target} failed: {result}")
                self.status_pub.publish(String(data=f"failed:{current_target}"))

            current_target = None


def main():
    rclpy.init()
    node = LotNavigator()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

