import sys

from auth import auth
from workflows import workflows
from operations import operations

def main():
    if len(sys.argv) < 3:
        print("Usage: python bulk-add-to-playlist.py <comma_separated_video_or_playlist_urls_to_add> <playlist_url_to_add_to> [-force] [-previewonly]")
        sys.exit(1)

    youtube = auth.get_authenticated_service()
    workflows.bulk_videos_playlist_workflow(youtube, videos_at_hand_label="videos_to_add", playlist_function=operations.add_videos_to_playlist)

if __name__ == "__main__":
    main()