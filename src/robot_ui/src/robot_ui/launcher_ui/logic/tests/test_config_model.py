import pytest

from PySide6.QtTest import QAbstractItemModelTester

import robot_ui.pathpilot  # noqa: F401

# from robot_ui.launcher_ui.logic import ConfigModel
# from robot_ui.launcher_ui.logic.config_model import Config


@pytest.fixture
def configs():
    from robot_ui.launcher_ui.logic.config_model import Config

    return [
        Config(name="gridded", pprlaunch_args="extra", roslaunch_args="birth"),
        Config(name="harmed", pprlaunch_args="knife", roslaunch_args="suggest"),
    ]


def test_config_data_model_implementation(configs):
    from robot_ui.launcher_ui.logic import ConfigModel

    model = ConfigModel()
    model._configs = configs
    _ = QAbstractItemModelTester(
        model, QAbstractItemModelTester.FailureReportingMode.Warning
    )
