import aiohttp

from typing import NamedTuple

PATHPILOT_HUB_API_ADDRESS = 'hub.pathpilot.com'


class PathPilotHUBAccountIdentification(NamedTuple):
    first_name: str
    last_name: str
    email_address: str
    id_number: int


class NoPathPilotHUBAccount(BaseException):
    pass


class PathPilotHUBError(BaseException):
    pass


async def verify_token(token: str) -> PathPilotHUBAccountIdentification:
    endpoint = f"https://{PATHPILOT_HUB_API_ADDRESS}/api/v1/token"
    headers = {
        'Content-type': 'application/json',
        'X-HubAuthToken': token,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    body = await response.json(content_type=None)
                    first_name = body.get('first_name', '')
                    last_name = body.get('last_name', '')
                    email = body.get('email', '')
                    id_number = body.get('id', None)
                    return PathPilotHUBAccountIdentification(
                        first_name=first_name,
                        last_name=last_name,
                        email_address=email,
                        id_number=str(id_number),
                    )
                raise NoPathPilotHUBAccount()
    except Exception:
        # Probably a better idea would be to differentiate beween errors
        raise NoPathPilotHUBAccount()


async def invalidate_token(token: str) -> None:
    endpoint = f'https://{PATHPILOT_HUB_API_ADDRESS}/api/v1/token'
    headers = {
        'Content-type': 'application/json',
        'X-HubAuthToken': token,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(endpoint, headers=headers) as response:
                if response.status == 400:
                    raise NoPathPilotHUBAccount()
                if response.status != 200:
                    body = await response.json(content_type=None)
                    raise PathPilotHUBError(body)
    except Exception:
        # Probably a better idea would be to differentiate beween errors
        raise PathPilotHUBError()
