#!/usr/bin/env python

import argparse
import enum
import os
import logging

from sh import roslaunch
from pathlib import Path

from launcher import (
    start_process,
    terminate_processes,
    sim_argument,
    tool_argument,
    wait_loop,
    add_default_arguments,
)

from typing import List

logger = logging.getLogger(f"{Path(__file__).name}")
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logging.root.setLevel(logging.INFO)


class EnumBase(enum.Enum):
    def __init__(self, alias):
        self._alias_ = alias

    def __str__(self):
        return str(self.value)

    @property
    def alias(self) -> str:
        return self._alias_

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.lower()

        for member in cls:
            if str(value).lower() in [
                member.name.lower(),
                member.alias.lower(),
            ]:
                return member

        return None

    @classmethod
    def all_possibilities(cls) -> List[str]:
        return [
            variant
            for name, member in cls.__members__.items()
            for variant in (
                name,
                member.alias,
            )
        ]


@enum.unique
class ToolsBaseEnum(EnumBase):
    def __init__(self, value, alias):
        super().__init__(alias)
        self._value_ = value

    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, str):
            value = str(value)

        for member in cls:
            if str(value).lower() in [
                member.name.lower(),
                member.alias.lower(),
                str(member.value).lower(),
            ]:
                return member

        return None

    @classmethod
    def all_possibilities(cls) -> List[str]:
        return list(
            dict.fromkeys(
                [
                    option
                    for name, member in cls.__members__.items()
                    for variant in (
                        name,
                        member.alias,
                        member.value,
                    )
                    for option in [variant, variant.lower(), variant.upper()]
                ]
            )
        )

    @classmethod
    def default(cls):
        raise NotImplementedError("SubEnum have to implement this property!")


@enum.unique
class ToolsZA6(ToolsBaseEnum):
    Nothing = ("none", "empty")

    @classmethod
    def default(cls):
        return ToolsZA6.Nothing


def options() -> argparse.Namespace:
    class SimulationAction(argparse.Action):
        def __init__(self, default=False, required=False, nargs=0, **kwargs):
            nargs = 0  # Always require no argument

            super().__init__(
                default=default, required=required, nargs=nargs, **kwargs
            )

        def __call__(self, parser, namespace, values, option_string=None):
            namespace.sim_explicit = True
            setattr(namespace, self.dest, True)

    class ToolsAction(argparse.Action):
        def __init__(
            self,
            default=None,
            choices=None,
            dest="tool",
            nargs=1,
            **kwargs,
        ):
            self._enum_type = kwargs.pop("type", None)

            if self._enum_type is None:
                raise ValueError("Enum Type not known!")
            if not issubclass(self._enum_type, ToolsBaseEnum):
                raise TypeError("Enum Type is not a ToolsBaseEnum!")

            choices = self._enum_type.all_possibilities()
            default = self._enum_type.default()
            nargs = 1

            super().__init__(
                default=default,
                choices=choices,
                dest=dest,
                nargs=nargs,
                **kwargs,
            )

        def __call__(self, parser, namespace, values, option_string=None):
            if isinstance(values, list):
                values = values[0]

            value = self._enum_type(values)
            setattr(namespace, self.dest, value)

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        help="Required sub-commands for version operations",
        dest="subparser_used",
    )

    parser_za6 = subparsers.add_parser("za6", help="Tormach ZA6 robot arm")

    add_default_arguments(
        parser_za6, skip_functions=["sim_argument", "tool_argument"]
    )

    sim_argument(parser_za6, action=SimulationAction)

    tool_argument(
        parser_za6,
        action=ToolsAction,
        type_of_value=ToolsZA6,
    )

    args = parser.parse_args()

    # Base checking
    if args.subparser_used == "za6":
        if args.sim and args.robot is not None:
            parser.error(
                "Requesting simulation while specifying the ZA6 robot is NOT possible!"
            )

        args.robot = 6

        if not args.sim:
            from pp_ros_launch.system.ethercat import EthercatNetworkHardware
            from sh import ethercat as ethercat_cli

            try:
                ethercat_slaves_output = ethercat_cli("slaves")
                devices = EthercatNetworkHardware.process_data(
                    ethercat_slaves_output
                )

                drives = devices.get("ec_drives", dict())
                tools = devices.get("tools", dict())

                staged_drive = None

                for number, drive in drives.items():
                    if drive["error"]:
                        raise ValueError(
                            f"Drive number {number} is in error state!"
                        )
                    if drive["name"] == staged_drive:
                        continue
                    elif staged_drive is None:
                        staged_drive = drive["name"]
                    elif staged_drive != drive["name"]:
                        raise ValueError("More than one drive type found!")

                if args.tool is None:
                    for number, tool in tools:
                        args.tool = tool

                logger.info(
                    "Automatic recognition of hardware found a real robot!"
                )

            except Exception:
                logger.info(
                    "Automatic recognition of hardware found no real robot, going to start SIM!"
                )
                args.sim = True
                args.tool = ToolsZA6.Nothing

    else:
        # No subparser used
        parser.error("No robot to start specified!")

    return args


def main():
    opt = options()

    za_robot = opt.robot
    extended_environment = {}
    configuration = f"ZA{za_robot}"

    display_env = os.environ.get("DISPLAY", "")
    if display_env.startswith("localhost:") or display_env == "":
        logger.warning("Modifying the DISPLAY environment variable!")

        extended_environment["DISPLAY"] = (
            ":0"  # For forwarded X display, force onboard GPU
        )

    base_command = f"za{za_robot}_robot robot_ui.launch"

    configuration += " SIM" if opt.sim else ""

    roslaunch_command = base_command
    roslaunch_command += " sim:=true" if opt.sim else " sim:=false"

    if opt.live:
        roslaunch_command += " live_coding:=true"
        roslaunch_command += " dev_mode:=true"
    if opt.tool:
        roslaunch_command += f" tool:={opt.tool}"
    if opt.debug:
        roslaunch_command += " hal_debug_output:=true hal_debug_level:=5"
    if opt.mastering:
        roslaunch_command += " mastering:=true"
        configuration += " Mastering"
    if opt.headless:
        roslaunch_command += " headless:=true"
        configuration += " Headless"

    configuration += " Development!!!"

    extended_environment["ROBOT_CONFIGURATION"] = configuration

    logger.info(
        "About to start the roslaunch process with arguments: "
        f"{roslaunch_command} and environment extension: {extended_environment}"
    )

    start_process(
        roslaunch, roslaunch_command, environment=extended_environment
    )
    wait_loop()
    terminate_processes()


if __name__ == "__main__":
    main()
