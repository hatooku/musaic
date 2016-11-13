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
from forms import *


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
@app.route('/', methods=['GET', 'POST'])


@app.route('/index', methods=['GET', 'POST'])
def index():
    auth_url = sp_oauth.get_authorize_url()
    return render_template("index.html", auth_url=auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')

    if code and state == STATE:
        token = sp_oauth.get_access_token(code)
        session["TOKEN"] = token
        return redirect('/logic')
    else:
        return 'gg'


@app.route('/mood')
def getMood():
    form_a = MoodButtons(request.form)
    form_b = MoodText(request.form)
    if form_a.is_submitted():
        mood = []
        if form_a.anger.data:
            mood  = [1, 0, 0, 0, 0]
        elif form_a.joy.data:
            mood  = [0, 1, 0, 0, 0]
        else: 
            mood  = [0, 0, 0, 1, 0]
        session['mood'] = mood
        return redirect('/logic')
    elif request.method == 'POST' and form_b.validate():
        mood = []
        session['mood'] = mood
        return redirect('/logic')
    return render_template("mood.html")

@app.route('/landing')
def landing():
    return render_template("index.html")



@app.route('/logic')
def logic():
    """
    Gets the first 20 saved songs from the user's Spotify library.
    Performs tone analysis on the songs and picks the scores which
    are closest to the user's mood.

    Each song is sent through IBM Watson Sentiment Analysis to get an encoding over
    the 5 possible emotions (anger, joy, fear, sadness, and disgust).

    We then sort songs based on how close the emotional encoding is to the user's
    desired encoding. Then for the top N songs we get a list of the URIs, and
    (song name, artist) tuples.
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
    # user_mood = session['mood']
    user_mood = np.array([0, 1, 0, 0, 0])

    # get all songs
    our_tracks = getAllTracks(sp)

    # choose 100 songs at random
    if len(our_tracks) > 100:
        # random.shuffle(our_tracks)
        our_tracks = our_tracks[0:100]

    # get the lyrics for all songs
    song_lyrics = []
    for song in our_tracks:
        lyrics = Lyrics.get_lyrics(song[0], song[1])
        if lyrics != '':
            song_lyrics.append((song[2], lyrics))

    # get the emotion scores of all songs
    emotion_by_song = tone.get_all_emotions(song_lyrics)

    # rank the songs based on closeness of emotional encoding to desired encoding
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

    # get the top N results
    results = []
    result_info = []
    for i in range(min(NUM_SONGS, len(song_rankings))):
        results.append(song_rankings[i][0])

    result_tracks = sp.tracks(results)

    for i in result_tracks['tracks']:
        # print i.keys()
        print i['uri'][12:]
        print '\n'

    session['result_tracks'] = result_tracks
   
    return redirect(url_for('result'))

    # if code:
    #     token = sp_oauth.get_access_token(code)
    #     session["TOKEN"] = token
    # token = sp_oauth.get_access_token(code)

    # auth_url = sp_oauth.get_authorize_url()
    # return render_template("index.html", auth_url=auth_url)

@app.route('/result')
def results():
    form = PlaylistButton(request.form)
    result_tracks = session['result_tracks']
    # print song_rankings
    # print result_tracks['tracks']
    # get names and artists of those songs
    for track in result_tracks['tracks']:
        # track = result['track']
        result_info.append((track['name'], track['artists'][0]['name']))

    # print result_info
    if form.is_submitted():
        print "making playlist"
        user = "caltechcalhacks"
        playlist_name = 'testing'
        list_of_uris = ["3VvBPkc24zC7x05mgJTyGO"]
        create_playlist(sp, list_of_uris, user, playlist_name)

    return render_template("results.html")

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



# launch
if __name__ == '__main__':
    app.secret_key = generateRandomString(16)
    app.run(host='0.0.0.0', port=PORT_NUMBER, debug=True)
