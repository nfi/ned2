import re
from threading import Event

from pyniryo2 import *

DEFAULT_ROBOT_IP = "10.10.10.10"
HOME_POSE = PoseObject(x=0.1340, y=-0.0001, z=0.1649, roll=0.002, pitch=1.006, yaw=-0.001)

class Ned2:
    """
    Niryo Ned2 robot arm support object
    """
    def __init__(self, robot_ip: str = DEFAULT_ROBOT_IP):
        self.__host = robot_ip
        self.__setup_event = Event()
        self.__move_event = Event()
        self.__has_errors = False
        self.__current_pose = HOME_POSE
        self.robot = None
        self.verbose = True

    def open(self):
        self.robot = NiryoRobot(self.__host)
        success = self.__call_setup(self.robot.arm.calibrate_auto,
                                    self.__calibrate_success_callback,
                                    self.__calibrate_failure_callback)
        if success:
            success = self.__call_setup(self.robot.tool.update_tool,
                                        self.__update_tool_success_callback,
                                        self.__update_tool_failure_callback)
        if not success:
            self.robot = None
        return success

    def close(self):
        robot = self.robot
        self.robot = None
        if robot:
            robot.arm.go_to_sleep()

    def is_offline(self):
        return self.robot is None

    def __check_offline(self):
        if self.is_offline():
            print("Ned2: offline")
            return True
        return False

    def hardware_status(self):
        return self.robot.arm.hardware_status() if self.robot else 'Not connected'

    def joints_state(self):
        if self.__check_offline():
            return None
        return self.robot.arm.joints_state() if self.robot else None

    def get_pose(self):
        return self.robot.arm.get_pose() if self.robot else self.__current_pose

    def move_pose(self, pose, title=None) -> bool:
        return self.__move_offline(pose, title) if self.is_offline() else self.__move(self.robot.arm.move_pose, pose, title)

    def move_joints(self, joints, title=None) -> bool:
        if self.__check_offline():
            return False
        return self.__move(self.robot.arm.move_joints, joints, title)

    def move_to_home_pose(self):
        if self.is_offline():
            self.__current_pose = HOME_POSE
        else:
            self.robot.arm.move_to_home_pose()

    @staticmethod
    def pose_to_str(pose: PoseObject):
        if not pose:
            return 'None'
        return ('PoseObject(x={:.4f}, y={:.4f}, z={:.4f}, roll={:.3f}, pitch={:.3f}, yaw={:.3f})'
                .format(pose.x, pose.y, pose.z, pose.roll, pose.pitch, pose.yaw))

    @staticmethod
    def pose_from_list(p):
        return PoseObject(p[0], p[1], p[2], p[3], p[4], p[5])

    def pose_from_str(self, input_text):
        try:
            float_pattern = r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?"
            matches = re.findall(float_pattern, input_text)
            float_list = [float(x) for x in matches]
            if len(float_list) != 6:
                raise ValueError("Input string must contain exactly six float numbers.")
            return self.pose_from_list(float_list)
        except ValueError as e:
            print("Failed to parse pose {}: {}".format(input_text, e))
            return None

    def pick_from_pose(self, pose):
        if self.__check_offline():
            return None
        return self.robot.pick_place.pick_from_pose(pose)

    def place_from_pose(self, pose):
        if self.__check_offline():
            return None
        return self.robot.pick_place.place_from_pose(pose)

    def open_gripper(self):
        if self.__check_offline():
            return None
        return self.robot.tool.open_gripper()

    def close_gripper(self):
        if self.__check_offline():
            return None
        return self.robot.tool.close_gripper()

    def __call_setup(self, setup_function, success_callback, failure_callback) -> bool:
        self.__setup_event.clear()
        setup_function(callback=success_callback, errback=failure_callback)
        self.__setup_event.wait(30)
        return self.__setup_event.is_set() and not self.__has_errors

    def __calibrate_success_callback(self, result):
        if self.verbose:
            print('Ned2: Calibrate:', result['message'])
        self.__setup_event.set()

    def __calibrate_failure_callback(self, result):
        self.__has_errors = True
        print('Ned2: Error: Calibrate:', result['message'])
        self.__setup_event.set()

    def __update_tool_success_callback(self, result):
        if self.verbose:
            print('Ned2: Update Tool:', result['message'])
        self.__setup_event.set()

    def __update_tool_failure_callback(self, result):
        self.__has_errors = True
        print('Ned2: Error: Update Tool:', result['message'])
        self.__setup_event.set()

    def __move_callback(self, result):
        if result['status'] == 1:
            if self.verbose:
                print('Ned2:  move successful:', result['message'])
        else:
            self.__has_errors = True
            print('Ned2:  Error: move failed:', result)
        self.__move_event.set()

    def __move(self, move_function, target, title=None):
        self.__has_errors = False
        self.__move_event.clear()
        if title is not None:
            print('Ned2: Move to', title)
        move_function(target, callback=self.__move_callback)
        self.__move_event.wait(20)
        if self.__has_errors:
            return False
        if not self.__move_event.is_set():
            print("*** timeout")
            return False
        self.__current_pose = self.robot.arm.get_pose()
        if title is not None and self.robot:
            print('Ned2:  move done. Pose is', self.pose_to_str(self.__current_pose))
        return True

    def __move_offline(self, pose, title=None):
        if title is not None:
            print('Ned2: Move to', title)
        self.__current_pose = pose
        if title is not None:
            print('Ned2:  move done. Pose is', self.pose_to_str(pose))
        return True
