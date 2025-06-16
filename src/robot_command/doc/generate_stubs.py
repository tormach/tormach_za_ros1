#!/usr/bin/env python3
from typing import Optional
import zipfile
import catkin_pkg.package
import importlib.util
import sys

from pathlib import Path
from os import access, W_OK
from argparse import ArgumentParser, Action, ArgumentError
from third_party.stub_generator import StubGenerator


def generate_stubs(
    output_stub_path: Path,
    package_name: Path,
    output_package_path: Optional[Path] = None,
) -> None:
    """
    This method generates stub files for a Python package called robot_command.
    The stub files are used for type hinting and auto-completion in code editors.

    :param output_stub_path: A Path object representing the directory where the stub files will be generated.
    :param package_name: A Path object representing the name of the package.
    :param output_package_path: A Path object representing the directory where the generated stub files will be packaged into a zip file. If this argument is not provided, the stub files will not be packaged.
    """
    catkin_dir = Path(__file__).parent.parent.resolve()
    catkin_package = catkin_pkg.package.parse_package(
        catkin_dir / catkin_pkg.package.PACKAGE_MANIFEST_FILENAME
    )
    stubs_path = catkin_dir / 'doc' / 'stubs'

    rpl_module_path = output_stub_path / 'rpl'
    calibration_module_path = output_stub_path / 'calibration'

    rpl_module_path.mkdir(parents=True, exist_ok=True)
    calibration_module_path.mkdir(parents=True, exist_ok=True)

    robot_command_module_init_path = output_stub_path / '__init__.pyi'
    rpl_module_init_path = rpl_module_path / '__init__.pyi'
    calibration_module_init_path = calibration_module_path / '__init__.pyi'

    readme_source_path = stubs_path / 'README.md'
    setup_source_path = stubs_path / 'setup.py'

    with open(robot_command_module_init_path, 'w') as f:
        f.write(f'__version__ = "{catkin_package.version}"')

    robot_command_name = 'robot_command'
    robot_command_rpl_name = 'robot_command.rpl'
    robot_command_calibration_name = 'robot_command.calibration'

    robot_command_source = catkin_dir / 'src' / 'robot_command'
    robot_command_init = robot_command_source / '__init__.py'
    robot_command_rpl_init = robot_command_source / 'rpl' / '__init__.py'
    robot_command_calibration_init = (
        robot_command_source / 'calibration' / '__init__.py'
    )

    spec_robot_command = importlib.util.spec_from_file_location(
        robot_command_name, robot_command_init
    )
    spec_rpl = importlib.util.spec_from_file_location(
        robot_command_rpl_name, robot_command_rpl_init
    )
    spec_calibration = importlib.util.spec_from_file_location(
        robot_command_calibration_name, robot_command_calibration_init
    )
    robot_command = importlib.util.module_from_spec(spec_robot_command)
    robot_command.rpl = importlib.util.module_from_spec(spec_rpl)
    robot_command.calibration = importlib.util.module_from_spec(
        spec_calibration
    )
    sys.modules[robot_command_name] = robot_command
    sys.modules[robot_command_rpl_name] = robot_command.rpl
    sys.modules[robot_command_calibration_name] = robot_command.calibration
    spec_robot_command.loader.exec_module(robot_command)
    spec_rpl.loader.exec_module(robot_command.rpl)
    spec_calibration.loader.exec_module(robot_command.calibration)

    StubGenerator(
        robot_command.rpl,
        members_from_other_modules=[],
        ignore_members=[
            'AsyncCommand',
            'CommandInterpreter',
            'Command',
            'ScopedCommand',
            'ProgramPosition',
            'rpl_program_start',
            'rpl_main_program_start',
            'rpl_main_program_end',
            'init_tpl_interpreter',
        ],
    ).generate_stubs().write_to_file(rpl_module_init_path)

    StubGenerator(robot_command.calibration).generate_stubs().write_to_file(
        calibration_module_init_path
    )

    if output_package_path is not None:
        package_file = 'robot_command-stubs.zip'

        with zipfile.ZipFile(
            output_package_path / package_file, 'w'
        ) as zip_file:
            zip_file.write(readme_source_path, arcname=readme_source_path.name)
            zip_file.write(setup_source_path, arcname=setup_source_path.name)
            zip_file.write(
                robot_command_module_init_path,
                arcname=str(
                    package_name
                    / robot_command_module_init_path.relative_to(
                        output_stub_path
                    )
                ),
            )
            zip_file.write(
                rpl_module_init_path,
                arcname=str(
                    package_name
                    / rpl_module_init_path.relative_to(output_stub_path)
                ),
            )
            zip_file.write(
                calibration_module_init_path,
                arcname=str(
                    package_name
                    / calibration_module_init_path.relative_to(output_stub_path)
                ),
            )


class PathExists(Action):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.default is not None:
            self.default = self.verify_directory_path(self.default)

    def verify_directory_path(self, directory_path):
        directory = Path(directory_path)

        try:
            # Will raise exception even in case file (and not a directory) exists
            # with the same path
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ArgumentError(
                self, f'Could not create directory {directory}'
            ) from e

        if not access(directory, W_OK):
            raise ArgumentError(self, f'Directory {directory} is not writeable')

        return directory

    def __call__(self, parser, namespace, values, option_string):
        if isinstance(values, list):
            values = [self.verify_directory_path(value) for value in values]
        else:
            values = self.verify_directory_path(values)
        setattr(namespace, self.dest, values)


def main():
    parser = ArgumentParser()

    parser.add_argument(
        '-o',
        '--output',
        action=PathExists,
        metavar='PATH',
        default=Path(__file__).parent / 'stubs' / 'robot_command-stubs',
        help='Output directory where the stubs should be generated',
        dest='output_path',
    )

    parser.add_argument(
        '-p',
        '--package',
        action=PathExists,
        metavar='PATH',
        default=None,
        help='Generate ZIP file with stub Python package',
        dest='package_path',
    )

    parser.add_argument(
        '-n',
        '--package-namespace',
        action='store',
        metavar='NAMESPACE',
        default=Path('robot_command-stubs'),
        type=Path,
        help='Name of the package namespace',
        dest='package_namespace',
    )

    args = parser.parse_args()

    generate_stubs(args.output_path, args.package_namespace, args.package_path)


if __name__ == '__main__':
    main()
