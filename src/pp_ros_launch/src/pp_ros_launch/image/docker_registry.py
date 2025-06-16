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

import aiohttp
import asyncio
import base64
import time
import re
import email.utils
import datetime

import pp_account
import logging

from typing import Callable, Union
from typing import NamedTuple

import pp_ros_launch.image.registry_information


logger = logging.getLogger('pp_ros_launch.image.docker_registry')


class DockerRegistryIOError(IOError):
    pass


class DockerRegistryUnauthorizedError(DockerRegistryIOError):
    def __init__(self, data=dict(), message="", *args):
        self.data = data
        self.message = message
        super().__init__(self.message, *args)


class DockerRegistryInvalidRequest(DockerRegistryIOError):
    pass


class WWWAuthorization(NamedTuple):
    bearer_realm: str
    service: str
    scope_type: str
    scope_name: str
    scope_actions: str


class _Singleton(type):
    # Should really be a loop-local storage
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]


class DockerRegistryRequest(metaclass=_Singleton):
    """
    The lowlevel class for sending requests to a remote Docker registry server.

    Holds open the aiohttp.ClientSession during its lifespan to avoid costly creation/deletion at each request
    """

    def __init__(
        self,
        timeout: int = 45,
        limit_connections_per_endpoint: int = 25,
        limit_requests_per_second: int = 50,
    ):
        self._timeout = timeout
        self._connector = limit_connections_per_endpoint
        # Single reusable session across the whole class
        self._session = None

        self.tokens = limit_requests_per_second
        self._max_tokens = limit_requests_per_second
        self.updated_at = time.monotonic()

    async def _close(self):
        await self.session.close()

    @property
    def session(self):
        """
        Ugly hack to quickly solve issue with Exception:
            Timeout context manager should be used inside a task
        which is probably caused by Event Loop or threads mishap
        in Qt applications

        Will require deeper study
        https://github.com/aio-libs/aiobotocore/issues/440
        """
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        connector = aiohttp.TCPConnector(limit_per_host=self._connector)
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=timeout, connector=connector
            )
        return self._session

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._close())
            else:
                loop.run_until_complete(self._close())
        except Exception:
            pass

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self._max_tokens
        if self.tokens + new_tokens >= 1:
            self.tokens = min(self.tokens + new_tokens, self._max_tokens)
            self.updated_at = now

    async def _wait_for_slot(self):
        while self.tokens <= 1:
            self.add_new_tokens()
            await asyncio.sleep(1)
        self.tokens -= 1

    async def request(
        self,
        http_method: str,
        req_address: str,
        req_address_params: dict = dict(),
        headers: dict = dict(),
        retries: int = 10,
        **kwargs,
    ) -> dict:
        await self._wait_for_slot()
        try:
            async with self.session.request(
                http_method,
                req_address,
                params=req_address_params,
                headers=headers,
                **kwargs,
            ) as response:
                # Execution will wait until the response status code is awailable here
                # Error codes from https://datatracker.ietf.org/doc/html/rfc6750#section-3
                if response.status == 400:
                    raise DockerRegistryInvalidRequest()
                elif response.status == (401 or 403):
                    # UNAUTHORIZED or invalid_token ERROR
                    # Request new Bearer token and resend
                    # insufficient_scope ERROR
                    body = await response.json(content_type=None)
                    raise DockerRegistryUnauthorizedError(
                        data=dict(headers=response.headers, body=body)
                    )
                elif response.status == 404:
                    raise DockerRegistryInvalidRequest()
                elif response.status == 429:
                    # Too many requests
                    # Need to wait for specified time period (default to 120 seconds)
                    try:
                        date = response.headers.get('Retry-After')
                        if date.isdigit():
                            delay = int(date)
                        else:
                            now = datetime.datetime.now().astimezone()
                            date = email.utils.parsedate_to_datetime(date)
                            delay = (date - now).total_seconds()
                    except Exception:
                        await asyncio.sleep(120)
                    finally:
                        await asyncio.sleep(delay)
                if response.status == 200:
                    body = await response.json(content_type=None)
                    return dict(
                        code=response.status,
                        headers=response.headers,
                        url=req_address,
                        url_params=req_address_params,
                        method=http_method,
                        response=body,
                    )
                elif retries > 1:
                    await asyncio.sleep(1)
                    return await self.request(
                        http_method,
                        req_address,
                        req_address_params=req_address_params,
                        headers=headers,
                        retries=retries - 1,
                        **kwargs,
                    )
                else:
                    # Out of options, log the error and raise an exception
                    raise DockerRegistryIOError()
        except asyncio.exceptions.TimeoutError:
            raise DockerRegistryIOError()
        except aiohttp.client_exceptions.ClientConnectorError:
            raise DockerRegistryIOError()


