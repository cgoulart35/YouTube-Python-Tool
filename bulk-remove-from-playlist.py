import sys

from auth import auth
from workflows import workflows
from operations import operations

def main():
    if len(sys.argv) < 3:
        print("Usage: python bulk-remove-from-playlist.py <comma_separated_video_or_playlist_urls_to_remove> <playlist_url_to_remove_from> [-force] [-previewonly]")
        sys.exit(1)

    youtube = auth.get_authenticated_service()
    workflows.bulk_videos_playlist_workflow(youtube, videos_at_hand_label="videos_to_remove", playlist_function=operations.remove_videos_from_playlist)

if __name__ == "__main__":
    main()