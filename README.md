# YouTube Python Tool
Suite of Python scripts to use for complex operations not supported on YouTube.

## Prerequisites
- Python 3.x installed
- Python Dependencies: `google-api-python-client` `google-auth-oauthlib`
- Create a Google Project with YouTube Data API v3 & generate/download OAuth2 client secret key file
- Create an environment variable that points to your OAuth2 client secret key file path
- Add yourself as a test user to your application

## Running any script
1. The first time you run the script you will be asked to sign into the Google/YouTube account you want to manage - this will generate you an authorization token locally.
2. In future updates, make sure to delete & regenerate your token to get the latest scope requirements.
3. Provide the `-force | -f` flag to skip the preview of the current operation's results and start executing the operation immediately.
3. Provide the `-previewonly | -p` flag to stop the operation right after giving a preview of the current operation's results.

## Running `bulk-add-to-playlist` Python script
1. This Python script allows you to add many videos to a YouTube playlist.
2. Run the Python script specifying videos/playlist of videos to add, and playlist to add to:
    ```python
    python bulk-add-to-playlist.py "playlistUrl1,playlistUr2,videoUrl1,playlistUrl3" "playlist_url"
    ```

## Running `bulk-remove-from-playlist` Python script
1. This Python script allows you to remove many videos from a YouTube playlist.
2. Run the Python script specifying videos/playlist of videos to remove, and playlist to remove from:
    ```python
    python bulk-remove-from-playlist.py "videoUrl1,playlistUrl1,videoUrl2,videoUrl3" "playlist_url"
    ```

## Running `divide-into-categories` Python script
1. This Python script allows you to group many videos into new playlists based on YouTube categories.
2. Run the Python script specifying videos/playlist of videos to divide into new playlists grouped by YouTube category:
    ```python
    python divide-into-categories.py "videoUrl1,playlistUrl1,videoUrl2,playlistUrl2"
    ```
3. Provide the `-name | -n` flag to skip being prompted for playlist names to automatically use the default generated names instead.