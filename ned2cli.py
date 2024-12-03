#!/usr/bin/env python3

import cmd
import os

import yaml

import ned2

BASE_POSE_FILE = 'base-saved-poses.yaml'
LOCAL_POSE_FILE = 'local-saved-poses.yaml'


class Ned2Cli(cmd.Cmd):
    prompt = 'Ned2> '
    intro = 'Welcome to Ned2CLI. Type "help" for available commands.'

    def __init__(self):
        super().__init__()
        self.__pose_file = LOCAL_POSE_FILE
        self.ned2 = ned2.Ned2()
        self.base_poses = self.__load_poses_from_yaml(BASE_POSE_FILE)
        self.poses = self.__load_poses_from_yaml(self.__pose_file)
        if not self.ned2.open():
            print("Failed to connect and setup the robot arm.")
            quit()

    def __get_pose(self, name):
        if not name:
            print("Please specify a pose name")
            return None
        p = self.poses.get(name, None)
        if not p:
            p = self.base_poses.get(name, None)
            if not p:
                # Try to parse pose values
                if '[' in name or "PoseObject" in name:
                    pose = self.ned2.pose_from_str(name)
                    if pose:
                        return pose
                print("Could not find the pose among the saved poses")
                return None
        return self.ned2.pose_from_list(p)

    @staticmethod
    def __load_poses_from_yaml(filename):
        if not os.path.exists(filename):
            return {}
        try:
            with open(filename, 'r') as file:
                return yaml.safe_load(file) or {}
        except (yaml.YAMLError, IOError) as e:
            print("Failed to read saved poses from {}: {}".format(filename, e))
            return {}

    def __save_poses_to_yaml(self):
        with open(self.__pose_file, 'w') as file:
            yaml.dump(self.poses, file, default_flow_style=False)

    def __print_poses(self, poses):
        [print(' ', key, self.ned2.pose_to_str(self.ned2.pose_from_list(value))) for key, value in poses.items()]
        print()

    def do_status(self, _line):
        """Show hardware status."""
        print('Hardware status:', self.ned2.robot.arm.hardware_status())

    def do_list(self, _line):
        """List saved poses"""
        if _line == "robot":
            print("Saved poses in the robot:")
            print(self.ned2.robot.saved_poses.get_saved_pose_list())
        else:
            if self.base_poses:
                print("Saved base poses:")
                self.__print_poses(self.base_poses)
            print("Saved poses:")
            self.__print_poses(self.poses)

    def do_pose(self, _line):
        """Show current arm pose"""
        print('Pose is', self.ned2.pose_to_str(self.ned2.robot.arm.get_pose()))

    def do_joints(self, _line):
        """Show current arm joints"""
        print('Joints are', self.ned2.robot.arm.joints_state())

    def do_save(self, line):
        """Save current pose as specified name"""
        if not line:
            print("Please provide a name for the post to save")
        else:
            self.poses[line] = self.ned2.robot.arm.get_pose().to_list()
            self.__save_poses_to_yaml()
            print("Saved current pose as", line)

    def do_remove(self, line):
        """Remove specified pose"""
        if not line:
            print("Please provide a pose name")
        elif line not in self.poses:
            print("Could not find the pose among saved poses")
        else:
            del self.poses[line]
            self.__save_poses_to_yaml()
            print('Removed the pose from saved poses')

    def do_remove_all(self, _line):
        """Remove all saved poses"""
        if self.poses:
            self.poses = {}
            self.__save_poses_to_yaml()
            print('Removed all saved poses')
        else:
            print("There are no saved poses to remove")

    def do_home(self, _line):
        """Move to home pose"""
        self.ned2.robot.arm.move_to_home_pose()

    def do_move(self, line):
        """Move to specified pose"""
        pose = self.__get_pose(line)
        if pose:
            self.ned2.move_pose(pose, line)

    def do_pick(self, line):
        """Pick up from specified pose"""
        pose = self.__get_pose(line)
        if pose:
            self.ned2.robot.pick_place.pick_from_pose(pose)

    def do_place(self, line):
        """Place to specified pose"""
        pose = self.__get_pose(line)
        if pose:
            self.ned2.robot.pick_place.place_from_pose(pose)

    def do_grasp(self, _line):
        """Close the gripper"""
        self.ned2.robot.tool.close_gripper()

    def do_close(self, _line):
        """Close the gripper"""
        self.ned2.robot.tool.close_gripper()

    def do_release(self, _line):
        """Open the gripper"""
        self.ned2.robot.tool.open_gripper()

    def do_open(self, _line):
        """Open the gripper"""
        self.ned2.robot.tool.open_gripper()

    @staticmethod
    def do_quit(_line):
        """Exit the CLI."""
        return True

    def postcmd(self, stop, line):
        print()
        return stop

    def onecmd(self, line):
        try:
            return super().onecmd(line)
        except Exception as e:
            print("Error {}".format(e))
            return False

if __name__ == '__main__':
    cli = Ned2Cli()
    cli.cmdloop()
    if cli.ned2 is not None:
        cli.ned2.close()
