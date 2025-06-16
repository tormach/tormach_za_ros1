import logging
import collections
import os
import shutil
from typing import List

import sys
import json
import datetime
import pytz
import urllib3

from . import openapi_client

from .openapi_client.rest import ApiException


# Used to describe a file or a directory in a hub account
CloudItem = collections.namedtuple(
    'CloudItem', ['fullpath', 'itemtype', 'group_type', 'group_id']
)

# Used to describe a file or a directory in a hub account and its local HD path
CombinedTransferItem = collections.namedtuple(
    'CombinedTransferItem',
    ['diskpath', 'cloudpath', 'itemtype', 'token', 'maxbytes'],
)
TransferItem = collections.namedtuple(
    'TransferItem', ['diskpath', 'cloud_item', 'maxbytes']
)


class AsyncResultWrapper:
    def __init__(self, asyncresult, callback):
        self.asyncresult = asyncresult
        self.callback = callback

    def get(self):
        return self.callback(self.asyncresult)

    def ready(self):
        return self.asyncresult.ready()

    def successful(self):
        return self.asyncresult.succesful()

    def wait(self, timeout=None):
        self.asyncresult.wait(timeout)


class APIError(Exception):
    """Base class for API exceptions in this module."""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class TokenError(APIError):
    def __init__(self, message):
        super().__init__(message)


class Connector:
    def __init__(self, server, redis, email=None, token=None):
        """Create a Connector object for the specified pp_hub server

        The redis store is used to save login tokens for anyone
        who has logged in on this machine

        Args:
            server (String): Server root URL
            redis (redis.Redis): Redis-py instance to store login tokens in
        """
        self.server = server
        self.redis = redis
        self.logger = logging.getLogger("pathpilot.pp_hub.connector")

        # Persist auth token token (typically a virtual pathpilot run)
        if email and token:
            self.redis.hset('pp_hub_settings', "email", email)
            self.redis.hset('pp_hub_settings', "token", token)
        elif self.redis.hexists('pp_hub_settings', "email"):
            # Look in redis to see if there is a long lived access token from previous runs
            email = self.redis.hget('pp_hub_settings', "email")
            token = self.redis.hget('pp_hub_settings', "token")
        else:
            # Upgrade an "old style" access token from the pp_hub_tokens hashmap if one exists, and
            # then delete it
            tokenlist = self.redis.hgetall("pp_hub_tokens")
            token = ''
            if len(tokenlist) > 0:
                email, token = tokenlist.popitem()
                self.logger.info(
                    "Found a PPHub login token in pp_hub_tokens: {}. Converting it to the new storage key.".format(
                        email
                    )
                )
                # This key was only used in pre-v2.8.0 PathPilot
                self.redis.delete("pp_hub_tokens")
                # Store these in the "new" keys
                self.redis.hset('pp_hub_settings', "email", email)
                self.redis.hset('pp_hub_settings', "token", token)

        # Configure API key authorization: HubTokenAuth
        self.configuration = openapi_client.Configuration(
            host=f"{self.server}/api/v1",
            api_key={
                'X-HubAuthToken': token,
            },
        )
        self.configuration.connection_pool_maxsize = 1
        self.api_client = openapi_client.ApiClient(self.configuration)

    def _clean_out_expired_authtoken(self):
        self.redis.hdel('pp_hub_settings', "email")
        self.redis.hdel('pp_hub_settings', "token")

        self.configuration = openapi_client.Configuration(
            host=f"{self.server}/api/v1",
            api_key={
                'X-HubAuthToken': None,
            },
        )
        self.configuration.connection_pool_maxsize = 1

        if self.api_client:
            self.api_client.close()

        self.api_client = openapi_client.ApiClient(self.configuration)

    @staticmethod
    def cloudutc_to_local_datetime(cloud_utc):
        import tzlocal

        # Boy did the following take way too long to figure out how to do in python...
        utcdatetime = datetime.datetime.strptime(
            cloud_utc, '%Y-%m-%d %H:%M:%S.%f'
        )
        utcdatetime = utcdatetime.replace(tzinfo=pytz.utc)
        tz = tzlocal.get_localzone()
        return utcdatetime.astimezone(tz)

    @staticmethod
    def local_filetime_to_cloudutc(epochsecs):
        utcstr = datetime.datetime.utcfromtimestamp(epochsecs).strftime(
            '%Y-%m-%d %H:%M:%S.%f'
        )
        return utcstr

    def timestamp_for_datetime(self, dt):
        # arg. python 2.7 does not have a POSIX timestamp() method on datetime objects.
        # supposedly it uses the same math...
        #   (dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()
        epoch_utcdatetime = datetime.datetime.strptime(
            '1970-01-01 00:00:00.0', '%Y-%m-%d %H:%M:%S.%f'
        )
        epoch_utcdatetime = epoch_utcdatetime.replace(tzinfo=pytz.utc)
        return (dt - epoch_utcdatetime).total_seconds()

    def login(self, email, password):
        """Log into the PP Hub service and store the login token in Redis

        Args:
            email (String): User's email address
            password (String): User's password

        Returns:
            String: Login token for the user if successful

        Raises:
            APIError: Raised if the server cannot log the user in. Contains the
            error message from the server
        """

        # Create an instance of the API class
        api_instance = openapi_client.DefaultApi(self.api_client)

        # Get a token
        asyncresult = api_instance.get_token(
            email=email, password=password, async_req=True
        )

        # Define the callback when the async is complete
        def callback(asyncresult):
            try:
                tokenobj = asyncresult.get()

                # persist auth token
                self.redis.hset('pp_hub_settings', "email", email)
                self.redis.hset('pp_hub_settings', "token", tokenobj.token)

                # Add the new token to any further request headers automatically
                # and get a new api_client object which uses it
                self.configuration = openapi_client.Configuration(
                    host=f"{self.server}/api/v1",
                    api_key={
                        'X-HubAuthToken': tokenobj.token,
                    },
                )
                self.configuration.connection_pool_maxsize = 1
                self.api_client = openapi_client.ApiClient(self.configuration)

                return tokenobj.token
            except ApiException:
                raise APIError('Error signing in to PathPilot HUB')
                '''
                e.status
                e.reason
                e.body
                try:
                    resp = r.json()
                    if 'error' in resp and resp['error'] is not None:
                        self.logger.warning("Error logging in to PP HUB status: {} {}".format(r.status_code, resp['error']))
                        raise APIError(resp['error'].get('human_readable', 'Unknown error'))

                except ValueError:
                    pass  # Could not even decode json, something really died on server

                self.logger.error("Error logging in to PP HUB POST status: {}  response body: {}".format(r.status_code, r.text))
                raise APIError('Sorry, the HUB server had an error - try again later.')
                '''
            except urllib3.exceptions.HTTPError:
                raise APIError('HUB server unavailable; try again later.')

        return AsyncResultWrapper(asyncresult, callback)

    def logout(self):
        # Create an instance of the API class
        api_instance = openapi_client.DefaultApi(self.api_client)

        # Delete the token no matter what, even if it didn't exist on the server
        self.redis.hdel('pp_hub_settings', "email")
        self.redis.hdel('pp_hub_settings', "token")

        # Revoke the current token (its in the Configuration)
        asyncresult = api_instance.revoke_token(async_req=True)

        # Define the callback when the async is complete
        def callback(asyncresult):
            try:
                asyncresult.get()
            except ApiException:
                raise APIError('Error signing out of PathPilot HUB')
            except urllib3.exceptions.HTTPError:
                raise APIError('HUB server unavailable; try again later.')

        return AsyncResultWrapper(asyncresult, callback)

    def get_cloud_files(
        self, path='gcode', stat=False, group_type=None, group_id=None
    ):
        """Get a list of files stored on PP HUB inside of "path"

        Args:
            path: String of path to file or folder
            stat: Boolean - lets caller specify a path and test for its existence, determine its
                  type (file or directory), size, and mtime and atimes.  If the path is a file,
                  without stat, the server interprets a GET as a download the full file request.
            group_type (str, optional): If specfied, get files from this group's storage
            group_id (int, optional): If specfied, get files from this group's storage

        Returns:
            Dict: Tree structure of the files stored for this user on the server

        Raises:
            APIError: Raised if the server cannot process the request at all. Will not be raised as long as some of the login tokens sent to the server were valid.
            TokenError: Description
        """
        # Create an instance of the API class
        api_instance = openapi_client.DefaultApi(self.api_client)

        email = self.redis.hget('pp_hub_settings', "email")
        token = self.redis.hget('pp_hub_settings', "token")

        if email and token:
            try:
                # the openapi get_files is used for both file download and directory listings.
                # it always writes the resulting data body to a temp file.
                path = path.lstrip(
                    '/'
                )  # just in case caller formed absolute path
                if group_id and group_type:
                    tmpfilepath = api_instance.get_files(
                        path,
                        stat=stat,
                        group_type=group_type,
                        group_id=group_id,
                    )
                else:
                    tmpfilepath = api_instance.get_files(path, stat=stat)
                with open(tmpfilepath) as datafile:
                    listingdict = json.load(datafile)
                os.remove(tmpfilepath)
                return listingdict

            except ApiException as e:
                if e.status == 401:
                    # Token must have expired so remove the cache to force sign-in look
                    self._clean_out_expired_authtoken()
                    raise TokenError("HUB session timeout; sign in required.")
                elif e.status == 404:
                    # Just means the file or dir no longer exists (or never did)
                    return {}
                else:
                    raise APIError(
                        "Could not decode a json response from the server {:d}".format(
                            e.status
                        )
                    )
            except urllib3.exceptions.HTTPError:
                raise APIError('HUB server unavailable; try again later.')

        else:
            # Nobody logged in
            self._clean_out_expired_authtoken()
            raise TokenError("HUB session timeout; sign in required.")

    @staticmethod
    def _combine_tx_item(item, token=None):
        return CombinedTransferItem(
            diskpath=item.diskpath,
            cloudpath=item.cloud_item.fullpath,
            itemtype=item.cloud_item.itemtype,
            token=token,
            maxbytes=item.maxbytes,
        )

    def download_cloud_items(self, transferitem_list: List[TransferItem]):
        """Download the files and directories in the transferitem_list

        Args:
            transferitem_list (List[TransferItem]): list of TransferItem data objects describing files or directories to download

        Raises:
            APIError: Thrown if file does not exist or token is invalid

        """
        # Create an instance of the API class
        api_instance = openapi_client.DefaultApi(self.api_client)

        for txitem in transferitem_list:
            txitem = self._combine_tx_item(txitem)
            if txitem.itemtype == 'f':
                # the openapi get_files is used for both file download and directory listings and stat calls
                # it always writes the resulting data body to a temp file.

                # The standard Range http header can be used to read just a small preview amount if desired
                if txitem.maxbytes is None:
                    # This means give me the whole file since there isn't an easy way to just delete the
                    # Range header from the api_client object.
                    self.api_client.set_default_header('Range', 'bytes=0-')
                else:
                    self.api_client.set_default_header(
                        'Range', f'bytes=0-{txitem.maxbytes - 1:d}'
                    )

                # xxxx adjust token in config header if needed
                try:
                    try:
                        strippedcloudpath = txitem.cloudpath.lstrip(
                            '/'
                        )  # just in case caller formed absolute path
                        tmpfilepath = api_instance.get_files(strippedcloudpath)
                        try:
                            os.rename(tmpfilepath, txitem.diskpath)
                        except OSError:  # e.g. when path not on same partition
                            shutil.copy(tmpfilepath, txitem.diskpath)
                            os.remove(tmpfilepath)
                    except ApiException as e:
                        t, v, tb = sys.exc_info()
                        if e.status == 416:
                            # The flash server returns this if its a zero byte file vs. just saying success.
                            # Some side effect of us using the Range header above, but this is an easier workaround
                            # then trying to alter flash request header parsing logic.
                            # Create a zero byte file at txitem.diskpath just as if the 'download' of the 0 byte file
                            # was successful.
                            with open(txitem.diskpath, 'w'):
                                pass
                        else:
                            raise t(v).with_traceback(tb)

                    # Do a stat call on the file so we know the mtime utc
                    tmpfilepath = api_instance.get_files(
                        strippedcloudpath, stat=True
                    )
                    with open(tmpfilepath) as datafile:
                        listingdict = json.load(datafile)
                    os.remove(tmpfilepath)

                    cloud_utc = listingdict['contents'][0]['mtime_utc']
                    dtlocal = self.cloudutc_to_local_datetime(cloud_utc)
                    mtime_secs = self.timestamp_for_datetime(dtlocal)

                    # Adjust mtime and atime for the file
                    os.utime(txitem.diskpath, (mtime_secs, mtime_secs))

                except ApiException as e:
                    if e.status == 401:
                        # Token must have expired so remove the cache to force sign-in look
                        self._clean_out_expired_authtoken()
                        raise TokenError(
                            "HUB session timeout; sign in required."
                        )
                    else:
                        raise APIError(e.reason)
                except urllib3.exceptions.HTTPError:
                    raise APIError('HUB server unavailable; try again later.')

            elif txitem.itemtype == 'd':
                if not os.path.exists(txitem.diskpath):
                    os.makedirs(txitem.diskpath)

        return True

    def upload_cloud_items(self, transferitem_list, recurse_dir):
        """Upload a list of TransferItems

        Args:
            transferitem_list (List[TransferItem]): Description
            recurse_dir (bool): If True and an item in the list is a directory, recurse into it and upload items inside of it

        Returns:
            None

        Raises:
            APIError: Description
            TokenError: Description
        """
        # Create an instance of the API class
        api_instance = openapi_client.DefaultApi(self.api_client)

        try:
            for txitem in transferitem_list:
                txitem = self._combine_tx_item(txitem)
                secs = os.path.getmtime(txitem.diskpath)
                mtime_utc = self.local_filetime_to_cloudutc(secs)
                secs = os.path.getatime(txitem.diskpath)
                atime_utc = self.local_filetime_to_cloudutc(secs)

                strippedcloudpath = txitem.cloudpath.lstrip('/')
                if txitem.itemtype == 'f':
                    self.logger.warning(
                        'upload_cloud_file: file={} cloud_path={:s}'.format(
                            txitem.diskpath, strippedcloudpath
                        )
                    )

                    # any overwrite issues were already taken care of by the UI thread before we got here
                    # so just pass true all the time for that arg.
                    api_instance.put_files(
                        strippedcloudpath,
                        filedata=txitem.diskpath,
                        overwrite='true',
                        mtime_utc=mtime_utc,
                        atime_utc=atime_utc,
                    )

                elif txitem.itemtype == 'd':
                    # create new directory first
                    api_instance.put_files(
                        strippedcloudpath,
                        dir=True,
                        mtime_utc=mtime_utc,
                        atime_utc=atime_utc,
                    )

                    if recurse_dir:
                        # now recursively iterate into the dir and compose
                        # a new transferitem_list of children
                        child_txitem_list = []
                        childlist = os.listdir(txitem.diskpath)
                        for childname in childlist:
                            child_diskpath = os.path.join(
                                txitem.diskpath, childname
                            )
                            child_cloudpath = os.path.join(
                                txitem.cloud_item.fullpath, childname
                            )
                            if os.path.isfile(child_diskpath):
                                itemtype = 'f'
                            elif os.path.isdir(child_diskpath):
                                itemtype = 'd'
                            child_txitem_list.append(
                                TransferItem(
                                    diskpath=child_diskpath,
                                    cloud_item=CloudItem(
                                        fullpath=child_cloudpath,
                                        itemtype=itemtype,
                                        group_type=txitem.cloud_item.group_type,
                                        group_id=txitem.cloud_item.group_id,
                                    ),
                                    max_bytes=None,
                                )
                            )

                        self.upload_cloud_items(child_txitem_list, recurse_dir)

            return True

        except ApiException as e:
            if e.status == 401:
                # Token must have expired so remove the cache to force sign-in look
                self._clean_out_expired_authtoken()
                raise TokenError("HUB session timeout; sign in required.")
            elif e.status == 403:
                # Account storage is full most likely.
                raise APIError("Account free space exhausted.")
            else:
                raise APIError(e.reason)
        except urllib3.exceptions.HTTPError:
            raise APIError('HUB server unavailable; try again later.')

    def rename_cloud_item(self, token, path, new_name):
        # Create an instance of the API class
        api_instance = openapi_client.DefaultApi(self.api_client)

        # Rename file
        try:
            api_instance.rename(path, newname=new_name)
            return True
        except ApiException as e:
            if e.status == 401:
                # Token must have expired so remove the cache to force sign-in look
                self._clean_out_expired_authtoken()
                raise TokenError("HUB session timeout; sign in required.")
            else:
                raise APIError(e.reason)
        except urllib3.exceptions.HTTPError:
            raise APIError('HUB server unavailable; try again later.')

    def new_cloud_folder(self, token, basepath, foldername):
        # Create an instance of the API class
        api_instance = openapi_client.DefaultApi(self.api_client)

        # Create directory
        try:
            fullpath = os.path.join(basepath, foldername).lstrip('/')
            api_instance.put_files(fullpath, dir=True)
            return True
        except ApiException as e:
            if e.status == 401:
                # Token must have expired so remove the cache to force sign-in look
                self._clean_out_expired_authtoken()
                raise TokenError("HUB session timeout; sign in required.")
            elif e.status == 403:
                # Account storage is full most likely.
                raise APIError("Account free space exhausted.")
            else:
                raise APIError(e.reason)
        except urllib3.exceptions.HTTPError:
            raise APIError('HUB server unavailable; try again later.')

    def delete_cloud_items(self, item_list):
        """Delete files and directories from the user's account on the server

        Args:
            item_list (list): list of namedtuple CloudItems to delete
        """
        # Create an instance of the API class
        api_instance = openapi_client.DefaultApi(self.api_client)

        for item in item_list:
            # Delete the file or directory
            try:
                api_instance.delete(
                    fullpath=item.fullpath,
                    group_type=item.group_type,
                    group_id=item.group_id,
                )
            except ApiException as e:
                if e.status == 401:
                    # Token must have expired so remove the cache to force sign-in look
                    self._clean_out_expired_authtoken()
                    raise TokenError("HUB session timeout; sign in required.")
                else:
                    raise APIError(e.reason)
            except urllib3.exceptions.HTTPError:
                raise APIError('HUB server unavailable; try again later.')

        return True

    def get_token_for_logged_in_user(self):
        """Return the auth token string for the user that is logged in


        Returns:
            String: Token for the user with email or None if it does not exist
        """
        if self.redis.hexists("pp_hub_settings", "token"):
            return self.redis.hget('pp_hub_settings', "token")
        else:
            return None

    def get_logged_in_email(self):
        if self.redis.hexists("pp_hub_settings", "email"):
            return self.redis.hget('pp_hub_settings', "email")
        else:
            return None

    def get_license(self, machineobj, ppversion, lcnc_command):
        m = openapi_client.Machine(
            guid=machineobj.machine_guid(),
            model=machineobj.model_name(),
            machineclass=machineobj.machine_class(),
            lic=machineobj.lic(),
            sn=machineobj.machine_sn(),
            ppversion=ppversion,
        )

        # Create an instance of the API class
        api_instance = openapi_client.DefaultApi(self.api_client)

        asyncresult = api_instance.get_license(m, async_req=True)

        def callback(asyncresult):
            try:
                body = asyncresult.get()
                lcnc_command.update_data(body)
                return True
            except ApiException as e:
                if e.status == 401:
                    # Token must have expired so remove the cache to force sign-in look
                    self._clean_out_expired_authtoken()
                    raise TokenError("HUB session timeout; sign in required.")
                else:
                    raise APIError(e.reason)
            except urllib3.exceptions.HTTPError:
                raise APIError('HUB server unavailable; try again later.')

            return False

        return AsyncResultWrapper(asyncresult, callback)

    def update_machine_status(self, machineobj, ppversion):
        m = openapi_client.Machine(
            guid=machineobj.machine_guid(),
            model=machineobj.model_name(),
            machineclass=machineobj.machine_class(),
            lic=machineobj.lic(),
            sn=machineobj.machine_sn(),
            ppversion=ppversion,
        )

        # Create an instance of the API class
        api_instance = openapi_client.DefaultApi(self.api_client)

        try:
            api_instance.update_machine_status(m)
            return True
        except ApiException as e:
            if e.status == 401:
                # Token must have expired so remove the cache to force sign-in look
                self._clean_out_expired_authtoken()
                raise TokenError("HUB session timeout; sign in required.")
            else:
                raise APIError(e.reason)
        except urllib3.exceptions.HTTPError:
            raise APIError('HUB server unavailable; try again later.')

        return False

    def upload_machine_logdata(self, machineguid, logdatazippath):
        try:
            # Create an instance of the API class
            api_instance = openapi_client.DefaultApi(self.api_client)
            filename = os.path.basename(logdatazippath)
            try:
                api_instance.upload_log_data(
                    filename, guid=machineguid, filedata=logdatazippath
                )
                return True
            except ApiException as e:
                if e.status == 401:
                    # Token must have expired so remove the cache to force sign-in look
                    self._clean_out_expired_authtoken()
                    raise TokenError("HUB session timeout; sign in required.")
                else:
                    raise APIError(e.reason)
            except urllib3.exceptions.HTTPError:
                raise APIError('HUB server unavailable; try again later.')
        except OSError:
            pass  # file not present or unreadable

        return False
