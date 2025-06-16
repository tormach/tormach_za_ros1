# import aiopathlib
# import aiofile
import pathlib
import logging
import datetime
import yaml
import uuid
import os
import pp_account.storage.api
import pp_account.storage.exceptions
from pp_account.storage.common import _Singleton

from typing import Dict, List, Union

# !!! IMPORTANT NOTICE !!!
# Generally, the use of asynchronous calls when performing I/O
# operations should be preffered (thus the need for aiofile
# and aiopathlib commented out imports), however by trial&error
# it was determined, that even the aiofile (which should be
# using the Linux kernel special support for asynchronous file
# operations) is slower on normal (read local) filesystem than
# the synchronous (blocking) alternative.
# For this reason the calls from Python standard library was
# chosen instead

logger = logging.getLogger('pp_account.storage.plaintext_file')

uuid_yaml_tag = '!UUID'
datetime_yaml_tag = '!Datetime'


def uuid_representer(dumper, data):
    return dumper.represent_scalar(uuid_yaml_tag, data.hex)


def uuid_constructor(loader, node):
    value = loader.construct_scalar(node)
    return uuid.UUID(hex=value)


def datetime_representer(dumper, data):
    return dumper.represent_scalar(
        datetime_yaml_tag, data.astimezone().isoformat()
    )


def datetime_constructor(loader, node):
    value = loader.construct_scalar(node)
    return datetime.datetime.fromisoformat(value)


yaml.add_representer(uuid.UUID, uuid_representer)
yaml.add_constructor(uuid_yaml_tag, uuid_constructor)

yaml.add_representer(datetime.datetime, datetime_representer)
yaml.add_constructor(datetime_yaml_tag, datetime_constructor)


class Service(pp_account.storage.api.Service, metaclass=_Singleton):
    COLLECTIONS_NAMESPACE = 'pathpilot_secrets'

    def __init__(self):
        if 'RUN_DIR' not in os.environ:
            logger.error('Environment variable RUN_DIR is not exported!')
            raise pp_account.storage.exceptions.ServiceError(
                'Environment variable RUN_DIR is not exported!'
            )

        # self._rundir = aiopathlib.AsyncPath(os.environ["RUN_DIR"])
        self._rundir = pathlib.Path(os.environ["RUN_DIR"])
        self._collections_base_path = self._rundir / self.COLLECTIONS_NAMESPACE

    async def prepare(self):
        if not self._rundir.exists():
            logger.warning(
                f'Trying to create the RUN_DIR {self._rundir} directory.'
            )
        self._collections_base_path.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        await self.prepare()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __await__(self):
        return self.prepare().__await__()

    async def search_items(self, query_parameters: Dict[str, str]) -> List[str]:
        _items = []
        for _collection in await self.get_collections():
            _items.extend(await _collection.search_items(query_parameters))
        return _items

    async def get_collections(self) -> List['Collection']:
        collection_files = self._collections_base_path.glob('*.yaml')
        return [
            Collection(collection_file) for collection_file in collection_files
        ]

    async def get_collection_by_alias(self, alias: str) -> 'Collection':
        _collection_file = self._collections_base_path / f'{alias}.yaml'
        if not _collection_file.exists():
            return None
        return Collection(_collection_file)

    async def create_collection(
        self,
        label: str,
        alias: str = None,
    ) -> 'Collection':
        identifier = uuid.uuid4()
        if not alias:
            alias = identifier.hex
        _collection_path = self._collections_base_path / f'{alias}.yaml'
        return await Collection.create_collection(
            _collection_path, label, alias, uuid.uuid4()
        )