class DockerRegistryAuthorization:
    _token_map = dict()
    _function_map = dict()
    _presumed_function_map = dict()

    def __init__(self, registry_domain: str):
        super().__init__()
        self._registry_domain = registry_domain
        self._request_provider = DockerRegistryRequest()

    @property
    def registry_domain(self) -> str:
        return self._registry_domain

    async def request(self, *args, **kwargs):
        return await self._request_provider.request(*args, **kwargs)

    async def _get_authorization_header(
        self, calling_function: Callable
    ) -> dict:
        """
        Return header dictionary with authorization information identifying the user

        Parameters:
        calling_function Callable: Function which sterted the remote communication (requesting function)

        Returns:
        dict:{"Authorization" : "Bearer token"} or {}
        """

        wanted_www_authorization = self._function_map.get(
            calling_function, None
        )

        if wanted_www_authorization is None:
            presumed_www_authorization = self._presumed_function_map.get(
                calling_function, None
            )  # Should never be none
            for key in self._token_map.keys():
                if (
                    key.scope_type == presumed_www_authorization.scope_type
                    and key.scope_name == presumed_www_authorization.scope_name
                    and set(presumed_www_authorization.scope_actions.split(','))
                    <= set(key.scope_actions.split(','))
                ):
                    wanted_www_authorization = key
                    break

            if wanted_www_authorization is None:
                return dict()

        wanted_token_item = self._token_map.get(wanted_www_authorization, None)
        now = time.time()

        if (
            wanted_token_item is None
            or wanted_token_item.get("expire_timestamp", now) - now <= 0
        ):
            return await self._authenticate(
                wanted_www_authorization, calling_function
            )

        return dict(
            Authorization=f'Bearer {wanted_token_item.get("bearer_token", "")}'
        )

    async def _authenticate(
        self,
        www_authorization: Union[str, WWWAuthorization],
        calling_function: Callable,
    ) -> None:
        """
        Authenticate agains the remote server and retrieves the Bearer token to use in requests

        Parameters:
        WWW_authorization (str or WWWAuthorization): 'Bearer realm="https://auth.docker.io/token",service="registry.docker.io",scope="repository:library:pull"'
                                      or 'WWWAuthorization' - Information needed to request the token
        calling_function Callable: Function which sterted the remote communication (requesting function)
        """

        if www_authorization is None:
            raise ValueError("www_authorization cannot be None!")

        if isinstance(www_authorization, str):
            bearer_realm_pattern = re.compile(
                r'Bearer realm=\"(?P<bearer_realm>[a-zA-Z0-9\.\~\-\_\/\:]+)\"'
            )
            service_pattern = re.compile(
                r'service=\"(?P<service>[a-zA-Z0-9\.\~\-\_\/\:]+)\"'
            )
            scope_pattern = re.compile(
                r'scope=\"(?P<type>\w+):(?P<name>[\w\.\-\/]+):(?P<action>(?:(?:pull|push|\*),?))\"'
            )
            # Missing the class resource from https://docs.docker.com/registry/spec/auth/scope/
            # www_authorization_pattern = re.compile(r'Bearer\srealm=\"(?P<bearer_realm>[\w\.\~\:\/]+)\",service=\"(?P<service>[\w\.\~\:\/]+)\"(?:,scope=\"(?P<scope_type>\w+):(?P<scope_name>[\w\.\/]+):(?P<scope_action>(?:(?:pull|push|\*),?)+)\")?')

            bearer_realm_match = bearer_realm_pattern.search(www_authorization)
            service_match = service_pattern.search(www_authorization)
            scope_match = scope_pattern.search(www_authorization)

            bearer_realm = (
                bearer_realm_match.groupdict().get('bearer_realm', None)
                if bearer_realm_match
                else None
            )
            service = (
                service_match.groupdict().get('service', None)
                if service_match
                else None
            )
            scope = scope_match.groupdict() if scope_match else None
            scope_type = scope.get('type', None) if scope else None
            scope_name = scope.get('name', None) if scope else None
            # Scope actions must be in form of string and not in a list of actual actions,
            # because the WWWAuthorization object is used as a key in dictionary and list
            # is NOT hashable
            scope_actions = scope.get('action', None) if scope else None

            if (bearer_realm or service) is None:
                raise DockerRegistryIOError()

            www_authorization = WWWAuthorization(
                bearer_realm, service, scope_type, scope_name, scope_actions
            )

        address_params = {
            "service": www_authorization.service,
            "offline_token": 1,
        }
        if (
            www_authorization.scope_type
            or www_authorization.scope_name
            or www_authorization.scope_actions
        ) is not None:
            address_params.update(
                {
                    "scope": f"{www_authorization.scope_type}:{www_authorization.scope_name}:{www_authorization.scope_actions}"
                }
            )

        headers = await self._get_login_headers()

        try:
            request_time = time.time()
            reply = await self.request(
                "GET", bearer_realm, address_params, headers
            )
        except Exception:
            reply = dict()
            # Do something

        bearer_token = reply.get("response", dict()).get("access_token", "")
        token_expires_in = reply.get("response", dict()).get("expires_in", 60)

        token_item = {
            www_authorization: {
                "bearer_token": bearer_token,
                "expire_timestamp": token_expires_in
                + request_time
                - 10,  # Fudge time
            }
        }

        function_item = {calling_function: www_authorization}

        self._token_map.update(token_item)
        self._function_map.update(function_item)

    async def _get_login_headers(self) -> dict:
        """
        Return header authorization for requesting the Bearer token

        """
        raise NotImplementedError("Subclasses must implement this method!")

    async def authorized_request(
        self,
        http_method: str,
        req_address: str,
        calling_function: Callable,
        req_address_params: dict = dict(),
        headers: dict = dict(),
        retries: int = 10,
    ):
        headers.update(await self._get_authorization_header(calling_function))
        try:
            return await self.request(
                http_method, req_address, req_address_params, headers, retries
            )
        except DockerRegistryUnauthorizedError as e:
            www_autheticate = e.data.get("headers", dict()).get(
                "WWW-Authenticate"
            )

            await self._authenticate(www_autheticate, calling_function)
            # Will raise to a calling function if there is additional problem
            # headers.update(await self._get_authorization_header(calling_function))

            # return await self.request(http_method, req_address, req_address_params, headers, retries)
            return await self.authorized_request(
                http_method,
                req_address,
                calling_function,
                req_address_params,
                headers,
                retries - 1,
            )


