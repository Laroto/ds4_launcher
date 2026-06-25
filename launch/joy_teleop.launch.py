from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    share_dir = get_package_share_directory('ds4_launcher')
    config_file = os.path.join(share_dir, 'config', 'keybinds.yaml')
    bridge_config_file = os.path.join(share_dir, 'config', 'body_pose_mode.yaml')

    print(f"Loading configuration file from: {config_file}")
 
    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    if not os.path.isfile(bridge_config_file):
        raise FileNotFoundError(f"Config file not found: {bridge_config_file}")

    return LaunchDescription([
        # Node to handle joystick input
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            output='screen',
            parameters=[{'dev': '/dev/input/js0'}],
        ),
        # Node to handle teleoperation
        Node(
            package='teleop_twist_joy',
            executable='teleop_node',
            name='teleop_twist_joy_node',
            output='screen',
            parameters=[config_file],
            remappings=[('cmd_vel', 'cmd_vel_raw')],
        ),
        Node(
            package='ds4_launcher',
            executable='ds4_body_pose_mode.py',
            name='ds4_control_bridge',
            output='screen',
            parameters=[bridge_config_file],
        )
    ])
