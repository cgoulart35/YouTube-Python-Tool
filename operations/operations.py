import re
import sys

def get_video_info_from_url(youtube, url):
    video_infos = []

    if "playlist" in url:
        playlist_id = re.search(r"list=([^&]+)", url).group(1)
        all_playlist_videos = get_all_playlist_data(youtube, playlist_id)
        for video_id, video_url, item_id in all_playlist_videos:
            video_infos.append((video_id, video_url))
    else:
        video_id = re.search(r"v=([^&]+)", url).group(1)
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_infos.append((video_id, video_url))

    return video_infos

def add_videos_to_playlist(youtube, videos_to_add, playlist_url, is_preview):
    playlist_id = re.search(r"list=([^&]+)", playlist_url).group(1)
    video_additions = []
    already_in_playlist = []
    failed = []

    # Retrieve all playlist contents first
    all_playlist_videos = get_all_playlist_data(youtube, playlist_id)
    playlist_videos_dict = {video_id: (video_url, item_id) for video_id, video_url, item_id in all_playlist_videos}

    # Process videos to add
    for video_id, video_url in videos_to_add:
        if video_id in playlist_videos_dict:
            print(f"Video {video_id} already found in playlist {playlist_id}")
            already_in_playlist.append((video_id, video_url))
        else:
            print(f"Video {video_id} not yet added to playlist {playlist_id}")
            video = (video_id, video_url)
            video_additions.append(video)
            if not is_preview:
                try:
                    youtube.playlistItems().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "playlistId": playlist_id,
                                "resourceId": {
                                    "kind": "youtube#video",
                                    "videoId": video_id
                                }
                            }
                        }
                    ).execute()
                    print(f"Added video {video_id} to playlist {playlist_id}")
                except Exception as e:
                    print(f"Error adding video {video_id} to playlist {playlist_id}: {e}")
                    failed.append((video, str(e)))
                    video_additions.remove(video)
    return {
        "no_actions": len(video_additions) == 0,
        "video_additions": video_additions,
        "already_in_playlist": already_in_playlist,
        "failed": failed
    }

def remove_videos_from_playlist(youtube, videos_to_remove, playlist_url, is_preview):
    playlist_id = re.search(r"list=([^&]+)", playlist_url).group(1)
    video_removals = []
    not_in_playlist = []
    failed = []

    # Retrieve all playlist contents first
    all_playlist_videos = get_all_playlist_data(youtube, playlist_id)
    playlist_videos_dict = {video_id: (video_url, item_id) for video_id, video_url, item_id in all_playlist_videos}

    # Process videos to remove
    for video_id, video_url in videos_to_remove:
        if video_id in playlist_videos_dict:
            print(f"Found video {video_id} in playlist {playlist_id}")
            video = (video_id, video_url)
            video_removals.append(video)
            if not is_preview:
                try:
                    youtube.playlistItems().delete(id=playlist_videos_dict[video_id][1]).execute()
                    print(f"Removed video {video_id} from playlist {playlist_id}")
                except Exception as e:
                    print(f"Error removing video {video_id} from playlist {playlist_id}: {e}")
                    failed.append((video, str(e)))
                    video_removals.remove(video)
        else:
            print(f"Video {video_id} not found in playlist {playlist_id}")
            not_in_playlist.append(video)
    return {
        "no_actions": len(video_removals) == 0,
        "video_removals": video_removals,
        "not_in_playlist": not_in_playlist,
        "failed": failed
    }

def get_all_playlist_data(youtube, playlist_id):
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
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                all_playlist_videos.append([video_id, video_url, item["id"]])
            request = youtube.playlistItems().list_next(request, response)
        except Exception as e:
            print(f"Error retrieving playlist {playlist_id} contents: {e}")
            sys.exit(1)

    return all_playlist_videos