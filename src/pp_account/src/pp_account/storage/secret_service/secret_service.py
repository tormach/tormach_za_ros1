#    Minimalistic implementation of the Secret Service API library for the sole
#    purpose of using from the Tormach PathPilot software.
#
#    Not functionally complete with the specification standard published at
#    https://specifications.freedesktop.org/secret-service/latest/

from dbus_next import Variant
from dbus_next.introspection import Node
from dbus_next.aio import MessageBus, ProxyObject
from dbus_next.errors import DBusError
import datetime
import os
import math
import asyncio
import pathlib
from hashlib import sha256
import logging
import hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import pp_account.storage.api
import pp_account.storage.exceptions
from pp_account.storage.common import _Singleton

from typing import Dict, List, Union, Tuple, Optional

logger = logging.getLogger('pp_account.storage.secret_service')


INTERFACE_PATH = (pathlib.Path(__file__).parent / 'interface').resolve()


class Service(pp_account.storage.api.Service, metaclass=_Singleton):
    """
    The Service object which provide base access to the base Secret Service API
    provider.

    Use as a singleton to reuse (keep opened) the Secret Service Session

    The implementation of dh-ietf1024-sha256-aes128-cbc-pkcs7 is taken mostly from
    the secretstorage python module
    """

    DH_PRIME_1024_BYTES = (
        0xFF,
        0xFF,
        0xFF,
        0xFF,
        0xFF,
        0xFF,
        0xFF,
        0xFF,
        0xC9,
        0x0F,
        0xDA,
        0xA2,
        0x21,
        0x68,
        0xC2,
        0x34,
        0xC4,
        0xC6,
        0x62,
        0x8B,
        0x80,
        0xDC,
        0x1C,
        0xD1,
        0x29,
        0x02,
        0x4E,
        0x08,
        0x8A,
        0x67,
        0xCC,
        0x74,
        0x02,
        0x0B,
        0xBE,
        0xA6,
        0x3B,
        0x13,
        0x9B,
        0x22,
        0x51,
        0x4A,
        0x08,
        0x79,
        0x8E,
        0x34,
        0x04,
        0xDD,
        0xEF,
        0x95,
        0x19,
        0xB3,
        0xCD,
        0x3A,
        0x43,
        0x1B,
        0x30,
        0x2B,
        0x0A,
        0x6D,
        0xF2,
        0x5F,
        0x14,
        0x37,
        0x4F,
        0xE1,
        0x35,
        0x6D,
        0x6D,
        0x51,
        0xC2,
        0x45,
        0xE4,
        0x85,
        0xB5,
        0x76,
        0x62,
        0x5E,
        0x7E,
        0xC6,
        0xF4,
        0x4C,
        0x42,
        0xE9,
        0xA6,
        0x37,
        0xED,
        0x6B,
        0x0B,
        0xFF,
        0x5C,
        0xB6,
        0xF4,
        0x06,
        0xB7,
        0xED,
        0xEE,
        0x38,
        0x6B,
        0xFB,
        0x5A,
        0x89,
        0x9F,
        0xA5,
        0xAE,
        0x9F,
        0x24,
        0x11,
        0x7C,
        0x4B,
        0x1F,
        0xE6,
        0x49,
        0x28,
        0x66,
        0x51,
        0xEC,
        0xE6,
        0x53,
        0x81,
        0xFF,
        0xFF,
        0xFF,
        0xFF,
        0xFF,
        0xFF,
        0xFF,
        0xFF,
    )

    DH_PRIME_1024 = int.from_bytes(DH_PRIME_1024_BYTES, 'big')

    with open(INTERFACE_PATH / 'org.freedesktop.Secret.Service.xml') as file:
        SERVICE_INTERFACE = Node.parse(file.read())
    with open(INTERFACE_PATH / 'org.freedesktop.Secret.Session.xml') as file:
        SESSION_INTERFACE = Node.parse(file.read())

    def __init__(self):
        self.__private_key = int.from_bytes(os.urandom(0x80), 'big')
        self._public_key = pow(2, self.__private_key, Service.DH_PRIME_1024)
        self._aes_key = None
        self._bus = None
        self._session_object = None
        self._session = None
        self._service_session_object = None
        self._service_session = None
        self._connected = False

    async def _close(self):
        await self._session.call_close()

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._close())
            else:
                loop.run_until_complete(self._close())
        except Exception:
            pass

    async def connect(self) -> 'Service':
        if not self._connected:
            self._bus = await MessageBus().connect()

            self._service_session_object = self._bus.get_proxy_object(
                'org.freedesktop.secrets',
                '/org/freedesktop/secrets',
                Service.SERVICE_INTERFACE,
            )

            self._service_session = self._service_session_object.get_interface(
                'org.freedesktop.Secret.Service'
            )

            output, result = await self._service_session.call_open_session(
                'dh-ietf1024-sha256-aes128-cbc-pkcs7',
                Variant('ay', self._int_to_bytes(self._public_key)),
            )

            self._session_object = self._bus.get_proxy_object(
                'org.freedesktop.secrets',
                result,
                Service.SESSION_INTERFACE,
            )

            self._session = self._session_object.get_interface(
                'org.freedesktop.Secret.Session'
            )

            self._set_aes_key(int.from_bytes(output.value, 'big'))

            self._connected = True
            logger.info('')

        return self

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __await__(self):
        return self.connect().__await__()

    @property
    def session_object_path(self) -> str:
        return self._session.path

    def get_proxy_object(
        self, bus_name: str, path: str, introspection: Node
    ) -> ProxyObject:
        return self._bus.get_proxy_object(bus_name, path, introspection)

    async def search_items(self, query_parameters: Dict[str, str]) -> List[str]:
        response = await self._service_session.call_search_items(
            query_parameters
        )
        found_items = response[0] + response[1]
        return [Item(i, self) for i in found_items]

    async def get_collections(self) -> List['Collection']:
        response = await self._service_session.get_collections()
        return [Collection(i, self) for i in response]

    async def get_collection_by_alias(self, alias: str) -> 'Collection':
        response = await self._service_session.call_read_alias(alias)
        if response == '/':
            return None
        return Collection(response, self)

    async def create_collection(
        self,
        label: str,
        alias: str = None,
    ) -> 'Collection':
        if alias is None:
            alias = ''
        elif alias != 'default':
            # Really? Did they actually create a functionality and then
            # limited it to just single keyword?
            _error = 'Only alias "default" is supported!'
            logger.error(_error)
            raise pp_account.storage.exceptions.ServiceError(_error)

        properties = {
            "org.freedesktop.Secret.Collection.Label": Variant('s', label),
        }

        try:
            (
                collection_object_path,
                prompt_object_path,
            ) = await self._service_session.call_create_collection(
                properties, alias
            )
        except DBusError as e:
            _error = f'Secret Service experienced a DBus related error during collection creation! ({e})'
            logger.error(_error)
            raise pp_account.storage.exceptions.ServiceError(_error)

        if prompt_object_path and prompt_object_path != '/':
            async with Prompt(prompt_object_path) as prompt:
                variant_response = await prompt.show()
                collection_object_path = variant_response.value

        if collection_object_path and collection_object_path != '/':
            return Collection(collection_object_path, self)

        _error = 'Secret Service experienced error during collection creation!'
        logger.error(_error)
        raise pp_account.storage.exceptions.ServiceError(_error)

    def encode_secret(self, secret: Union[str, bytes]):
        if isinstance(secret, str):
            secret = secret.encode('utf-8')
        # PKCS-7 style padding
        padding = 0x10 - (len(secret) & 0xF)
        secret += bytes((padding,) * padding)
        aes_iv = os.urandom(0x10)
        aes = algorithms.AES(self._aes_key)
        encryptor = Cipher(
            aes, modes.CBC(aes_iv), default_backend()
        ).encryptor()
        encrypted_secret = encryptor.update(secret) + encryptor.finalize()
        return [
            self.session_object_path,
            aes_iv,
            encrypted_secret,
            'text/plain',
        ]

    def decode_secret(self, secret: Tuple) -> str:
        aes = algorithms.AES(self._aes_key)
        aes_iv = bytes(secret[1])
        decryptor = Cipher(
            aes, modes.CBC(aes_iv), default_backend()
        ).decryptor()
        encrypted_secret = secret[2]
        padded_secret = (
            decryptor.update(bytes(encrypted_secret)) + decryptor.finalize()
        )
        assert isinstance(padded_secret, bytes)
        secret = padded_secret[: -padded_secret[-1]]
        return secret.decode('utf-8')

    async def unlock(self, item: Union[str, List[str]]) -> None:
        if isinstance(item, str):
            items = [item]

        unlocked, prompt_object_path = await self._service_session.call_unlock(
            items
        )

        async with Prompt(prompt_object_path) as prompt:
            await prompt.show()

    def _int_to_bytes(self, number: int) -> bytes:
        return number.to_bytes(math.ceil(number.bit_length() / 8), 'big')

    def _set_aes_key(self, provider_public_key: int) -> None:
        common_secret_int = pow(
            provider_public_key,
            self.__private_key,
            Service.DH_PRIME_1024,
        )
        common_secret = self._int_to_bytes(common_secret_int)
        # Prepend NULL bytes if needed
        common_secret = b'\x00' * (0x80 - len(common_secret)) + common_secret
        # HKDF with null salt, empty info and SHA-256 hash
        salt = b'\x00' * 0x20
        pseudo_random_key = hmac.new(salt, common_secret, sha256).digest()
        output_block = hmac.new(pseudo_random_key, b'\x01', sha256).digest()
        # Resulting AES key should be 128-bit
        self._aes_key = output_block[:0x10]


