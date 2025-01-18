import json
import re
import sys
from datetime import datetime
from operations import operations

def get_command_flags():
    return {
        "force": '-force' in sys.argv or '-f' in sys.argv,
        "previewonly": '-previewonly' in sys.argv or '-p' in sys.argv,
        "name": '-name' in sys.argv or '-n' in sys.argv
    }

def clean_data(data):
    if isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items() if v not in [None, [], "", 0]}
    elif isinstance(data, list):
        return [clean_data(item) for item in data if item not in [None, [], "", 0]]
    else:
        return data

def save_json(data, prefix, message):
    cleaned_data = clean_data(data)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{prefix}-{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(cleaned_data, f, indent=4)
    print(f"{message} {filename}")

def finish_preview_workflow(preview_contents, preview_only):
    save_json(preview_contents, "preview", "Preview generated. Please review: ")
    if preview_only:
        print("Exiting due to -previewonly flag.")
        sys.exit(0)
    if preview_contents["preview_data"]["no_actions"] == True:
        print("Exiting with no operations to execute.")
        sys.exit(0)
    
    user_input = input("Do you want to proceed? (yes/no): ")
    if user_input.lower() != 'yes' and user_input.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)

def get_videos_at_hand(youtube, urls, categories):
    videos_at_hand = {}
    unavailable_video_data = {}
    unavailable_playlist_ids = set()

    # Get video details from video or playlist URLs
    for url in urls:
        if "playlist" in url:
            try: 
                playlist_id = re.search(r"list=([^&]+)", url).group(1)
            except Exception as e:
                print(f"Invalid playlist URL provided: {url}")
                unavailable_playlist_ids.add(url)
                continue

            all_playlist_videos = operations.get_all_playlist_video_data(youtube, playlist_id, categories)

            # If failed to retrieve playlist contents, skip to the next URL
            if not all_playlist_videos[0]:
                unavailable_playlist_ids.add(playlist_id)
                continue

            # If there are unavailable videos in the playlist, save their IDs for later
            if len(all_playlist_videos[1]["unavailable_video_data"]) > 0:
                for video in all_playlist_videos[1]["unavailable_video_data"]:
                    unavailable_video_data[video["video_id"]] = {
                        "video_id": video["video_id"],
                        "playlist_item_id": video["playlist_item_id"]
                    }

            # Add available videos to the list of videos at hand
            for video in all_playlist_videos[1]["all_playlist_videos"]:
                videos_at_hand[video["video_id"]] = {
                    "video_id": video["video_id"],
                    "video_url": video["video_url"],
                    "video_title": video["video_title"],
                    "video_category": video["video_category"],
                    "playlist_item_id": video["playlist_item_id"]
                }
        else:
            try: 
                video_id = re.search(r"v=([^&]+)", url).group(1)
            except Exception as e:
                print(f"Invalid video URL provided: {url}")
                unavailable_video_data[url] = {
                    "video_id": url,
                    "playlist_item_id": None
                }
                continue
            
            # Get video details missing from the playlist response
            video_details = operations.get_single_video_data(youtube, video_id)

            # If videos is unavailable, save ID for later
            if not video_details[0]:
                unavailable_video_data[video_id] = {
                    "video_id": video_id,
                    "playlist_item_id": None
                }
                continue

            # Add available videos to the list of videos at hand
            videos_at_hand[video_id] = {
                "video_id": video_id,
                "video_url": url,
                "video_title": video_details["title"],
                "video_category": categories.get(video_details["categoryId"], "Unknown")
            }

    return {
        "videos_at_hand": videos_at_hand,
        "unavailable_videos": unavailable_video_data,
        "unavailable_playlist_ids": list(unavailable_playlist_ids),
    }

def categorize_videos(videos_at_hand):
    categories = {}
    for video_id in videos_at_hand:
        video = videos_at_hand[video_id]
        category = video["video_category"]
        if category not in categories:
            categories[category] = {}
        categories[category][video_id] = video
    return categories

def get_playlist_name(category, default_playlist_name, use_auto_names):
    auto_name = get_default_playlist_name(default_playlist_name, category)
    if use_auto_names:
        return auto_name
    else:
        return input(f"Enter playlist name for category '{category}' (or press Enter to use auto-generated name '{auto_name}'): ") or auto_name

def get_default_playlist_name(default_playlist_name, category):
    if default_playlist_name is not None:
        return f"{default_playlist_name}_{category}"
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        return f"{category}_{timestamp}"