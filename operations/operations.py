import re
import sys
import math

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

        # Fetch playlist items
        playlist_items = []
        request = youtube.playlistItems().list(
            part="id,contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )
        while request:
            response = request.execute()
            playlist_items.extend(response.get("items", []))
            request = youtube.playlistItems().list_next(request, response)

        # Batch video details retrieval
        video_ids = [item["contentDetails"]["videoId"] for item in playlist_items]
        video_details = fetch_video_details_batch(youtube, video_ids)

        for item in playlist_items:
            video_id = item["contentDetails"]["videoId"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_data = video_details.get(video_id)

            if not video_data:
                print(f"No details found for video {video_id}")
                unavailable_video_data.append({"video_id": video_id, "playlist_item_id": item["id"]})
                continue

            all_playlist_videos.append({
                "video_id": video_id,
                "video_url": video_url,
                "video_title": video_data["title"],
                "video_category": categories.get(video_data["categoryId"], "Unknown"),
                "playlist_item_id": item["id"]
            })

        return (True, {
            "all_playlist_videos": all_playlist_videos,
            "unavailable_video_data": unavailable_video_data
        })
    except Exception as e:
        print(f"Error retrieving playlist {playlist_id} contents:\n{e}\n")
        return (False, None)

def fetch_video_details_batch(youtube, video_ids):
    video_details = {}
    try:
        def batch_callback(request_id, response, exception):
            if exception:
                print(f"Error retrieving video details for {request_id}: {exception}")
            else:
                video_details[request_id] = response['items'][0]['snippet']

        # Creating the batch request to fetch video details
        batch = youtube.new_batch_http_request(callback=batch_callback)

        # Process video_ids in chunks of 50
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i + 50]  # Chunk of 50 video IDs
            for video_id in batch_ids:
                # Add video request to the batch
                batch.add(
                    youtube.videos().list(part="snippet", id=video_id),
                    request_id=video_id  # Pass the video ID as the request ID
                )

            # Execute the batch request after adding the 50 video details fetch operations
            try:
                batch.execute()
            except Exception as e:
                print(f"Error executing batch request: {e}")

            # Clear the batch to prepare for the next batch
            batch = youtube.new_batch_http_request(callback=batch_callback)
            
    except Exception as e:
        print(f"Error retrieving batch video details:\n{e}\n")
    return video_details

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
        "failed": failed,
        "video_additions_total": len(video_additions),
        "already_in_playlist_total": len(already_in_playlist),
        "failed_total": len(failed)
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
        "failed": failed,
        "video_removals_total": len(video_removals),
        "not_in_playlist_total": len(not_in_playlist),
        "failed_total": len(failed)
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