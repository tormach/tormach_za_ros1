from .subsystem import SubSystem, SubSystemCheck


class MotherboardHardwareSupported(SubSystemCheck):
    """Look up motherboard information from a database.

    This non-fatal check passes data to other checks.
    """

    name = "motherboard_hardware_supported"
    fatal = False

    # The tuples in this dictionary are:
    #     svendor, product, bvendor, bname
    motherboard_database = {
        # CPUs 0,1 and 2,3 share caches; separating them will cause
        # large latency spikes
        ("GIGABYTE", "GB-BXBT-1900", None, None): dict(
            rt_cpus="2,3", max_cstate=True, desc="Gigabyte Brix GB-BXBT-1900"
        ),
        # Beta customer controller
        (None, None, "ASUSTeK COMPUTER INC.", "PRIME H310M-A R2.0"): dict(
            rt_cpus="5", max_cstate=True, desc="Beta customer controller"
        ),
        # Bas's dev box
        (None, "20HHCTO1WW", None, None): dict(
            rt_cpus="2,3", desc="Bas's dev box"
        ),
        # Yanling i7 IWill
        ("YANLING", "YL-KBRL2 Series", None, None): dict(
            rt_cpus="3,7", max_cstate=True, desc="Yanling i7 IWill"
        ),
        # Unknown default
        (None, None, None, None): dict(desc="Unknown hardware"),
    }

    hw_svendor_file = "/sys/devices/virtual/dmi/id/sys_vendor"
    hw_pname_file = "/sys/devices/virtual/dmi/id/product_name"
    hw_bvendor_file = "/sys/devices/virtual/dmi/id/board_vendor"
    hw_bname_file = "/sys/devices/virtual/dmi/id/board_name"

    def run_check(self):
        svendor = self.set_cache(
            'sys_vendor',
            self.read_file_contents(self.hw_svendor_file, first_line_only=True),
        )
        product = self.set_cache(
            'product_name',
            self.read_file_contents(self.hw_pname_file, first_line_only=True),
        )
        bvendor = self.set_cache(
            'board_vendor',
            self.read_file_contents(self.hw_bvendor_file, first_line_only=True),
        )
        bname = self.set_cache(
            'board_name',
            self.read_file_contents(self.hw_bname_file, first_line_only=True),
        )
        res = False
        for board_ids, settings in self.motherboard_database.items():
            if board_ids == (None, None, None, None):
                # Catch-all; skip this
                continue
            match = True
            for ix, id_string in enumerate((svendor, product, bvendor, bname)):
                if board_ids[ix] is None:
                    continue  # `None` matches anything
                if board_ids[ix] != id_string:
                    match = False
                    break
            if match:
                res = True
                self.set_cache('data', settings)
                break
        if res:
            data = self.get_cache('data')
            self.log_info("Found supported motherboard {}".format(data['desc']))
        else:
            self.set_cache(
                'data', self.motherboard_database[(None, None, None, None)]
            )
            self.log_warning(
                "Motherboard hardware not supported; "
                "realtime performance may suffer"
            )
        return res


class RTCPUs(SubSystemCheck):
    """Configure the Docker container's real-time CPUs.

    This non-fatal check depends on the
    ``motherboard_hardware_supported`` check.  If it fails, the
    real-time CPUs ``cpuset`` cgroup will not be configured in the
    container..
    """

    name = "RT_CPUs"
    depends = "motherboard_hardware_supported"
    fatal = False

    def run_check(self):
        if not self.have_cache('data', "motherboard_hardware_supported"):
            self.log_warning("Unable to determine RT CPUs on unknown hardware")
            return False
        data = self.get_cache('data', "motherboard_hardware_supported")
        if 'rt_cpus' not in data:
            self.log_warning("Unknown RT CPUs for this hardware")
            return False
        self.set_config('rt_cpus', data['rt_cpus'])
        self.log_info("Using RT CPUs {}".format(self.get_config('rt_cpus')))
        return True

    def docker_run_environment(self):
        if self.cached_result():
            return self.docker_environ_param(
                'RT_CPUS', self.get_config('rt_cpus')
            )
        else:
            return dict()


class GrubCmdline(SubSystemCheck):
    """Configure the host's GRUB command line.

    This non-fatal check depends on the
    ``motherboard_hardware_supported`` check.  If it fails, real-time
    CPUs will not be isolated at boot time.
    """

    name = "grub_cmdline"
    depends = "motherboard_hardware_supported"
    fatal = False

    # FIXME no way to tie this into bare metal install right now
    def run_check(self):
        data = self.get_cache('data', name="motherboard_hardware_supported")
        cmdline = ""
        rt_cpus = data.get('rt_cpus', None)
        if rt_cpus is not None:
            cmdline += f"isolcpus={rt_cpus} "
        max_cstate = data.get('max_cstate', None)
        if max_cstate is not None:
            cmdline += "intel_idle.max_cstate=1 "
        if cmdline:
            cmdline = cmdline.rstrip()
            self.set_config('cmdline', cmdline)
            self.log_info("GRUB command line:  '%s'" % cmdline)
        else:
            self.log_info("No GRUB command line set")
        return True


class Motherboard(SubSystem):
    """Check motherboard from a database and configure the GRUB command
    line and container real-time CPUs.
    """

    name = "Motherboard"
    check_classes = [MotherboardHardwareSupported, RTCPUs, GrubCmdline]
