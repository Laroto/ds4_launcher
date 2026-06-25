#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool


class Ds4BodyPoseMode(Node):
    def __init__(self):
        super().__init__("ds4_control_bridge")

        self.declare_parameter("joy_topic", "joy")
        self.declare_parameter("mode_topic", "body_pose_mode")
        self.declare_parameter("input_cmd_topic", "cmd_vel_raw")
        self.declare_parameter("output_cmd_topic", "cmd_vel")
        self.declare_parameter("body_pose_button", 1)
        self.declare_parameter("walking_button", 3)
        self.declare_parameter("speed_axis", 7)
        self.declare_parameter("speed_axis_threshold", 0.5)
        self.declare_parameter("speed_step_ratio", 0.1)
        self.declare_parameter("min_speed_scale", 0.5)
        self.declare_parameter("max_speed_scale", 1.5)

        joy_topic = self.get_parameter("joy_topic").get_parameter_value().string_value
        mode_topic = self.get_parameter("mode_topic").get_parameter_value().string_value
        input_cmd_topic = (
            self.get_parameter("input_cmd_topic").get_parameter_value().string_value)
        output_cmd_topic = (
            self.get_parameter("output_cmd_topic").get_parameter_value().string_value)
        self.body_pose_button = (
            self.get_parameter("body_pose_button").get_parameter_value().integer_value)
        self.walking_button = (
            self.get_parameter("walking_button").get_parameter_value().integer_value)
        self.speed_axis = self.get_parameter("speed_axis").get_parameter_value().integer_value
        self.speed_axis_threshold = (
            self.get_parameter("speed_axis_threshold").get_parameter_value().double_value)
        self.speed_step_ratio = (
            self.get_parameter("speed_step_ratio").get_parameter_value().double_value)
        self.min_speed_scale = (
            self.get_parameter("min_speed_scale").get_parameter_value().double_value)
        self.max_speed_scale = (
            self.get_parameter("max_speed_scale").get_parameter_value().double_value)

        self.previous_buttons = []
        self.previous_speed_axis_state = 0
        self.body_pose_mode_enabled = False
        self.speed_scale = 1.0

        self.mode_publisher = self.create_publisher(Bool, mode_topic, 10)
        self.cmd_publisher = self.create_publisher(TwistStamped, output_cmd_topic, 10)
        self.create_subscription(Joy, joy_topic, self.joy_callback, 10)
        self.create_subscription(Bool, mode_topic, self.mode_callback, 10)
        self.create_subscription(TwistStamped, input_cmd_topic, self.cmd_callback, 10)

    def joy_callback(self, msg: Joy):
        self.publish_on_press(msg, self.body_pose_button, True)
        self.publish_on_press(msg, self.walking_button, False)
        self.update_speed_scale(msg)
        self.previous_buttons = list(msg.buttons)

    def mode_callback(self, msg: Bool):
        self.body_pose_mode_enabled = msg.data

    def cmd_callback(self, msg: TwistStamped):
        if self.body_pose_mode_enabled:
            self.cmd_publisher.publish(msg)
            return

        scaled_msg = TwistStamped()
        scaled_msg.header = msg.header
        scaled_msg.twist.linear.x = msg.twist.linear.x * self.speed_scale
        scaled_msg.twist.linear.y = msg.twist.linear.y * self.speed_scale
        scaled_msg.twist.linear.z = msg.twist.linear.z * self.speed_scale
        scaled_msg.twist.angular.x = msg.twist.angular.x * self.speed_scale
        scaled_msg.twist.angular.y = msg.twist.angular.y * self.speed_scale
        scaled_msg.twist.angular.z = msg.twist.angular.z * self.speed_scale
        self.cmd_publisher.publish(scaled_msg)

    def publish_on_press(self, msg: Joy, button_index: int, enabled: bool):
        if button_index < 0 or button_index >= len(msg.buttons):
            return

        was_pressed = (
            button_index < len(self.previous_buttons) and
            self.previous_buttons[button_index] == 1)
        is_pressed = msg.buttons[button_index] == 1
        if not is_pressed or was_pressed:
            return

        mode_msg = Bool()
        mode_msg.data = enabled
        self.mode_publisher.publish(mode_msg)
        self.body_pose_mode_enabled = enabled
        self.get_logger().info(
            f"Published body_pose_mode={str(enabled).lower()} from DS4 button {button_index}.")

    def update_speed_scale(self, msg: Joy):
        if self.body_pose_mode_enabled or self.speed_axis < 0 or self.speed_axis >= len(msg.axes):
            self.previous_speed_axis_state = 0
            return

        axis_value = msg.axes[self.speed_axis]
        axis_state = 0
        if axis_value >= self.speed_axis_threshold:
            axis_state = 1
        elif axis_value <= -self.speed_axis_threshold:
            axis_state = -1

        if axis_state == self.previous_speed_axis_state or axis_state == 0:
            self.previous_speed_axis_state = axis_state
            return

        if axis_state > 0:
            self.speed_scale = min(
                self.max_speed_scale, self.speed_scale * (1.0 + self.speed_step_ratio))
        else:
            self.speed_scale = max(
                self.min_speed_scale, self.speed_scale / (1.0 + self.speed_step_ratio))

        self.previous_speed_axis_state = axis_state
        self.get_logger().info(f"Updated walking speed scale to {self.speed_scale:.2f}.")


def main():
    rclpy.init()
    node = Ds4BodyPoseMode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