class PathPilotRegistryAuthorization(DockerRegistryAuthorization):
    """ """

    async def _get_authorization_header(
        self, calling_function: Callable
    ) -> dict:
        registry_account = (
            await pp_account.ContainerRegistryAccount.default_account(
                self.registry_domain
            )
        )

        return dict(Authorization=f'Bearer {await registry_account.password()}')

    async def _authenticate(
        self, WWW_authorization: str, calling_function: Callable
    ) -> None:
        # Open the Secret Service API and search for 'tormach' collection, Item 'docker.pathpilot.com'
        # and return the secret, respective cache it here

        # Or maybe just raise an exception and thus request an authetication
        pass


class DockerHUBRegistryAuthorization(DockerRegistryAuthorization):
    """ """

    # Around 300 times seems to be a sweet spot for
    token_usage_limit = 300
    hub_extension_api_address = "hub.docker.com"

    def __init__(self, registry_domain: str):
        super().__init__(registry_domain)
        self._token_counter = dict()
        self._extension_token = None
        self._login_base64 = None
        self._account = None

    @property
    def extension_api_address(self) -> str:
        return f"https://{self.hub_extension_api_address}"

    async def _get_authorization_header(
        self, calling_function: Callable
    ) -> dict:
        authorization_header = (
            await DockerRegistryAuthorization._get_authorization_header(
                self, calling_function
            )
        )
        # Fastline for when is the return value of super()._get_authorization_header empty
        if not authorization_header:
            return authorization_header

        wanted_www_authorization = self._function_map.get(calling_function)
        token_usage_count = self._token_counter.get(wanted_www_authorization, 0)

        # Act as if no authorization is available if the token is overused
        if token_usage_count > DockerHUBRegistryAuthorization.token_usage_limit:
            del self._token_counter[wanted_www_authorization]
            return dict()

        self._token_counter[wanted_www_authorization] = token_usage_count + 1

        return authorization_header

    async def _get_extension_authorization_header(self):
        """ """

        http_method = "POST"
        endpoint_address = "v2/users/login"

        if self._extension_token is None:
            authorization_data = await self._get_extension_login_data()
            reply = await self.request(
                http_method,
                f"{self.extension_api_address}/{endpoint_address}",
                data=authorization_data,
            )

            self._extension_token = reply.get('response', dict()).get(
                'token', ''
            )

        return dict(Authorization=f'Bearer {self._extension_token}')

    async def _get_login_information(self) -> tuple:
        """ """

        if self._account is None:
            self._account = (
                await pp_account.ContainerRegistryAccount.default_account(
                    self.registry_domain
                )
            )

        return (await self._account.username(), await self._account.password())

    async def _get_extension_login_data(self) -> dict:
        """ """

        login_information = await self._get_login_information()
        return dict(
            username=login_information[0], password=login_information[1]
        )

    async def _get_login_headers(self) -> dict:
        if self._login_base64 is None:
            login_information = await self._get_login_information()
            self._login_base64 = base64.b64encode(
                f"{login_information[0]}:{login_information[1]}".encode("ascii")
            ).decode('utf-8')

        return dict(Authorization=f"Basic {self._login_base64}")


