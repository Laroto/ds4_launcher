# ds4_launcher

Convenience package for driving ANTSY from a DualShock 4. This repo is mostly launch and config, plus one small bridge node, `ds4_body_pose_mode.py`, that switches between walking mode and body-pose mode and handles one-shot service/button actions.

## Launch file

Run it with:

```bash
ros2 launch ds4_launcher joy_teleop.launch.py
```

That launch starts three nodes:

- `joy/joy_node`
- `teleop_twist_joy/teleop_node`
- `ds4_launcher/ds4_body_pose_mode.py`

## Nodes and parameters

### `joy_node`

This is the standard ROS joystick driver. In this launch file it gets one parameter:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `dev` | `"/dev/input/js0"` | Linux joystick device path used to read the DS4. |

### `teleop_twist_joy_node`

This is the standard `teleop_twist_joy` node. Its parameters come from `config/keybinds.yaml`.

Parameters:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `enable_button` | `5` | Deadman button index. Here it is DS4 `R1`. |
| `enable_turbo_button` | `4` | Turbo-enable button index. Here it is DS4 `L1`. |
| `axis_linear.x` | `1` | Axis index used for walking `linear.x` and body-pose `linear.x`. |
| `axis_linear.y` | `0` | Axis index used for walking `linear.y` and body-pose `linear.y`. |
| `axis_linear.z` | `7` | Axis index used for body-pose `linear.z`. |
| `scale_linear.x` | `0.25` | Normal walking/body-pose scale for `linear.x`. |
| `scale_linear.y` | `0.18` | Normal walking/body-pose scale for `linear.y`. |
| `scale_linear.z` | `0.03` | Normal body-pose scale for `linear.z`. |
| `scale_linear_turbo.x` | `0.50` | Turbo scale for `linear.x`. |
| `scale_linear_turbo.y` | `0.32` | Turbo scale for `linear.y`. |
| `scale_linear_turbo.z` | `0.060` | Turbo scale for `linear.z`. |
| `axis_angular.yaw` | `2` | Axis index used for yaw. |
| `axis_angular.roll` | `3` | Axis index used for body-pose roll. |
| `axis_angular.pitch` | `6` | Axis index used for body-pose pitch. |
| `scale_angular.yaw` | `0.35` | Normal yaw scale. |
| `scale_angular.roll` | `0.2` | Normal roll scale. |
| `scale_angular.pitch` | `0.2` | Normal pitch scale. |
| `scale_angular_turbo.yaw` | `1.0` | Turbo yaw scale. |
| `scale_angular_turbo.roll` | `0.4` | Turbo roll scale. |
| `scale_angular_turbo.pitch` | `0.4` | Turbo pitch scale. |
| `publish_stamped_twist` | `true` | Publish `geometry_msgs/TwistStamped` instead of `Twist`. |

The launch remaps this node’s `cmd_vel` output to `cmd_vel_raw`.

### `ds4_control_bridge`

This is the repo-provided bridge node in `scripts/ds4_body_pose_mode.py`.

Parameters:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `joy_topic` | `"joy"` | Joystick topic to read button state from. |
| `mode_topic` | `"body_pose_mode"` | Topic used to publish and monitor current body-pose mode. |
| `input_cmd_topic` | `"cmd_vel_raw"` | Incoming command topic from `teleop_twist_joy`. |
| `output_cmd_topic` | `"cmd_vel"` | Outgoing command topic after speed scaling and mode handling. |
| `body_pose_button` | `1` | Button index that publishes `body_pose_mode=true` once. Default DS4 mapping: `Circle`. |
| `walking_button` | `3` | Button index that publishes `body_pose_mode=false` once. Default DS4 mapping: `Square`. |
| `rest_pose_button` | `2` | Button index that requests the rest pose and walking mode. Default DS4 mapping: `Triangle`. |
| `rest_pose_service` | `"go_to_rest_pose"` | Service called when the rest-pose button is pressed. |
| `recovery_button` | `0` | Button index used for the disable/recover toggle. Default DS4 mapping: `Cross`. |
| `motor_disable_service` | `"/motors/disable"` | Service called on the first recovery-button press. |
| `motor_enable_service` | `"/motors/enable"` | Service called on the second recovery-button press. |
| `control_reset_service` | `"/control/reset"` | Service called before re-enabling motors on the second recovery-button press. |
| `speed_axis` | `7` | Axis index used for speed scaling in walking mode. Default DS4 mapping: D-pad up/down. |
| `speed_axis_threshold` | `0.5` | Minimum axis magnitude needed before a speed-step event is triggered. |
| `speed_step_ratio` | `0.1` | Per-step speed scaling increment. |
| `min_speed_scale` | `0.5` | Lower clamp for the walking speed multiplier. |
| `max_speed_scale` | `1.5` | Upper clamp for the walking speed multiplier. |

## Default controls

- `R1`: deadman
- `L1`: turbo
- left stick: walking `x/y`
- right stick left/right: yaw
- right stick up/down: roll in body-pose mode
- D-pad left/right: pitch in body-pose mode
- D-pad up/down: Z in body-pose mode, speed scaling in walking mode
- `Circle`: publish `body_pose_mode=true` once
- `Square`: publish `body_pose_mode=false` once
- `Triangle`: publish walking mode and call `go_to_rest_pose`
- `Cross`: first press disables motors, second press resets control and re-enables motors