class Collection(pp_account.storage.api.Collection):
    with open(INTERFACE_PATH / 'org.freedesktop.Secret.Collection.xml') as file:
        COLLECTION_INTERFACE = Node.parse(file.read())

    def __init__(
        self,
        collection_object_path: str,
        service_session: Optional[Service] = None,
    ):
        self._collection_object_path = collection_object_path
        self._collection_object = None
        self._collection = None
        self._service_session = service_session
        self._connected = False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __await__(self):
        return self.connect().__await__()

    async def connect(self) -> 'Collection':
        if not self._connected:
            if self._service_session is None:
                self._service_session = await Service()
            self._collection_object = self._service_session.get_proxy_object(
                'org.freedesktop.secrets',
                self._collection_object_path,
                Collection.COLLECTION_INTERFACE,
            )
            self._collection = self._collection_object.get_interface(
                'org.freedesktop.Secret.Collection'
            )

            self._connected = True

        return self

    async def create_item(
        self,
        label: str,
        secret: Union[str, bytes],
        attributes: Dict[str, str],
        overwrite: bool = True,
    ) -> 'Item':
        if await self._collection.get_locked():
            await self._service_session.unlock(self._collection.path)

        properties = {
            "org.freedesktop.Secret.Item.Label": Variant('s', label),
            "org.freedesktop.Secret.Item.Attributes": Variant(
                r'a{ss}', attributes
            ),
        }

        try:
            item_path, prompt_path = await self._collection.call_create_item(
                properties,
                self._service_session.encode_secret(secret),
                overwrite,
            )
        except DBusError:
            logger.error('Secret Service experienced a DBus related error!')
            raise pp_account.storage.exceptions.ServiceError()

        return Item(item_path)

    async def search_items(self, query_parameters: Dict[str, str]) -> List[str]:
        response = await self._collection.call_search_items(query_parameters)
        return [Item(i, self._service_session) for i in response]

    async def get_created(self):
        response = await self._collection.get_created()
        return datetime.datetime.fromtimestamp(response)

    async def get_modified(self):
        response = await self._collection.get_modified()
        return datetime.datetime.fromtimestamp(response)

    async def get_label(self):
        response = await self._collection.get_label()
        return response