class DockerRegistry(DockerRegistryAuthorization):
    @property
    def registry_address(self) -> str:
        return f"https://{self.registry_domain}"

    async def get_all_repositories_names(self) -> list:
        """
        Acquire a list of all Docker repositories in a registry

        Returns:
        list[str]: List of all repositories user can see
        """

        http_method = "GET"
        endpoint_address = "v2/_catalog"

        reply = await self.authorized_request(
            http_method,
            f"{self.registry_address}/{endpoint_address}",
            DockerRegistry.get_all_repositories,
        )

        return reply.get('response', dict()).get('repositories', [])

    async def get_all_repositories(self) -> list:
        """ """

        repository_list = await self.get_all_repositories_names()
        repositories = []
        for repository in repository_list:
            repositories.append(
                DockerRepository(repository, self.registry_domain)
            )

        return repositories


class PathPilotDockerRegistry(DockerRegistry, PathPilotRegistryAuthorization):
    """ """

    def __init__(self):
        DockerRegistry.__init__(
            self,
            pp_ros_launch.image.registry_information.PATHPILOT_HUB_REGISTRY.domain,
        )
        PathPilotRegistryAuthorization.__init__(
            self,
            pp_ros_launch.image.registry_information.PATHPILOT_HUB_REGISTRY.domain,
        )

    async def get_all_repositories(self) -> list:
        """ """

        repository_list = await self.get_all_repositories_names()
        repositories = []
        for repository in repository_list:
            repositories.append(PathPilotDockerRepository(repository))

        return repositories