class Collection(pp_account.storage.api.Collection):
    def __init__(self, collection_file: Union[str, pathlib.Path]):
        if isinstance(collection_file, str):
            collection_file = pathlib.Path(collection_file)
        if collection_file.suffix not in ['.yaml']:
            logger.error(f'Unknown type of collection file {collection_file}.')
            raise pp_account.storage.exceptions.ServiceError(
                f'Unknown type of collection file {collection_file}.'
            )

        self._collection_file = collection_file
        self._collection_data = None

    async def prepare(self):
        if not self._collection_file.exists():
            logger.error(
                f'Collection file {self._collection_file} does not exist!'
            )
            raise pp_account.storage.exceptions.ServiceError(
                f'Collection file {self._collection_file} does not exist!'
            )

    async def __aenter__(self):
        await self.prepare()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __await__(self):
        return self.prepare().__await__()

    class CollectionObject(yaml.YAMLObject):
        yaml_tag = '!Collection'

        def __init__(
            self,
            label: str,
            created: datetime.datetime,
            modified: datetime.datetime,
            identifier: uuid.UUID,
            items: List['Item.ItemObject'] = [],
        ):
            self.label = label
            self.created = created
            self.modified = modified
            self.items = items
            self.identifier = identifier

        def __repr__(self):
            return (
                f'{self.__class__.__name__}(label={self.label}, '
                f'created={self.created}, '
                f'modified={self.modified}, '
                f'items={self.items}, identifier={str(self.identifier)})'
            )

        @classmethod
        def from_yaml(cls, loader, node):
            mapping = loader.construct_mapping(node)
            return cls(
                label=mapping.get('label'),
                identifier=mapping.get('identifier'),
                created=mapping.get('created'),
                modified=mapping.get('modified'),
                items=mapping.get('items'),
            )

    @classmethod
    async def create_collection(
        cls,
        collection_file: Union[str, pathlib.Path],
        label: str,
        alias: str,
        identifier: uuid.UUID,
    ):
        if isinstance(collection_file, str):
            collection_file = pathlib.Path(collection_file)
        if not isinstance(identifier, uuid.UUID):
            logger.error(
                f'Collection identifier {identifier} is not uuid.UUID!'
            )
            raise pp_account.storage.exceptions.ServiceError(
                f'Collection identifier {identifier} is not uuid.UUID!'
            )
        if collection_file.suffix not in ['.yaml']:
            logger.error(f'Unknown type of collection file {collection_file}.')
            raise pp_account.storage.exceptions.ServiceError(
                f'Unknown type of collection file {collection_file}.'
            )
        if not collection_file.parent.exists():
            collection_file.parent.mkdir(parents=True)
        collection_file.touch()

        _collection_object = cls.CollectionObject(
            label=label,
            created=datetime.datetime.now(datetime.timezone.utc),
            modified=datetime.datetime.now(datetime.timezone.utc),
            items=[],
            identifier=identifier,
        )
        data = yaml.dump(
            _collection_object, allow_unicode=True, encoding='utf-8'
        )
        # async with aiofile.AIOFile(collection_file, 'wb+') as file:
        #    writer = aiofile.Writer(file)
        #    await writer(data)
        #    await file.fsync()

        with open(collection_file, 'wb+') as file:
            file.write(data)

        return cls(collection_file)

    async def _read_collection_file(self) -> CollectionObject:
        # async with aiofile.async_open(self._collection_file) as file:
        #    _data = await file.read()

        with open(self._collection_file, 'r+') as file:
            _data = file.read()

        return yaml.load(_data, Loader=yaml.Loader)

    def _check_collection(self, data) -> bool:
        if not isinstance(data, Collection.CollectionObject):
            return False

        return True

    async def _store_collection_file(self, data: CollectionObject):
        # store_path = aiopathlib.AsyncPath(self._collection_file.parent / (self._collection_file.name + '.temp'))
        data.items = sorted(data.items, key=lambda item: item.modified)
        data.modified = datetime.datetime.now(datetime.timezone.utc)
        yaml_string = yaml.dump(
            data, Dumper=yaml.Dumper, allow_unicode=True, encoding='utf-8'
        )

        # async with aiofile.AIOFile(self._collection_file, 'w+') as file:
        #    writer = aiofile.Writer(file)
        #    await writer(yaml_string)
        #    await file.fsync()

        with open(self._collection_file, 'wb+') as file:
            file.write(yaml_string)

        # store_path.replace(self._collection_file)

    async def create_item(
        self,
        label: str,
        secret: Union[str, bytes],
        attributes: Dict[str, str],
        overwrite: bool = True,
    ) -> 'Item':
        if isinstance(secret, bytes):
            secret = secret.decode('utf-8')

        _collection_object = await self._read_collection_file()
        _item = None

        if overwrite:
            for item in _collection_object.items:
                if item.attributes == attributes:
                    _item = item
                    _item.secret = secret
                    _item.label = label
                    _item.modified = datetime.datetime.now(
                        datetime.timezone.utc
                    )
                    break
        if not _item:
            _item = Item.ItemObject(
                label=label,
                created=datetime.datetime.now(datetime.timezone.utc),
                modified=datetime.datetime.now(datetime.timezone.utc),
                secret=secret,
                identifier=uuid.uuid4(),
                attributes=attributes,
            )
            _collection_object.items.append(_item)

        await self._store_collection_file(_collection_object)

        return Item(_item.identifier, self)

    async def get_items(self) -> List['Item']:
        sorted_items = sorted(
            (await self._read_collection_file()).items,
            key=lambda item: item.modified,
            reverse=True,
        )
        return [Item(i.identifier, self) for i in sorted_items]

    async def search_items(self, query_parameters: Dict[str, str]) -> List[str]:
        _items = await self.get_items()
        _found_items = []
        for item in _items:
            if (
                query_parameters.items()
                <= (await item.get_attributes()).items()
            ):
                _found_items.append(item)
        return _found_items

    async def get_created(self) -> datetime.datetime:
        return (await self._read_collection_file()).created

    async def get_modified(self) -> datetime.datetime:
        return (await self._read_collection_file()).modified

    async def get_label(self) -> str:
        return (await self._read_collection_file()).label


