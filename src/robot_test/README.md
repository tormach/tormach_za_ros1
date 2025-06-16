# Robot System Test Suite

This ROS package contains system level tests for the robot system.

To run all test programs launch:

```bash
python3 -m pytest $(rospack find robot_test)/tests/simulation
```

```bash
python3 -m pytest $(rospack find robot_test)/tests/simulation/determinism/ test_arm_configs_user_forced_tool_change_mocked.py
```

Note: Alternatively, we should be able to launch the tests via `rostests`,
but for some reason this causes errors with rospy.
```bash
rostest robot_test system_tests.launch
```
