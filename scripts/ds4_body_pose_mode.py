#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool


class Ds4BodyPoseMode(Node):
    def __init__(self):
        super().__init__("ds4_body_pose_mode")

        self.declare_parameter("joy_topic", "joy")
        self.declare_parameter("mode_topic", "body_pose_mode")
        self.declare_parameter("body_pose_button", 1)
        self.declare_parameter("walking_button", 3)

        joy_topic = self.get_parameter("joy_topic").get_parameter_value().string_value
        mode_topic = self.get_parameter("mode_topic").get_parameter_value().string_value
        self.body_pose_button = (
            self.get_parameter("body_pose_button").get_parameter_value().integer_value)
        self.walking_button = (
            self.get_parameter("walking_button").get_parameter_value().integer_value)

        self.previous_buttons = []
        self.publisher = self.create_publisher(Bool, mode_topic, 10)
        self.create_subscription(Joy, joy_topic, self.joy_callback, 10)

    def joy_callback(self, msg: Joy):
        self.publish_on_press(msg, self.body_pose_button, True)
        self.publish_on_press(msg, self.walking_button, False)
        self.previous_buttons = list(msg.buttons)

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
        self.publisher.publish(mode_msg)
        self.get_logger().info(
            f"Published body_pose_mode={str(enabled).lower()} from DS4 button {button_index}.")


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
