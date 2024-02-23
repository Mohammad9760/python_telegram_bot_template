import re
import requests
import asyncio
from ytmusicapi import YTMusic
from bs4 import BeautifulSoup

YOUTUBE_URL_PATTERN = r'https://music\.youtube\.com/watch\S+'
SPOTIFY_URL_PATTERN = r'https://open\.spotify\.com\S+'

def extract_singer_and_track_from_spotify(spotify_link):

    # scrapes the track name and artist name from Spotify page
    response = requests.get(spotify_link)
    soup = BeautifulSoup(response.content, 'html.parser')
    singer = soup.find_all('a', href=lambda href: href and href.startswith('/artist/'))[0].text
    song = soup.find_all('h1')[0].text

    return song, singer



def process_input(message):

    # check if the message contains a Spotify link
    links = re.findall(SPOTIFY_URL_PATTERN, message)
    if links:
        return extract_singer_and_track_from_spotify(links[0])
    
    links = re.findall(YOUTUBE_URL_PATTERN, message)
    if links:
        return message[34:]

    return find_results(message)



ytmusic = YTMusic()

def find_results(query):

    # return a list of tuples with title and id
    results = [('"{}" - {} \n'.format(result['title'], result['artists'][0]['name']), result['videoId']) for result in ytmusic.search(query, 'songs')]

    return results


def get_song_id(track_name, artist_name):
    
    # retrieve the Youtube id that we then use to download the song
    return ytmusic.search(f"{artist_name} {track_name}", 'songs', limit=1)[0]['videoId']


def get_genre(artist, album):
    url = f'https://getgenre.com/artist/{artist}/album/{album}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    print(soup)


def find_meta_data(id):

    meta_data = {}
    playlist = ytmusic.get_watch_playlist(id)
    
    
    try: # to get lyrics
        lyrics = ytmusic.get_lyrics(playlist["lyrics"])
        meta_data['lyrics'] = str(lyrics.get('lyrics'))
    except Exception: # don't try to catch the particular exception this is fine
        pass
    
    try: # to get released year and album name
        album = ytmusic.get_album(playlist['tracks'][0]['album']['id'])
        meta_data['year'] = str(album['year'])
        meta_data['album'] = str(album['title'])
    except KeyError:
        pass
    
    song = ytmusic.get_song(playlist['tracks'][0].get('videoId'))
    try: # to get the cover image url
        cover = song["videoDetails"]["thumbnail"]["thumbnails"][0]
        meta_data['cover_art_url'] = cover.get('url')[:-15]
    except Exception:
        pass

    meta_data['title'] = song['videoDetails']['title']
    meta_data['artist'] = song['videoDetails']['author']

    # get_genre(meta_data['artist'], meta_data['album'])

    return meta_data
