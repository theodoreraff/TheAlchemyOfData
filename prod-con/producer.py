import requests
import time
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from confluent_kafka import Producer, KafkaException
from dotenv import load_dotenv
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, DimAlbum, DimArtist, DimSong
from sqlalchemy.exc import OperationalError


# read config from client.properties for kafka producer
def read_config():
    config = {}
    try:
        with open("client.properties") as fh:
            for line in fh:
                line = line.strip()
                if len(line) != 0 and line[0] != "#":
                    parameter, value = line.strip().split('=', 1)
                    config[parameter] = value.strip()
    except FileNotFoundError:
        print("Error: Configuration file 'client.properties' not found.")
    except Exception as e:
        print(f"Error reading configuration file: {e}")
    return config


# fetch artist data from spotify api using spotipy
def fetch_artist_data(artist_id: str) -> dict:
    try:
        response = sp.artist(artist_id)
    except requests.exceptions.ReadTimeout:
        print(f"Timeout occurred for artist_id: {artist_id}. Retrying...")
        response = sp.artist(artist_id)
    data = {
        "artist_id": artist_id,
        "name": response['name'],
        "external_url": response['external_urls']['spotify'],
        "follower_count": response['followers']['total'],
        "image_url": response['images'][0]['url'],
        "popularity": response['popularity'],
    }
    return data


# fetch album data from spotify api using spotipy
def fetch_album_data(album_id: str) -> dict:
    try:
        response = sp.album(album_id)
    except requests.exceptions.ReadTimeout:
        print(f"Timeout occurred for album_id: {album_id}. Retrying...")
        response = sp.album(album_id)
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


# fetch song data from spotify api using spotipy
def fetch_song_data(song_id: str) -> dict:
    try:
        response = sp.track(song_id)
    except requests.exceptions.ReadTimeout:
        print(f"Timeout occurred for song_id: {song_id}. Retrying...")
        response = sp.track(song_id)
    data = {
        "song_id": song_id,
        "title": response['name'],
        "disc_number": response['disc_number'],
        "duration_ms": response['duration_ms'],
        "explicit": response['explicit'],
        "external_url": response['external_urls']['spotify'],
        "preview_url": response['preview_url'] if 'preview_url' in response else 'No preview available',
        "popularity": response['popularity'],
    }
    return data


# produce data to kafka topic
def produce_to_kafka(data, config, topic):
    producer = Producer(config)

    def delivery_callback(err, msg):
        if err:
            print(f'ERROR: Message failed delivery: {err}')
        else:
            key = msg.key().decode('utf-8') if msg.key() else None
            value = msg.value().decode('utf-8') if msg.value() else None
            print(f"Produced event to topic {msg.topic()}: key = {key} value = {value}")

    try:
        producer.produce(topic, value=json.dumps(data).encode('utf-8'), callback=delivery_callback)
        producer.flush()
        print(f"Produced data to topic {topic}\n")
    except KafkaException as e:
        print(f"Error producing to Kafka: {e}")


if __name__ == '__main__':
    config = read_config()
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

    # spotify initialization
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    sp = Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

    # psql initialization
    psql_link = os.getenv('PSQL_DB_LINK')
    engine = create_engine(psql_link)
    Session = sessionmaker(bind=engine)

    # create all table if not exist
    Base.metadata.create_all(engine)

    # Create a single session
    session = Session()

    # endpoint initialization
    endpoint_url = 'http://127.0.0.1:5000'
    last_fetched = int(time.time()) * 1000

    try:
        while True:
            now = int(time.time()) * 1000
            data = {
                'after': last_fetched
            }
            try:
                response = requests.post(endpoint_url, json=data).json()
                if response['status_code'] == 204:
                    print(response)
                elif response['status_code'] == 200:
                    for item in response['items']:
                        song_data = session.query(DimSong).filter_by(song_id=item['song_id']).first()
                        if not song_data:
                            produce_to_kafka(fetch_song_data(item['song_id']), config, 'song_topic')
                        album_data = session.query(DimAlbum).filter_by(album_id=item['album_id']).first()
                        if not album_data:
                            produce_to_kafka(fetch_album_data(item['album_id']), config, 'album_topic')
                        artist_data = session.query(DimArtist).filter_by(artist_id=item['artist_id']).first()
                        if not artist_data:
                            produce_to_kafka(fetch_artist_data(item['artist_id']), config, 'artist_topic')
                        item_data = {
                            'song_id': item['song_id'],
                            'album_id': item['album_id'],
                            'artist_id': item['artist_id'],
                            'played_at': item['played_at']
                        }
                        produce_to_kafka(item_data, config, 'item_topic')
            except OperationalError as e:
                print(f"Database operation failed: {e}")
                session.rollback()

            last_fetched = now
            time.sleep(60)
    except KeyboardInterrupt:
        print("Process interrupted by user.")
    finally:
        session.close()
        engine.dispose()
        print("All sessions closed and resources released.")