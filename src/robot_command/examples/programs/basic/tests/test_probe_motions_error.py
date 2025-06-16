"""
Basic test cases to demonstrate expected behavior for a probe. Before running
this program, make sure that the probe is connected, configured, and properly
mounted to the end-effector flange.
"""
from robot_command.rpl import *
import rospy
import numpy as np
set_units("mm", "deg")
# Position above work in Z, known to not be in contact
# Position where probe will be in contact
probe_prep_pose = p[-80., 400., 300., -33., 88., 145.]
probe_clearance_pose = p[-80., 400., 200., -33., 88., 145.]
probe_contact_pose = p[-80., 400., 110., -33., 88., 145.]
probe_vel = 0.02
retract_vel = 0.08
traverse_vel = 0.25


# Helper functions


def is_contact_below_clearance(probe_result_pose, clearance_pose):
    return probe_result_pose.z < clearance_pose.z


def assert_probe_contact(probe_res, clearance_pose):
    rospy.loginfo(f"Expect probe contact (clearance position is {clearance_pose}), got result {probe_res}")
    assert probe_res
    assert probe_res[0] == 1
    assert is_contact_below_clearance(probe_res[3], clearance_pose)


def assert_no_probe_contact(probe_res):
    rospy.loginfo(f"Expect no probe contact and empty result, got result {probe_res}")
    assert not probe_res


# Individual test cases


def test_probe_result_validity():
    movej(probe_prep_pose, v=traverse_vel)
    movel(probe_clearance_pose, v=traverse_vel)
    res = movel(probe_contact_pose, probe=2, v=probe_vel)
    assert_probe_contact(res, probe_clearance_pose)

    # Retract, then do an "optional" probe move that won't reach contact
    movel(probe_prep_pose, v=retract_vel, probe=6)
    res = movel(probe_clearance_pose, v=probe_vel, probe=3)
    assert_no_probe_contact(res)


def test_probe_start_in_contact_error():
    movej(probe_prep_pose, v=traverse_vel)
    movej(probe_clearance_pose, v=traverse_vel)
    rospy.loginfo("Expect failure to reach contact and no result")
    res = movel(probe_contact_pose, probe=2, v=probe_vel)
    assert_probe_contact(res, probe_clearance_pose)

    for m in [0, 2, 3]:
        try:
            # This move should fail with an error because it's in contact
            rospy.loginfo(f"Testing contact-at-start for probe mode {m}")
            res = movel(probe_clearance_pose, probe=m, v=probe_vel)
            assert False
        except ProbeContactAtStartError as e:
            rospy.loginfo(f"Caught expected exception {e}")
    movel(probe_prep_pose, v=retract_vel, probe=6)


def test_probe_expect_contact_failure():
    # Test for failure to reach contact in the probe
    movej(probe_prep_pose, v=traverse_vel)
    try:
        movel(probe_clearance_pose, probe=2, v=retract_vel, a=0.25)
        assert False
    except ProbeFailedError as e:
        rospy.loginfo(f"Caught expected exception {e}")
    movel(probe_clearance_pose, probe=6, v=probe_vel, a=0.25)


def test_probe_repeatability():
    # This test is a heuristic to look for large repeatability errors in probing
    movej(probe_prep_pose, v=traverse_vel)
    movel(probe_clearance_pose, v=traverse_vel)
    probe_poses = []
    for k in range(10):
        res = movel(probe_contact_pose, probe=2, v=probe_vel, a=0.25)
        assert_probe_contact(res, probe_clearance_pose)
        probe_poses.append(res[3].to_list())
        movel(probe_clearance_pose, probe=6, v=retract_vel, a=0.25)

    pose_array = np.array(probe_poses)
    rospy.loginfo(f"Probe result data: {pose_array}")
    deltas = np.max(pose_array, 0) - np.min(pose_array, 0)
    rospy.loginfo(f"deltas (at flange): {deltas}")
    # TODO tool offset / probe model
    # For now, do this indirectly by constraining the deltas (1mm, 0.001rad)
    # Note that probe repeatability depends on velocity, planning accuracy, etc.
    assert np.max(deltas[0:3]) < 1e-3


def main():
    # Move to initial position
    #test_probe_result_validity()
    #test_probe_start_in_contact_error()
    #test_probe_expect_contact_failure()
    test_probe_repeatability()

    movej(probe_prep_pose, v=retract_vel)
    notify("Test Passed")
    exit()
