import asyncio
import pp_account
from .subsystem import (
    SubSystem,
    SubSystemCheck,
)

from typing import Dict


class PathPilotHUBAccountLoginData(SubSystemCheck):
    """Get the PathPilot HUB credentials from the storage backend

    Automatically retrieve stored user login information from the
    pp_account module and prepare them for passing into the Robot
    ROS container.

    Pass nothing if no account is available.
    """

    name = 'pathpilot_hub_account_login_data'
    fatal = False

    async def get_default_account_data(self):
        account = await pp_account.PathPilotHUBAccount.default_account()
        self.email_address = await account.email_address()
        self.token = await account.password()

    def run_check(self):
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.get_default_account_data())
        except (Exception, BaseException):
            # We do not care about the cause of the exception
            self.email_address = None
            self.token = None
        return True

    def docker_run_environment(self) -> Dict:
        environment = dict()
        if self.email_address and self.token:
            environment.update(
                {'PPHUB_EMAIL': self.email_address, 'PPHUB_TOKEN': self.token}
            )

        return environment


class PathPilotHUBAccount(SubSystem):
    """Pass the PathPilot HUB account credentials"""

    name = "pathpilot_hub_account"

    check_classes = [PathPilotHUBAccountLoginData]
