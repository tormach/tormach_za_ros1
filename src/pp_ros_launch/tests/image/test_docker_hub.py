from pp_ros_launch.image.docker_hub import (
    DockerRegistryAuth,
    DockerRepo,
    DockerRegistryIOError,
    requests,
)
import pytest
import base64
import json
from pprint import pprint

if hasattr(base64, 'encodebytes'):
    encodebytes = base64.encodebytes
    decodebytes = base64.decodebytes
else:
    encodebytes = base64.encodestring
    decodebytes = base64.decodestring


class TestDockerRegistryAuth:
    tc = DockerRegistryAuth

    env = dict(HOME='/home/pathpilot')
    credentials = b"docker_hub_id:docker_hub_passwd"
    credentials_b64 = encodebytes(credentials).decode('utf-8').rstrip()
    docker_config_file = env['HOME'] + '/.docker/config.json'
    docker_config = {
        "auths": {"https://index.docker.io/v1/": {"auth": credentials_b64}},
        "HttpHeaders": {"User-Agent": "Docker-Client/18.09.1 (linux)"},
    }

    file_data = {docker_config_file: json.dumps(docker_config)}

    @pytest.fixture
    def obj(self, mock_open, mock_env):
        return self.tc()

    def test_get_config_from_file(self, obj):
        c_b64 = obj.get_config_from_file().encode('utf-8')
        c = decodebytes(c_b64)
        print(c_b64, '->', c)
        assert c == self.credentials

    def test_auth(self, obj):
        assert obj.auth == self.credentials_b64

    def test_auth_basic_headers(self, obj):
        assert 'Authorization' in obj.auth_basic_headers
        auth = obj.auth_basic_headers['Authorization']
        assert self.credentials_b64 in auth
        assert 'Basic' in auth

    def test_req_method(self, obj, mock_requests):
        m = obj.req_method("GET /thingy?some_attr=1&other_attr=2")
        assert m is self.req.get


class TestDockerRepo(TestDockerRegistryAuth):
    tc = DockerRepo

    @pytest.fixture
    def obj(self, mock_open, mock_container_env, mock_requests):
        self.tc.clean_cache()
        return self.tc(self.docker_repo)

    def test_scope(self, obj):
        assert obj.scope() == 'repository:%s:pull' % self.docker_repo
        assert obj.scope('push') == 'repository:%s:push' % self.docker_repo

    def test_request(self, obj):
        obj.some_attr = 'foo'
        spec = "GET /thingy?some_attr=<some_attr>&other_attr=2"
        headers = dict(Authorization='my_token')
        rsp = obj.request(spec, headers)
        pprint(rsp)
        debug = rsp['debug']
        assert debug['headers']['Authorization'] == 'my_token'
        assert debug['method'] == self.req.get
        assert debug['url'] == (
            'https://registry-1.docker.io/thingy?some_attr=foo&other_attr=2'
        )
        assert rsp['expires_in'] == 50
        assert rsp['obj'] is self.last_req

    def test_request_fail(self, obj):
        self.exception = requests.ConnectionError
        with pytest.raises(DockerRegistryIOError):
            obj.request('GET /thingy', dict(Authorization='my_token'))

    def test_token(self, obj):
        t = obj.token('push')
        pprint(t)
        pprint(self.last_req)
        assert t is self.req.token

    def test_auth_token_headers(self, obj):
        default_tok = obj.auth_token_headers()
        assert 'Authorization' in default_tok
        assert default_tok['Authorization'] == "Bearer " + str(self.req.token)

    def test_get_tags_list(self, obj):
        tags_in = [0]
        self.rsp = dict(tags=tags_in)
        tags_out = obj.get_tags_list()
        assert (
            'https://registry-1.docker.io/v2/%s/tags/list' % self.docker_repo
            in self.reqs
        )
        assert tags_out == tags_in

    def test_get_manifests_by_reference(self, obj):
        m = obj.get_manifests_by_reference('tag_name')
        print(m)

        assert (
            'https://registry-1.docker.io/v2/%s/manifests/tag_name'
            % self.docker_repo
            in self.reqs
        )
        assert 'obj' in m
        assert m['obj'] is self.last_req

    def test_get_blob_by_digest(self, obj):
        b = obj.get_blob_by_digest('deadbeef')
        print(b)

        assert (
            'https://registry-1.docker.io/v2/%s/blobs/deadbeef'
            % self.docker_repo
            in self.reqs
        )
        assert 'obj' in b
        assert b['obj'] is self.last_req

    def test_delete_manifests_by_reference(self, obj):
        # Delete doesn't work on Docker Hub
        pass

    def test_get_labels(self, obj):
        # Mock get_manifests_by_reference object
        self.rsp = dict(config=dict(digest='deadbeef', Labels='my_labels'))
        lbls = obj.get_labels('tag_name')
        assert lbls == 'my_labels'
