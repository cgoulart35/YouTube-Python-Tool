import re
import sys

# Operations workflows depend on

def get_video_categories(youtube):
    try:
        request = youtube.videoCategories().list(
            part="snippet",
            regionCode="US"
        )
        response = request.execute()
        categories = {item["id"]: item["snippet"]["title"] for item in response["items"]}
        return categories
    except Exception as e:
        print(f"Error retrieving video categories:\n{e}\n")
        sys.exit(1)

# Error proof operations

def get_all_playlist_video_data(youtube, playlist_id, categories):
    try:
        all_playlist_videos = []
        unavailable_video_data = []
        request = youtube.playlistItems().list(
            part="id,contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )
        while request:
            response = request.execute()
            for item in response["items"]:
                video_id = item["contentDetails"]["videoId"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                # Get video details
                video_details = get_single_video_data(youtube, video_id)
                if not video_details[0]:
                    unavailable_video_data.append({
                        "video_id": video_id,
                        "playlist_item_id": item["id"]
                    })
                    continue
                video_title = video_details[1]["title"]
                video_category = video_details[1]["categoryId"]

                all_playlist_videos.append({
                    "video_id": video_id,
                    "video_url": video_url,
                    "video_title": video_title,
                    "video_category": categories.get(video_category, "Unknown"),
                    "playlist_item_id": item["id"]
                })
            request = youtube.playlistItems().list_next(request, response)
        return (True, {
            "all_playlist_videos": all_playlist_videos,
            "unavailable_video_data": unavailable_video_data
        })
    except Exception as e:
        print(f"Error retrieving playlist {playlist_id} contents:\n{e}\n")
        return (False, None)
    
def get_single_video_data(youtube, video_id):
    try:
        video_details_request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        video_details_response = video_details_request.execute()
        if not video_details_response["items"]:
            print(f"No details found for video {video_id}")
            return (False, None)
        return (True, video_details_response["items"][0]["snippet"])
    except Exception as e:
        print(f"Error retrieving video {video_id} contents:\n{e}\n")
        return (False, None)

def add_videos_to_playlist(youtube, videos_to_add, playlist_url, destination_playlist_videos, is_preview):
    playlist_id = re.search(r"list=([^&]+)", playlist_url).group(1) if playlist_url != None else None
    video_additions = []
    already_in_playlist = []
    failed = []

    # Process videos to add
    for video_id in videos_to_add:
        video = videos_to_add[video_id]
        if video_id in destination_playlist_videos:
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
                    print(f"Error adding video {video_id} to playlist {playlist_id}:\n{e}\n")
                    failed.append((video, str(e)))
                    video_additions.remove(video)
    return {
        "no_actions": len(video_additions) == 0,
        "video_additions": video_additions,
        "already_in_playlist": already_in_playlist,
        "failed": failed
    }

def remove_videos_from_playlist(youtube, videos_to_remove, playlist_url, destination_playlist_videos, is_preview):
    playlist_id = re.search(r"list=([^&]+)", playlist_url).group(1)
    video_removals = []
    not_in_playlist = []
    failed = []

    # Process videos to remove
    for video_id in videos_to_remove:
        video = videos_to_remove[video_id]
        if video_id in destination_playlist_videos:
            print(f"Found video {video_id} in playlist {playlist_id}")
            video_removals.append(video)
            if not is_preview:
                try:
                    youtube.playlistItems().delete(id=destination_playlist_videos[video_id]["playlist_item_id"]).execute()
                    print(f"Removed video {video_id} from playlist {playlist_id}")
                except Exception as e:
                    print(f"Error removing video {video_id} from playlist {playlist_id}:\n{e}\n")
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

def get_single_playlist_data(youtube, url):
    try:
        playlist_id = re.search(r"list=([^&]+)", url).group(1)
        request = youtube.playlists().list(
            part="snippet",
            id=playlist_id
        )
        response = request.execute()
        if response["items"]:
            return response["items"][0]["snippet"]
        else:
            return None
    except Exception as e:
        print(f"Error retrieving single playlist:\n{e}\n")
        return None

def create_playlist(youtube, playlist_name):
    # Create a new playlist
    try:
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

        print(f"Created playlist {playlist_id}")
        return (True, {
            "playlist_id": playlist_id,
            "playlist_url": playlist_url
        })
    except Exception as e:
        print(f"Error creating playlist {playlist_name}:\n{e}\n")
        return (False, None)