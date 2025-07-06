import requests # For making HTTP requests to Flask API
import time # For time-related operations (e.g., sleeping, timestamps)
from spotipy import Spotify # Spotify API client library
from spotipy.oauth2 import SpotifyClientCredentials # For Spotify API authentication
from confluent_kafka import Producer, KafkaException # Kafka producer client library
from dotenv import load_dotenv # To load environment variables from .env file
import os # For interacting with the operating system (e.g., environment variables)
import json # For working with JSON data
from sqlalchemy import create_engine # For creating SQLAlchemy engine to connect to DB
from sqlalchemy.orm import sessionmaker # For creating SQLAlchemy sessions
from models import Base, DimAlbum, DimArtist, DimSong # Import SQLAlchemy models for DB schema
from sqlalchemy.exc import OperationalError # For handling database operation errors

# Load environment variables from the .env file located in the parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def read_config():
    """
    Reads Kafka producer configuration from 'client.properties' file.
    This file typically contains Kafka broker details.
    """
    config = {}
    try:
        with open("client.properties") as fh:
            for line in fh:
                line = line.strip()
                if len(line) != 0 and line[0] != "#": # Ignore empty lines and comments
                    parameter, value = line.strip().split('=', 1)
                    config[parameter] = value.strip()
    except FileNotFoundError:
        print("Error: Configuration file 'client.properties' not found.")
    except Exception as e:
        print(f"Error reading configuration file: {e}")
    return config


def fetch_artist_data(artist_id: str) -> dict:
    """
    Fetches artist data from the Spotify API using Spotipy.
    Handles potential read timeouts by retrying.
    """
    try:
        response = sp.artist(artist_id)
    except requests.exceptions.ReadTimeout:
        print(f"Timeout occurred for artist_id: {artist_id}. Retrying...")
        response = sp.artist(artist_id) # Retry on timeout
    data = {
        "artist_id": artist_id,
        "name": response['name'],
        "external_url": response['external_urls']['spotify'],
        "follower_count": response['followers']['total'],
        "image_url": response['images'][0]['url'],
        "popularity": response['popularity'],
    }
    return data


def fetch_album_data(album_id: str) -> dict:
    """
    Fetches album data from the Spotify API using Spotipy.
    Handles potential read timeouts by retrying.
    """
    try:
        response = sp.album(album_id)
    except requests.exceptions.ReadTimeout:
        print(f"Timeout occurred for album_id: {album_id}. Retrying...")
        response = sp.album(album_id) # Retry on timeout
    data = {
        "album_id": album_id,
        "title": response['name'],
        "total_tracks": response['total_tracks'],
        "release_date": response['release_date'],
        "external_url": response['external_urls']['spotify'],
        "image_url": response['images'][0]['url'],
        "label": response['label'],
        "popularity": response['popularity'],
    }
    return data


def fetch_song_data(song_id: str) -> dict:
    """
    Fetches song (track) data from the Spotify API using Spotipy.
    Handles potential read timeouts by retrying.
    """
    try:
        response = sp.track(song_id)
    except requests.exceptions.ReadTimeout:
        print(f"Timeout occurred for song_id: {song_id}. Retrying...")
        response = sp.track(song_id) # Retry on timeout
    data = {
        "song_id": song_id,
        "title": response['name'],
        "disc_number": response['disc_number'],
        "duration_ms": response['duration_ms'],
        "explicit": response['explicit'],
        "external_url": response['external_urls']['spotify'],
        "preview_url": response['preview_url'] if 'preview_url' in response else 'No preview available', # Handle missing preview_url
        "popularity": response['popularity'],
    }
    return data


def produce_to_kafka(data: dict, config: dict, topic: str):
    """
    Produces data to a specified Kafka topic.
    Includes a delivery callback for logging success or failure.
    """
    producer = Producer(config) # Initialize Kafka Producer

    def delivery_callback(err, msg):
        """Callback function for Kafka message delivery reports."""
        if err:
            print(f'ERROR: Message failed delivery: {err}')
        else:
            key = msg.key().decode('utf-8') if msg.key() else None
            value = msg.value().decode('utf-8') if msg.value() else None
            print(f"Produced event to topic {msg.topic()}: key = {key} value = {value}")

    try:
        # Produce the message (data converted to JSON bytes)
        producer.produce(topic, value=json.dumps(data).encode('utf-8'), callback=delivery_callback)
        producer.flush() # Ensure all outstanding messages are delivered
        print(f"Produced data to topic {topic}\n")
    except KafkaException as e:
        print(f"Error producing to Kafka: {e}")


if __name__ == '__main__':
    # Read Kafka producer configuration
    config = read_config()
    # Load environment variables for Spotify and PostgreSQL
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

    # Spotify API initialization
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    # Use Client Credentials Flow for fetching artist/album/song details (not user-specific)
    sp = Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

    # PostgreSQL database initialization
    psql_link = os.getenv('PSQL_DB_LINK') # Database connection string
    engine = create_engine(psql_link) # Create SQLAlchemy engine
    Session = sessionmaker(bind=engine) # Create a session factory

    # Create all tables defined in models.py if they do not already exist
    Base.metadata.create_all(engine)

    # Create a single SQLAlchemy session for database interactions
    session = Session()

    # Flask API endpoint initialization
    endpoint_url = 'http://127.0.0.1:5000' # URL of the local Flask web service
    last_fetched = int(time.time()) * 1000 # Timestamp of the last fetched song (in milliseconds)

    try:
        # Main loop to continuously fetch and produce data
        while True:
            now = int(time.time()) * 1000 # Current timestamp
            data = {
                'after': last_fetched # Request data played after this timestamp
            }
            try:
                # Make a POST request to the Flask API to get recently played tracks
                response = requests.post(endpoint_url, json=data).json()

                if response['status_code'] == 204:
                    print(response) # No new data
                elif response['status_code'] == 200:
                    # Process each new item (listening history)
                    for item in response['items']:
                        # Check if song/album/artist already exists in dimension tables
                        # If not, fetch full details from Spotify API and produce to respective Kafka topics

                        song_data = session.query(DimSong).filter_by(song_id=item['song_id']).first()
                        if not song_data:
                            produce_to_kafka(fetch_song_data(item['song_id']), config, 'song_topic')

                        album_data = session.query(DimAlbum).filter_by(album_id=item['album_id']).first()
                        if not album_data:
                            produce_to_kafka(fetch_album_data(item['album_id']), config, 'album_topic')

                        artist_data = session.query(DimArtist).filter_by(artist_id=item['artist_id']).first()
                        if not artist_data:
                            produce_to_kafka(fetch_artist_data(item['artist_id']), config, 'artist_topic')

                        # Prepare fact data (listening event) and produce to 'item_topic'
                        item_data = {
                            'song_id': item['song_id'],
                            'album_id': item['album_id'],
                            'artist_id': item['artist_id'],
                            'played_at': item['played_at']
                        }
                        produce_to_kafka(item_data, config, 'item_topic')
            except OperationalError as e:
                print(f"Database operation failed: {e}")
                session.rollback() # Rollback transaction on database error
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error to Flask API: {e}. Retrying...")
            except Exception as e:
                print(f"An unexpected error occurred in main loop: {e}")

            last_fetched = now # Update last_fetched timestamp for the next iteration
            time.sleep(60) # Wait for 1 minute before fetching new data
    except KeyboardInterrupt:
        print("Process interrupted by user.") # Handle graceful exit on Ctrl+C
    finally:
        session.close() # Close SQLAlchemy session
        engine.dispose() # Dispose of SQLAlchemy engine resources
        print("All sessions closed and resources released.")