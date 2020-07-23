"""helper functions for Microsoft Graph"""
# Copyright (c) Microsoft. All rights reserved. Licensed under the MIT license.
# See LICENSE in the project root for license information.
# Note: This started from an ADAL sample and is being customized once I learned
# ADAL Python sucks and MSAL Python is the way to go (but didn't provide samples
# as nice as this one)

import base64
import mimetypes
import os
import sys
import urllib
import webbrowser
import json
import logging
import adal
import msal
import pyperclip
import requests
import atexit
import pickle
import datetime

from . import config


def api_endpoint(url):
    """Convert a relative path such as /me/photo/$value to a full URI based
    on the current RESOURCE and API_VERSION settings in config.py.
    """
    if urllib.parse.urlparse(url).scheme in ["http", "https"]:
        return url  # url is already complete
    return urllib.parse.urljoin(
        f"{config.RESOURCE}/{config.API_VERSION}/", url.lstrip("/")
    )


def refresh_flow_session_adal(client_id, refresh_token):
    """Obtain an access token from Azure AD (via device flow) and create
    a Requests session instance ready to make authenticated calls to
    Microsoft Graph.

    client_id = Application ID for registered "Azure AD only" V1-endpoint app
    refresh_token = existing token stored somewhere that we should try to open

    Returns Requests session object if user signed in successfully. The session
    includes the access token in an Authorization header.

    User identity must be an organizational account (ADAL does not support MSAs).
    """
    ctx = adal.AuthenticationContext(config.AUTHORITY_URL, api_version=None)
    token_response = ctx.acquire_token_with_refresh_token(
        refresh_token, client_id, config.RESOURCE
    )

    if not token_response.get("accessToken", None):
        return None

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f'Bearer {token_response["accessToken"]}',
            "SdkVersion": "sample-python-adal",
            "x-client-SKU": "sample-python-adal",
        }
    )
    return session


def device_flow_session_adal(client_id, *, auto=False, secret=None):
    """Obtain an access token from Azure AD (via device flow) and create
    a Requests session instance ready to make authenticated calls to
    Microsoft Graph.

    client_id = Application ID for registered "Azure AD only" V1-endpoint app
    auto      = whether to copy device code to clipboard and auto-launch browser

    Returns Requests session object if user signed in successfully. The session
    includes the access token in an Authorization header.

    User identity must be an organizational account (ADAL does not support MSAs).
    """
    ctx = adal.AuthenticationContext(config.AUTHORITY_URL, api_version=None)
    device_code = ctx.acquire_user_code(config.RESOURCE, client_id)

    # display user instructions
    if auto:
        pyperclip.copy(device_code["user_code"])  # copy user code to clipboard
        webbrowser.open(device_code["verification_url"])  # open browser
        print(
            f'The code {device_code["user_code"]} has been copied to your clipboard, '
            f'and your web browser is opening {device_code["verification_url"]}. '
            "Paste the code to sign in."
        )
    else:
        print(device_code["message"])

    token_response = ctx.acquire_token_with_device_code(
        config.RESOURCE, device_code, client_id
    )
    if not token_response.get("accessToken", None):
        return None

    refresh_token = token_response.get("refreshToken", None)

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f'Bearer {token_response["accessToken"]}',
            "SdkVersion": "sample-python-adal",
            "x-client-SKU": "sample-python-adal",
        }
    )
    return (session, refresh_token)


def tryLoginAdal(client_id):
    """
    This will try to look for an existing refresh token in a pickle,
    then refresh that login first with ADAL login before 
    going into the device flow session.
    """
    refresh_token = None

    path = "microsoft.pickle"

    if os.path.exists(path):
        with open(path, "rb") as token:
            refresh_token = pickle.load(token)

    session = None

    if refresh_token:
        session = refresh_flow_session_adal(client_id, refresh_token)

    if not session:
        session, refresh_token = device_flow_session_adal(client_id, auto=True)

        # Save the credentials for the next run
        with open(path, "wb") as token:
            pickle.dump(refresh_token, token)

    return session


