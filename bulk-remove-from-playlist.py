import sys

from auth import auth
from operations import operations

def main():
    if len(sys.argv) != 3:
        print("Usage: python bulk-remove-from-playlist.py <comma_separated_video_or_playlist_urls_to_remove> <playlist_url_to_remove_from>")
        sys.exit(1)
    
    urls = sys.argv[1].split(',')
    playlist_url = sys.argv[2]

    youtube = auth.get_authenticated_service()

    video_ids_to_remove = []
    for url in urls:
        video_ids_to_remove.extend(operations.get_video_ids_from_url(youtube, url))
    video_ids_to_remove = list(set(video_ids_to_remove))

    operations.remove_videos_from_playlist(youtube, video_ids_to_remove, playlist_url)

    print("Script completed.")

if __name__ == "__main__":
    main()