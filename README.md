# 🎧 Weekly Spotify Wrapped Pipeline

## ✨ Project Overview
This project demonstrates an end-to-end Machine Learning Engineering pipeline designed to generate personalized "Weekly Spotify Wrapped" insights. It leverages real-time data streaming to process listening history, store it, and utilize Generative AI to provide unique weekly recaps and recommendations. Inspired by the popular Spotify Wrapped feature, this pipeline aims to offer continuous insights into music listening habits without waiting for a year.

## 🚀 Key Features
-   **Spotify Data Ingestion:** Fetches recently played tracks from Spotify API via a Flask web service.
-   **Real-time Data Streaming:** Utilizes **Apache Kafka** as a messaging system to handle real-time data streams (songs, albums, artists, history).
-   **Stream Processing & Data Warehousing:** Employs **Apache Spark Streaming** to process and analyze real-time data, then stores it in a **PostgreSQL** database following a Star Schema (Fact and Dimension tables).
-   **AI-Powered Insights:** Integrates **Google Gemini AI** to generate personalized weekly recap summaries, mood recaps, and music recommendations based on listening history.
-   **Email Delivery:** Delivers AI-generated insights directly to the user's email.
-   **Automated Orchestration (Planned):** Designed for weekly scheduling via external tools (e.g., Airflow, cron, iOS automation).

## 💻 Tech Stack
-   **Main Programming Language:** Python
-   **Web Service:** Flask (for Spotify API integration and insight endpoints)
-   **Messaging System:** Apache Kafka (for real-time data streams)
-   **Stream Processing:** Apache Spark Streaming
-   **Database:** PostgreSQL (for structured data storage, Star Schema)
-   **Generative AI:** Google Gemini AI
-   **Containerization:** Docker (for Kafka cluster setup)
-   **ORM:** SQLAlchemy (for database interaction)

## ⚙️ Project Structure 
```
.
├── README.md
├── .env                # Environment variables (sensitive data)
├── requirements.txt    # Python package dependencies
├── flask_backend       # Flask web service for API calls & insights
│   └── app.py
│   └── utils.py
├── kafka-clusters      # Docker Compose setup for Kafka & Control Center
│   └── docker-compose.yml
└── prod-con            # Producer, Consumer, & Spark Streaming scripts
├── client.properties
├── models.py
├── producer.py
├── spark-consumer-album.py
├── spark-consumer-artist.py
├── spark-consumer-history.py
└── spark-consumer-song.py
```

## 🚀 How to Set Up & Run
*(Note: This is a high-level guide. Refer to individual script comments for detailed setup.)*

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/your-username/weekly-spotify-wrapped-pipeline.git](https://github.com/your-username/weekly-spotify-wrapped-pipeline.git) # Ganti dengan link repo kamu
    cd weekly-spotify-wrapped-pipeline
    ```
2.  **Environment Setup:**
    * Create and activate a Python virtual environment.
    * Install dependencies: `pip install -r requirements.txt`
3.  **API Keys & Credentials:**
    * Obtain Spotify Client ID/Secret, Gemini API Key, Google App Password.
    * Configure PostgreSQL database details.
    * Update these in your `.env` file (root directory).
4.  **Kafka Broker Setup:**
    * Navigate to `kafka-clusters/` and run `docker compose up -d --build`.
    * Create Kafka topics: `album_topic`, `artist_topic`, `song_topic`, `item_topic` via Confluent Control Center (`http://127.0.0.1:9021`).
5.  **Run Flask Web Service:**
    * Navigate to `flask_backend/` and run `flask run --reload`.
    * Access `http://127.0.0.1:5000/login` to authenticate with Spotify.
6.  **Run Producer & Consumers:**
    * Start the producer: `python prod-con/producer.py`
    * Start each Spark consumer (album, artist, song, history) in separate terminals (requires Apache Spark installation & JDBC driver).

## 💡 Future Enhancements
-   Implement a unified Spark consumer for all topics.
-   Add data quality checks within the Spark streaming process.
-   Containerize the entire pipeline (Flask, Producer, Consumers) using Docker Compose for easier deployment.
-   Set up dedicated orchestration for the AI insight generation (e.g., Apache Airflow).
-   Integrate with a cloud-based data platform (e.g., AWS S3, EMR, Kinesis).

## 📄 License
This project is open-source under the MIT License.
