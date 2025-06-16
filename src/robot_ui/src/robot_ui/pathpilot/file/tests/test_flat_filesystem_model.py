import os

import pytest

from PySide6.QtCore import Qt, QModelIndex, QDateTime, QTime, QLocale
from PySide6.QtTest import QAbstractItemModelTester

from robot_ui.pathpilot.file import FlatFileSystemModel


def timestamp_today_with_time(h, m):
    date_time = QDateTime().currentDateTime()
    date_time.setTime(QTime(h, m))
    return int(date_time.toMSecsSinceEpoch() / 1000.0)


@pytest.fixture
def filesystem(tmpdir):
    subdir = tmpdir.mkdir('vinelike')
    f = tmpdir.join('gatling.py')
    f.write(b'0')
    msecs = timestamp_today_with_time(12, 0)
    os.utime(str(f), (msecs, msecs))
    f = tmpdir.join('showish.txt')
    f.write(b'0' * 1124)
    f = subdir.join('assishly.py')
    f.write('in2p')

    os.utime(str(subdir), (1514808000, 1514808000))

    return str(tmpdir)


def test_files_are_represented_correctly_in_model(filesystem):
    model = FlatFileSystemModel()
    model.rootPath = filesystem

    assert model.rowCount(QModelIndex()) == 3
    assert model.columnCount(QModelIndex()) == 5

    expected = {
        'vinelike': dict(
            FileNameRole='vinelike',
            IsDirRole=True,
            SizeRole=[1, '1 item'],
            PathRole=os.path.join(filesystem, 'vinelike'),
            LastModifiedRole=[1514808000000, lambda x: x.date()],
        ),
        'gatling.py': dict(
            FileNameRole='gatling.py',
            IsDirRole=False,
            SizeRole=[1, '1.0 B'],
            PathRole=os.path.join(filesystem, 'gatling.py'),
            LastModifiedRole=[
                timestamp_today_with_time(12, 0) * 1000,
                lambda x: x.time(),
            ],
        ),
        'showish.txt': dict(
            FileNameRole='showish.txt',
            IsDirRole=False,
            SizeRole=[1124, '1.1 KiB'],
            PathRole=os.path.join(filesystem, 'showish.txt'),
            # No LastModifiedTimestampRole in this case
        ),
    }

    for row in range(3):
        index = model.index(row, 0, QModelIndex())
        assert model.data(index, model.Roles.FileNameRole) in expected
        e = expected[model.data(index, model.Roles.FileNameRole)]
        locale = QLocale()
        for attr in e.keys():
            data = e[attr]
            if not isinstance(data, list):
                data = [data, str(data)]

            if attr == 'LastModifiedRole':
                conv = data[1]
                display = locale.toString(
                    conv(QDateTime.fromMSecsSinceEpoch(data[0])),
                    QLocale.ShortFormat,
                )

            else:
                display = data[1]
            assert model.data(index, getattr(model.Roles, attr)) == data[0]
            column = getattr(model.Roles, attr) - model.Roles.FirstDataRole - 1
            column_index = model.index(
                row,
                column,
                QModelIndex(),
            )
            assert model.data(column_index, Qt.DisplayRole) == display


def test_file_system_model_implementation(filesystem):
    model = FlatFileSystemModel()
    model.rootPath = filesystem
    _ = QAbstractItemModelTester(
        model, QAbstractItemModelTester.FailureReportingMode.Warning
    )
