#!/usr/bin/env python3

from pyniryo2 import *
from threading import Event

# Some example arm poses
raised_center_pose = PoseObject(
    x=0.2003, y=-0.0171, z=0.2848,
    roll=-0.769, pitch=1.543, yaw=-0.752
)
raised_center_joints = [-0.081, 0.239, -0.595, -0.017, -1.201, -0.093]

place_center_pose = PoseObject(
    x=0.2495, y=-0.0109, z=0.0945,
    roll=-2.763, pitch=1.533, yaw=-2.725
)
place_center_joints = [-0.042, -0.544, -0.646, -0.041, -0.414, -0.043]

place_left_pose = PoseObject(
    x=0.2464, y=-0.1004, z=0.0930,
    roll=-1.523, pitch=1.557, yaw=-1.398
)
place_left_joints = [-0.386, -0.588, -0.570, -0.029, -0.405, -0.488]

# Default robot arm address
robot_ip: str = "10.10.10.10"

_setup_event: Event = Event()
_move_event: Event = Event()
_has_errors: bool = False


def _calibrate_success_callback(result):
    print('Calibrate:', result['message'])
    _setup_event.set()


def _calibrate_failure_callback(result):
    global _has_errors
    _has_errors = True
    print('Error: Calibrate:', result['message'])
    _setup_event.set()


def _update_tool_success_callback(result):
    print('Update Tool:', result['message'])
    _setup_event.set()


def _update_tool_failure_callback(result):
    global _has_errors
    _has_errors = True
    print('Error: Update Tool:', result['message'])
    _setup_event.set()


def _move_callback(result):
    global _has_errors
    if result['status'] == 1:
        print('  move successful:', result['message'])
    else:
        _has_errors = True
        print('  Error: move failed:', result)
    _move_event.set()


def close(robot):
    robot.arm.go_to_sleep()


def _pose_to_str(pose: PoseObject):
    return ('PoseObject(x={:.4f}, y={:.4f}, z={:.4f}, roll={:.3f}, pitch={:.3f}, yaw={:.3f})'
            .format(pose.x, pose.y, pose.z, pose.roll, pose.pitch, pose.yaw))


def move_pose(robot, title, pose):
    _move_event.clear()
    print('Move to', title)
    robot.arm.move_pose(pose, callback=_move_callback)
    _move_event.wait(30)
    if not _move_event.is_set() or _has_errors:
        print('  exiting due to error')
        close(robot)
        quit()
    print('   move done. Pose is', _pose_to_str(robot.arm.get_pose()))


def move_joints(robot, title, joints):
    _move_event.clear()
    print('Move to', title)
    robot.arm.move_joints(joints, callback=_move_callback)
    _move_event.wait(30)
    if not _move_event.is_set() or _has_errors:
        print('  exiting due to error')
        close(robot)
        quit()
    print('  move done. Pose is', _pose_to_str(robot.arm.get_pose()))


def run_actions(robot):
    move_joints(robot, 'raised center', raised_center_joints)
    robot.pick_place.pick_from_pose(place_left_pose)
    robot.pick_place.place_from_pose(place_center_pose)
    move_joints(robot, 'raised center', raised_center_joints)
    robot.tool.grasp_with_tool()


if __name__ == "__main__":
    ned2_robot: NiryoRobot = NiryoRobot(robot_ip)

    # Calibrate robot arm if needed. The robot arm must always be in a calibrated state
    _setup_event.clear()
    ned2_robot.arm.calibrate_auto(callback=_calibrate_success_callback, errback=_calibrate_failure_callback)
    _setup_event.wait(25)
    if not _setup_event.is_set() or _has_errors:
        close(ned2_robot)
        quit()

    _setup_event.clear()
    ned2_robot.tool.update_tool(callback=_update_tool_success_callback, errback=_update_tool_failure_callback)
    _setup_event.wait(25)
    if not _setup_event.is_set() or _has_errors:
        close(ned2_robot)
        quit()

    run_actions(ned2_robot)

    close(ned2_robot)
