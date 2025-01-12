import os
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes for accessing YouTube data (including private playlists and managing playlists)
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube'
]

def get_authenticated_service():
    # Load credentials from file or authorize if necessary
    credentials = None
    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                os.environ['SECRET_JSON_YOUTUBE_API_PATH'], SCOPES)
            credentials = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())

    # Build the YouTube API client with the OAuth credentials
    youtube = build('youtube', 'v3', credentials=credentials)
    print("Authenticated successfully")
    return youtube