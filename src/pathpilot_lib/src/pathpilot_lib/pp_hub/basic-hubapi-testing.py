import openapi_client
from openapi_client.rest import ApiException
from pprint import pprint

API_URL = "http://127.0.0.1:5001/api/v1"


# Configure API key authorization: HubTokenAuth
configuration = openapi_client.Configuration(
    host=API_URL,
    api_key={
        'X-HubAuthToken': '',
    },
)

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.DefaultApi(api_client)

    # Get a token
    try:
        tokenobj = api_instance.get_token(
            email='testman@gmail.com', password='testing'
        )
    except ApiException as e:
        print("Exception: %s\n" % e)


configuration = openapi_client.Configuration(
    host=API_URL,
    api_key={
        'X-HubAuthToken': tokenobj.token,
    },
)

with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.DefaultApi(api_client)

    # List files
    try:
        listing = api_instance.get_files('gcode')
        pprint(listing)
    except ApiException as e:
        print("Exception: %s\n" % e)

    # Download a full file
    try:
        listing = api_instance.get_files('gcode/WOWmom.nc')
        pprint(listing)
    except ApiException as e:
        print("Exception: %s\n" % e)

    # Delete a file
    try:
        listing = api_instance.delete('gcode/delete-me.nc')
        pprint(listing)
    except ApiException as e:
        print("Exception: %s\n" % e)

    # Create a directory
    try:
        listing = api_instance.put_files('gcode/new-folder', dir=True)
        pprint(listing)
    except ApiException as e:
        print("Exception: %s\n" % e)

    # Upload file
    try:
        listing = api_instance.put_files(
            'gcode/holy-shit-batman.nc',
            filedata='/home/alexander/postinstall.txt',
            overwrite='true',
        )
        pprint(listing)
    except ApiException as e:
        print("Exception: %s\n" % e)

    # Rename file
    # try:
    #     listing = api_instance.rename_files(
    #         'gcode/holy-shit-batman.nc', newname='VICTORY.nc'
    #     )
    #     pprint(listing)
    # except ApiException as e:
    #     print("Exception: %s\n" % e)


# KILLER - WORKS PERFECTLY

with openapi_client.ApiClient(
    configuration, header_name='Range', header_value='bytes=0-15'
) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.DefaultApi(api_client)

    # Download a file
    try:
        listing = api_instance.get_files('gcode/WOWmom.nc')
        pprint(listing)
    except ApiException as e:
        print("Exception: %s\n" % e)

    # Revoke a token
    try:
        api_instance.revoke_token()
    except ApiException as e:
        print("Exception: %s\n" % e)
