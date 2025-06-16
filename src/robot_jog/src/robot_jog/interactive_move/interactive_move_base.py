class InteractiveMoveBase:
    JOG_OFFSET_SET_POSE_SERVICE = 'jog/offset/set_pose'
    JOG_OFFSET_SET_JOINTS_SERVICE = 'jog/offset/set_joints'
    JOG_OFFSET_CHECK_POSE_REACHABLE_SERVICE = 'jog/offset/check_pose_reachable'
    JOG_ABSOLUTE_SET_POSE_SERVICE = 'jog/absolute/set_pose'
    JOG_ABSOLUTE_SET_JOINTS_SERVICE = 'jog/absolute/set_joints'
    JOG_ABSOLUTE_CHECK_POSE_REACHABLE_SERVICE = (
        'jog/absolute/check_pose_reachable'
    )
    JOG_CONTINUOUS_SET_POSE_SERVICE = 'jog/continuous/set_pose'
    JOG_CONTINUOUS_SET_JOINTS_SERVICE = 'jog/continuous/set_joints'
    EXECUTE_TRAJECTORY_FEEDBACK_TOPIC = 'execute_trajectory/feedback'
    JOG_EXECUTE_TOPIC = 'jog/execute'
    JOG_ACTIVE_TOPIC = 'jog/active'
    JOG_FAILED_TOPIC = 'jog/failed'
    JOG_COMPLETED_TOPIC = 'jog/completed'
    PLANNING_FRAME_TOPIC = 'user_frames/active_frame'
    TOOL_FRAME_TOPIC = 'tool_frames/active_frame'
    JOGRATE_PARAM = 'user_config/jograte'
