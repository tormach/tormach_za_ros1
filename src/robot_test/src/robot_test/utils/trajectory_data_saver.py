import rospy
from moveit_msgs.msg import MoveGroupActionFeedback, ExecuteTrajectoryActionGoal
from sensor_msgs.msg import JointState
import time
import json
import threading

import xml.etree.ElementTree as ET
import os
import subprocess


class TrajectoryDataSaver:
    def __init__(self, program_name: str = "program", time_limit: float = 0.5):
        self.program_name = program_name
        self.program_start_time = time.strftime("%Y-%m-%d_%H:%M:%S")
        self.time_limit = time_limit
        self.processing = True  # for handling the planning time
        self.allow_data_capture = False
        self.record_joint_states = False
        self.new_move_started = False
        self.time_lock = threading.Lock()
        self.callback_lock = threading.Condition()
        self.move_start_time = None
        self.timer = None
        self.git_root = None
        self.last_joints = None

        self.reset_data()

        def get_git_details(path):
            try:
                git_root_directory = (
                    subprocess.check_output(
                        ['git', 'rev-parse', '--show-toplevel'], cwd=path
                    )
                    .decode('utf-8')
                    .strip()
                )
                branch_name = (
                    subprocess.check_output(
                        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=path
                    )
                    .decode('utf-8')
                    .strip()
                )
                commit_id = (
                    subprocess.check_output(
                        ['git', 'rev-parse', 'HEAD'], cwd=path
                    )
                    .decode('utf-8')
                    .strip()
                )
                commit_message = (
                    subprocess.check_output(
                        ['git', 'log', '-1', '--pretty=%B'], cwd=path
                    )
                    .decode('utf-8')
                    .strip()
                )
                date = (
                    subprocess.check_output(
                        ['git', 'log', '-1', '--pretty=%cd'], cwd=path
                    )
                    .decode('utf-8')
                    .strip()
                )
                return (
                    branch_name,
                    commit_id,
                    commit_message,
                    date,
                    git_root_directory,
                )
            except subprocess.CalledProcessError:
                rospy.logerr("Not a git repository")
                return None, None, None, None, None

        path_to_git_repo = os.getcwd()  # Get the current working directory
        (
            git_branch,
            git_commit,
            commit_message,
            commit_date,
            git_root,
        ) = get_git_details(path_to_git_repo)

        if git_root:
            self.git_root = git_root
            file_path = os.path.join(
                git_root,
                "src/tormach/za6/za6_description/urdf/za6_robot_macro.xacro",
            )
            tree = ET.parse(file_path)
            root = tree.getroot()

            linear_offset_j3 = None
            linear_offset_j5 = None

            for property_tag in root.findall(
                ".//xacro:property",
                namespaces={"xacro": "http://www.ros.org/wiki/xacro"},
            ):
                name = property_tag.get('name')
                if name == 'linear_offset_j3':
                    linear_offset_j3 = property_tag.get('value')
                elif name == 'linear_offset_j5':
                    linear_offset_j5 = property_tag.get('value')

        self.system_configuration = {
            'program_name': self.program_name,
            'number_of_moves': None,
            'j3_offset': linear_offset_j3,
            'j5_offset': linear_offset_j5,
            'git_branch': git_branch,
            'git_commit': git_commit,
            'commit_message': commit_message,
            'commit_date': commit_date,
            'run_date': self.program_start_time,
        }

        # self.trajectory_data.append(self.system_configuration)

        self.planning_subscriber = rospy.Subscriber(
            "/move_group/feedback",
            MoveGroupActionFeedback,
            self.planning_callback,
        )
        self.trajectory_subscriber = rospy.Subscriber(
            "/execute_trajectory/goal",
            ExecuteTrajectoryActionGoal,
            self.trajectory_callback,
        )

        self.joint_states_subscriber = rospy.Subscriber(
            "/joint_states",
            JointState,
            self.joint_states_callback,
        )

    def append_move_name(self, name):
        self.move_names.append(name)

    def planning_callback(self, msg):
        if not self.processing:
            return

        with self.time_lock:
            if msg.status.status == 1:
                self.planning_time['start'] = time.time()
            elif msg.status.status == 3:
                self.planning_time['end'] = time.time()

    def stop_recording_joint_states(self):
        self.record_joint_states = False

    def joint_states_callback(self, msg):
        with self.callback_lock:
            if (
                not self.processing
                or not self.allow_data_capture
                or not self.record_joint_states
            ):
                return

            # If a new move has started, record the start time
            if self.new_move_started:
                self.new_move_started = False
                self.move_start_time = time.time()

            elapsed_time = time.time() - self.move_start_time

            # Append joint data to the last existing move
            current_move_data = self.trajectory_data[-1]
            current_move_data['execution_time'].append(elapsed_time)

            for i in range(6):
                current_move_data['hardware_joints'][i]['positions'].append(
                    msg.position[i]
                )
                current_move_data['hardware_joints'][i]['velocities'].append(
                    msg.velocity[i]
                )
                current_move_data['hardware_joints'][i]['efforts'].append(
                    msg.effort[i]
                )

    def trajectory_callback(self, msg):
        if not self.processing or not self.allow_data_capture:
            return

        if len(self.move_names) == 0:
            move_data = {
                'move_name': None,
                'planned_time': [],
                'motion_plan': [
                    {'positions': [], 'velocities': []} for _ in range(6)
                ],
                'execution_time': [],
                'hardware_joints': [
                    {'positions': [], 'velocities': [], 'efforts': []}
                    for _ in range(6)
                ],
            }
        else:
            if self.processed_names >= len(self.move_names):
                raise Exception("Too many move names received")

            # Create a new dictionary for this move
            move_data = {
                'move_name': self.move_names[self.processed_names],
                'planned_time': [],
                'motion_plan': [
                    {'positions': [], 'velocities': []} for _ in range(6)
                ],
                'execution_time': [],
                'hardware_joints': [
                    {'positions': [], 'velocities': [], 'efforts': []}
                    for _ in range(6)
                ],
            }

        self.last_joints = msg.goal.trajectory.joint_trajectory.points[
            -1
        ].positions

        with self.callback_lock:
            for point in msg.goal.trajectory.joint_trajectory.points:
                move_data['planned_time'].append(point.time_from_start.to_sec())
                for position, velocity, joint in zip(
                    point.positions, point.velocities, move_data['motion_plan']
                ):
                    joint['positions'].append(position)
                    joint['velocities'].append(velocity)

            self.trajectory_data.append(
                move_data
            )  # Append the move data to the trajectory data

            # num_pts = len(msg.goal.trajectory.joint_trajectory.points)

            self.processed_names += 1

            # if timer is running, cancel it
            if self.timer:
                self.timer.cancel()

            self.record_joint_states = True
            # start timer to stop recording joint states
            delay_in_seconds = (
                move_data['planned_time'][-1] + 0.020
            )  # Set this to the desired delay, add 20ms
            self.timer = threading.Timer(
                delay_in_seconds, self.stop_recording_joint_states
            )
            self.timer.start()

            self.new_move_started = True

    def save_trajectory_points(self, name: str = None):
        data_path = os.path.join(self.git_root, "data")
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        if name is None:
            save_filename = (
                self.program_name + "_" + self.program_start_time + ".json"
            )
        else:
            save_filename = name

        save_full_path = os.path.join(data_path, save_filename)

        self.system_configuration["number_of_moves"] = len(self.move_names)
        # self.trajectory_data.prepend(self.system_configuration)

        data_to_save = {}
        data_to_save["system_config"] = self.system_configuration
        data_to_save["trajectory_data"] = self.trajectory_data

        with open(save_full_path, 'w') as file:
            json.dump(data_to_save, file, indent=4)

        # with open('data/jabadu.json', 'w') as file:
        #     json.dump(self.system_configuration, file, indent=4)

        # rospy.logerr(self.system_configuration)

    def check_planning_time(self):
        if self.planning_time['end'] is None:
            print(f"Planning did not end within {self.time_limit}s")
            return False

        planning_duration = (
            self.planning_time['end'] - self.planning_time['start']
        )

        if planning_duration >= self.time_limit:
            print(f"Planning time too long: {planning_duration}s")
            return False

        return True

    def joints_position(self):
        # return the list consisted of the last positions of each joint
        # return self.last_joints
        # rospy.logerr(self.trajectory_data[-1])
        return [
            self.trajectory_data[-1]['motion_plan'][i]['positions'][-1]
            for i in range(6)
        ]

    def reset_data(self):
        if self.timer:
            self.timer.cancel()

        self.move_names = []
        self.planning_time = {'start': None, 'end': None}
        self.real_world_joint_data = []
        self.trajectory_data = []
        self.processed_names = 0

    def reset_planning_data(self):
        self.planning_time = {'start': None, 'end': None}

    def final_cleanup(self):
        self.planning_subscriber.unregister()
        self.trajectory_subscriber.unregister()
        self.joint_states_subscriber.unregister()
        if self.timer:
            self.timer.cancel()
        self.processing = False
        self.allow_data_capture = False
        self.record_joint_states = False
