import os

import pytest
import rospy

from robot_command.rpl.trajectory import Trajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


def write_csv_file(tmpdir, source):
    path = os.path.join(str(tmpdir), 'wire.csv')
    with open(path, 'w') as f:
        f.write(source)
    return path


@pytest.fixture
def valid_csv_file(tmpdir):
    data = '''\
Time, Joint 1, Joint 2, Joint 3, Joint 4, Joint 5, Joint 6
0.000000, 7.244792, 4.263126, 0.150116, 0.000000, 85.586761, 97.244789
0.041667, 7.248114, 4.235431, 0.180024, 0.000000, 85.584541, 97.248116
0.083333, 7.257930, 4.153757, 0.268141, 0.000000, 85.578102, 97.257927
0.125000, 7.274034, 4.020254, 0.411907, 0.000000, 85.567841, 97.274033
0.166667, 7.296255, 3.837059, 0.608639, 0.000000, 85.554306, 97.296257
0.208333, 7.324442, 3.606339, 0.855510, 0.000000, 85.538147, 97.324440
0.250000, 7.358471, 3.330249, 1.149614, 0.000000, 85.520134, 97.358475
'''
    return write_csv_file(tmpdir, data)


def test_loading_trajectory_from_file_works(valid_csv_file):
    trajectory = Trajectory.load_from_csv(valid_csv_file)

    assert isinstance(trajectory, JointTrajectory)
    assert len(trajectory.points) == 7
    assert len(trajectory.joint_names) == 6
    assert trajectory.points[2].time_from_start.to_sec() == pytest.approx(
        0.083333
    )
    assert trajectory.points[0].positions == pytest.approx(
        [
            0.12644547402214504,
            0.07440558512737577,
            0.002620018459923808,
            0.0,
            1.4937707755674745,
            1.697241748457164,
        ]
    )
    assert trajectory.points[0].time_from_start >= rospy.Duration(nsecs=1)


@pytest.fixture
def valid_csv_file_with_velocities(tmpdir):
    data = '''\
Time, Joint 1 Pos, Joint 2 Pos, Joint 3 Pos, Joint 4 Pos, Joint 5 Pos, Joint 6 Pos, Joint 1 Vel, Joint 2 Vel, Joint 3 Vel, Joint 4 Vel, Joint 5 Vel, Joint 6 Vel
0.000000,87.291122,38.578148,26.669157,-28.628771,107.99157,57.031302999999994,14.72050073602452,7.729350386467445,45.4866522743325,-20.668701033435127,-66.90975334548732,-24.963401248169777
0.041667,87.593498,38.751209,27.593588,-29.045978999999996,106.596123,56.49086,15.118799244060027,8.653049567347848,46.221547688922705,-20.860398956979864,-69.7723465113821,-27.022148648892276
0.083333,87.900734,38.941677,28.528013,-29.463474,105.148834,55.90786,15.36180076809032,9.523400476169721,46.721252336062754,-20.87475104373781,-72.36445361822354,-29.150001457500103
0.125000,88.20948,39.148338,29.467779,-29.877947,103.65531200000001,55.280823,15.437299228134878,10.333049483347672,46.988297650585075,-20.72364896381735,-74.67609626619476,-31.3518484324076
'''
    return write_csv_file(tmpdir, data)


def test_loading_trajectory_with_velocities_from_file_works(
    valid_csv_file_with_velocities,
):
    trajectory = Trajectory.load_from_csv(valid_csv_file_with_velocities)

    assert isinstance(trajectory, JointTrajectory)
    assert len(trajectory.points) == 4
    assert len(trajectory.joint_names) == 6
    assert trajectory.points[1].time_from_start.to_sec() == pytest.approx(
        0.041667
    )
    assert trajectory.points[1].velocities == pytest.approx(
        [
            0.2638728257568772,
            0.15102420528849075,
            0.806718192539277,
            -0.3640826450788896,
            -1.2177571734659969,
            -0.4716254648865074,
        ]
    )
    assert trajectory.points[0].time_from_start >= rospy.Duration(nsecs=1)


@pytest.fixture
def csv_file_missing_columns(tmpdir):
    data = '''\
Time, Joint 1, Joint 2, Joint 3, Joint 4, Joint 5, Joint 6
0.000000, 7.244792, 4.263126, 0.150116, 0.000000, 85.586761, 97.244789
0.041667, 7.248114, 4.235431, 0.180024
0.083333, 7.257930, 4.153757, 0.268141, 0.000000, 85.578102, 97.257927
'''
    return write_csv_file(tmpdir, data)


