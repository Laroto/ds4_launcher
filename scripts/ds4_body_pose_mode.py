#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool
from std_srvs.srv import Trigger


class Ds4BodyPoseMode(Node):
    def __init__(self):
        super().__init__("ds4_control_bridge")

        self.declare_parameter("joy_topic", "joy")
        self.declare_parameter("mode_topic", "body_pose_mode")
        self.declare_parameter("input_cmd_topic", "cmd_vel_raw")
        self.declare_parameter("output_cmd_topic", "cmd_vel")
        self.declare_parameter("body_pose_button", 1)
        self.declare_parameter("walking_button", 3)
        self.declare_parameter("rest_pose_button", 2)
        self.declare_parameter("rest_pose_service", "go_to_rest_pose")
        self.declare_parameter("recovery_button", 0)
        self.declare_parameter("motor_disable_service", "/motors/disable")
        self.declare_parameter("motor_enable_service", "/motors/enable")
        self.declare_parameter("control_reset_service", "/control/reset")
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
        self.rest_pose_button = (
            self.get_parameter("rest_pose_button").get_parameter_value().integer_value)
        self.rest_pose_service = (
            self.get_parameter("rest_pose_service").get_parameter_value().string_value)
        self.recovery_button = (
            self.get_parameter("recovery_button").get_parameter_value().integer_value)
        self.motor_disable_service = (
            self.get_parameter("motor_disable_service").get_parameter_value().string_value)
        self.motor_enable_service = (
            self.get_parameter("motor_enable_service").get_parameter_value().string_value)
        self.control_reset_service = (
            self.get_parameter("control_reset_service").get_parameter_value().string_value)
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
        self.recovery_armed = False

        self.mode_publisher = self.create_publisher(Bool, mode_topic, 10)
        self.cmd_publisher = self.create_publisher(TwistStamped, output_cmd_topic, 10)
        self.rest_pose_client = self.create_client(Trigger, self.rest_pose_service)
        self.motor_disable_client = self.create_client(Trigger, self.motor_disable_service)
        self.motor_enable_client = self.create_client(Trigger, self.motor_enable_service)
        self.control_reset_client = self.create_client(Trigger, self.control_reset_service)
        self.rest_pose_future = None
        self.pending_trigger_futures = []
        self.create_subscription(Joy, joy_topic, self.joy_callback, 10)
        self.create_subscription(Bool, mode_topic, self.mode_callback, 10)
        self.create_subscription(TwistStamped, input_cmd_topic, self.cmd_callback, 10)

    def joy_callback(self, msg: Joy):
        self.publish_on_press(msg, self.body_pose_button, True)
        self.publish_on_press(msg, self.walking_button, False)
        self.call_rest_pose_on_press(msg, self.rest_pose_button)
        self.recover_control_on_press(msg, self.recovery_button)
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

        self.publish_mode(enabled)
        self.get_logger().info(
            f"Published body_pose_mode={str(enabled).lower()} from DS4 button {button_index}.")

    def call_rest_pose_on_press(self, msg: Joy, button_index: int):
        if button_index < 0 or button_index >= len(msg.buttons):
            return

        was_pressed = (
            button_index < len(self.previous_buttons) and
            self.previous_buttons[button_index] == 1)
        is_pressed = msg.buttons[button_index] == 1
        if not is_pressed or was_pressed:
            return

        self.publish_mode(False)

        if not self.rest_pose_client.wait_for_service(timeout_sec=0.0):
            self.get_logger().warning(
                f"Rest-pose service '{self.rest_pose_service}' is not available.")
            return

        self.rest_pose_future = self.rest_pose_client.call_async(Trigger.Request())
        self.rest_pose_future.add_done_callback(self.on_rest_pose_response)
        self.get_logger().info("Requested resting pose from DS4 triangle button.")

    def recover_control_on_press(self, msg: Joy, button_index: int):
        if button_index < 0 or button_index >= len(msg.buttons):
            return

        was_pressed = (
            button_index < len(self.previous_buttons) and
            self.previous_buttons[button_index] == 1)
        is_pressed = msg.buttons[button_index] == 1
        if not is_pressed or was_pressed:
            return

        self.publish_mode(False)
        self.publish_zero_command()
        if not self.recovery_armed:
            self.call_trigger_service(
                self.motor_disable_client, self.motor_disable_service, "motor disable")
            self.recovery_armed = True
            self.get_logger().warning(
                "Requested motor disable from DS4 cross button. Press cross again to reset control and enable motors.")
            return

        self.call_trigger_service(
            self.control_reset_client, self.control_reset_service, "control reset")
        self.call_trigger_service(
            self.motor_enable_client, self.motor_enable_service, "motor enable")
        self.recovery_armed = False
        self.get_logger().warning("Requested control reset and motor enable from DS4 cross button.")

    def publish_mode(self, enabled: bool):
        mode_msg = Bool()
        mode_msg.data = enabled
        self.mode_publisher.publish(mode_msg)
        self.body_pose_mode_enabled = enabled

    def publish_zero_command(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        self.cmd_publisher.publish(msg)

    def call_trigger_service(self, client, service_name: str, description: str):
        if not client.wait_for_service(timeout_sec=0.0):
            self.get_logger().warning(f"{description} service '{service_name}' is not available.")
            return

        future = client.call_async(Trigger.Request())
        self.pending_trigger_futures.append(future)
        future.add_done_callback(
            lambda completed_future: self.on_trigger_response(completed_future, description))

    def on_rest_pose_response(self, future):
        try:
            response = future.result()
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warning(f"Rest-pose service call failed: {exc}")
            return

        if response.success:
            self.get_logger().info(response.message)
        else:
            self.get_logger().warning(response.message)

    def on_trigger_response(self, future, description: str):
        try:
            response = future.result()
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warning(f"{description} service call failed: {exc}")
            return
        finally:
            if future in self.pending_trigger_futures:
                self.pending_trigger_futures.remove(future)

        if response.success:
            self.get_logger().info(f"{description}: {response.message}")
        else:
            self.get_logger().warning(f"{description}: {response.message}")

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
