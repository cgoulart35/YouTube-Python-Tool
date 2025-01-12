import json
import sys
from datetime import datetime
from operations import operations

def bulk_videos_playlist_workflow(youtube, videos_at_hand_label, playlist_function):
    urls = sys.argv[1].split(',')
    playlist_url = sys.argv[2]
    force = '-force' in sys.argv or '-f' in sys.argv
    preview_only = '-previewonly' in sys.argv or '-p' in sys.argv

    videos_at_hand = []
    for url in urls:
        videos_at_hand.extend(operations.get_video_info_from_url(youtube, url))
    videos_at_hand = list(set(videos_at_hand))

    input_data = {
        "playlist_url": playlist_url,
        videos_at_hand_label: videos_at_hand
    }

    if not force or preview_only:
        preview_data = playlist_function(youtube, videos_at_hand, playlist_url, is_preview=True)
        preview_contents = {
            "input_data": input_data,
            "preview_data": preview_data
        }

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

    result_data = playlist_function(youtube, videos_at_hand, playlist_url, is_preview=False)
    result_contents = {
        "input_data": input_data,
        "result_data": result_data
    }
    save_json(result_contents, "result", "Operation completed. Result saved to: ")


def save_json(data, prefix, message):
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{prefix}-{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"{message} {filename}")