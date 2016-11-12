import os, sys
import random, math
from flask import Flask, render_template, request, redirect, url_for, session
import spotipy
from spotipy import oauth2
import spotipy.util as util


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
    token = session["TOKEN"]
    access_token = token["access_token"]

    sp = spotipy.Spotify(auth=access_token)

    tracks = sp.getAllTracks(sp)

    print tracks

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
