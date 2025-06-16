#
# docker_hub.py
#
# A simple wrapper for the Docker registry API
#
# I looked at other libraries, and ultimately wrote my own only for
# the bits I needed for the simplicity and minimal dependencies.
#
# This was originally written to go inside my overlay repo, where it
# was used in a Docker Hub automated build hook.
# https://github.com/zultron/ros_overlay
#
# API call examples
#   https://gist.github.com/alexanderilyin/8cf68f85b922a7f1757ae3a74640d48a
# Docker registry API
#   https://docs.docker.com/registry/spec/api/
#   https://docs.docker.com/registry/spec/auth/token/

import os
import json
import requests
import time


class DockerRegistryIOError(IOError):
    pass


class DockerRegistryAuth:
    _auth = dict()
    _tokens = dict()

    _index_domain = "index.docker.io"
    _params = dict(
        auth_domain="auth.docker.io", auth_service="registry.docker.io"
    )

    @classmethod
    def update_params(cls, params, **kwargs):
        params.update(cls._params)
        for k, v in kwargs.items():
            params[k] = v

    def __init__(self):
        # Get stuff into __dict__
        self.__dict__.update(self._params)

    def get_config_from_environment(self):
        # This works in the Docker Hub automatic build environment
        DOCKERCFG_str = os.environ['DOCKERCFG']
        DOCKERCFG = json.loads(DOCKERCFG_str)
        for data in DOCKERCFG.values():
            if data['serveraddress'] == self.api_domain:
                return data

        raise RuntimeError("Couldn't find config for %s API" % self.api_domain)

    def get_config_from_file(self):
        # This works after `docker login`
        config_path = os.environ.get(
            'DOCKER_CONFIG', os.path.join(os.environ['HOME'], '.docker')
        )
        config = os.path.join(config_path, 'config.json')
        with open(config) as f:
            DOCKERCFG = json.load(f)
        for name, data in DOCKERCFG['auths'].items():
            if 'auth' in data and name.startswith(
                "https://%s/" % self._index_domain
            ):
                return data['auth']

        raise RuntimeError(
            "Couldn't find config for %s API" % self._index_domain
        )

    @property
    def auth(self):
        if 'service_config' in self._params:
            return self._params['service_config']
        else:
            if 'DOCKERCFG' in os.environ:
                res = self.get_config_from_environment()['auth']
            else:
                res = self.get_config_from_file()
            self._params['service_config'] = res
            return res

    @property
    def auth_basic_headers(self):
        return dict(Authorization="Basic %s" % self.auth)

    def auth_token_headers(self, access='pull'):
        return dict(Authorization="Bearer %s" % self.token(access))

    def scope(self, access='pull'):
        return f'{self.scope_prefix}:{self.name}:{access}'

    def req_method(self, spec):
        # "GET /v2/<name>/tags/list" -> requests.get
        return getattr(requests, spec.split(' ', 1)[0].lower())

    def req_url(self, spec, extra_kwargs=None):
        # "GET /v2/<name>/tags/list" -> "https://domain/v2/{name}/tags/list"
        if extra_kwargs is None:
            extra_kwargs = {}
        fmt = spec.split(' ', 1)[1].replace('<', '{').replace('>', '}')
        kwargs = dict(scope=self.scope(extra_kwargs.get('access', 'pull')))
        kwargs.update(self.__dict__)
        kwargs.update(extra_kwargs)
        return ("https://{api_domain}" + fmt).format(**kwargs)

    def request(
        self, spec, headers=None, return_json=True, access='pull', **req_kwargs
    ):
        if headers is None:
            headers = {}
        req_method = self.req_method(spec)
        req_url = self.req_url(spec, req_kwargs)
        if 'Authorization' not in headers:
            headers.update(self.auth_token_headers(access))
        try:
            rsp = req_method(req_url, headers=headers)
        except requests.ConnectionError as e:
            raise DockerRegistryIOError(*e.args)

        if not rsp.ok:
            print(req_method, req_url, headers)
            print(rsp)
            print(rsp.__dict__)
            print(rsp.request.__dict__)
            raise RuntimeError("Request failed for '%s'" % req_url)
        if return_json:
            rsp_json = rsp.json()
            rsp_json['debug'] = dict(
                headers=headers, method=req_method, url=req_url
            )
            rsp_json['obj'] = rsp
            return rsp_json
        else:
            return rsp

    def get_token(self, access='pull'):
        now = time.time()
        if self._tokens.get(self.scope(access), {}).get('expires', 0) > now:
            # print "Reusing token for scope %s" % self.scope(access)
            return self._tokens[self.scope(access)]['token']

        spec = "GET /token?service=<auth_service>&scope=<scope>&offline_token=1"
        token = self.request(
            spec, headers=self.auth_basic_headers, api_domain=self.auth_domain
        )

        token['expires'] = now + token['expires_in'] - 10  # Fudge time
        self._tokens[self.scope(access)] = token
        return token['token']

    def clear_token(self, access):
        if self.scope(access) in self._tokens:
            del self._tokens[self.scope(access)]

    def token(self, access='pull'):
        return self.get_token(access)


class DockerRepo(DockerRegistryAuth):
    scope_prefix = 'repository'

    _params = dict()
    DockerRegistryAuth.update_params(_params, api_domain="registry-1.docker.io")
    _no_clean_params = {'api_domain', 'auth_service', 'auth_domain'}

    @classmethod
    def clean_cache(cls):
        for k in list(cls._params.keys()):
            if k in cls._no_clean_params:
                continue
            cls._params.pop(k, None)

    def __init__(self, name):
        self.name = name

        super().__init__()

    # Basic requests
    def get_tags_list(self):
        spec = "GET /v2/<name>/tags/list"
        return self.request(spec)['tags']

    def get_manifests_by_reference(self, reference):
        if reference not in self._params.setdefault('manifests', dict()):
            spec = "GET /v2/<name>/manifests/<reference>"
            headers = dict(
                Accept="application/vnd.docker.distribution.manifest.v2+json"
            )
            rsp = self.request(spec, reference=reference, headers=headers)
            rsp['digest'] = rsp['obj'].headers['Docker-Content-Digest']
            self._params['manifests'][reference] = rsp
        return self._params['manifests'][reference]

    def get_blob_by_digest(self, digest):
        if digest not in self._params.setdefault('blog_digest', dict()):
            spec = "GET /v2/<name>/blobs/<digest>"
            blob = self.request(spec, digest=digest)
            self._params['blog_digest'][digest] = blob
        return self._params['blog_digest'][digest]

    def delete_manifests_by_reference(self, reference):
        if not reference.startswith('sha256:'):
            # Look up digest using name
            i = self.get_manifests_by_reference(reference)
            print("Using digest {} for name {}".format(i['digest'], reference))
            reference = i['digest']

        spec = "DELETE /v2/<name>/manifests/<reference>"
        # name = repo; reference = image digest
        return self.request(
            spec, reference=reference, access='delete,pull,push'
        )

    def get_labels(self, reference):
        img = self.get_manifests_by_reference(reference)
        config_digest = img.get('config', dict()).get('digest', None)
        if config_digest is None:
            return None
        config_blob = self.get_blob_by_digest(config_digest)
        labels = config_blob.get('config', dict()).get('Labels')
        return labels