@pytest.fixture
def csv_file_with_invalid_syntax(tmpdir):
    data = '''\
Time, Joint 1, Joint 2, Joint 3, Joint 4, Joint 5, Joint 6
0.000000, 7.244dsf792, 4.263126, 0.150116, 0.000000, 85.586761, 97.244789
0.041667, 7.248114, 4.235431, 0.180024, 0.000000, 85.584541, 97.248116
'''
    return write_csv_file(tmpdir, data)


def test_loading_csv_file_with_missing_column_raises_error(
    csv_file_missing_columns,
):
    with pytest.raises(IOError):
        Trajectory.load_from_csv(csv_file_missing_columns)


def test_loading_csv_file_with_incorrect_syntax_raises_error(
    csv_file_with_invalid_syntax,
):
    with pytest.raises(ValueError):
        Trajectory.load_from_csv(csv_file_with_invalid_syntax)


@pytest.fixture
def velocity_trajectory():
    trajectory = JointTrajectory()
    trajectory.joint_names = [f'joint_{i+1}' for i in range(6)]
    positions = [
        [
            1.4840531837180981,
            0.6640154706563184,
            0.3230963634201565,
            -0.43994777999738116,
            2.0673387116228064,
            1.0550129959606882,
        ],
        [
            1.4855755646114426,
            0.6628938871724018,
            0.33188507358832897,
            -0.44242209837134844,
            2.05879370177809,
            1.0527848562777145,
        ],
        [
            1.487598767733647,
            0.6621830145680646,
            0.34174196016530717,
            -0.44572288250601266,
            2.048383126949209,
            1.0499215738266479,
        ],
    ]
    velocities = [
        [
            0.07611904086127015,
            -0.05607917139186919,
            0.43943548643685115,
            -0.12371591251256824,
            -0.4272504708732965,
            -0.11140697857833862,
        ],
        [
            0.10116016116823295,
            -0.03554363199404817,
            0.4928443534911275,
            -0.16503921498517202,
            -0.5205287674704757,
            -0.14316412971153625,
        ],
        [
            0.12494898756745017,
            -0.015262903545548637,
            0.5424474317328393,
            -0.20255679420624115,
            -0.6095370121604142,
            -0.1747371199850575,
        ],
    ]
    times = [
        rospy.Duration.from_sec(0.0),
        rospy.Duration.from_sec(0.1231),
        rospy.Duration.from_sec(0.2341),
    ]
    for i, pos in enumerate(positions):
        point = JointTrajectoryPoint()
        point.time_from_start = times[i]
        point.positions = pos
        point.velocities = velocities[i]
        trajectory.points.append(point)
    return trajectory


@pytest.fixture
def position_trajectory(velocity_trajectory):
    for point in velocity_trajectory.points:
        point.velocities = []
    return velocity_trajectory


def test_saving_trajectory_with_positions_to_file_works(
    tmpdir, position_trajectory
):
    path = tmpdir.join('also.csv')
    Trajectory.save_to_csv(path, position_trajectory)

    def check_row(row, time, pos):
        row = [float(s) for s in row.split(',')]
        assert len(row) == 7
        assert row[0] == pytest.approx(time)
        assert row[1:7] == pytest.approx(pos)

    with open(path) as f:
        header = [s.strip() for s in f.readline().split(',')]
        assert len(header) == 7
        assert header == ['Time'] + [f'Joint {i+1} Pos' for i in range(6)]
        check_row(
            f.readline(),
            0.0,
            [
                85.029984,
                38.045284,
                18.512058000000003,
                -25.207151,
                118.449783,
                60.447792,
            ],
        )
        f.readline()
        check_row(
            f.readline(),
            0.2341,
            [
                85.233131,
                37.94029200000001,
                19.580372,
                -25.53804,
                117.363708,
                60.156075,
            ],
        )


def test_saving_trajectory_with_velocities_works(tmpdir, velocity_trajectory):
    path = tmpdir.join('wisdom.csv')
    Trajectory.save_to_csv(path, velocity_trajectory)

    def check_row(row, time, vel):
        row = [float(s) for s in row.split(',')]
        assert len(row) == 13
        assert row[0] == pytest.approx(time)
        assert row[7:13] == pytest.approx(vel)

    with open(path) as f:
        header = [s.strip() for s in f.readline().split(',')]
        assert len(header) == 13
        assert header == ['Time'] + [f'Joint {i+1} Pos' for i in range(6)] + [
            f'Joint {i+1} Vel' for i in range(6)
        ]
        check_row(
            f.readline(),
            0.0,
            [
                4.361299781934639,
                -3.2130998393448906,
                25.1777987411099,
                -7.088399645579892,
                -24.479648776016997,
                -6.383149680843175,
            ],
        )
        f.readline()
        check_row(
            f.readline(),
            0.2341,
            [
                7.159049642047489,
                -0.8744999562751972,
                31.079948446002533,
                -11.605649419717583,
                -34.92389825380607,
                -10.011699499414865,
            ],
        )