class Item(pp_account.storage.api.Item):
    def __init__(self, identifier: uuid.UUID, collection: Collection):
        if not isinstance(identifier, uuid.UUID):
            logger.error(f'Identifier {identifier} is not uuid.UUID!')
            raise pp_account.storage.exceptions.ServiceError(
                f'Identifier {identifier} is not uuid.UUID!'
            )
        if not isinstance(collection, Collection):
            logger.error(f'Collection {collection} is not valid!')
            raise pp_account.storage.exceptions.ServiceError(
                f'Collection {collection} is not valid!'
            )

        self._identifier = identifier
        self._collection = collection

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __await__(self):
        pass

    class ItemObject(yaml.YAMLObject):
        yaml_tag = '!Item'

        def __init__(
            self,
            label: str,
            created: datetime.datetime,
            modified: datetime.datetime,
            secret: str,
            identifier: uuid.UUID,
            attributes: Dict[str, str] = {},
        ):
            self.label = label
            self.created = created
            self.modified = modified
            self.secret = secret
            self.attributes = attributes
            self.identifier = identifier

        def __repr__(self):
            return (
                f'{self.__class__.__name__}(label={self.label}, '
                f'reated={self.created}, '
                f'modified={self.modified}, '
                f'secret={self.secret}, attributes={self.attributes}, '
                f'identifier={self.identifier})'
            )

        @classmethod
        def from_yaml(cls, loader, node):
            mapping = loader.construct_mapping(node)
            return cls(
                label=mapping.get('label'),
                identifier=mapping.get('identifier'),
                created=mapping.get('created'),
                modified=mapping.get('modified'),
                secret=mapping.get('secret'),
                attributes=mapping.get('attributes'),
            )

    async def _get_current_item_object(self):
        collection_file = await self._collection._read_collection_file()
        return next(
            (
                i
                for i in collection_file.items
                if i.identifier == self._identifier
            ),
            None,
        )

    async def _set_current_item_object(self, item: ItemObject):
        collection_file = await self._collection._read_collection_file()
        items = [
            i for i in collection_file.items if i.identifier != self._identifier
        ]
        item.modified = datetime.datetime.now(datetime.timezone.utc)
        items.append(item)
        collection_file.items = items
        await self._collection._store_collection_file(collection_file)

    async def _pop_current_item_object(self):
        collection_file = await self._collection._read_collection_file()
        items = [
            i for i in collection_file.items if i.identifier != self._identifier
        ]
        collection_file.items = items
        await self._collection._store_collection_file(collection_file)

    async def get_secret(self) -> str:
        return (await self._get_current_item_object()).secret

    async def get_modified(self) -> datetime.datetime:
        return (await self._get_current_item_object()).modified

    async def get_created(self) -> datetime.datetime:
        return (await self._get_current_item_object()).created

    async def set_secret(self, secret: Union[str, bytes]) -> None:
        _item = await self._get_current_item_object()
        _item.secret = secret
        await self._set_current_item_object(_item)

    async def get_label(self) -> str:
        return (await self._get_current_item_object()).label

    async def get_attributes(self) -> Dict[str, str]:
        return (await self._get_current_item_object()).attributes

    async def delete(self) -> None:
        await self._pop_current_item_object()
