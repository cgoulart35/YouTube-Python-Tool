import re
import sys

def get_video_info_from_url(youtube, url):
    video_infos = []

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
                video_id = item["contentDetails"]["videoId"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_infos.append((video_id, video_url))
            request = youtube.playlistItems().list_next(request, response)
    else:
        video_id = re.search(r"v=([^&]+)", url).group(1)
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_infos.append((video_id, video_url))

    return video_infos

def remove_videos_from_playlist(youtube, videos_to_remove, playlist_url, is_preview):
    playlist_id = re.search(r"list=([^&]+)", playlist_url).group(1)
    video_removals = []
    not_in_playlist = []
    failed = []

    # Retrieve all playlist contents first
    all_playlist_videos = []
    request = youtube.playlistItems().list(
        part="id,contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )

    while request:
        try:
            response = request.execute()
            for item in response["items"]:
                video_id = item["contentDetails"]["videoId"]
                all_playlist_videos.append((video_id, item["id"]))
            request = youtube.playlistItems().list_next(request, response)
        except Exception as e:
            print(f"Error retrieving playlist {playlist_id} contents: {e}")
            sys.exit(1)

    # Process videos to remove
    for video_id, video_url in videos_to_remove:
        found = False
        for playlist_video_id, playlist_item_id in all_playlist_videos:
            if video_id == playlist_video_id:
                print(f"Found video {video_id} in playlist {playlist_id}")
                found = True
                if not is_preview:
                    try:
                        youtube.playlistItems().delete(id=playlist_item_id).execute()
                        print(f"Removed video {video_id} from playlist {playlist_id}")
                        video_removals.append((video_id, video_url))
                    except Exception as e:
                        print(f"Error removing video {video_id} from playlist {playlist_id}: {e}")
                        failed.append((video_id, str(e)))
                        continue
                break
        if not found:
            print(f"Video {video_id} not found in playlist {playlist_id}")
            not_in_playlist.append((video_id, video_url))

    return {
        "exit_early": len(video_removals) == 0,
        "removed_videos": video_removals,
        "not_in_playlist": not_in_playlist,
        "failed": failed
    }