import aiohttp
import asyncio
import logging

pertinent_addresses = [
    'https://tormach.com',
    'http://docker.pathpilot.com',
    'https://docker.com',
    'https://hub.pathpilot.com',
]

comp_name = 'internet_checker'
logger = logging.getLogger(comp_name)


async def check_connection(timeout: int = 5) -> bool:
    futures = []
    client_timeout = aiohttp.ClientTimeout(total=timeout)

    async def _check(address: str):
        try:
            async with session.get(address) as response:
                await response.text()
        except Exception as e:
            e.check_connection_address = address
            raise e

    async with aiohttp.ClientSession(timeout=client_timeout) as session:
        for address in pertinent_addresses:
            futures.append(asyncio.ensure_future(_check(address)))
        try:
            awaitable = asyncio.gather(*futures)
            await awaitable
            return True
        except aiohttp.client_exceptions.ClientConnectorError as e:
            awaitable.cancel()
            logger.warning(
                f'Client Connector Error occured when trying the address {e.check_connection_address}'
            )
            return False
        except asyncio.exceptions.TimeoutError as e:
            awaitable.cancel()
            logger.warning(
                f'Timeout Error occured when trying the address {e.check_connection_address}. '
                f'Limiting time set to {timeout} s.'
            )
            return False
        except Exception as e:
            awaitable.cancel()
            logger.warning(
                f'Generic error Error occured when trying the address {e.check_connection_address}'
            )
            return False
