import pytest
import io
import os
import builtins
from unittest.mock import MagicMock, patch
from pprint import pformat


@pytest.fixture()
def mock_env(request):
    """Mock environment variables

    The test class may set an `env` :py:class:`dict` attribute to seed
    the environment for all tests.

    The test class instance may update its own `env` attribute for
    specific tests.
    """
    inst = request.instance

    # Save original environment
    if not hasattr(inst, "env_orig"):
        inst.env_orig = os.environ.copy()

    # Initialize env, picking up any `env` class attribute
    env = getattr(inst, 'env', dict()).copy()
    patcher = patch.dict('os.environ', values=env, clear=True)

    patcher.start()
    inst.env = patcher.in_dict

    yield inst.env
    patch.stopall()


@pytest.fixture()
def mock_os_path_exists(request):
    inst = request.instance
    inst.file_data = getattr(inst, 'file_data', dict()).copy()
    if not hasattr(inst, 'file_objs'):
        inst.file_objs = dict()

    realexists = os.path.exists

    def mock_os_path_exists_func(path):
        if path in inst.file_data:
            exists = inst.file_data[path] is not None
            print(f'os.path.exists({path}):  {exists}')
            return exists
        else:
            return realexists(path)

    inst.mock_os_path_exists = MagicMock(
        name="mock_os_path_exists", side_effect=mock_os_path_exists_func
    )

    patch('os.path.exists', inst.mock_os_path_exists).start()
    yield inst.mock_os_path_exists
    patch.stopall()


@pytest.fixture()
def mock_open(request, mock_os_path_exists):
    """Mock open() and its returned file object; allow multiple files.

    Data is set in test object ``file_data`` dict with (path : string)
    mappings, and may be read from and written to.

    Also mock :py:method:`os.path.exists` for completeness.
    """
    inst = request.instance
    inst.file_data = getattr(inst, 'file_data', dict()).copy()
    if not hasattr(inst, 'file_objs'):
        inst.file_objs = dict()

    realopen = builtins.open

    def mock_open_func(path, mode='r', **kwargs):
        # Use real open() for paths not in file_data dict
        if path not in inst.file_data:
            print(
                "mock_open Returning real open('{}','{}',{})".format(
                    path, mode, kwargs
                )
            )
            return realopen(path, mode=mode, **kwargs)

        # Accommodate fake paths not existing
        if inst.file_data[path] is None:
            raise FileNotFoundError(
                "mock_open(%s):  Fake file not found" % path
            )

        # Fake open()ing a fake path
        print(
            "mock_open Returning fake open('{}','{}',{})".format(
                path, mode, kwargs
            )
        )
        fobj = inst.file_objs[path] = io.StringIO(inst.file_data.get(path))
        if mode in ('w', 'a'):
            real_close = fobj.close

            def close():
                inst.file_data[path] = fobj.getvalue()
                real_close()

            fobj.close = close
        return inst.file_objs[path]

    inst.mock_open = MagicMock(name="mock_open", side_effect=mock_open_func)

    patch('builtins.open', inst.mock_open).start()
    yield inst.mock_open
    patch.stopall()


@pytest.fixture()
def mock_time(request):
    """Mock time.time()

    Fake ``time.time()`` using a Mock side-effect in the test object's
    :py:attr:`times` attribute, or (if not set) return 0 to 99,
    incrementing by one on each call.
    """
    inst = request.instance
    patcher = patch('time.time', side_effect=getattr(inst, 'times', range(100)))
    inst.time = patcher.start()
    yield patcher
    patch.stopall()


@pytest.fixture()
def mock_requests(request, mock_time):
    """Mock requests class

    Mock ``requests.get()``.  The test instance's ``rsp`` attribute
    will serve as the response, or an empty :py:class:`dict`
    otherwise.

    If the test instance has an ``exception`` attribute, that exception
    will be mocked and raised.
    """
    inst = request.instance
    inst.req = MagicMock(name='requests')
    inst.reqs = dict()

    def req_get(url, headers=dict()):
        print("mock requests.get('%s')" % (url))
        inst.reqs[url] = headers

        if hasattr(inst, 'exception'):
            raise inst.exception('Mocked exception')

        rsp = MagicMock(name='get(%s)' % url, ok=True)
        rsp.json.return_value = dict(
            expires_in=inst.time() + 50, token=inst.req.token
        )
        rsp.json.return_value.update(getattr(inst, 'rsp', dict()))
        inst.reqs[url]['rsp'] = inst.last_req = rsp
        return rsp

    inst.req.get.side_effect = req_get
    patcher_get = patch('requests.get', new=inst.req.get)
    inst.req_get = patcher_get.start()
    yield inst.req
    patch.stopall()


