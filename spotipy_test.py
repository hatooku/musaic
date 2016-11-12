import sys
import spotipy
import spotipy.oauth2
import spotipy.util as util

creds = spotipy.oauth2.SpotifyClientCredentials(
                client_id='05f9f3eed587428a83af4ba630bba08c',
                client_secret='fd20b73ca2ae47aab8172982417bbdd2')
token = creds.get_access_token()

scope = 'user-library-read'

if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    print "Usage: %s username" % (sys.argv[0],)
    sys.exit()

token = util.prompt_for_user_token(username, scope,
                                   client_id='05f9f3eed587428a83af4ba630bba08c',
                                   client_secret='fd20b73ca2ae47aab8172982417bbdd2')

if token:
    sp = spotipy.Spotify(auth=token)
    results = sp.current_user_saved_tracks()
    for item in results['items']:
        track = item['track']
        print track['name'] + ' - ' + track['artists'][0]['name']
else:
    print "Can't get token for", username

# spotify = spotipy.Spotify()

# name = 'Kanye West'
# results = spotify.search(q='artist:' + name, type='artist')
# print results

# if len(sys.argv) > 1:
#     name = ' '.join(sys.argv[1:])
# else:
#     name = 'Radiohead'

# results = spotify.search(q='artist:' + name, type='artist')
# items = results['artists']['items']
# if len(items) > 0:
#     artist = items[0]
#     print artist['name'], artist['images'][0]['url']