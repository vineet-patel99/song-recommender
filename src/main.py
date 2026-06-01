import requests
import os
from dotenv import load_dotenv
import pandas as pd
    
load_dotenv()
api_key = os.getenv("API_KEY")
base_url = 'http://ws.audioscrobbler.com/2.0/?method'

# parseTrackInfo(link: string) -> dict[str, str] | None
#takes in a string and returns a dictionary containing two values
def parseTrackInfo(link):
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

        if " by " in title:
            song_name, artist_name = title.split(" by ", 1)
        elif " - " in title:
            song_name, artist_name = title.split(" - ", 1)
        elif " | " in title:
            song_name, artist_name = title.split(" | ", 1)
        else:
            song_name, artist_name = title, ""

        return {"name": song_name.strip(), "artist": artist_name.strip()}

    return None
    

    

def _extract_track_entries(data):
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
        name = track.get("name")
        artist = track.get("artist")
        artist_name = artist.get("name") if isinstance(artist, dict) else artist
        if name and artist_name:
            results.append({"name": name, "artist": artist_name})
    return results


# extract_trackandartist(data: dict) -> dict[str, str] | None
# extracting the data from the recs
def extract_trackandartist(data):
    tracks = _extract_track_entries(data)
    return tracks[0] if tracks else None


def _fetch_lastfm_data(params):
    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

# get_recs_by_genre(genre: str) -> list[dict[str, str]]
def get_recs_by_genre(genre):
    params = {
        'method': 'tag.getToptracks',
        'tag': genre,
        'limit': 5,
        'api_key': api_key,
        'format': 'json'        
    }
    try:
        #should follow ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag=disco&limit=5&api_key=API_KEY&format=json
        response = requests.get(base_url, params=params)
        if(response.status_code > 29):
            data=response.json()
    except Exception as e:
        print(f"error fetching the recommendations: {e}")
    
    return []
        
# get_similar_by_song(song: dict[str, str]) -> list[dict[str, str]]
def get_similar_by_song(song):
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
    try:
        data = _fetch_lastfm_data(params)
        tracks = _extract_track_entries(data)
        if tracks:
            return tracks

        fallback_params = {
            'method': 'track.search',
            'artist': song['artist'],
            'track': song['name'],
            'limit': 5,
            'api_key': api_key,
            'format': 'json'
        }
        fallback_data = _fetch_lastfm_data(fallback_params)
        return _extract_track_entries(fallback_data)
    except Exception as e:
        print(f"error fetching the recommendations: {e}")
    
    return []





print(get_similar_by_song(
    parseTrackInfo("https://www.youtube.com/watch?v=HYLxs7Gonac&list=RDHYLxs7Gonac&start_radio=1")
    ))

