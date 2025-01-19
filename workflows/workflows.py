import re
import sys
from operations import operations
from workflows import common

def bulk_videos_playlist_workflow(youtube, videos_at_hand_label, playlist_function):
    print("Calculating...")
    urls = re.sub(r'\s+', '', sys.argv[1]).split(',')
    playlist_url = sys.argv[2]
    flags = common.get_command_flags()

    categories = operations.get_video_categories(youtube)

    destination_playlist_data = common.get_videos_at_hand(youtube, [playlist_url], categories)
    if len(destination_playlist_data["unavailable_playlist_ids"]) > 0:
        print("Please provide a valid playlist URL to modify.")
        sys.exit(1)
    destination_playlist_videos = {}
    destination_playlist_videos.update(destination_playlist_data["videos_at_hand"])
    destination_playlist_videos.update(destination_playlist_data["unavailable_videos"])

    videos_at_hand = common.get_videos_at_hand(youtube, urls, categories)
    input_data = {
        "playlist_url": playlist_url,
        videos_at_hand_label: list(videos_at_hand["videos_at_hand"].values()),
        "unavailable_videos": list(videos_at_hand["unavailable_videos"].values()),
        "unavailable_playlist_ids": videos_at_hand["unavailable_playlist_ids"],
        videos_at_hand_label + "_total": len(list(videos_at_hand["videos_at_hand"].values())),
        "unavailable_videos_total": len(list(videos_at_hand["unavailable_videos"].values())),
        "unavailable_playlist_ids_total": len(videos_at_hand["unavailable_playlist_ids"]),
    }

    if not flags['force'] or flags['previewonly']:
        preview_data = playlist_function(youtube, videos_at_hand["videos_at_hand"], playlist_url, destination_playlist_videos, is_preview=True)
        preview_contents = {
            "input_data": input_data,
            "preview_data": preview_data
        }
        common.finish_preview_workflow(preview_contents, flags['previewonly'])

    result_data = playlist_function(youtube, videos_at_hand["videos_at_hand"], playlist_url, destination_playlist_videos, is_preview=False)
    result_contents = {
        "input_data": input_data,
        "result_data": result_data
    }
    common.save_json(result_contents, "result", "Operation completed. Result saved to: ")

def divide_into_categories_workflow(youtube):
    print("Calculating...")
    urls = re.sub(r'\s+', '', sys.argv[1]).split(',')
    flags = common.get_command_flags()

    default_playlist_name = None
    if len(urls) == 1 and "playlist" in urls[0]:
        playlist_data = operations.get_single_playlist_data(youtube, urls[0])
        if playlist_data != None:
            default_playlist_name = playlist_data["title"]        

    categories = operations.get_video_categories(youtube)

    videos_at_hand = common.get_videos_at_hand(youtube, urls, categories)
    input_data = {
        "videos_to_categorize": list(videos_at_hand["videos_at_hand"].values()),
        "unavailable_videos": list(videos_at_hand["unavailable_videos"].values()),
        "unavailable_playlist_ids": videos_at_hand["unavailable_playlist_ids"],
        "videos_to_categorize_total": len(list(videos_at_hand["videos_at_hand"].values())),
        "unavailable_videos_total": len(list(videos_at_hand["unavailable_videos"].values())),
        "unavailable_playlist_ids_total": len(videos_at_hand["unavailable_playlist_ids"])
    }

    categories_data = common.categorize_videos(videos_at_hand["videos_at_hand"])
    playlist_names = {}
    if not flags['force'] or flags['previewonly']:
        playlists_creations_preview = []
        for category, videos in categories_data.items():
            playlist_name = common.get_playlist_name(category, default_playlist_name, flags['name'])
            playlist_names[category] = playlist_name
            playlist_preview_data = operations.add_videos_to_playlist(youtube, videos, playlist_url=None, destination_playlist_videos=[], is_preview=True)
            playlists_creations_preview.append({
                "playlist_name": playlist_name,
                "playlist_preview_data": playlist_preview_data
            })
        preview_data = {
            "no_actions": len(playlists_creations_preview) == 0,
            "playlists_creations": playlists_creations_preview,
            "playlists_creations_total": len(playlists_creations_preview)
        }
        preview_contents = {
            "input_data": input_data,
            "preview_data": preview_data
        }
        common.finish_preview_workflow(preview_contents, flags['previewonly'])

    playlists_creations = []
    failed = []
    for category, videos in categories_data.items():
        if category in playlist_names:
            playlist_name = playlist_names[category]
        else:
            playlist_name = common.get_playlist_name(category, default_playlist_name, flags['name'])
        playlist = operations.create_playlist(youtube, playlist_name)
        if not playlist [0]:
            failed.append({
                "playlist_name": playlist_name,
                "videos_not_categorized": videos
            })
            continue

        playlist_result_data = operations.add_videos_to_playlist(youtube, videos, playlist[1]["playlist_url"], destination_playlist_videos=[], is_preview=False)
        playlists_creations.append({
            "playlist_name": playlist_name,
            "playlist_id": playlist[1]["playlist_id"],
            "playlist_url": playlist[1]["playlist_url"],
            "playlist_result_data": playlist_result_data
        })
    result_data = {
        "no_actions": len(playlists_creations) == 0,
        "playlists_creations": playlists_creations,
        "failed": failed,
        "playlists_creations_total": len(playlists_creations),
        "failed_total": len(failed),
    }
    result_contents = {
        "input_data": input_data,
        "result_data": result_data
    }
    common.save_json(result_contents, "result", "Operation completed. Result saved to: ")