def device_flow_session_msal(client_id, scope):
    """Obtain an access token from Microsoft (via device flow) and create
    a Requests session instance ready to make authenticated calls to
    Microsoft Graph.

    client_id = Application ID
    scope = what we want access to

    Returns Requests session object if user signed in successfully. The session
    includes the access token in an Authorization header.

    Adapted from ADAL sample and otherwise taken from https://github.com/AzureAD/microsoft-authentication-library-for-python/blob/dev/sample/device_flow_sample.py
    """

    cache = msal.SerializableTokenCache()
    CACHE_FILE = "microsoft.bin"
    if os.path.exists(CACHE_FILE):
        cache.deserialize(open(CACHE_FILE, "r").read())
    atexit.register(
        lambda: open(CACHE_FILE, "w").write(cache.serialize())
        # Hint: The following optional line persists only when state changed
        if cache.has_state_changed
        else None
    )

    app = msal.PublicClientApplication(
        client_id, authority=config.AUTHORITY_URL, token_cache=cache
    )

    result = None

    accounts = app.get_accounts()
    if accounts:
        logging.info("Account(s) exists in cache, probably with token too. Let's try.")
        # NOTE: this is dumb and doesn't even check the user choice, comment it, take the first one instead
        # print("Pick the account you want to use to proceed:")
        # for a in accounts:
        #     print(a["username"])
        # # Assuming the end user chose this one
        chosen = accounts[0]
        # Now let's try to find a token in cache for this account
        result = app.acquire_token_silent(scope, account=chosen)

    if not result:
        logging.info("No suitable token exists in cache. Let's get a new one from AAD.")

        flow = app.initiate_device_flow(scopes=scope)
        if "user_code" not in flow:
            raise ValueError(
                "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4)
            )

        print(flow["message"])
        sys.stdout.flush()  # Some terminal needs this to ensure the message is shown

        # Ideally you should wait here, in order to save some unnecessary polling
        # input("Press Enter after signing in from another device to proceed, CTRL+C to abort.")

        result = app.acquire_token_by_device_flow(flow)  # By default it will block
        # You can follow this instruction to shorten the block time
        #    https://msal-python.readthedocs.io/en/latest/#msal.PublicClientApplication.acquire_token_by_device_flow
        # or you may even turn off the blocking behavior,
        # and then keep calling acquire_token_by_device_flow(flow) in your own customized loop.

    if "access_token" in result:
        session = requests.Session()
        session.headers.update({"Authorization": f'Bearer {result["access_token"]}'})
        return session
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))  # You may need this when reporting a bug
        return None


def profile_photo(session, *, user_id="me", save_as=None):
    """Get profile photo, and optionally save a local copy.

    session = requests.Session() instance with Graph access token
    user_id = Graph id value for the user, or 'me' (default) for current user
    save_as = optional filename to save the photo locally. Should not include an
              extension - the extension is determined by photo's content type.

    Returns a tuple of the photo (raw data), HTTP status code, content type, saved filename.
    """

    endpoint = "me/photo/$value" if user_id == "me" else f"users/{user_id}/$value"
    photo_response = session.get(api_endpoint(endpoint), stream=True)
    photo_status_code = photo_response.status_code
    if photo_response.ok:
        photo = photo_response.raw.read()
        # note we remove /$value from endpoint to get metadata endpoint
        metadata_response = session.get(api_endpoint(endpoint[:-7]))
        content_type = metadata_response.json().get("@odata.mediaContentType", "")
    else:
        photo = ""
        content_type = ""

    if photo and save_as:
        extension = content_type.split("/")[1]
        filename = save_as + "." + extension
        with open(filename, "wb") as fhandle:
            fhandle.write(photo)
    else:
        filename = ""

    return (photo, photo_status_code, content_type, filename)


def list_mail(session, *, user_id="me", search=None):
    """List email from current user.

    session      = requests.Session() instance with Graph access token
    user_id = Graph id value for the user, or 'me' (default) for current user
    search  = optional text to search for

    Returns the whole JSON for the message request
    """

    # MAIL_QUERY = 'https://graph.microsoft.com/v1.0/me/messages?$search="{query}"'

    endpoint = "me/messages" if user_id == "me" else f"users/{user_id}/messages"

    if search:
        endpoint += '?$search="%s"' % search

    response = session.get(api_endpoint(endpoint))
    response.raise_for_status()
    return response.json()


def create_event(session, *, user_id="me", subject, start, end):
    """
    session = requests.Session() from an MSAL/ADAL login
    user_id = Graph id value for the user, or 'me' (default) for current user
    subject = title of calendar event
    start = start date/time (will attempt replace to utc if necessary)
    end = end date/time (will attempt replace to utc if necessary)
    """

    endpoint = "me/events" if user_id == "me" else f"users/{user_id}/events"

    startutciso = (
        start.astimezone(datetime.timezone.utc).replace(tzinfo=None).isoformat()
    )
    endutciso = end.astimezone(datetime.timezone.utc).replace(tzinfo=None).isoformat()

    body = {
        "subject": subject,
        "start": {"dateTime": startutciso, "timeZone": "UTC"},
        "end": {"dateTime": endutciso, "timeZone": "UTC"},
    }

    return session.post(api_endpoint(endpoint), json=body)


