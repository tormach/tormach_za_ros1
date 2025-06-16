from .subsystem import (
    SubSystem,
    SubSystemCheck,
    SubSystemDockerEnvCheck,
    SubSystemDockerVolumeCheck,
    SubSystemExecutableCheck,
)
import re
import os


class HaveGlxinfoExecutable(SubSystemExecutableCheck):
    """Assert the ``glxinfo`` executable exists."""

    name = "have_glxinfo_executable"
    executable = "glxinfo"


class GPUEnvironment(SubSystemDockerEnvCheck):
    """Pass ``DISPLAY`` and ``XDG_RUNTIME_DIR`` environment variables into
    the Docker container.

    Non-fatal.
    """

    name = "gpu_environment"
    fatal = False
    env_vars = ['DISPLAY', 'XDG_RUNTIME_DIR']


class XDGRuntimeDir(SubSystemDockerVolumeCheck):
    """Bind-mount the directory from the ``XDG_RUNTIME_DIR`` environment
    variable.
    """

    name = "xdg_runtime_dir"
    depends = 'gpu_environment'

    @property
    def path(self):
        cache = self.get_cache('vars_set', name=self.depends)
        if 'XDG_RUNTIME_DIR' in cache:
            return cache['XDG_RUNTIME_DIR']
        else:
            # This will cause a failure and won't bind-mount directory
            return ''


class X11Socket(SubSystemDockerVolumeCheck):
    """Bind-mount the X11 socket directory into the container.

    Non-fatal.
    """

    name = "x11_socket"
    fatal = False
    path = '/tmp/.X11-unix'

    @property
    def host_path(self):
        if os.environ.get("VIRTUAL_PATHPILOT", None):
            # Create a volume
            return 'x11_socket'
        else:
            # Bind-mount host path
            return self.path


# class DevDRI(SubSystemDockerVolumeCheck):
#    """Bind-mount the DRI device node into the container.
#
#    Non-fatal.
#    """
#
#    name = "dev_dri"
#    fatal = False
#    path = '/dev/dri'


class GPUConfiguration(SubSystemCheck):
    """Determine GPU configuration based on ``glxinfo`` output.

    This non-fatal command depends on the ``gpu_configuration`` check.
    Depending on the detected GPU, it may bind-mount device nodes or
    set environment variables in the Docker container.
    """

    name = "gpu_configuration"
    depends = "have_glxinfo_executable"
    fatal = False

    gpu_database = {
        # Brix; John's ThinkPad X201t:  No special config
        "Intel Open Source Technology Center": {
            r".*": {"info": "Intel driver"}
        },
        # Alexander's NVidia w/proprietary drivers
        "NVIDIA Corporation": {
            r".*": {
                "info": "NVIDIA proprietary driver",
                "docker_run_args": {
                    "environment": {
                        "NVIDIA_VISIBLE_DEVICES": "all",
                        "NVIDIA_DRIVER_CAPABILITIES": "graphics",
                    },
                    "args": {"runtime": "nvidia"},
                },
            }
        },
        # SSH forwarded X connection (Probably will never see this)
        "VMware, Inc.": {
            r".*": {
                "info": "Virtual graphics hardware",
                "warning": "The GUI will not run with this hardware!",
            }
        },
        # Bas's NVidia w/FOSS drivers:  No special config
        "nouveau": {r".*": {"info": "Nouveau driver"}},
        # Rob's AMD RX 580 GPU
        "X.Org": {
            r".*POLARIS.*": {
                "info": "Polaris driver",
                "docker_run_args": {
                    "volumes": {'/dev/kfd': {"bind": "/dev/kfd", "mode": "rw"}}
                },
            }
        },
    }

    def _glxinfo_string(self, s):
        string_re_raw = fr'^{s}: (.*)$'
        string_re = re.compile(string_re_raw)
        lines = self.get_cmd_stdout(['glxinfo', '-display', ':0'])
        if lines is None:
            return None
        for line in lines.decode("utf-8").split('\n'):
            line_cooked = line.rstrip()
            m = string_re.match(line_cooked)
            if m:
                return m.group(1)
        else:
            return None

    def run_check(self):
        ogl_vendor = self._glxinfo_string("OpenGL vendor string")
        self.log_info(f"OpenGL vendor:  {ogl_vendor}")
        ogl_renderer = self._glxinfo_string("OpenGL renderer string")
        self.log_info(f"OpenGL renderer:  {ogl_renderer}")

        renderer_data = self.gpu_database.get(ogl_vendor, None)
        if renderer_data is None:
            w = f"Unrecognized GPU hardware '{ogl_vendor}'"
            self.log_warning(w + '; the GUI may not run')
            return False
        for r_re, sub_info in renderer_data.items():
            if re.compile(r_re).match(ogl_renderer):
                self.log_info(sub_info['info'])
                if 'warning' in sub_info:
                    self.log_warning(sub_info['warning'])
                    return False
                else:
                    self.sub_info = sub_info
                    return True
        else:
            w = f"Unrecognized GPU hardware '{ogl_renderer}'"
            self.log_warning(w + '; the GUI may not run')
            return False

    def docker_run_volumes(self):
        if not self.cached_result():
            return dict()
        return self.sub_info.get('docker_run_args', dict()).get(
            'volumes', dict()
        )

    def docker_run_environment(self):
        if not self.cached_result():
            return dict()
        return self.sub_info.get('docker_run_args', dict()).get(
            'environment', dict()
        )

    def docker_run_args(self):
        if not self.cached_result():
            return dict()
        return self.sub_info.get('docker_run_args', dict()).get('args', dict())


class GPU(SubSystem):
    """Check the host's GPU and configure the Docker container for it."""

    name = "GPU"

    check_classes = [
        HaveGlxinfoExecutable,
        GPUEnvironment,
        X11Socket,
        #        DevDRI,
        GPUConfiguration,
        XDGRuntimeDir,
    ]
