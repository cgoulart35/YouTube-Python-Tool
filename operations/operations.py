import re
import sys

def get_video_categories(youtube):
    request = youtube.videoCategories().list(
        part="snippet",
        regionCode="US"
    )
    response = request.execute()
    categories = {item["id"]: item["snippet"]["title"] for item in response["items"]}
    return categories

def get_single_playlist_name(youtube, urls):
    if len(urls) == 1 and "playlist" in urls[0]:
        playlist_id = re.search(r"list=([^&]+)", urls[0]).group(1)
        request = youtube.playlists().list(
            part="snippet",
            id=playlist_id
        )
        response = request.execute()
        if response["items"]:
            return response["items"][0]["snippet"]["title"]
    return None

def get_all_video_data(youtube, video_id):
    video_details_request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    video_details_response = video_details_request.execute()
    return video_details_response["items"][0]["snippet"]

def get_all_playlist_video_data(youtube, playlist_id, categories):
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

                # Get video details
                video_details = get_all_video_data(youtube, video_id)
                video_title = video_details["title"]
                video_category = video_details["categoryId"]

                all_playlist_videos.append({
                    "video_id": video_id,
                    "video_url": video_url,
                    "video_title": video_title,
                    "video_category": categories.get(video_category, "Unknown"),
                    "item_id": item["id"]
                })
            request = youtube.playlistItems().list_next(request, response)
        except Exception as e:
            print(f"Error retrieving playlist {playlist_id} contents: {e}")
            sys.exit(1)

    return all_playlist_videos

def get_video_info_from_url(youtube, url, categories):
    video_infos = []

    if "playlist" in url:
        playlist_id = re.search(r"list=([^&]+)", url).group(1)
        all_playlist_videos = get_all_playlist_video_data(youtube, playlist_id, categories)
        for video in all_playlist_videos:
            video_infos.append({
                "video_id": video["video_id"],
                "video_url": video["video_url"],
                "video_title": video["video_title"],
                "video_category": video["video_category"]
            })
    else:
        video_id = re.search(r"v=([^&]+)", url).group(1)
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Get video details
        video_details = get_all_video_data(youtube, video_id)
        video_title = video_details["title"]
        video_category = video_details["categoryId"]

        video_infos.append({
            "video_id": video_id,
            "video_url": video_url,
            "video_title": video_title,
            "video_category": categories.get(video_category, "Unknown"),
        })

    return video_infos

def add_videos_to_playlist(youtube, videos_to_add, playlist_url, is_preview, categories):
    playlist_id = re.search(r"list=([^&]+)", playlist_url).group(1) if playlist_url != None else None
    video_additions = []
    already_in_playlist = []
    failed = []

    # Retrieve all playlist contents first
    all_playlist_videos = get_all_playlist_video_data(youtube, playlist_id, categories) if playlist_id != None else []
    playlist_videos_dict = {video["video_id"]: (video["video_url"], video["item_id"]) for video in all_playlist_videos}

    # Process videos to add
    for video in videos_to_add:
        video_id = video["video_id"]
        if video_id in playlist_videos_dict:
            print(f"Video {video_id} already found in playlist {playlist_id}")
            already_in_playlist.append(video)
        else:
            print(f"Video {video_id} not yet added to playlist {playlist_id}")
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

def remove_videos_from_playlist(youtube, videos_to_remove, playlist_url, is_preview, categories):
    playlist_id = re.search(r"list=([^&]+)", playlist_url).group(1)
    video_removals = []
    not_in_playlist = []
    failed = []

    # Retrieve all playlist contents first
    all_playlist_videos = get_all_playlist_video_data(youtube, playlist_id, categories)
    playlist_videos_dict = {video["video_id"]: (video["video_url"], video["item_id"]) for video in all_playlist_videos}

    # Process videos to remove
    for video in videos_to_remove:
        video_id = video["video_id"]
        if video_id in playlist_videos_dict:
            print(f"Found video {video_id} in playlist {playlist_id}")
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

def create_playlist(youtube, playlist_name):
    # Create a new playlist
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": playlist_name,
                "description": "Created with YouTube Python Tool.",
                "tags": [],
                "defaultLanguage": "en"
            },
            "status": {
                "privacyStatus": "private"
            }
        }
    )
    response = request.execute()

    # Extract playlist ID and URL from the response
    playlist_id = response["id"]
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    return (playlist_id, playlist_url)