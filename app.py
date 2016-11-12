import os, sys
import random, math
from flask import Flask, render_template, request, redirect, url_for, session
import spotipy
from spotipy import oauth2
import spotipy.util as util
import lyrics as Lyrics
import tone as tone
import numpy as np
from operator import itemgetter

def getAllTracks(sp):
    tracks = []

    SONGS_PER_TIME = 50
    offset=0

    while True:
        SPTracks = sp.current_user_saved_tracks(limit=SONGS_PER_TIME, offset=offset) 

        if len(SPTracks["items"]) == 0:
        #if offset >= 50:
            break

        for song in SPTracks["items"]:
            track = song["track"]
            song_item = (track["name"], track["artists"][0]["name"], track["uri"])
            tracks.append(song_item)

        offset += SONGS_PER_TIME

    return tracks


def generateRandomString(length): 
    text = '';
    possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

    for i in range(length):
        text += possible[int(math.floor(random.random() * len(possible)))]

    return text


# global variables
PORT_NUMBER = int(os.environ.get('PORT', 8888))
SPOTIPY_CLIENT_ID = '05f9f3eed587428a83af4ba630bba08c'
SPOTIPY_CLIENT_SECRET = 'fd20b73ca2ae47aab8172982417bbdd2'

PRODUCTION = False

if PRODUCTION:
    SPOTIPY_REDIRECT_URI = 'https://hello.herokuapp.com/callback'
else:
    SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'

SCOPE = 'user-library-read playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private'
CACHE = '.spotipyoauthcache'

STATE = generateRandomString(16)
NUM_SONGS = 5

sp_oauth = oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,
                               state=STATE,scope=SCOPE,cache_path=CACHE)

# initialization
app = Flask(__name__)
app.config.update(
    DEBUG=True,
)


# controllers
@app.route('/')
@app.route('/index')
def index():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')

    if code and state == STATE:
        token = sp_oauth.get_access_token(code)
        session["TOKEN"] = token
        # auth_url = sp_oauth.get_authorize_url()
        # return render_template(auth_url)
        return redirect(url_for('logic'))
    else:
        return 'gg'


@app.route('/logic')
def logic():
    """Performs the logic for determining which songs to take

    gets the first 20 saved songs from the user's spotify library.
    Performs tone analysis on the songs and pciks the scores which
    are closes to the users mood. Each songs gets an array of values for each
    emotion and the logic sorts songs on arrays are closest to the users. Gets
    a list of their uri and a list of (song name, artist).

    """
    token = session["TOKEN"]
    access_token = token["access_token"]
    sp = spotipy.Spotify(auth=access_token)
    
    # Hard coding for now, but we'll add user input
    user_mood = np.array([0, 1, 0, 0, 0])

    # get all songs
    our_tracks = getAllTracks(sp)
    
    # choose 100 songs at random
    if len(our_tracks) > 100:
        random.shuffle(our_tracks)
        our_tracks = our_tracks[0:100]
    # get the lyrics for all songs
    song_lyrics = []
    for song in our_tracks:
        lyrics = Lyrics.get_lyrics(song[0], song[1])
        if lyrics != '':
            song_lyrics.append((song[2], lyrics))

    # get the emotion scores of all songs
    emotion_by_song = tone.get_all_emotions(song_lyrics)

    # rank the songs
    song_rankings = []
    for song_data in emotion_by_song:
        feeling = song_data[1]
        difference = np.linalg.norm(user_mood - feeling)
        song_rankings.append((song_data[0], difference))

    song_rankings = sorted(song_rankings, key=itemgetter(1))

   # get the top 5 results
    results = []
    result_info = []
    for i in range(min(NUM_SONGS, len(song_rankings))):
        results.append(song_rankings[i][0])

    result_tracks = sp.tracks(results)
    print 'hello'
    # print result_tracks['tracks']
    # get names and artists of those songs
    for track in result_tracks['tracks']:
        # track = result['track']
        result_info.append((track['name'], track['artists'][0]['name']))

    print result_info

    return render_template("index.html")

    # if code:
    #     token = sp_oauth.get_access_token(code)
    #     session["TOKEN"] = token
    # token = sp_oauth.get_access_token(code)

    # auth_url = sp_oauth.get_authorize_url()
    # return render_template("index.html", auth_url=auth_url)


# launch
if __name__ == '__main__':
    app.secret_key = generateRandomString(16)
    app.run(host='0.0.0.0', port=PORT_NUMBER, debug=True)
