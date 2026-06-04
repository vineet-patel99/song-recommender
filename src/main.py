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

def _fetch_lastfm_data(params):
    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

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
        if not isinstance(track, dict):
            continue

        name = track.get("name") or track.get("title") or track.get("track")
        artist = track.get("artist")
        if isinstance(artist, dict):
            artist_name = artist.get("name") or artist.get("text") or artist.get("#text")
        else:
            artist_name = artist

        if name and artist_name:
            results.append({"name": str(name).strip(), "artist": str(artist_name).strip()})
    return results

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
    
    return _extract_track_entries(data)
        
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
        
    except Exception as e:
        print(f"error fetching the recommendations: {e}")
    
    return _extract_track_entries(data)




#testing area
data = parseTrackInfo("https://music.youtube.com/watch?v=4jBYUm3ux-I")

print(get_similar_by_song(data))

