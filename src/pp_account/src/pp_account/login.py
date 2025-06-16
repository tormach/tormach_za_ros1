import asyncio
import os
import logging

from .storage import (
    search_items,
    delete_items,
    create_item,
    ServiceError,
)

from typing import Dict, List
from .hub import token as hub_token_access


class PathPilotAccountError(BaseException):
    pass


class NoAccountError(PathPilotAccountError):
    pass


class AccountInvalidError(PathPilotAccountError):
    pass


logger = logging.getLogger('pp_account.login')

if (os.environ.get('PATHPILOT_USE_SECRET_SERVICE', '0')).lower() in [
    'true',
    'on',
    '1',
]:
    import pp_account.storage.secret_service as secret_provider

    logger.warning(
        'Using Freedesktop.org Secret Service as PP Account '
        'Storage backend for accessing user data'
    )
else:
    import pp_account.storage.plaintext_file as secret_provider

    logger.warning(
        'Using unencrypted Plaintext file as PP Account '
        'Storage backend for accessing user data'
    )


class Account:
    @classmethod
    async def default_account(
        cls, query_parameters: Dict[str, str]
    ) -> 'Account':
        list_of_items = await search_items(
            secret_provider.Service, query_parameters
        )
        lenght = len(list_of_items)
        if lenght == 1:
            return cls(list_of_items[0])

        elif lenght > 1:
            newest_item = list_of_items[0]
            newest_item_modified = await list_of_items[0].get_modified()

            for i in list_of_items[:1]:
                modified = await i.get_modified()
                if modified > newest_item_modified:
                    newest_item = i
                    newest_item_modified = modified

            return cls(item=newest_item)

        raise NoAccountError()

    def __init__(self, item: secret_provider.Item):
        self._item = item

    async def username(self) -> str:
        async with self._item as i:
            username = (await i.get_attributes()).get('username', None)
        if username is None:
            raise AccountInvalidError()
        return username

    async def password(self) -> str:
        async with self._item as i:
            return await i.get_secret()


class PathPilotHUBAccount(Account):
    @classmethod
    async def create_account(
        cls,
        username: str,
        token: str,
        first_name: str,
        last_name: str,
        email_address: str,
        id_number: int,
    ) -> 'PathPilotHUBAccount':
        attributes = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'email_address': email_address,
            'id_number': id_number,
            'pathpilot_hub': 'robot',
            'tormach_container_registry': 'docker.pathpilot.com',
        }
        item = await create_item(
            secret_provider.Service,
            'Tormach PathPilot HUB Account',
            token,
            attributes,
        )
        return cls(item=item)

    @classmethod
    async def default_account(cls) -> 'PathPilotHUBAccount':
        return await super().default_account(
            {
                'pathpilot_hub': 'robot',
                'tormach_container_registry': 'docker.pathpilot.com',
            }
        )

    @classmethod
    async def all_accounts(cls) -> List['PathPilotHUBAccount']:
        items = await search_items(
            secret_provider.Service,
            {
                'pathpilot_hub': 'robot',
                'tormach_container_registry': 'docker.pathpilot.com',
            },
        )

        return [cls(item=item) for item in items]

    async def first_name(self) -> str:
        async with self._item as i:
            first_name = (await i.get_attributes()).get('first_name', None)
        if first_name is None:
            raise AccountInvalidError()
        return first_name

    async def last_name(self) -> str:
        async with self._item as i:
            last_name = (await i.get_attributes()).get('last_name', None)
        if last_name is None:
            raise AccountInvalidError()
        return last_name

    async def full_name(self) -> str:
        return f"{await self.first_name()} {await self.last_name()}"

    async def email_address(self) -> str:
        async with self._item as i:
            email_address = (await i.get_attributes()).get(
                'email_address', None
            )
        if email_address is None:
            raise AccountInvalidError()
        return email_address

    async def verify(self) -> bool:
        try:
            response = await hub_token_access.verify_token(
                await self.password()
            )
            if isinstance(
                response, hub_token_access.PathPilotHUBAccountIdentification
            ):
                return True
            else:
                return False
        except hub_token_access.NoPathPilotHUBAccount:
            return False

    async def delete(self) -> None:
        logger.error(
            f'Trying to invalidate account {await self.email_address()}'
        )
        try:
            await hub_token_access.invalidate_token(await self.password())
        except (
            hub_token_access.NoAccountError,
            hub_token_access.PathPilotHUBError,
        ) as e:
            # Do not fail if the token is not valid or there is a PathPilot HUB
            # network or availability issue
            logger.debug(f'Exception {e.__class__.__qualname__} body: {e}')
        await delete_items(self._item)


class ContainerRegistryAccount(Account):
    @classmethod
    async def default_account(
        cls, registry_address: str
    ) -> 'ContainerRegistryAccount':
        return await super().default_account(
            {'tormach_container_registry': registry_address}
        )

    @classmethod
    async def create_account(
        cls, username: str, token: str, registry_address: str
    ) -> 'ContainerRegistryAccount':
        attributes = {
            'username': username,
            'tormach_container_registry': registry_address,
        }
        item = await secret_provider.create_item(
            f'Tormach Container registry "{registry_address}"' ' Account',
            token,
            attributes,
        )
        return cls(item)


async def verify_and_store_pathpilot_hub_account(
    token: str,
) -> PathPilotHUBAccount:
    """Check the validity of given user token against Tormach's
    PathPilot remote server, download user information and create
    new Account item in the account backend

    Args:
        token (str): Secret user token used for identification

    Returns:
        PathPilotHUBAccount: Account object
    """
    try:
        account_information = await hub_token_access.verify_token(token)
        account = await PathPilotHUBAccount.create_account(
            account_information.email_address,
            token,
            account_information.first_name,
            account_information.last_name,
            account_information.email_address,
            account_information.id_number,
        )
        return account
    except hub_token_access.NoPathPilotHUBAccount:
        return None
    except ServiceError:
        return None


async def complete_logout() -> None:
    """Remove all stored PathPilot HUB accounts from the storag
    backend
    """

    accounts = await PathPilotHUBAccount.all_accounts()
    if accounts:
        await asyncio.gather(
            *[asyncio.create_task(account.delete()) for account in accounts]
        )
