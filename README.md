# YouTube Python Tool
Suite of Python scripts to use for complex operations not supported on YouTube.

## Prerequisites
- Python 3.x installed
- Python Dependencies: `google-api-python-client` `google-auth-oauthlib`
- Create YouTube Data API v3 service account & generate/download client secret key
- Add service account email as a manager to your YouTube account
- Create an environment variable that points to your client secret key path

## Running `bulk-remove-from-playlist` Python script
1. This Python script allows you to remove many videos from a YouTube playlist.
2. Run the Python script specifying videos/playlist of videos to remove, and playlist to remove from:
    ```python
    python bulk-remove-from-playlist.py "videoUrl1,playlistUrl1,videoUrl2,videoUrl3" "playlist_url"
    ```