class Prompt:
    with open(INTERFACE_PATH / 'org.freedesktop.Secret.Prompt.xml') as file:
        PROMPT_INTERFACE = Node.parse(file.read())

    def __init__(
        self, object_path: str, service_session: Optional[Service] = None
    ):
        self._prompt_object_path = object_path
        self._prompt_object = None
        self._prompt = None
        self._service_session = service_session
        self._connected = False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __await__(self):
        return self.connect().__await__()

    async def connect(self) -> 'Collection':
        if not self._connected:
            if self._service_session is None:
                self._service_session = await Service()
            self._prompt_object = self._service_session.get_proxy_object(
                'org.freedesktop.secrets',
                self._prompt_object_path,
                Prompt.PROMPT_INTERFACE,
            )
            self._prompt = self._prompt_object.get_interface(
                'org.freedesktop.Secret.Prompt'
            )

            self._connected = True

        return self

    async def show(self) -> Variant:
        prompt_solved = asyncio.Event()
        error_occured = True
        prompt_result = None

        await self._prompt.call_prompt('0')

        def callback_signal(error: Exception, result):
            nonlocal error_occured
            nonlocal prompt_result
            error_occured = error
            prompt_result = result
            prompt_solved.set()

        self._prompt.on_completed(callback_signal)

        await prompt_solved.wait()

        if error_occured:
            logger.error(
                'Secret Service Prompt could not be solved, '
                'probably cancelled by user!'
            )
            raise pp_account.storage.exceptions.UserError()

        return prompt_result


