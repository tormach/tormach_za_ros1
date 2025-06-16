import pytest
import sys
from .test_subsystem import (
    TestSubSystem,
    TestSubSystemCheck,
    TestSubSystemExecutableCheck,
    TestSubSystemDockerVolumeCheck,
    TestSubSystemDockerEnvCheck,
)
from pp_ros_launch.system.gpu import (
    GPU,
    HaveGlxinfoExecutable,
    GPUEnvironment,
    X11Socket,
    #    DevDRI,
    GPUConfiguration,
)


if sys.version_info[0] == 2:

    def my_bytes(s, enc):
        return bytes(s)

else:

    def my_bytes(s, enc):
        return bytes(s, enc)


@pytest.fixture
def mock_glxinfo_brix(request, mock_subprocess_popen):
    request.instance.mock_subprocess_stdout = my_bytes(
        # Brix (incomplete)
        "Extended renderer info (GLX_MESA_query_renderer):\n"
        "OpenGL vendor string: Intel Open Source Technology Center\n"
        "OpenGL renderer string: Mesa DRI Intel(R) Bay Trail \n"
        "OpenGL core profile version string: 3.3 [...]\n",
        'utf-8',
    )
    return mock_subprocess_popen.popen_obj


@pytest.fixture
def mock_glxinfo_polaris(request, mock_subprocess_popen):
    request.instance.mock_subprocess_stdout = my_bytes(
        # bogus for Rob's polaris
        "Extended renderer info (GLX_MESA_query_renderer):\n"
        "OpenGL vendor string: X.Org\n"
        "OpenGL renderer string: bogusPOLARISbogus\n"
        "OpenGL core profile version string: 3.3 [...]\n",
        'utf-8',
    )
    return mock_subprocess_popen


@pytest.fixture
def mock_glxinfo_unsupported(request, mock_subprocess_popen):
    request.instance.mock_subprocess_stdout = my_bytes(
        # Bogus
        "Extended renderer info (GLX_MESA_query_renderer):\n"
        "OpenGL vendor string: Bogus vendor\n"
        "OpenGL renderer string: Bogus renderer\n"
        "OpenGL core profile version string: 3.3 [...]\n",
        'utf-8',
    )
    return mock_subprocess_popen


class TestHaveGlxinfoExecutable(TestSubSystemExecutableCheck):
    test_class = HaveGlxinfoExecutable


class TestGPUEnvironment(TestSubSystemDockerEnvCheck):
    test_class = GPUEnvironment
    expected_environment = dict(
        DISPLAY=':0', XDG_RUNTIME_DIR='/run/user/1000', PATH='/usr/bin'
    )


class TestX11Socket(TestSubSystemDockerVolumeCheck):
    test_class = X11Socket


# class TestDevDRI(TestSubSystemDockerVolumeCheck):
#    test_class = DevDRI


class TestGPUConfiguration(TestSubSystemCheck):
    test_class = GPUConfiguration
    fatal = False

    @pytest.fixture()
    def obj(self):
        for obj in self.obj_fixture():
            obj.set_cache('result', True, "have_glxinfo_executable")
            yield obj

    @pytest.fixture()
    def obj_pass(self, mock_glxinfo_brix):
        for obj in self.obj_fixture():
            obj.set_cache('result', True, "have_glxinfo_executable")
            yield obj

    @pytest.fixture()
    def obj_fail(self, mock_glxinfo_unsupported):
        for obj in self.obj_fixture():
            obj.set_cache('result', True, "have_glxinfo_executable")
            yield obj

    def test_gpu_database_sanity(self):
        l3_keys = dict(info=str, warning=str, docker_run_args=dict)
        for l1_key, l1_data in self.test_class.gpu_database.items():
            # OGL vendor
            print("l1_key:", l1_key)
            assert isinstance(l1_key, str)
            for l2_key, l2_data in l1_data.items():
                # OGL renderer
                print("l2_key:", l2_key)
                assert isinstance(l2_key, str)
                for l3_key, l3_data in l2_data.items():
                    print("l3_key:", l3_key)
                    print("l3_data:", l3_data)
                    assert l3_key in l3_keys
                    assert isinstance(l3_data, l3_keys[l3_key])

    def test_glxinfo_string_brix(self, obj, mock_glxinfo_brix):
        assert (
            obj._glxinfo_string("OpenGL vendor string")
            == "Intel Open Source Technology Center"
        )
        assert (
            obj._glxinfo_string("OpenGL renderer string")
            == "Mesa DRI Intel(R) Bay Trail"
        )

    def test_glxinfo_string_unsupported(self, obj, mock_glxinfo_unsupported):
        assert obj._glxinfo_string("OpenGL vendor string") == "Bogus vendor"
        assert obj._glxinfo_string("OpenGL renderer string") == "Bogus renderer"

    def test_run_check_polaris(self, obj, mock_glxinfo_polaris):
        print(obj)
        assert obj.run_check() is True

    def test_docker_run_volumes_polaris(self, obj, mock_glxinfo_polaris):
        obj.set_cache('result', True, "have_glxinfo_executable")
        assert obj.check_result is True
        drv = obj.docker_run_volumes()
        assert isinstance(drv, dict)
        assert len(drv) == 1
        assert '/dev/kfd' in drv


class TestGPU(TestSubSystem):
    test_class = GPU
    # Mocking TestHaveGlxinfoExecutable failure causes other tests to fail in
    # the wrong place; leave it out
    check_test_classes = [
        TestGPUEnvironment,
        TestX11Socket,
        #        TestDevDRI,
        TestGPUConfiguration,
    ]

    @pytest.fixture()
    def obj_pass(
        self, mock_glxinfo_brix, mock_env, mock_open, mock_find_executable
    ):
        self.env.update(TestGPUEnvironment.expected_environment)
        self.file_data[X11Socket.path] = ''
        # self.file_data[DevDRI.path] = ''
        self.file_data[
            TestGPUEnvironment.expected_environment['XDG_RUNTIME_DIR']
        ] = ''
        self.executable_map["glxinfo"] = "/usr/bin/glxinfo"
        yield from self.obj_fixture()

    @pytest.fixture()
    def obj_fail(self, mock_glxinfo_unsupported, mock_env, mock_open):
        self.env.update(dict(PATH='/usr/bin'))
        self.file_data[X11Socket.path] = None
        # self.file_data[DevDRI.path] = None
        yield from self.obj_fixture()