class DockerHUBRegistry(DockerRegistry, DockerHUBRegistryAuthorization):
    """ """

    def __init__(self, namespace='tormach'):
        DockerRegistry.__init__(
            self,
            pp_ros_launch.image.registry_information.DOCKER_HUB_REGISTRY.domain,
        )
        DockerHUBRegistryAuthorization.__init__(
            self,
            pp_ros_launch.image.registry_information.DOCKER_HUB_REGISTRY.domain,
        )
        self._namespace = namespace

    @property
    def namespace(self) -> str:
        return self._namespace

    async def get_all_repositories_names(self) -> list:
        http_method = "GET"
        endpoint_address = f"v2/repositories/{self.namespace}"

        headers = await self._get_extension_authorization_header()
        reply = await self.request(
            http_method,
            f"{self.extension_api_address}/{endpoint_address}",
            headers=headers,
        )

        return [
            f"{self.namespace}/{i['name']}"
            for i in reply.get('response', dict()).get('results', dict())
        ]

    async def get_all_repositories(self) -> list:
        """ """

        repository_list = await self.get_all_repositories_names()
        repositories = []
        for repository in repository_list:
            repositories.append(DockerHUBRepository(repository))

        return repositories


class DockerRepository(DockerRegistryAuthorization):
    def __init__(self, repository: str, registry_domain: str):
        super().__init__(registry_domain)

        self._cache = dict()
        self._repository_name = repository
        # self._registry_domain = registry_domain

        base_pull_www_authorization = WWWAuthorization(
            scope_type="repository",
            scope_name=f"{self.name}",
            scope_actions="pull",
            bearer_realm=None,
            service=None,
        )

        self._presumed_function_map.update(
            {
                DockerRepository.get_tags_list: base_pull_www_authorization,
                DockerRepository.get_manifests_by_reference: base_pull_www_authorization,
                DockerRepository.get_blob_by_digest: base_pull_www_authorization,
            }
        )
        # DockerRepository.get_labels_by_reference: base_pull_www_authorization})

    @property
    def registry_address(self) -> str:
        return f"https://{self._registry_domain}"

    @property
    def name(self) -> str:
        return self._repository_name

    @property
    def full_name(self) -> str:
        return f"{self.registry_address}/{self._repository_name}"

    async def get_tags_list(self):
        http_method = "GET"
        endpoint_address = f"v2/{self.name}/tags/list"

        if self._cache.get(DockerRepository.get_tags_list, None) is None:
            reply = await self.authorized_request(
                http_method,
                f"{self.registry_address}/{endpoint_address}",
                DockerRepository.get_tags_list,
            )

            # Make sure the tags attribute have reasonable value(s) even in situation
            # the remote server returns None as a reply (or omits the key:value pair
            # altogether)
            _response = reply.get('response', None)
            if not _response:
                logger.warning(f'Reply "{reply}" includes no "response" field!')
                _response = dict()
            _tags = _response.get('tags', None)
            if not _tags:
                logger.warning(
                    f'Response in reply "{reply}" includes no "tags" field!'
                )
                _tags = list()

            self._cache[DockerRepository.get_tags_list] = list(_tags)

        return self._cache.get(DockerRepository.get_tags_list, [])

    async def get_manifests_by_reference(self, reference):
        http_method = "GET"
        endpoint_address = f"v2/{self.name}/manifests/{reference}"

        headers = dict(
            Accept="application/vnd.docker.distribution.manifest.v2+json"
        )
        if (
            self._cache.setdefault(
                DockerRepository.get_manifests_by_reference, dict()
            ).get(reference, None)
            is None
        ):
            reply = await self.authorized_request(
                http_method,
                f"{self.registry_address}/{endpoint_address}",
                DockerRepository.get_manifests_by_reference,
                headers=headers,
            )

            docker_content_digets = reply.get('headers', dict()).get(
                'Docker-Content-Digest', ''
            )
            reply.get('response', dict()).update(
                {'docker-content-digest': docker_content_digets}
            )

            self._cache[DockerRepository.get_manifests_by_reference][
                reference
            ] = dict(reply['response'])

        return self._cache[DockerRepository.get_manifests_by_reference][
            reference
        ]

    async def get_blob_by_digest(self, digest):
        http_method = "GET"
        endpoint_address = f"v2/{self.name}/blobs/{digest}"

        if (
            self._cache.setdefault(
                DockerRepository.get_blob_by_digest, dict()
            ).get(digest, None)
            is None
        ):
            reply = await self.authorized_request(
                http_method,
                f"{self.registry_address}/{endpoint_address}",
                DockerRepository.get_blob_by_digest,
            )

            self._cache[DockerRepository.get_blob_by_digest][digest] = dict(
                reply.get('response', dict())
            )

        return self._cache[DockerRepository.get_blob_by_digest][digest]


