import re
from threading import Event

from pyniryo2 import *

DEFAULT_ROBOT_IP = "10.10.10.10"

class Ned2:
    """
    Niryo Ned2 robot arm support object
    """
    def __init__(self, robot_ip: str = DEFAULT_ROBOT_IP):
        self.__host = robot_ip
        self.__setup_event = Event()
        self.__move_event = Event()
        self.robot = None
        self.__has_errors = False
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
            self.close()
        return success

    def move_pose(self, pose, title=None) -> bool:
        return self.__move(self.robot.arm.move_pose, pose, title)

    def move_joints(self, joints, title=None) -> bool:
        return self.__move(self.robot.arm.move_joints, joints, title)

    def close(self):
        robot = self.robot
        self.robot = None
        if robot:
            robot.arm.go_to_sleep()

    @staticmethod
    def pose_to_str(pose: PoseObject):
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
            print("Failed to parse pose:", e)
            return None

    def __call_setup(self, setup_function, success_callback, failure_callback) -> bool:
        self.__setup_event.clear()
        setup_function(callback=success_callback, errback=failure_callback)
        self.__setup_event.wait(25)
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
        self.__move_event.wait(30)
        if not self.__move_event.is_set() or self.__has_errors:
            return False
        if title is not None:
            print('Ned2:  move done. Pose is', self.pose_to_str(self.robot.arm.get_pose()))
        return True