@pytest.fixture()
def mock_socket(request, mock_time):
    """Mock socket class

    If the test instance has an ``exception`` attribute, that exception
    will be mocked and raised.
    """
    inst = request.instance
    inst.req = MagicMock(name='socket.socket')
    inst.reqs = dict()

    def req_recvfrom(size):
        print(f"mock socket.recvfrom({size})")
        response = getattr(inst, 'receive_data', [])
        address = getattr(inst, 'address', None)

        if hasattr(inst, 'exception'):
            raise inst.exception('Mocked exception')

        return (response, address)

    inst.req.recvfrom.side_effect = req_recvfrom
    patcher_get = patch('socket.socket.recvfrom', new=inst.req.recvfrom)
    inst.req_recvfrom = patcher_get.start()
    yield inst.req
    patch.stopall()


@pytest.fixture()
def mock_find_executable(request):
    # Mock distutils.spawn.find_executable()
    inst = request.instance

    inst.executable_map = getattr(inst, 'executable_map', dict()).copy()

    def find_executable(name):
        return inst.executable_map.get(name, None)

    mock_find_executable = MagicMock(
        name="mock_find_executable", side_effect=find_executable
    )

    patch('distutils.spawn.find_executable', mock_find_executable).start()
    yield mock_find_executable
    patch.stopall()


@pytest.fixture()
def mock_subprocess_popen(request):
    # Mock subprocess.Popen()
    inst = request.instance

    mock_popen_obj = MagicMock(name="mock_subprocess_popen_obj")
    mock_popen_obj.wait.return_value = 0

    inst.mock_popen = MagicMock(
        name="mock_subprocess_popen", return_value=mock_popen_obj
    )

    def mock_output(*args, **kwargs):
        if not hasattr(inst, "mock_subprocess_stdout"):
            inst.mock_subprocess_stdout = 'Bogus stdout\n'
        return inst.mock_subprocess_stdout

    inst.mock_check_output = MagicMock(
        name="mock_subprocess_check_output", side_effect=mock_output
    )

    patch('subprocess.Popen', inst.mock_popen).start()
    patch('subprocess.check_output', inst.mock_check_output).start()
    yield mock_popen_obj
    patch.stopall()


@pytest.fixture()
def mock_termios(request, mock_env):
    """Mock termios

    If test instance ``have_tty`` attribute is ``False``, raise
    ``termios.error`` on ``tcgetattr()``.

    Also set a ``TERM`` environment variable default value.
    """
    inst = request.instance

    inst.termios = MagicMock(name="mock_termios")
    tcgetattr_res = [1280, 1, 191, 35379, 15, 15]  # Partial list
    inst.tcgetattr_res = getattr(inst, 'tcgetattr_res', tcgetattr_res)

    class mock_termios_error(RuntimeError):
        pass

    def tcgetattr_side_effect(fd):
        if not inst.have_tty:
            raise mock_termios_error()
        else:
            return inst.tcgetattr_res

    inst.termios.tcgetattr.side_effect = tcgetattr_side_effect
    inst.termios_error = mock_termios_error
    patch('termios.tcgetattr', inst.termios.tcgetattr).start()
    patch('termios.error', mock_termios_error).start()

    inst.env.setdefault('TERM', 'dumb')
    yield inst.termios
    patch.stopall()


@pytest.fixture()
def mock_uid_gid(request):
    inst = request.instance

    def getuid():
        res = getattr(inst, 'uid', 1000)
        print('Mock os.getuid() = %s' % res)
        return res

    def getgid():
        res = getattr(inst, 'gid', 1000)
        print('Mock os.getgid() = %s' % res)
        return res

    patch('os.getuid', side_effect=getuid).start()
    patch('os.getgid', side_effect=getgid).start()
    yield
    patch.stopall()


@pytest.fixture()
def mock_cwd(request):
    inst = request.instance

    def getcwd():
        return getattr(inst, 'cwd', '/home/pathpilot')

    inst.getcwd = patch('os.getcwd', side_effect=getcwd).start()
    yield inst.getcwd
    patch.stopall()


