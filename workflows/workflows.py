import json
import sys
from datetime import datetime
from operations import operations

def save_json(data, prefix, message):
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{prefix}-{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"{message} {filename}")

def finish_preview_workflow(preview_contents, preview_only, preview_data):
    save_json(preview_contents, "preview", "Preview generated. Please review: ")
    if preview_only:
        print("Exiting due to -previewonly flag.")
        sys.exit(0)
    if preview_data["no_actions"] == True:
        print("Exiting with no operations to execute.")
        sys.exit(0)
    
    user_input = input("Do you want to proceed? (yes/no): ")
    if user_input.lower() != 'yes' and user_input.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)

def get_videos_at_hand(youtube, urls, categories):
    videos_at_hand = []
    seen_video_ids = set()
    
    for url in urls:
        video_info = operations.get_video_info_from_url(youtube, url, categories)
        for video in video_info:
            video_id = video['video_id']
            if video_id not in seen_video_ids:
                seen_video_ids.add(video_id)
                videos_at_hand.append(video)
    
    return videos_at_hand

def bulk_videos_playlist_workflow(youtube, videos_at_hand_label, playlist_function):
    urls = sys.argv[1].split(',')
    playlist_url = sys.argv[2]
    force = '-force' in sys.argv or '-f' in sys.argv
    preview_only = '-previewonly' in sys.argv or '-p' in sys.argv

    categories = operations.get_video_categories(youtube)
    videos_at_hand = get_videos_at_hand(youtube, urls, categories)
    input_data = {
        "playlist_url": playlist_url,
        videos_at_hand_label: videos_at_hand
    }

    if not force or preview_only:
        preview_data = playlist_function(youtube, videos_at_hand, playlist_url, is_preview=True, categories=categories)
        preview_contents = {
            "input_data": input_data,
            "preview_data": preview_data
        }
        finish_preview_workflow(preview_contents, preview_only, preview_data)

    result_data = playlist_function(youtube, videos_at_hand, playlist_url, is_preview=False, categories=categories)
    result_contents = {
        "input_data": input_data,
        "result_data": result_data
    }
    save_json(result_contents, "result", "Operation completed. Result saved to: ")

def get_default_playlist_name(default_playlist_name, category):
    if default_playlist_name is not None:
        return f"{default_playlist_name}_{category}"
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        return f"{category}_{timestamp}"

def get_playlist_name(category, default_playlist_name, use_auto_names):
    auto_name = get_default_playlist_name(default_playlist_name, category)
    if use_auto_names:
        return auto_name
    else:
        return input(f"Enter playlist name for category '{category}' (or press Enter to use auto-generated name '{auto_name}'): ") or auto_name

def categorize_videos(videos_at_hand):
    categories = {}
    for video in videos_at_hand:
        category = video["video_category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(video)
    return categories

def divide_into_categories_workflow(youtube):
    urls = sys.argv[1].split(',')
    force = '-force' in sys.argv or '-f' in sys.argv
    preview_only = '-previewonly' in sys.argv or '-p' in sys.argv
    use_auto_names = '-name' in sys.argv or '-n' in sys.argv

    default_playlist_name = operations.get_single_playlist_name(youtube, urls)
    categories = operations.get_video_categories(youtube)
    videos_at_hand = get_videos_at_hand(youtube, urls, categories)
    categories_data = categorize_videos(videos_at_hand)

    playlist_names = {}
    if not force or preview_only:
        preview_contents = []
        for category, videos in categories_data.items():
            playlist_name = get_playlist_name(category, default_playlist_name, use_auto_names)
            playlist_names[category] = playlist_name
            preview_data = operations.add_videos_to_playlist(youtube, videos, playlist_url=None, is_preview=True, categories=categories)
            preview_contents.append({
                "playlist_name": playlist_name,
                "preview_data": preview_data
            })
        finish_preview_workflow(preview_contents, preview_only, preview_data)

    result_contents = []
    for category, videos in categories_data.items():
        if category in playlist_names:
            playlist_name = playlist_names[category]
        else:
            playlist_name = get_playlist_name(category, default_playlist_name, use_auto_names)
        playlist = operations.create_playlist(youtube, playlist_name)
        result_data = operations.add_videos_to_playlist(youtube, videos, playlist[1], is_preview=False, categories=categories)
        result_contents.append({
            "playlist_name": playlist_name,
            "playlist_id": playlist[0],
            "playlist_url": playlist[1],
            "result_data": result_data
        })
    save_json(result_contents, "result", "Operation completed. Result saved to: ")