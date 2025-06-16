from typing import NamedTuple


class InvalidRegistryInformationError(BaseException):
    pass


class RegistryInformation(NamedTuple):
    name: str
    domain: str
    prefix: str


PATHPILOT_HUB_REGISTRY = RegistryInformation(
    name='Tormach PathPilot HUB registry',
    domain='docker.pathpilot.com',
    prefix='docker.pathpilot.com',
)

DOCKER_HUB_REGISTRY = RegistryInformation(
    name='Docker HUB registry',
    domain='registry-1.docker.io',
    prefix='',
)

_known_registries = [PATHPILOT_HUB_REGISTRY, DOCKER_HUB_REGISTRY]


def get_registry_information_from_prefix(prefix: str) -> RegistryInformation:
    # Special Docker HUB case
    if prefix == 'docker.io':
        prefix = ''

    for registry in _known_registries:
        if registry.prefix == prefix:
            return registry

    raise InvalidRegistryInformationError()
