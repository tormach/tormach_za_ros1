from PySide6.QtCore import QObject, Signal, Property
from PySide6.QtQml import QmlElement

import pp_account

import qasync

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class AccountProvider(QObject):
    noValidAccount = Signal()
    validAccount = Signal()
    userUncooperative = Signal()
    deletedAllAccount = Signal()
    userAccountExistsChanged = Signal(bool)
    userEmailAddressChanged = Signal(str)
    userForenameChanged = Signal(str)
    userSurnameChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._account: pp_account.login.PathPilotHUBAccount = None

        # These should be queried ad-hoc from the _account
        self._user_forename = None
        self._user_surname = None
        self._user_email_address = None

    async def _update_user_information(self) -> None:
        self._user_forename = (
            (await self._account.first_name()) if self._account else None
        )
        self._user_surname = (
            (await self._account.last_name()) if self._account else None
        )
        self._user_email_address = (
            (await self._account.email_address()) if self._account else None
        )

        self.userForenameChanged.emit(self._user_forename)
        self.userSurnameChanged.emit(self._user_surname)
        self.userEmailAddressChanged.emit(self._user_email_address)

    @qasync.asyncSlot(str)
    async def verifyNewAccount(self, token: str) -> None:
        try:
            account = (
                await pp_account.login.verify_and_store_pathpilot_hub_account(
                    token
                )
            )
        except pp_account.storage.exceptions.UserError:
            self.userUncooperative.emit()
            return
        if not account:
            self.noValidAccount.emit()
            return
        self._account = account
        await self._update_user_information()
        self.userAccountExistsChanged.emit(True)
        self.validAccount.emit()

    @qasync.asyncSlot()
    async def verifyDefaultAccount(self) -> None:
        try:
            default_account = (
                await pp_account.login.PathPilotHUBAccount.default_account()
            )
            status = await default_account.verify()
        except pp_account.login.NoAccountError:
            self.noValidAccount.emit()
            return
        except pp_account.storage.exceptions.UserError:
            self.userUncooperative.emit()
            return

        if status:
            self._account = default_account
            self.userAccountExistsChanged.emit(True)
            await self._update_user_information()
            self.validAccount.emit()
        else:
            self.noValidAccount.emit()

    @qasync.asyncSlot()
    async def logout(self) -> None:
        try:
            await pp_account.login.complete_logout()
        except Exception:
            return

        self._account = None
        self.userAccountExistsChanged.emit(False)
        await self._update_user_information()
        self.deletedAllAccount.emit()

    @Property(bool, notify=userAccountExistsChanged)
    def userAccountExists(self) -> bool:
        return True if self._account is not None else False

    @Property(str, notify=userEmailAddressChanged)
    def userEmailAddress(self) -> str:
        return self._user_email_address if self._user_email_address else ''

    @Property(str, notify=userForenameChanged)
    def userForename(self) -> str:
        return self._user_forename if self._user_forename else ''

    @Property(str, notify=userSurnameChanged)
    def userSurname(self) -> str:
        return self._user_surname if self._user_surname else ''
