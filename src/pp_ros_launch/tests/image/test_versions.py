from pp_ros_launch.image.versions import (
    PPRosImageVersion,
    PPRosHubImageVersion,
    PPRosLocalImageVersion,
    PPRosImageVersionException,
    DockerRegistryIOError,
)
import pytest
import datetime


class _Thing:
    def __init__(self, **kwargs):
        for attr, val in kwargs.items():
            setattr(self, attr, val)


class BaseTestPPRosImageVersion:
    tc = PPRosImageVersion
    # Patch up PPRosImageVersion attributes set from os.environ in the
    # mock_container_env fixture
    patch_versions_module = True

    @pytest.fixture
    def mock_docker(self):
        raise NotImplementedError("mock_docker fixture not defined")

    @pytest.fixture
    def obj(self, mock_container_env):
        return self.tc(self.tag)

    def test_attrs(self, obj, mock_docker):
        assert obj.docker_repo == self.docker_repo

    def test_parse_image_tag(self, mock_container_env):
        (
            ros_distro,
            image_type,
            debian_suite,
            image_version_major,
            image_version_hash,
        ) = self.tc.parse_image_tag(self.tag)
        assert ros_distro == self.ros_distro
        assert image_type == self.image_type
        assert debian_suite == self.debian_suite
        assert image_version_major == self.image_version_major
        assert image_version_hash == self.image_version_hash

    def test_init(self, obj):
        assert obj.ros_distro == self.ros_distro
        assert obj.image_type == self.image_type
        assert obj.debian_suite == self.debian_suite
        assert obj.image_version_major == self.image_version_major
        assert obj.image_version_hash == self.image_version_hash

    def test_construct_image_tag(self, mock_container_env):
        tag = self.tc.construct_image_tag(
            self.ros_distro,
            self.image_type,
            self.debian_suite,
            self.image_version_major,
            self.image_version_hash,
        )
        assert tag == self.tag

    def test_is_valid_image_tag(self, mock_container_env):
        assert self.tc.is_valid_image_tag(self.tag)
        for t in self.tc.image_types:
            assert self.tc.is_valid_image_tag(
                self.tag.replace(self.image_type, t)
            )
        print("self.tag:", self.tag)
        assert not self.tc.is_valid_image_tag(
            self.tag.replace(self.image_type, 'bogus')
        )
        assert not self.tc.is_valid_image_tag(
            self.tag.replace(self.image_tag_version, 'bogus')
        )

    def test_all_images(self, mock_docker):
        images = self.tc.all_images()
        tags = [i.image_tag for i in images]
        print(tags)
        print([t[0] for t in self.test_docker_tags if t[1]])
        assert tags == [t[0] for t in self.test_docker_tags if t[1]]

    def test_image_by_version(self, mock_docker):
        for itag, iver, itype in self.test_docker_tags:
            if iver:
                print("itag:", itag, "iver:", iver, "itype:", itype)
                assert self.tc.image_by_version(iver, itype).image_tag == itag

    def test_image_by_tag(self, mock_docker):
        for itag, iver, itype in self.test_docker_tags:
            if iver:
                assert isinstance(self.tc.image_by_tag(itag), self.tc)
                assert self.tc.image_by_tag(itag).image_tag == itag
            else:
                assert self.tc.image_by_tag(itag) is None

    def test_image_version(self, obj):
        assert obj.image_version == self.image_version

    def test_this_image(self, mock_container_env):
        obj = self.tc.this_image()
        assert obj.image_version == self.image_version

    def test_image_labels(self, obj, mock_docker):
        assert obj.image_labels() == self.labels

    def test_label(self, obj, mock_docker):
        for label, val in self.labels.items():
            assert obj.label(label) == val

    def test_software_version(self, obj, mock_docker):
        assert (
            obj.software_version
            == self.labels['com.tormach.pathpilot.robot.version']
        )

    def test_image_name(self, obj, mock_docker):
        assert obj.image_name == (self.docker_repo + ':' + self.tag)

    def _set_release_version(
        self, obj, name: str, version: str, git_rev: str, codename: str
    ):
        # Mock software_version by faking cache
        labels = {'com.tormach.pathpilot.robot.version': version}
        if git_rev is not None or '':
            labels['com.tormach.pathpilot.robot.git.rev'] = git_rev
        if codename is not None or '':
            labels['com.tormach.pathpilot.robot.codename'] = codename

        if self.tc is PPRosHubImageVersion:
            labels = {
                'labels': labels,
                'date': datetime.datetime.now().isoformat(),
            }
            # Docker hub
            conf = self.tc._get_config_obj().setdefault(
                'image_label_cache', dict()
            )
            conf[obj.image_name] = labels
        else:
            # Local images
            obj._image_data = _Thing(labels=labels)
        assert (
            obj.image_labels()['com.tormach.pathpilot.robot.version'] == version
        )
        print(name, obj.software_version)

    def test_cmp(self, obj, mock_docker):
        obj_gt = self.tc(
            self.tag.replace(
                str(self.image_version_major), str(self.image_version_major + 1)
            )
        )
        obj_lt = self.tc(
            self.tag.replace(
                str(self.image_version_major), str(self.image_version_major - 1)
            )
        )

        self.tc.get_stash().pop('config', None)
        self._set_release_version(obj_gt, 'obj_gt', '0.1.3', None, 'Test run')
        self._set_release_version(obj, 'obj', '0.1.1', None, 'Test run')
        self._set_release_version(obj_lt, 'obj_lt', '0.1.0', None, 'Test run')
        # __lt__
        assert obj_lt < obj
        assert obj < obj_gt
        assert obj_lt < obj_gt
        assert not obj < obj_lt
        assert not obj_gt < obj
        assert not obj_gt < obj_lt
        assert not obj < obj
        # __gt__
        assert obj_gt > obj
        assert obj > obj_lt
        assert obj_gt > obj_lt
        assert not obj > obj_gt
        assert not obj_lt > obj
        assert not obj_lt > obj_gt
        assert not obj > obj
        # __le__
        assert obj_lt <= obj
        assert obj <= obj_gt
        assert obj_lt <= obj_gt
        assert obj <= obj
        assert not obj <= obj_lt
        assert not obj_gt <= obj
        assert not obj_gt <= obj_lt
        # __ge__
        assert obj_gt >= obj
        assert obj >= obj_lt
        assert obj_gt >= obj_lt
        assert obj >= obj
        assert not obj >= obj_gt
        assert not obj_lt >= obj
        assert not obj_lt >= obj_gt
        # __eq__
        assert obj == obj
        assert obj_gt == obj_gt
        assert obj_lt == obj_lt
        assert not obj_gt == obj
        assert not obj_gt == obj_lt
        assert not obj == obj_lt
        # __ne__
        assert obj_gt != obj
        assert obj_gt != obj_lt
        assert obj != obj_lt
        assert not obj != obj
        assert not obj_gt != obj_gt
        assert not obj_lt != obj_lt

        print("Check semver metadata is ignored")
        # Everything after the '+' is ignored for equality purposes
        self._set_release_version(obj_gt, 'obj_gt', '0.1.1', '10800000', None)
        self._set_release_version(obj_lt, 'obj_lt', '0.1.1', '10900000', None)
        assert obj_lt == obj_gt

        # These cause "TypeError: '>' not supported between instances
        # of 'int' and 'str'" error on Ubuntu with older `semver`
        # because the hash is parsed as follows:
        #
        # ['pre.', 108, '.c', 20,  'c',  541, 'a'] 0.1.0-pre.108.c20c541a
        # ['pre.', 108, '.c', '0', 'a', 2966, 'd'] 0.1.0-pre.108.c0a2966d
        print("Check for Ubuntu semver")
        self._set_release_version(
            obj_gt, 'obj_gt', '0.1.1-pre.108.c20c541a', None, 'Test run'
        )
        self._set_release_version(
            obj_lt, 'obj_lt', '0.1.1-pre.108.c0a2966d', None, 'Test run'
        )
        assert obj_lt == obj_gt

        # In newer semver, "ValueError: 0.1.0-pre.99.07924946 is not
        # valid SemVer string" because the last bit begins with '0'.
        # This is fixed by translating the final '.' to '+'.
        print("Check semver pre-processing")
        self._set_release_version(
            obj, 'obj', '0.1.0-pre.99.07924946', None, 'Test run'
        )
        assert obj == obj


