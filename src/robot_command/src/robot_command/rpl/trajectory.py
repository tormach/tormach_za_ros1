import csv
from math import radians, degrees

import rospy
from trajectory_msgs.msg import JointTrajectoryPoint, JointTrajectory


class Trajectory:
    JOINT_NAMES = [f'joint_{i+1}' for i in range(6)]

    @staticmethod
    def load_from_csv(path: str):
        trajectory = JointTrajectory(joint_names=Trajectory.JOINT_NAMES)
        for row in Trajectory._read_csv(path):
            if len(row) < 7:
                raise OSError('CSV file has incorrect format')
            p = JointTrajectoryPoint(
                time_from_start=rospy.Duration.from_sec(float(row[0])),
                positions=[radians(float(p)) for p in row[1:7]],
            )
            if len(row) >= 13:
                p.velocities = [radians(float(v)) for v in row[7:13]]
            if len(row) >= 19:
                p.accelerations = [radians(float(a)) for a in row[13:19]]

            trajectory.points.append(p)
        if len(trajectory.points) > 0:
            trajectory.points[0].time_from_start.nsecs += 1
        return trajectory

    @staticmethod
    def save_to_csv(path: str, trajectory: JointTrajectory):
        if len(trajectory.points) == 0:
            raise RuntimeError("Trajectory does not contain points")
        has_velocities = len(trajectory.points[0].velocities) > 0
        has_accelerations = len(trajectory.points[0].accelerations) > 0

        def create_rows():
            header = ['Time']
            header += [f'Joint {i+1} Pos' for i in range(6)]
            if has_velocities:
                header += [f'Joint {i+1} Vel' for i in range(6)]
            if has_accelerations:
                header += [f'Joint {i+1} Acc' for i in range(6)]
            yield header
            for point in trajectory.points:
                row = [point.time_from_start.to_sec()]
                row += [degrees(p) for p in point.positions]
                if has_velocities:
                    row += [degrees(v) for v in point.velocities]
                if has_accelerations:
                    row += [degrees(a) for a in point.accelerations]
                yield row

        Trajectory._write_csv(path, create_rows())

    @staticmethod
    def _write_csv(path, data):
        with open(path, 'w', newline='') as csvfile:
            dbwriter = csv.writer(
                csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            for row in data:
                dbwriter.writerow(row)

    @staticmethod
    def _read_csv(path):
        with open(path) as csvfile:
            dbreader = csv.reader(
                filter(lambda row_: row_[0] != '#', csvfile),
                delimiter=',',
                quotechar='"',
            )
            columns = None
            for row in dbreader:
                if columns is None:
                    columns = row
                    continue
                yield row
