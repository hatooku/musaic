import os
import sys
import random
import math
from flask import Flask, render_template, request, redirect, url_for, session
import spotipy
from spotipy import oauth2
import spotipy.util as util
import lyrics as Lyrics
import tone as tone
import numpy as np
from operator import itemgetter


def kullback_leibler(start_dist, end_dist):
    """
    Assumes start_dist, end_dist are NumPy arrays.
    Computes Kullback-Leibler divergence from start dist to end dist.
    """
    kl_vec = np.multiply(end_dist, np.log(end_dist / start_dist))

    # Gotta deal with 0 * log(0)s and such...
    for i, e in enumerate(kl_vec):
        if e == np.nan:
            kl_vec[i] = 0
    return np.sum(kl_vec)


def getAllTracks(sp):
    """
    Pulls all saved songs from user library, 50 at a time (Spotify rate limit).
    """
    tracks = []

    SONGS_PER_TIME = 50  # number of songs to request from Spotify API.
    offset = 0  # index to start song requests

    while True:
        SPTracks = sp.current_user_saved_tracks(limit=SONGS_PER_TIME,
                                                offset=offset)

        if len(SPTracks["items"]) == 0:
            break

        for song in SPTracks["items"]:
            track = song["track"]
            song_item = (track["name"], track["artists"][0]["name"], track["uri"])
            tracks.append(song_item)

        offset += SONGS_PER_TIME

    return tracks


def create_playlist(sp, list_of_uris, user, playlist_name):
    """
    Given a list of Spotify URIs and a desired playlist name, add all the songs
    specified by the URIs to a new playlist.
    """
    new_playlist = sp.user_playlist_create(user, playlist_name, public=True)['uri']
    results = sp.user_playlist_add_tracks(user, new_playlist,
                                          list_of_uris, position=None)
    return results


def generateRandomString(length): 
    text = ''
    possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

    for i in range(length):
        text += possible[int(math.floor(random.random() * len(possible)))]

    return text


# global variables
PORT_NUMBER = int(os.environ.get('PORT', 8888))
SPOTIPY_CLIENT_ID = '05f9f3eed587428a83af4ba630bba08c'
SPOTIPY_CLIENT_SECRET = 'fd20b73ca2ae47aab8172982417bbdd2'

PRODUCTION = False

if PRODUCTION:
    SPOTIPY_REDIRECT_URI = 'https://musicapp.herokuapp.com/callback'
else:
    SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'

SCOPE = 'user-library-read playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private'
CACHE = '.spotipyoauthcache'

STATE = generateRandomString(16)
NUM_SONGS = 10

sp_oauth = oauth2.SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI,
                               state=STATE, scope=SCOPE, cache_path=CACHE)

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


@app.route('/landing')
def landing():
    return render_template("index.html")


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
    
    EMOTION_IDX = {
    "anger" : 0,
    "joy" : 1,
    "fear" : 2,
    "sadness" : 3,
    "disgust" : 4
    }
    # Hard coding for now, but we'll add user input
    # user_mood = np.array([0] * 5)
    # mood = 'sadness'
    # user_mood[EMOTION_IDX[mood]] = 1
    user_mood = np.array([0.5, 0, 0, 0.5, 0])

    # get all songs
    our_tracks = getAllTracks(sp)

    # choose 100 songs at random
    if len(our_tracks) > 100:
        #random.shuffle(our_tracks)
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
        feeling = song_data[1] / np.sum(song_data[1])
        # cost = kullback_leibler(feeling, user_mood)
        # cost = kullback_leibler(user_mood, feeling)
        difference = np.linalg.norm(user_mood - feeling)
        # specific_difference = np.abs(user_mood[EMOTION_IDX[mood]] - feeling[user_mood[EMOTION_IDX[mood]]])
        # cost = difference + specific_difference
        cost = difference
        song_rankings.append((song_data[0], cost, feeling))

    song_rankings = sorted(song_rankings, key=itemgetter(1))

   # get the top 5 results
    results = []
    result_info = []
    for i in range(min(NUM_SONGS, len(song_rankings))):
        results.append(song_rankings[i][0])

    result_tracks = sp.tracks(results)

    # print song_rankings
    # print result_tracks['tracks']
    # get names and artists of those songs
    for track in result_tracks['tracks']:
        # track = result['track']
        result_info.append((track['name'], track['artists'][0]['name']))

    # print result_info

    user = "caltechcalhacks"
    playlist_name = 'testing'
    list_of_uris = ["3VvBPkc24zC7x05mgJTyGO"]
    create_playlist(sp, list_of_uris, user, playlist_name)

    return redirect(url_for('landing'))

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
