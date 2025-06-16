import asyncio

from .api import Item, Service
from typing import Type, Dict, List


async def search_items(
    service: Type[Service], query_parameters: Dict[str, str]
) -> List[Item]:
    """Search the Service backend for items meeting the given dictionary
    of query parameters

    Args:
        service (Type[Service]): Type of backend service class
        query_parameters (Dict[str, str]): Dictionary of parameters to filter
                                           the items in the backend

    Raises:
        RuntimeError: When passed arguments are invalid

    Returns:
        List[Item]: Found item objects
    """

    if query_parameters is None:
        raise RuntimeError('Ivalid usage: query_parameters cannot be None')
    if not service:
        raise RuntimeError('Ivalid usage: service cannot be None')

    if 'tormach_application' not in query_parameters.keys():
        query_parameters.update({'tormach_application': 'pathpilot'})
    async with service() as service_session:
        return await service_session.search_items(query_parameters)


async def delete_items(items_to_delete: List[Item]):
    """Asynchronously delete list of Item objects in the Service backend

    Args:
        items_to_delete (List[Item]): Itenw which will be deleted

    Raises:
        RuntimeError: When passed arguments are invalid
    """

    if not items_to_delete:
        raise RuntimeError('Ivalid usage: items_to_delete cannot be None')

    if not isinstance(items_to_delete, list):
        items_to_delete = [items_to_delete]

    tasks = []

    async def _delete_item(item_to_delete):
        async with item_to_delete as item:
            await item.delete()

    for item in items_to_delete:
        tasks.append(asyncio.create_task(_delete_item(item)))

    await asyncio.gather(*tasks)


async def create_item(
    service: Type[Service],
    label: str,
    secret: str,
    attributes: Dict[str, str],
    overwrite=True,
) -> Item:
    """Create a new item (with Tormach PathPilot specification)
    in the default collection (alias 'default) in the Service
    backend and returns the accessing object

    Args:
        service (Type[Service]): Type of backend service class
        label (str): Label of the item
        secret (str): Secret (password) to store
        attributes (Dict[str, str]): Attributes to store with the item
        overwrite (bool, optional): Owewrite item with the same attributtes.
                                    Defaults to True.

    Raises:
        RuntimeError: When passed arguments are invalid

    Returns:
        Item: Accessor object to the created item
    """

    if not service:
        raise RuntimeError('Ivalid usage: service cannot be None')
    if not label:
        raise RuntimeError('Ivalid usage: label cannot be None')
    if not secret:
        raise RuntimeError('Ivalid usage: secret cannot be None')
    if attributes is None:
        raise RuntimeError('Ivalid usage: attributes cannot be None')

    if 'tormach_application' not in attributes.keys():
        attributes.update({'tormach_application': 'pathpilot'})

    async with service() as service_session:
        default_collection = await service_session.get_collection_by_alias(
            "default"
        )
        if not default_collection:
            default_collection = await service_session.create_collection(
                "Default keyring collection for Tormach PathPilot", "default"
            )
        async with default_collection as _default_collection:
            async with default_collection as _default_collection:
                return await _default_collection.create_item(
                    label, secret, attributes, overwrite
                )
