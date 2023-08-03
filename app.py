from flask import Flask, render_template,request
import os
import re
from dotenv import load_dotenv
import requests
import spotipy
from pytube import YouTube
from spotipy.oauth2 import SpotifyClientCredentials
import urllib.request
from moviepy.editor import *
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import time
import shutil
from rich.console import Console


app = Flask(__name__)
app.static_folder = 'static'
@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/results", methods = ['POST', "GET"])
def result():

    output = request.form.to_dict()
    
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    client_credentials_manager = SpotifyClientCredentials( client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
    global sp, Song_url
    Song_url = output["Song_url"]
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    main()
    return render_template("endpage.html")
    
    


def main():
    url = validate_url(Song_url.strip())
    if "track" in url:
        songs = [track_data(url)]
    elif "playlist" in url:
        songs = playlist_data(url)
    
    start = time.time()
    downloaded = 0
    for i, track_info in enumerate(songs, start= 1):
        search_term = f"{track_info['artist_name']} {track_info['track_title']} audio"
        video_link = find_on_youtube(search_term)
        console.print(
                f"[magenta]({i}/{len(songs)})[/magenta] Downloading '[cyan]{track_info['artist_name']} - {track_info['track_title']}[/cyan]'..."
        )
        audio = download_vid(video_link)
        if audio:
            set_metadata(track_info, audio)
            os.replace(audio, f"../music/{os.path.basename(audio)}")
            console.print(
                    "[blue]______________________________________________________________________"
                )
            downloaded+=1

        
        shutil.rmtree(f"../music/temp")
        end = time.time()
        os.chdir(f"../music")
        print(f"Download Location: {os.getcwd()}")
        
        console.print(
            f"Download Complete: {downloaded}/{len(songs)} song(s) downloaded".center(70, " "), style="on green"
        )
        console.print(
            f"Total time taken: {round(end- start)} sec".center(70, " "),style="on white"
        )        










def validate_url(sp_url):
    if re.search(r"^(https?://)?open\.spotify\.com/playlist|track.+$", sp_url):
        return sp_url
    

def track_data(track_url):
    req = requests.get(track_url)
    if req.status_code != 200:
        return render_template("error_url.html")
    
    track = sp.track(track_url)
    track_metadata = {
        "artist_name": track["artists"][0]["name"],
        "track_title": track["name"],
        "track_number": track["track_number"],
        "isrc": track["external_ids"]["isrc"],
        "album_art": track["album"]["images"][1]["url"],
        "album_name": track["album"]["name"],
        "release_date": track["album"]['release_date'],
        "artists": [artist["name"] for artist in track["artists"]]
    }
    return track_metadata

def playlist_data(playlist_url):
    req = requests.get(playlist_url)
    if req.status_code != 200:
        return render_template("error_page.html")
    
    pl = sp.playlist(playlist_url)
    if not pl["public"]:
        return render_template("error_private_playlist.html")
    
    playlist = sp.playlist_tracks(playlist_url)
    tracks = [item["track"] for item in playlist["items"]]
    tracks_info = []
    for track in tracks:
        track_url = f"https://open.spotify.com/track/{track['id']}"
        track_info = track_data(track_url)
        tracks_info.append(track_info)

    return tracks_info


def find_on_youtube(query):
    phrase = query.replace(" ", "+")
    search_link = f"https://www.youtube.com/results?search_query=" + phrase

    cnt = 0
    while cnt<3:
        try:
            response = urllib.request.urlopen(search_link)
            break
        except:
            cnt+=1

    else:
        return render_template("error_network.html")
    
    search_result = re.findall(r"watch\?v=(\S{11})", response.read().decode())
    first_vid = f"https://www.youtube.com/watch?v="+ search_result[0]

    return first_vid


def download_vid(yt_link):
    yt = YouTube(yt_link)
    yt.title = "".join([c for c in yt.title if c not in ['/', '\\', '|', '?', '*', ':', '>', '<', '"']])

    #download the music
    video = yt.streams.filter(only_audio=True).first()
    vid_file = video.download(output_path="../music/temp")
    
    #convert video to mp3
    base = os.path.splitext(vid_file)[0]
    audio_file = base + ".mp3"
    mp4_no_frame = AudioFileClip(vid_file)
    mp4_no_frame.write_audiofile(audio_file, logger = None)
    mp4_no_frame.close()
    os.remove(vid_file)
    os.replace(audio_file, f"../music/temp/{yt.title}.mp3")
    audio_file = f"../music/temp/{yt.title}.mp3"

    return audio_file

def set_metadata(metadata, file_path):
    mp3file = EasyID3(file_path)

    mp3file["albumartist"] = metadata["artist_name"]
    mp3file["artist"] = metadata["artists"]
    mp3file["album"] = metadata["album_name"]
    mp3file["title"] = metadata["track_title"]
    mp3file["date"] = metadata["release_date"]
    mp3file["tracknumber"] = str(metadata["track_number"])
    mp3file["isrc"] = metadata["isrc"]
    mp3file.save()

    audio = ID3(file_path)
    with urllib.request.urlopen(metadata["album_art"]) as albumart:
        audio["APIC"] = APIC(
            encoding = 3, mime = "image/jpeg", type = 3, desc = "Cover", data = albumart.read()
        )
    audio.save(v2_version= 3)

if __name__ == '__main__':
    console = Console()
    load_dotenv()
    app.run(debug = True, port = 5001)