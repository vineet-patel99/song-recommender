import requests
import os
from dotenv import load_dotenv
    
load_dotenv()
api_key = os.getenv("API_KEY")
base_url = 'http://ws.audioscrobbler.com/2.0/?method' #base url used when fetching last.fm data
songList = dict()
# parseTrackInfo(link: string) -> dict[str, str] | None
#takes in a string and returns a dictionary containing two values
def parseTrackInfo(link):
    """Parse a Spotify or YouTube link and extract song title and artist.

    Parameters:
    - link (str): A URL pointing to a Spotify track or YouTube (music) video.

    Returns:
    - dict: {'name': <song title>, 'artist': <artist name>} when parsing succeeds.
    - None: if the link is not a supported provider or parsing fails.
    """
    # seeing if the link is either from spotify or youtube
    # using https://open.spotify.com/track/3qRJbfpuFtfezml4hnNUgw?si=264e6980c47745e5 as test for spotify
    # using https://www.youtube.com/watch?v=HYLxs7Gonac&list=RDHYLxs7Gonac&start_radio=1 as a test for yt
    from urllib.parse import quote_plus

    spotifyIdentifier = "https://open.spotify.com/track"
    youtubeIdentifier1 = "https://www.youtube.com" #used for regular youtube music videos
    youtubeIdentifier2 = "https://music.youtube.com" #used for youtube music tracks

    if spotifyIdentifier in link:
        response = requests.get(
            f"https://open.spotify.com/oembed?url={quote_plus(link)}",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return {"name": data.get("title", ""), "artist": data.get("author_name", "")}

    if youtubeIdentifier1 in link or youtubeIdentifier2 in link:
        response = requests.get(
            f"https://www.youtube.com/oembed?url={quote_plus(link)}&format=json",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        title = data.get("title", "")
        artist_name = data.get('author_name', '')
        if " - Topic" in artist_name:
            artist_name = artist_name[0:artist_name.find(' - Topic')] 
        if " by " in title:
            song_name, artist_name = title.split(" by ", 1)
        elif " - " in title:
            song_name, artist_name = title.split(" - ", 1)
        elif " | " in title:
            song_name, artist_name = title.split(" | ", 1)
        else:
            song_name, artist_name = title, artist_name

        return {"name": song_name.strip(), "artist": artist_name.strip()}

    return None

def fetch_lastfm_data(params):
    """Fetch JSON data from the Last.fm API using provided query parameters.

    Parameters:
    - params (dict): Query parameters to include in the GET request.

    Returns:
    - dict: Parsed JSON response from the API.

    Raises:
    - requests.HTTPError: If the HTTP request returned an unsuccessful status.
    """
    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def get_song_info(song):

    url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&artist={song["artist"]}&track={song["name"]}&format=json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    images = data.get("track", {}).get("album", {}).get("image", [])
    if isinstance(images, dict):
        images = [images]

    return next(
        (image for image in images if image.get("size") == "extralarge"),
        images[0] if images else {},
    )

    


'''
takes in .json data and parses it into a dictionary containing each song's name and artist
- need to get the album cover data as well as most used color in the album cover to generate
a proper "card" for the app/website
'''
def extract_track_entries(data):
    """Extract a normalized list of track dictionaries from various Last.fm response shapes.

    Parameters:
    - data (dict): Raw JSON response from Last.fm that may contain tracks in different keys.

    Returns:
        - list[dict]: Each item is {'name': <track name>, 'artist': <artist name>,
            'image': <album cover URL>}.
    """
    container = (
        data.get("tracks")
        or data.get("toptracks")
        or data.get("similartracks")
        or data.get("results", {}).get("trackmatches")
        or {}
    )
    track_list = container.get("track", []) if isinstance(container, dict) else []
    if isinstance(track_list, dict):
        track_list = [track_list]

    results = []
    for track in track_list:
        if not isinstance(track, dict):
            continue

        name = track.get("name") or track.get("title") or track.get("track")
        artist = track.get("artist")
        if isinstance(artist, dict):
            artist_name = artist.get("name") or artist.get("text") or artist.get("#text")
        else:
            artist_name = artist

        if name and artist_name:
            song = {"name": str(name).strip(), "artist": str(artist_name).strip()}
            image = get_song_info(song)
            results.append({**song, "image": image.get("#text", "")})
    return results

def get_similar_by_song(song):
    """Get tracks similar to a given song using Last.fm's track.getSimilar method.

    Parameters:
    - song (dict): A dictionary with keys 'name' and 'artist'.

    Returns:
    - list[dict]: Normalized list of similar tracks with 'name' and 'artist'.
    """

    if not song:
        return []

    params = {
        'method': 'track.getSimilar',
        'artist': song['artist'],
        'track': song['name'],
        'limit': 5,
        'api_key': api_key,
        'format': 'json'        
    }
    data = {}
    try:
        data = fetch_lastfm_data(params)
        
    except Exception as e:
        print(f"error fetching the recommendations: {e}")
    
    return extract_track_entries(data)