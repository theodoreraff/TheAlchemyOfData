from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Define the schema for the tables
class DimArtist(Base):
    __tablename__ = 'dim_artist'
    artist_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    external_url = Column(String, nullable=False)
    follower_count = Column(Integer, nullable=False)
    image_url = Column(String, nullable=False)
    popularity = Column(Integer, nullable=False)

class DimAlbum(Base):
    __tablename__ = 'dim_album'
    album_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    total_tracks = Column(Integer, nullable=False)
    release_date=Column(DateTime, nullable=False)
    external_url = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    label = Column(String, nullable=False)
    popularity = Column(Integer, nullable=False)

class DimSong(Base):
    __tablename__ = 'dim_song'
    song_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    disc_number = Column(Integer, nullable=False)
    duration_ms = Column(BigInteger, nullable=False)
    explicit = Column(Boolean, nullable=False)
    external_url = Column(String, nullable=False)
    preview_url = Column(String, nullable=False)
    popularity = Column(Integer, nullable=False)

class FactHistory(Base):
    __tablename__ = 'fact_history'
    listening_id = Column(Integer, primary_key=True, autoincrement=True)
    played_at = Column(DateTime, nullable=False)
    song_id = Column(String, ForeignKey('dim_song.song_id'), nullable=False)
    album_id = Column(String, ForeignKey('dim_album.album_id'), nullable=False)
    artist_id = Column(String, ForeignKey('dim_artist.artist_id'), nullable=False)