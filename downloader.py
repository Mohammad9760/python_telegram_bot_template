import os
import re
import urllib.request
import requests
# from yt_dlp import YoutubeDL
import music_tag
import finder

YOUTUBE_URL = "https://music.youtube.com/watch?v="


def download_song(id):
    meta_data = finder.find_meta_data(id)


    
    # return (art_work, meta_data)
    return f"{YOUTUBE_URL}{id}"
    

def download_cover_photo(url):
    try:
        path_name = "./cover.png"
        urllib.request.urlretrieve(url, path_name)
    except urllib.request.HTTPError:
        pass
    with open(path_name, 'rb') as img_in:
        art_work = img_in.read()
        return art_work