class TestPPRosHubImageVersion(BaseTestPPRosImageVersion):
    tc = PPRosHubImageVersion

    @pytest.fixture
    def mock_docker(self, mock_docker_hub):
        print('Mocking docker hub client')
        return mock_docker_hub

    def test_image_manifest(self):
        # Used for debugging
        pass

    def test_all_images_fail(self, mock_docker_hub):
        self.docker_hub_exception = DockerRegistryIOError
        with pytest.raises(PPRosImageVersionException):
            self.tc.all_images()

    def test_image_labels_fail(self, obj, mock_docker_hub):
        obj.clear_stash()  # Cached results break the test
        self.docker_hub_exception = DockerRegistryIOError
        with pytest.raises(PPRosImageVersionException):
            print(obj.image_labels())


class TestPPRosLocalImageVersion(BaseTestPPRosImageVersion):
    tc = PPRosLocalImageVersion

    @pytest.fixture
    def mock_docker(self, mock_docker_local):
        print('Mocking local docker client')
        yield mock_docker_local

    @property
    def docker_pull_messages(self):
        return [
            {
                'status': f'Pulling from {self.docker_repo}',
                'id': 'kinetic-dist-stretch-56.fac3042a',
            },
            # (Doesn't yield)
            {
                'status': 'Already exists',
                'progressDetail': {},
                'id': '6f2f362378c5',
            },
            # 1/1, 0
            {
                'status': 'Pulling fs layer',
                'progressDetail': {},
                'id': '17adc92fa90e',
            },
            # 1/2, 0
            {
                'status': 'Pulling fs layer',
                'progressDetail': {},
                'id': '46ae700d03e4',
            },
            # 1/3, 0
            {
                'status': 'Downloading',
                'progressDetail': {'current': 367, 'total': 367},
                'id': '17adc92fa90e',
                'progress': '[============================================'
                '======>]     367B/367B',
            },
            # 1/3, (367/2) / (367) = 50
            {
                'status': 'Downloading',
                'progressDetail': {'current': 229, 'total': 229},
                'id': '46ae700d03e4',
                'progress': '[============================================='
                '=====>]     229B/229B',
            },
            # 1/3, (367/2 + 229/2) / (367 + 229) = 50
            {
                'status': 'Download complete',
                'progressDetail': {},
                'id': '17adc92fa90e',
            },
            # 1/3, (367/2 + 229/2) / (367 + 229) = 50
            {
                'status': 'Verifying Checksum',
                'progressDetail': {},
                'id': '46ae700d03e4',
            },
            # 1/3, (367/2 + 229/2) / (367 + 229) = 50
            {
                'status': 'Extracting',
                'progressDetail': {'current': 367, 'total': 367},
                'id': '17adc92fa90e',
                'progress': '[=============================================='
                '====>]     367B/367B',
            },
            # 1/3, (367 + 229/2) / (367 + 229) = 80
            {
                'status': 'Download complete',
                'progressDetail': {},
                'id': '46ae700d03e4',
            },
            # 1/3, (367 + 229/2) / (367 + 229) = 80
            {
                'status': 'Extracting',
                'progressDetail': {'current': 367, 'total': 367},
                'id': '17adc92fa90e',
                'progress': '[==============================================='
                '===>]     367B/367B',
            },
            # 1/3, (367 + 229/2) / (367 + 229) = 80
            {
                'status': 'Pull complete',
                'progressDetail': {},
                'id': '17adc92fa90e',
            },
            # 2/3, (229/2) / (229) = 50
            {
                'status': 'Extracting',
                'progressDetail': {'current': 229, 'total': 229},
                'id': '46ae700d03e4',
                'progress': '[================================================'
                '==>]     229B/229B',
            },
            # 2/3, (229) / (229) = 100
            {
                'status': 'Pull complete',
                'progressDetail': {},
                'id': '46ae700d03e4',
            },
            # 3/3, 0
            {
                'status': 'Digest: sha256:51ad6d2e429f4a250fe7d856d3472e99f67ca'
                '4a15a74fbd21edfbe251b2bfada'
            },
            # (Doesn't yield)
            {
                'status': 'Status: Image is up to date for '
                f'{self.docker_repo}:kinetic-dist-stretch-56.fac3042a'
            },
            # (Doesn't yield)
        ]

    def test_pull(self, obj, mock_docker):
        statuses = list(obj.pull('kinetic-dist-stretch-56.fac3042a'))
        print(statuses)
        assert statuses == [
            (100, 0),
            (50, 0),
            (int(100 / 3), 0),
            (int(100 / 3), 50),
            (int(100 / 3), 50),
            (int(100 / 3), 50),
            (int(100 / 3), 50),
            (int(100 / 3), 80),
            (int(100 / 3), 80),
            (int(100 / 3), 80),
            (int(100 * 2 / 3), 50),
            (int(100 * 2 / 3), 100),
            (100, 0),
        ]