@pytest.fixture()
def mock_groups(request):
    inst = request.instance

    default_group_db = dict(docker=801, ethercat=802, test_group=803)

    def group_to_gid(group):
        groups = getattr(inst, 'sys_groups', default_group_db)
        if group not in groups:
            raise KeyError('mock getgrnam(): name not found: %s' % group)
        m = MagicMock(name=f'grp.getgrnam({group})')
        m.gr_name = group
        m.gr_passwd = None
        m.gr_gid = groups.get(group)
        m.gr_mem = list()  # Unimplemented
        print(f'mock grp.getprnam({group}): gid={m.gr_gid}')
        return m

    def group_ids():
        default_gids = sorted(
            [24, 25, 27, 29, 30, 1000] + list(default_group_db.values())
        )
        gids = getattr(inst, 'group_ids', default_gids)
        print('mock os.getgroups():', gids)
        return gids

    inst.getgrnam = patch('grp.getgrnam', side_effect=group_to_gid).start()
    inst.getgroups = patch("os.getgroups", side_effect=group_ids).start()

    yield
    patch.stopall()


@pytest.fixture()
def mock_container_env(request, mock_env):
    """Mock environment variables set in a typical container

    If the test class ``patch_versions_module`` attribute is
    ``True``, also patch
    ``pp_ros_launch.image.versions.PPRosImageVersion`` attributes set
    from :py:attr:`os.environ`.  The test object may set attributes
    ``image_version_major``, ``image_version_hash``, which are
    combined into ``image_version``, and ``ros_distro``,
    ``debian_suite``, ``image_type`` and ``docker_repo``.  Missing
    attributes will be set to reasonable defaults.

    This also adds some test data that can be overridden:  a
    ``test_docker_tags`` attribute, a list of (tag, image version,
    image type) tuples, and a ``labels`` attribute, a dictinory of
    image labels.
    """
    inst = request.instance
    patch_versions_module = getattr(inst, 'patch_versions_module', False)

    # Set $DOCKER_REPO mock environment variable and add shortcut
    inst.docker_repo = inst.env['DOCKER_REPO'] = "tormach/ros_public"

    # Mock up environment
    # - Set defaults for Docker-related environment and patch
    #   PPRosImageVersion class attributes
    inst.image_version_major = getattr(inst, 'image_version_major', 42)
    inst.image_version_hash = getattr(inst, 'image_version_hash', 'deadbeef')

    if patch_versions_module:
        from pp_ros_launch.image.versions import PPRosImageVersion
    defaults = dict(
        ROS_DISTRO='kinetic',
        IMAGE_TYPE='dist',
        DEBIAN_SUITE='stretch',
        IMAGE_VERSION=f'{inst.image_version_major}+{inst.image_version_hash}',
        DOCKER_REPO=inst.docker_repo,
    )
    for name, val in defaults.items():
        # Set test object attribute defaults
        setattr(inst, name.lower(), getattr(inst, name.lower(), val))
        # Mock environment
        inst.env.setdefault(name, getattr(inst, name.lower()))
        if patch_versions_module:
            # Patch PPRosImageVersion attributes
            patch.object(PPRosImageVersion, name, val).start()
            assert getattr(PPRosImageVersion, name) == val  # Sanity
    inst.tag = '{}-{}-{}-{}.{}'.format(
        inst.ros_distro,
        inst.image_type,
        inst.debian_suite,
        inst.image_version_major,
        inst.image_version_hash,
    )
    inst.image_tag_version = defaults['IMAGE_VERSION'].replace('+', '.')
    # Debug output
    print('environment:', pformat(inst.env))

    # Add test data
    inst.labels = {
        'com.tormach.pathpilot.robot.version': '0.1.0',
        'com.tormach.pathpilot.robot.image.type': inst.image_type,
        'com.tormach.pathpilot.robot.git.rev': '0000aaaa',
    }

    test_docker_tags = [
        (inst.tag, inst.image_version, inst.image_type),
        ('kinetic-devel-stretch-46.b2387cf5', '46+b2387cf5', 'devel'),
        ('kinetic-devel-stretch-44.de725e51', '44+de725e51', 'devel'),
        ('kinetic-dist-stretch-44.de725e51', '44+de725e51', 'dist'),
        # Tests old `ver.hash` format
        ('kinetic-devel-stretch-33.148234fb', '33.148234fb', 'devel'),
        ('kinetic-dist-stretch-32.a8925c52', '32+a8925c52', 'dist'),
        ('kinetic-dist-stretch-41.deadbeef', '41+deadbeef', 'dist'),
        ('kinetic-dist-stretch-43.deadbeef', '43+deadbeef', 'dist'),
        ('bogus', None, None),
    ]
    inst.test_docker_tags = getattr(inst, 'test_docker_tags', test_docker_tags)

    yield mock_env
    patch.stopall()