class Item(pp_account.storage.api.Item):
    with open(INTERFACE_PATH / 'org.freedesktop.Secret.Item.xml') as file:
        ITEM_INTERFACE = Node.parse(file.read())

    def __init__(
        self, object_path: str, service_session: Optional[Service] = None
    ):
        self._item_object_path = object_path
        self._item_object = None
        self._item = None
        self._service_session = service_session
        self._connected = False

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __await__(self):
        return self.connect().__await__()

    async def connect(self) -> 'Collection':
        if not self._connected:
            if self._service_session is None:
                self._service_session = await Service()
            self._item_object = self._service_session.get_proxy_object(
                'org.freedesktop.secrets',
                self._item_object_path,
                Item.ITEM_INTERFACE,
            )
            self._item = self._item_object.get_interface(
                'org.freedesktop.Secret.Item'
            )

            self._connected = True

        return self

    async def get_secret(self) -> str:
        if await self.get_locked():
            await self._unlock()
        encoded_secret = await self._item.call_get_secret(
            self._service_session.session_object_path
        )
        secret = self._service_session.decode_secret(encoded_secret)
        return secret

    async def get_locked(self) -> bool:
        return await self._item.get_locked()

    async def get_modified(self) -> datetime.datetime:
        try:
            timestamp = await self._item.get_modified()
            modified = datetime.datetime.fromtimestamp(timestamp)
        except Exception:
            modified = datetime.datetime.fromtimestamp(0)
        return modified

    async def get_created(self) -> datetime.datetime:
        try:
            timestamp = await self._item.get_created()
            created = datetime.datetime.fromtimestamp(timestamp)
        except Exception:
            created = datetime.datetime.fromtimestamp(0)
        return created

    async def set_secret(self, secret: Union[str, bytes]) -> None:
        if await self.get_locked():
            await self._unlock()
        await self._item.call_set_secret(
            self._service_session.encode_secret(secret)
        )

    async def get_label(self) -> str:
        return await self._item.get_label()

    async def get_attributes(self) -> Dict[str, str]:
        return await self._item.get_attributes()

    async def get_type(self) -> str:
        return await self._item.get_type()

    async def delete(self) -> None:
        if await self.get_locked():
            await self._unlock()
        await self._item.call_delete()

    async def _unlock(self) -> None:
        await self._service_session.unlock(self._item.path)
