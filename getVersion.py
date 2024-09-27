import requests
# GitHub releases URL
RELEASES_URL = "https://api.github.com/repos/music-bot-development/music-bot/releases/latest"


def fetch_latest_release():
    """Fetch the latest release version from GitHub."""
    try:
        response = requests.get(RELEASES_URL)
        response.raise_for_status()
        release_data = response.json()
        return release_data["tag_name"]  # Assuming the version is in the 'tag_name' field
    except (requests.RequestException, KeyError) as e:
        print(f"Error fetching the latest release: {e}")
        return "Unknown version"
