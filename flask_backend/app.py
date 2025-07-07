# Standard Library Imports
import json
import os
import secrets
import time
import uuid

# Third-Party Library Imports
from dotenv import load_dotenv
from flask import Flask, redirect, session, request, url_for
from spotipy import Spotify, SpotifyOAuth
import requests


# Local Application Imports
from utils import get_insight


# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Get Spotify API credentials from environment variables
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

# Global variable to store Spotify token info (though session is also used)
TOKEN_INFO = ''

# Initialize Flask application
app = Flask(__name__)
# Set a secret key for session management, crucial for security
app.secret_key = secrets.token_hex(16)

def create_spotify_oauth():
    """
    Creates and returns a SpotifyOAuth object for handling Spotify's OAuth flow.
    This object manages the authentication process with Spotify.
    """
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for('redirect_page', _external=True),  # Redirect URI after Spotify login
        scope='user-read-recently-played'  # Scope defines what data we can access (recently played tracks)
    )


def get_token():
    """
    Retrieves the Spotify access token.
    It loads the token from a file, checks if it's expired, and refreshes it if needed.
    Redirects to login if no valid token is found.
    """
    token_info = load_token_info()
    if not token_info:
        # If no token info is found, redirect user to Spotify login
        return redirect(url_for('login', _external=True))

    # Check if the token is expired (less than 10 minutes remaining)
    is_expired = token_info['expires_at'] - int(time.time()) < 600
    if is_expired:
        # If expired, refresh the access token using the refresh token
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        save_token_info(token_info)  # Save the new token info
    return token_info['access_token']  # Return the valid access token


def save_token_info(token_info):
    """
    Saves the Spotify token information (access token, refresh token, expiry) to a local file.
    This avoids re-authenticating with Spotify every time.
    """
    with open('token_info.json', 'w') as f:
        f.write(json.dumps(token_info))


def load_token_info():
    """
    Loads the Spotify token information from a local file.
    Handles cases where the file doesn't exist or is empty.
    """
    try:
        with open('token_info.json', 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        # Return None if the token file does not exist
        return None
    except KeyError:
        # Return None if the token file exists but is malformed/empty
        return None


@app.route('/', methods=['POST'])
def stream_data():
    """
    API endpoint to stream recently played Spotify tracks.
    It fetches data from Spotify and returns it as JSON.
    Requires a POST request with an 'after' timestamp in the body.
    """
    try:
        # Get a valid Spotify access token
        token_info = get_token()
    except:
        # Handle cases where user is not logged in or token is invalid
        print('User not logged in / token expired')
        return redirect(url_for('login', _external=True))

    # Initialize Spotify client with the access token
    sp = Spotify(auth=token_info)

    # Get the 'after' timestamp from the request body to fetch new tracks
    req_data = request.get_json()
    recent_played = sp.current_user_recently_played(after=req_data['after'])

    # If no new items are played, return 204 No Content
    if not recent_played['items']:  # Simplified check for empty list
        return {
            "status_code": 204,
            "message": "No new data"
        }

    # Process each recently played item to extract relevant data
    items = []
    for item in recent_played['items']:
        # Extract relevant details for each played track
        played_at = item['played_at'][0],  # Timestamp when the track was played
        song_id = item['track']['id']  # Spotify ID of the song
        album_id = item['track']['album']['id']  # Spotify ID of the album
        artist_id = item['track']['artists'][0]['id']  # Spotify ID of the primary artist

        # Append extracted data to the items list
        items.append({
            'id': uuid.uuid4().hex,  # Generate a unique ID for this listening event
            'played_at': played_at,
            'song_id': song_id,
            'album_id': album_id,
            'artist_id': artist_id,
        })

    # Return the processed items as a JSON response
    return {
        'status_code': 200,
        'message': f'{len(items)} new songs',
        'items': items,
    }


@app.route('/insight', methods=['GET'])
def insight():
    """
    API endpoint to trigger the generation and delivery of weekly Spotify insights.
    Calls the get_insight function from utils.py.
    """
    ai_resp = get_insight()  # Call utility function to generate insights
    if ai_resp != 'Success':
        # Handle internal server errors if insight generation fails
        return {
            "status_code": 500,
            "message": "Internal Server Error"
        }
    # Return success message if insights are generated and sent (e.g., via email)
    return {
        "status_code": 200,
        "message": "Success. Check your email for the insights"
    }


@app.route('/login', methods=['GET'])
def login():
    """
    API endpoint to initiate the Spotify OAuth login process.
    Redirects the user to Spotify's authorization page.
    """
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirect_page():
    """
    Callback endpoint for Spotify's OAuth flow.
    After user authorizes, Spotify redirects to this URL with an authorization code.
    This code is then used to get the access token and refresh token.
    """
    session.clear()  # Clear any previous session data
    code = request.args.get('code')  # Get the authorization code from Spotify's redirect

    # Exchange the authorization code for access and refresh tokens
    token_info = create_spotify_oauth().get_access_token(code)
    save_token_info(token_info)  # Save the token info for future use
    session[TOKEN_INFO] = token_info  # Store token info in Flask session

    # Redirect user to the homepage after successful authentication
    return redirect(url_for('homepage', _external=True))  # Assuming 'homepage' is defined elsewhere, or use '/'