#    async def get_labels_by_reference(self, reference):
#        image = await self.get_manifests_by_reference(reference)
#
#        config_digest = image.get('config', dict()).get('digest', None)
#        if config_digest is None:
#            return None
#
#        config_blob = await self.get_blob_by_digest(config_digest)
#        import pprint
#        pprint.pprint(config_blob)
#
#        labels = config_blob.get('config', dict()).get('Labels')
#
#        return labels


class PathPilotDockerRepository(
    DockerRepository, PathPilotRegistryAuthorization
):
    """ """

    def __init__(self, repository):
        DockerRepository.__init__(
            self,
            repository,
            pp_ros_launch.image.registry_information.PATHPILOT_HUB_REGISTRY.domain,
        )


class DockerHUBRepository(DockerRepository, DockerHUBRegistryAuthorization):
    """ """

    def __init__(self, repository: str, namespace: str = None):
        if namespace is None:
            ns_repo = repository.split('/', 1)
            if len(ns_repo) != 2:
                raise ValueError(
                    "Repository must contain the namespace when not specified"
                    "otherwise."
                )
            namespace = ns_repo[0]
            repository = ns_repo[1]

        self._namespace = namespace
        DockerRepository.__init__(
            self,
            repository,
            pp_ros_launch.image.registry_information.DOCKER_HUB_REGISTRY.domain,
        )

    @property
    def name(self) -> str:
        return f"{self._namespace}/{self._repository_name}"

    @property
    def full_name(self) -> str:
        return (
            f"{self.registry_address}/{self._namespace}/{self._repository_name}"
        )


def docker_registry_factory(
    registry_information: pp_ros_launch.image.registry_information.RegistryInformation,
) -> DockerRegistry:
    if (
        registry_information.domain
        == pp_ros_launch.image.registry_information.PATHPILOT_HUB_REGISTRY.domain
    ):
        return PathPilotDockerRegistry()
    if (
        registry_information.domain
        == pp_ros_launch.image.registry_information.DOCKER_HUB_REGISTRY.domain
    ):
        return DockerHUBRegistry()
    else:
        registry_pattern = re.compile(
            r'^(?:https:\/\/)?(?P<registry_domain>[\w\.\-\~]+)\/?(?:.){0,}$'
        )

        registry_match = registry_pattern.search(registry_information.domain)
        if registry_match is None:
            raise ValueError(
                f'Invalid registry address {registry_information.domain}!'
            )
        registry_domain = registry_match.group('registry_domain')

        return DockerRegistry(registry_domain)


def docker_repository_factory(
    repository_name: str,
    registry_information: pp_ros_launch.image.registry_information.RegistryInformation,
) -> DockerRepository:
    if (
        registry_information.prefix
        == pp_ros_launch.image.registry_information.PATHPILOT_HUB_REGISTRY.prefix
    ):
        return PathPilotDockerRepository(repository_name)
    elif (
        registry_information.prefix
        == pp_ros_launch.image.registry_information.DOCKER_HUB_REGISTRY.prefix
    ):
        return DockerHUBRepository(repository_name)
    else:
        registry_pattern = re.compile(
            r'^(?P<registry_prefix>[\w\.\-\~\:]+)\/?(?:.){0,}$'
        )

        registry_match = registry_pattern.search(registry_information.prefix)
        if registry_match is None:
            raise ValueError(
                f'Invalid registry address {registry_information.prefix}!'
            )
        registry_prefix = registry_match.group('registry_prefix')

        return DockerRepository(repository_name, registry_prefix)
