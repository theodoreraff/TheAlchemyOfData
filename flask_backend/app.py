import uuid
import json
from flask import Flask, redirect, session, request, url_for
from spotipy import Spotify, SpotifyOAuth
import os
from dotenv import load_dotenv
import secrets
import time
from utils import get_insight

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
TOKEN_INFO = ''
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for('redirect_page', _external=True),
        scope='user-read-recently-played'
    )


def get_token():
    token_info = load_token_info()
    if not token_info:
        return redirect(url_for('login', _external=True))

    is_expired = token_info['expires_at'] - int(time.time()) < 600
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        save_token_info(token_info)
    return token_info['access_token']


def save_token_info(token_info):
    # save token info to a file
    with open('token_info.json', 'w') as f:
        f.write(json.dumps(token_info))


def load_token_info():
    try:
        with open('token_info.json', 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return None
    except KeyError:
        return None


@app.route('/', methods=['POST'])
def stream_data():
    try:
        token_info = get_token()
    except:
        print('User not logged in / token expired')
        return redirect(url_for('login', _external=True))
    sp = Spotify(auth=token_info)

    req_data = request.get_json()
    recent_played = sp.current_user_recently_played(after=req_data['after'])
    if recent_played['items'] == []:
        return {
            "status_code": 204,
            "message": "No new data"
        }

    # after = request.form.get('after')
    items = []
    for item in recent_played['items']:
        played_at = item['played_at'][0],
        song_id = item['track']['id']
        album_id = item['track']['album']['id']
        artist_id = item['track']['artists'][0]['id']
        items.append({
            'id': uuid.uuid4().hex,
            'played_at': played_at,
            'song_id': song_id,
            'album_id': album_id,
            'artist_id': artist_id,
        })

    return {
        'status_code': 200,
        'message': f'{len(items)} new songs',
        'items': items,
    }


@app.route('/insight', methods=['GET'])
def insight():
    ai_resp = get_insight()
    if ai_resp != 'Success':
        return {
            "status_code": 500,
            "message": "Internal Server Error"
        }
    return {
        "status_code": 200,
        "message": "Success. Check your email for the insights"
    }


@app.route('/login', methods=['GET'])
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    save_token_info(token_info)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('homepage', _external=True), )