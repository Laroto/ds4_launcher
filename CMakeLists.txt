cmake_minimum_required(VERSION 3.8)
project(ds4_launcher)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(joy REQUIRED)
find_package(teleop_twist_joy REQUIRED)

# Install configuration files
install(
  DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

# Install launch files
install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

# Export the package
ament_package()