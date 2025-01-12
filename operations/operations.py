import re

def get_video_ids_from_url(youtube, url):
    video_ids = []

    if "playlist" in url:
        playlist_id = re.search(r"list=([^&]+)", url).group(1)
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )
        while request:
            response = request.execute()
            for item in response["items"]:
                video_ids.append(item["contentDetails"]["videoId"])
            request = youtube.playlistItems().list_next(request, response)
    else:
        video_id = re.search(r"v=([^&]+)", url).group(1)
        video_ids.append(video_id)

    return video_ids

def remove_videos_from_playlist(youtube, video_ids, playlist_url):
    playlist_id = re.search(r"list=([^&]+)", playlist_url).group(1)

    for video_id in video_ids:
        request = youtube.playlistItems().list(
            part="id,contentDetails",
            playlistId=playlist_id,
            videoId=video_id,
            maxResults=1
        )
        response = request.execute()
        if response["items"]:
            playlist_item_id = response["items"][0]["id"]
            youtube.playlistItems().delete(id=playlist_item_id).execute()
            print(f"Removed video {video_id} from playlist {playlist_id}")