@pytest.fixture
def mock_docker_local(request, mock_container_env):
    inst = request.instance

    print('Patching docker local client')

    # Mock newer Python docker module API
    patch('docker.__version__', (6, 1, 2)).start()

    def images_get(name):
        tag = (name.split(':') + [''])[1]
        for t in inst.test_docker_tags:
            if t[0] == tag:
                print('mock_docker_local images.get():  Found image', tag)
                inst.get_rv = MagicMock(
                    name='docker image %s' % t[0], labels=inst.labels
                )
                return inst.get_rv
        print(
            f'mock_docker_local images.get():  Unable to find image tag {tag}'
        )
        raise RuntimeError('No such image "%s"' % name)

    def images_list(**kwargs):
        print(
            'mock_docker_local images.list():  returning\n',
            pformat([itag for itag, iver, itype in inst.test_docker_tags]),
        )
        return [
            MagicMock(
                name='docker image %s' % itag,
                tags=[f'{inst.docker_repo}:{itag}', 'bogus:foo', 'bogus'],
            )
            for itag, iver, itype in inst.test_docker_tags
        ]

    def pull_msgs(repo, tag=None, stream=False, decode=False):
        # For raw API pull() method
        default = [
            {
                'status': f'Pulling from {inst.docker_repo}',
                'id': 'kinetic-dist-stretch-56.fac3042a',
            },
            {
                'status': 'Digest: sha256:51ad6d2e429f4a250fe7d856d3472e99f67ca'
                '4a15a74fbd21edfbe251b2bfada'
            },
            {
                'status': 'Status: Image is up to date for '
                f'{inst.docker_repo}:kinetic-dist-stretch-56.fac3042a'
            },
        ]
        msgs = getattr(inst, 'docker_pull_messages', default)
        yield from msgs

    docker_client = inst.docker_client = MagicMock(name='docker.from_env()')
    docker_client.images.get.side_effect = images_get
    docker_client.images.list.side_effect = images_list

    # pull() method
    docker_client_raw = MagicMock(name='docker.APIClient')
    docker_client.api = docker_client_raw
    docker_client_raw.pull = MagicMock(
        name='docker.APIClient.pull()', side_effect=pull_msgs
    )

    patch('docker.from_env', return_value=docker_client).start()

    yield docker_client
    patch.stopall()


@pytest.fixture()
def mock_docker_hub(request, mock_container_env):
    """Patch ``pp_ros_launch.image.docker_hub.DockerRepo``

    Patch up ``get_tags_list`` to return list of tags in the test
    instance ``test_docker_tags`` attribute.

    Patch up ``get_labels`` to return the test instance ``labels``
    attribute.
    """
    inst = request.instance

    def mock_get_tags_list():
        if hasattr(inst, 'docker_hub_exception'):
            print('mock_get_tags_list() raising exception')
            raise inst.docker_hub_exception('Mock docker_hub exception')

        res = [t[0] for t in inst.test_docker_tags]
        print("get_tags_list() -> %s" % res)
        return res

    def mock_get_labels(reference):
        if hasattr(inst, 'docker_hub_exception'):
            print('mock_get_labels(%s) raising exception' % reference)
            raise inst.docker_hub_exception('Mock docker_hub exception')

        return inst.labels

    # Patch pp_ros_launch.image.docker_hub.DockerRepo methods
    patch(
        'pp_ros_launch.image.docker_hub.DockerRepo.get_tags_list',
        side_effect=mock_get_tags_list,
    ).start()
    patch(
        'pp_ros_launch.image.docker_hub.DockerRepo.get_labels',
        side_effect=mock_get_labels,
    ).start()

    yield
    patch.stopall()


@pytest.fixture
def mock_cl_args(request):
    # Mock args object from argparse parser
    inst = request.instance

    # Test command line arguments
    class cl_arg_class:
        pass

    cl_args = inst.cl_args_obj = cl_arg_class()
    cl_args.state_file = getattr(
        inst,
        '_default_state_path',
        '/home/pathpilot/.pathpilot/launcher_config.yaml',
    )
    cl_args.__dict__.update(getattr(inst, 'cl_args', dict()))
    return cl_args


@pytest.fixture
def mock_logging():
    def getlogger(name='default'):
        def log_func(name):
            def log(*args, **kwargs):
                print(f"Log message:  {name}:  {args} {kwargs}")

            return log

        logger = MagicMock(name="logger<%s>" % name)
        for func in ('debug', 'info', 'warning', 'error', 'critical', 'fatal'):
            setattr(logger, func, log_func(func))

        return logger

    patch('logging.getLogger', side_effect=getlogger).start()
    yield
    patch.stopall()
