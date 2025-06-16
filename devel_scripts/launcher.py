import argparse
import os
import shlex
import sys
import time
import logging
from typing import Dict, List, Callable, Union, Type  # noqa: F401
import sh  # noqa: F401

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TIMEOUT = 1.0

processes: List[sh.RunningCommand] = []


class ProgramTerminated(Exception):
    pass


def check_pid(pid):
    """Check For the existence of a unix pid."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def start_process(command, line: str, environment: Dict[str, str] = {}):
    """

    :type command: sh.Command
    """
    new_environment = os.environ.copy()
    new_environment.update(environment)

    processes.append(
        command(
            shlex.split(line),
            _env=new_environment,
            _out=sys.stdout,
            _err=sys.stderr,
            _bg=True,
        )
    )
    time.sleep(TIMEOUT)


def terminate_processes():
    for process in processes:
        if process is None:
            continue
        try:
            process.terminate()
        except OSError:
            pass
        process.wait()


def check_processes():
    for process in processes:
        if process is None:
            continue
        if not check_pid(process.pid):
            raise ProgramTerminated()


def wait_loop():
    try:
        while True:
            check_processes()
            time.sleep(TIMEOUT)
    except KeyboardInterrupt:
        pass
    except ProgramTerminated:
        logger.warning("A program terminated, stopping other processes.")


def live_argument(
    parser: argparse.ArgumentParser,
    action: Union[Type[argparse.Action], str] = "store_true",
) -> None:
    parser.add_argument(
        "-l", "--live", help="enable live-coding", action=action
    )


def tool_argument(
    parser: argparse.ArgumentParser,
    action: Union[Type[argparse.Action], str] = "store",
    type_of_value="str",
) -> None:
    parser.add_argument(
        "-t",
        "--tool",
        help="choose an end effector tool",
        action=action,
        metavar="TOOL",
        type=type_of_value,
    )


def sim_argument(
    parser: argparse.ArgumentParser,
    action: Union[Type[argparse.Action], str] = "store_true",
) -> None:
    parser.add_argument(
        "-s", "--sim", help="simulation configuration", action=action
    )


def debug_argument(
    parser: argparse.ArgumentParser,
    action: Union[Type[argparse.Action], str] = "store_true",
) -> None:
    parser.add_argument(
        "-d", "--debug", help="set hal DEBUG level to 5", action=action
    )


def mastering_argument(
    parser: argparse.ArgumentParser,
    action: Union[Type[argparse.Action], str] = "store_true",
) -> None:
    parser.add_argument(
        "-m",
        "--mastering",
        help="Enable extended joint limits for robot mastering",
        action=action,
    )


def headless_argument(
    parser: argparse.ArgumentParser,
    action: Union[Type[argparse.Action], str] = "store_true",
) -> None:
    parser.add_argument(
        "-H",
        "--headless",
        help="Run in headless mode (no GUI)",
        action=action,
    )


def add_default_arguments(
    parser=argparse.ArgumentParser(),
    skip_functions: Union[List[Union[str, Callable]], str] = [],
):
    _skip_possibilities = [
        live_argument,
        tool_argument,
        sim_argument,
        debug_argument,
        mastering_argument,
        headless_argument,
    ]

    if not isinstance(skip_functions, list):
        skip_functions = [skip_functions]

    functions_to_skip = [
        (
            function
            if isinstance(function, Callable)
            else {f.__name__: f for f in _skip_possibilities}[function]
        )
        for function in skip_functions
    ]

    function_set = [
        function
        for function in _skip_possibilities
        if function not in functions_to_skip
    ]

    for function in function_set:
        function(parser)

    return parser
