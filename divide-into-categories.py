import sys

from auth import auth
from workflows import workflows

def main():
    if len(sys.argv) < 2:
        print("Usage: python divide-into-categories.py <comma_separated_video_or_playlist_urls_to_divide> [-force] [-previewonly] [-name]")
        sys.exit(1)

    youtube = auth.get_authenticated_service()
    workflows.divide_into_categories_workflow(youtube)

if __name__ == "__main__":
    main()