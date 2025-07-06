from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship # Import relationship for foreign key relationships

# Base class for declarative models
Base = declarative_base()

# Define the schema for the dimension and fact tables following Kimball principles (Star Schema)

class DimArtist(Base):
    """
    Dimension table for Artist data.
    Stores unique artist information.
    """
    __tablename__ = 'dim_artist'
    artist_id = Column(String, primary_key=True, comment="Unique Spotify ID for the artist")
    name = Column(String, nullable=False, comment="Name of the artist")
    external_url = Column(String, nullable=False, comment="URL to the artist's Spotify page")
    follower_count = Column(Integer, nullable=False, comment="Total number of followers on Spotify")
    image_url = Column(String, nullable=False, comment="URL to the artist's image")
    popularity = Column(Integer, nullable=False, comment="Popularity score of the artist (0-100)")

    # Relationship to FactHistory (optional, for ORM queries)
    # histories = relationship("FactHistory", back_populates="artist_dim")

class DimAlbum(Base):
    """
    Dimension table for Album data.
    Stores unique album information.
    """
    __tablename__ = 'dim_album'
    album_id = Column(String, primary_key=True, comment="Unique Spotify ID for the album")
    title = Column(String, nullable=False, comment="Title of the album")
    total_tracks = Column(Integer, nullable=False, comment="Total number of tracks in the album")
    release_date=Column(DateTime, nullable=False, comment="Release date of the album")
    external_url = Column(String, nullable=False, comment="URL to the album's Spotify page")
    image_url = Column(String, nullable=False, comment="URL to the album's cover art image")
    label = Column(String, nullable=False, comment="Record label of the album")
    popularity = Column(Integer, nullable=False, comment="Popularity score of the album (0-100)")

    # Relationship to FactHistory (optional)
    # histories = relationship("FactHistory", back_populates="album_dim")

class DimSong(Base):
    """
    Dimension table for Song data.
    Stores unique song (track) information.
    """
    __tablename__ = 'dim_song'
    song_id = Column(String, primary_key=True, comment="Unique Spotify ID for the song")
    title = Column(String, nullable=False, comment="Title of the song")
    disc_number = Column(Integer, nullable=False, comment="Number of the disc the track appears on")
    duration_ms = Column(BigInteger, nullable=False, comment="Duration of the track in milliseconds")
    explicit = Column(Boolean, nullable=False, comment="True if the track is explicit, False otherwise")
    external_url = Column(String, nullable=False, comment="URL to the song's Spotify page")
    preview_url = Column(String, nullable=False, comment="URL to a 30-second preview (if available)")
    popularity = Column(Integer, nullable=False, comment="Popularity score of the song (0-100)")

    # Relationship to FactHistory (optional)
    # histories = relationship("FactHistory", back_populates="song_dim")

class FactHistory(Base):
    """
    Fact table for listening history data.
    Records each instance of a song being played, linking to dimension tables.
    Follows a star schema design.
    """
    __tablename__ = 'fact_history'
    listening_id = Column(Integer, primary_key=True, autoincrement=True, comment="Unique ID for each listening event")
    played_at = Column(DateTime, nullable=False, comment="Timestamp when the song was played")
    song_id = Column(String, ForeignKey('dim_song.song_id'), nullable=False, comment="Foreign key to dim_song table")
    album_id = Column(String, ForeignKey('dim_album.album_id'), nullable=False, comment="Foreign key to dim_album table")
    artist_id = Column(String, ForeignKey('dim_artist.artist_id'), nullable=False, comment="Foreign key to dim_artist table")

    # Relationships to dimension tables (optional, for ORM queries)
    # song_dim = relationship("DimSong", back_populates="histories")
    # album_dim = relationship("DimAlbum", back_populates="histories")
    # artist_dim = relationship("DimArtist", back_populates="histories")