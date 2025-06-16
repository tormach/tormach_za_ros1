"""API specification for implementations of secret
storage backends.

Every 'public' function which will be used by the
end user of the 'storage' module should be declared
here.
"""

import datetime

from typing import Dict, List, Union


class Service:
    """Class defining the acees point to the storage backend.

    Instantiating and awaiting will create a session to the backend.
    """

    async def __aenter__(self):
        raise NotImplementedError(
            'Function __aenter__ has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def __aexit__(self, exc_type, exc, tb):
        raise NotImplementedError(
            'Function __aexit__ has to be implemented! '
            'It cannot inherit from the interface!'
        )

    def __await__(self):
        raise NotImplementedError(
            'Function __await__ has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def search_items(self, query_parameters: Dict[str, str]) -> List[str]:
        raise NotImplementedError(
            'Function search_items has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def get_collections(self) -> List['Collection']:
        raise NotImplementedError(
            'Function get_collections has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def get_collection_by_alias(self, alias: str) -> 'Collection':
        raise NotImplementedError(
            'Function get_collection_by_alias has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def create_collection(
        self,
        label: str,
        alias: str = None,
    ) -> 'Collection':
        raise NotImplementedError(
            'Function create_collection has to be implemented! '
            'It cannot inherit from the interface!'
        )


class Collection:
    """Class representing a single collection in the storage backend
    and all available methods to modify the collection.
    """

    async def __aenter__(self):
        raise NotImplementedError(
            'Function __aenter__ has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def __aexit__(self, exc_type, exc, tb):
        raise NotImplementedError(
            'Function __aexit__ has to be implemented! '
            'It cannot inherit from the interface!'
        )

    def __await__(self):
        raise NotImplementedError(
            'Function __await__ has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def create_item(
        self,
        label: str,
        secret: Union[str, bytes],
        attributes: Dict[str, str],
        overwrite: bool = True,
    ) -> 'Item':
        raise NotImplementedError(
            'Function create_item has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def search_items(self, query_parameters: Dict[str, str]) -> List[str]:
        raise NotImplementedError(
            'Function search_items has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def get_created(self):
        raise NotImplementedError(
            'Function get_created has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def get_modified(self):
        raise NotImplementedError(
            'Function get_modified has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def get_label(self):
        raise NotImplementedError(
            'Function get_label has to be implemented! '
            'It cannot inherit from the interface!'
        )


class Item:
    """Class representating a single item in the collection
    and all available methods to modify it.
    """

    async def __aenter__(self):
        raise NotImplementedError(
            'Function __aenter__ has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def __aexit__(self, exc_type, exc, tb):
        raise NotImplementedError(
            'Function __aexit__ has to be implemented! '
            'It cannot inherit from the interface!'
        )

    def __await__(self):
        raise NotImplementedError(
            'Function __await__ has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def get_secret(self) -> str:
        raise NotImplementedError(
            'Function get_secret has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def get_modified(self) -> datetime.datetime:
        raise NotImplementedError(
            'Function get_modified has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def get_created(self) -> datetime.datetime:
        raise NotImplementedError(
            'Function get_created has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def set_secret(self, secret: Union[str, bytes]) -> None:
        raise NotImplementedError(
            'Function set_secret has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def get_label(self) -> str:
        raise NotImplementedError(
            'Function get_label has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def get_attributes(self) -> Dict[str, str]:
        raise NotImplementedError(
            'Function get_attributes has to be implemented! '
            'It cannot inherit from the interface!'
        )

    async def delete(self) -> None:
        raise NotImplementedError(
            'Function delete has to be implemented! '
            'It cannot inherit from the interface!'
        )
