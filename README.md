# ds4_launcher
Simple PS4 controller launcher with custom config files for controlling your robot with a remote.
This package only contains the launch files with the custom parameter files.

## How to use:

- Connect the remote (choose 1 of the options)
    - USB cable
    - Run `ds4drv` - this is a service connects to the remote via Bluetooth and creates all the input devices for normal
- Launch the file with `ros2 launch ds4_launcher joy_teleop.launch.py`

## Keybinds:

- R1 -> Deadman switch
- L1 -> Fast mode (can be used in alternative to deadman switch)
- Left Up/Down thumbstick -> linear X velocity.
- Left Left/Right thumbstick -> linear Y velocity
- Right Left/Right thumbstick -> yaw
- Right Up/Down thumbstick -> roll in body-pose mode
- D-pad Left/Right -> pitch in body-pose mode
- D-pad Up/Down -> Z in body-pose mode, walking-speed scale in walking mode
- Circle -> publish `body_pose_mode=true` once
- Square -> publish `body_pose_mode=false` once
- D-pad Up/Down in walking mode -> increase/decrease speed scale in 10% steps
