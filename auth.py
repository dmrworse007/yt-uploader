"""OAuth handling for Google Drive (read) + YouTube (upload).

First run opens a browser so you can grant access to YOUR Google account
(the one that owns the YouTube channel and the Drive folder). After that,
credentials are cached in token.json and refreshed automatically -- no
further human interaction needed, which is what makes the hourly schedule
possible.
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes: read-only Drive, and YouTube upload.
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def get_credentials(client_secret_file: str, token_file: str) -> Credentials:
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secret_file):
                raise FileNotFoundError(
                    f"Missing {client_secret_file}. Download your OAuth "
                    "client credentials from Google Cloud Console and save "
                    "them here. See README.md step 3."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_file, SCOPES
            )
            # Opens a local browser window for the one-time consent.
            creds = flow.run_local_server(port=0)
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds
