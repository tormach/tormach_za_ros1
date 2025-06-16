from .subsystem import (
    SubSystem,
    SubSystemCheck,
    SubSystemGroupCheck,
    SubSystemExecutableCheck,
)

import re


class EthercatKmodLoaded(SubSystemCheck):
    """Assert the EtherLab Master kernel module is loaded."""

    name = "ethercat_kmod_loaded"
    fatal = False

    def run_check(self):
        fc = self.read_file_contents("/proc/modules")
        if fc is not None:
            for line in fc:
                if line.startswith("ec_master"):
                    self.log_info(
                        "Ethercat kernel module 'ec_master' is loaded"
                    )
                    return True
        self.log_fatal("Ethercat kernel module 'ec_master' not loaded")
        self.log_recommendation(
            "Resolve 'ec_master' kernel module loading and reboot"
        )
        return False


class EthercatCharacterDeviceExists(SubSystemCheck):
    """Checkthe ``/dev/EtherCAT0`` device node in the /dev FS."""

    name = "ethercat_character_device_exists"
    path = "/dev/EtherCAT0"
    depends = "ethercat_kmod_loaded"

    def run_check(self):
        res = self.path_exists(self.path)
        if not res:
            self.log_warning(
                "Check init scripts and dmesg to resolve problem and reboot (or you may only run SIM)"
            )
        else:
            self.log_info(f"EtherCAT character device at {self.path} found!")
        return res


class UserInEthercatGroup(SubSystemGroupCheck):
    """Assert the user is in the ``ethercat`` POSIX group."""

    name = "user_in_ethercat_group"
    depends = "ethercat_kmod_loaded"
    group = "ethercat"


class EthercatExecutableExists(SubSystemExecutableCheck):
    """Assert the ``ethercat`` executable exists."""

    name = "ethercat_executable_exists"
    executable = "ethercat"
    depends = "ethercat_kmod_loaded"

    def run_check(self):
        res = super().run_check()
        if not res:
            self.log_recommendation(
                "Ensure the igh-ethercat package is installed and restart"
            )
        return res


class EthercatNetworkHardware(SubSystemCheck):
    """Get state of hardware present on the line"""

    name = "ethercat_network_hardware"
    depends = "ethercat_executable_exists"

    ec_base_regex_string: str = (
        r"^(?P<AbsRingPos>[0-9]{1,3}) {1,}(?P<AliasAdd>[0-9]):(?P<RelPos>[0-9]) {1,}(?P<State>PREOP|SAFEOP|OP) {1,}(?P<Error>\+|E) {1,}"
    )
    drive_620_regex_string: str = (
        r"(?P<Drive620>IS620N_ECAT_v[0-9]{1,}\.[0-9]{1,}\.[0-9]{1,})"
    )
    drive_660_regex_string: str = r"(?P<Drive660>SV660_1Axis_[0-9]{5})"
    itegva_board_regex_string: str = (
        r"(?P<ITegva>E7.820.003 [\/\(\) \._\-a-zA-Z0-9]{1,})"
    )
    robotiq_regex_string: str = r"(?P<Robotiq>netX50)"
    tool_group_open_regex_string: str = r"(?P<Tool>"
    io_group_open_regex_string: str = r"(?P<IO>"
    drive_group_open_regex_string: str = r"(?P<Drive>"
    group_close_regex_string: str = r")"
    noncatching_group_open_regex_string: str = r"(?:"
    or_regex_string: str = r"|"
    end_regex_string: str = r"$"
    ec_complete_regex: re.Pattern = re.compile(
        ec_base_regex_string
        + noncatching_group_open_regex_string
        + drive_group_open_regex_string
        + drive_620_regex_string
        + or_regex_string
        + drive_660_regex_string
        + group_close_regex_string
        + or_regex_string
        + io_group_open_regex_string
        + itegva_board_regex_string
        + group_close_regex_string
        + or_regex_string
        + tool_group_open_regex_string
        + robotiq_regex_string
        + group_close_regex_string
        + group_close_regex_string
        + end_regex_string
    )

    def run_check(self) -> bool:
        readout = self.get_cmd_stdout(["ethercat", "slaves"])
        if readout is None:
            self.log_warning("Cannot run the 'ethercat slaves' command")
            return False
        lines: str = readout.decode("utf-8")
        self.set_cache("slaves_report", lines)
        self.log_info("Got info about slaves on network")
        return True

    @classmethod
    def process_data(cls, data=None) -> dict:
        drives620: dict = dict()
        drives660: dict = dict()
        general_io: dict = dict()
        tools: dict = dict()

        if data:
            for device in data.splitlines():
                match: re.Match = cls.ec_complete_regex.match(device)
                if match:
                    item: dict = {}
                    item["error"] = (
                        False if (match.group("Error") == "+") else True
                    )
                    if match.group("Drive"):
                        if match.group("Drive620"):
                            item["name"] = "Drive620"
                            drives620[int(match.group("AbsRingPos"))] = item
                            continue
                        elif match.group("Drive660"):
                            item["name"] = "Drive660"
                            drives660[int(match.group("AbsRingPos"))] = item
                            continue
                    elif match.group("IO"):
                        if match.group("ITegva"):
                            item["name"] = "ITegva"
                            general_io[int(match.group("AbsRingPos"))] = item
                            continue
                    elif match.group("Tool"):
                        if match.group("Robotiq"):
                            item["name"] = "Robotiq"
                            tools[int(match.group("AbsRingPos"))] = item
                            continue
        return (
            {
                "ec_drives": {**drives620, **drives660},
                "general_io": general_io,
                "tools": tools,
            }
            if (drives620 or drives660 or general_io or tools)
            else dict()
        )

    def result_data(self) -> dict():
        try:
            if self.cached_result():
                state = self.get_cache("slaves_report")
                output = self.process_data(state)
                self.log_info(f"Found EC devices: {output}")
                return output
        except RuntimeError as e:
            self.log_info(
                f"Could not load data about devices on EtherCAT network: {e.args}"
            )
        return dict()


class EtherCAT(SubSystem):
    """Check the EtherCAT base system and pass into the container."""

    name = "EtherCAT"

    check_classes = [
        EthercatKmodLoaded,
        EthercatCharacterDeviceExists,
        UserInEthercatGroup,
        EthercatExecutableExists,
        EthercatNetworkHardware,
    ]