def move_mail(session, *, messageid, folderid):
    """Move an email into a specific folder
    session = requests.Session()
    messageid = the ID of the message out of the messages list api
    folderid = the ID of the folder to put it into. has to be encoded or a well-known one
            Find well-known ones here: https://docs.microsoft.com/en-us/graph/api/resources/mailfolder?view=graph-rest-1.0
    """

    endpoint = f"me/messages/{messageid}/move"

    body = {"destinationId": folderid}

    return session.post(api_endpoint(endpoint), json=body)


def send_mail(
    session, *, subject, recipients, body="", content_type="HTML", attachments=None
):
    """Send email from current user.

    session      = requests.Session() instance with Graph access token
    subject      = email subject (required)
    recipients   = list of recipient email addresses (required)
    body         = body of the message
    content_type = content type (default is 'HTML')
    attachments  = list of file attachments (local filenames)

    Returns the response from the POST to the sendmail API.
    """

    # Create recipient list in required format.
    recipient_list = [{"EmailAddress": {"Address": address}} for address in recipients]

    # Create list of attachments in required format.
    attached_files = []
    if attachments:
        for filename in attachments:
            b64_content = base64.b64encode(open(filename, "rb").read())
            mime_type = mimetypes.guess_type(filename)[0]
            mime_type = mime_type if mime_type else ""
            attached_files.append(
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "ContentBytes": b64_content.decode("utf-8"),
                    "ContentType": mime_type,
                    "Name": filename,
                }
            )

    # Create email message in required format.
    email_msg = {
        "Message": {
            "Subject": subject,
            "Body": {"ContentType": content_type, "Content": body},
            "ToRecipients": recipient_list,
            "Attachments": attached_files,
        },
        "SaveToSentItems": "true",
    }

    # Do a POST to Graph's sendMail API and return the response.
    return session.post(
        api_endpoint("me/microsoft.graph.sendMail"),
        headers={"Content-Type": "application/json"},
        json=email_msg,
    )


def sharing_link(session, *, item_id, link_type="view"):
    """Get a sharing link for an item in OneDrive.

    session   = requests.Session() instance with Graph access token
    item_id   = the id of the DriveItem (the target of the link)
    link_type = 'view' (default), 'edit', or 'embed' (OneDrive Personal only)

    Returns a tuple of the response object and the sharing link.
    """
    endpoint = f"me/drive/items/{item_id}/createLink"
    response = session.post(
        api_endpoint(endpoint),
        headers={"Content-Type": "application/json"},
        json={"type": link_type},
    )

    if response.ok:
        # status 201 = link created, status 200 = existing link returned
        return (response, response.json()["link"]["webUrl"])
    return (response, "")


def make_folder(session, *, foldername, parent=None):
    """Create a folder in OneDrive
    session  = requests.Session() instance with Graph access token
    foldername = name of the new folder
    parent = optional, defaults to root. otherwise, path to subfolder
    """
    if not parent:
        endpoint = f"me/drive/root/children"
    else:
        endpoint = f"me/drive/root:/{parent}:/children"

    payload = {}
    payload["name"] = foldername
    payload["folder"] = {}

    return session.post(api_endpoint(endpoint), json=payload)


def upload_file_handle(session, *, iterable, filename, folder=None):
    """Upload a file to OneDrive
    Needs Files.ReadWrite scope

    session  = requests.Session() instance with Graph access token
    iterable = file-like iterator with bytes to upload
    filename = name of the file to place in OneDrive
    folder   = destination subfolder/path in OneDrive 
               None (default) = root folder

    File is uploaded and the response object is returned.
    If file already exists, it is overwritten.
    If folder does not exist, it is created.

    API documentation:
    https://developer.microsoft.com/en-us/graph/docs/api-reference/v1.0/api/driveitem_put_content
    """
    # create the Graph endpoint to be used
    if folder:
        # create endpoint for upload to a subfolder
        endpoint = f"me/drive/root:/{folder}/{filename}:/content"
    else:
        # create endpoint for upload to drive root folder
        endpoint = f"me/drive/root/children/{filename}/content"

    return session.put(
        api_endpoint(endpoint),
        headers={"content-type": "application/octet-stream"},
        data=iterable,
    )


def upload_file(session, *, ospath, folder=None):
    """Upload a file to OneDrive

    session  = requests.Session() instance with Graph access token
    ospath = local filename; may include a path
    folder   = destination subfolder/path in OneDrive for Business
               None (default) = root folder

    File is uploaded and the response object is returned.
    If file already exists, it is overwritten.
    If folder does not exist, it is created.

    API documentation:
    https://developer.microsoft.com/en-us/graph/docs/api-reference/v1.0/api/driveitem_put_content
    """
    fname_only = os.path.basename(ospath)

    with open(ospath, "rb") as fhandle:
        return upload_file_handle(
            session, iterable=fhandle, filename=fname_only, folder=folder
        )
