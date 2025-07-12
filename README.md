# 🎧 Weekly Spotify Wrapped Pipeline

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-3.0+-orange.svg)](https://kafka.apache.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.0+-red.svg)](https://spark.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-20.0+-lightblue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🚀 **A Real-Time Data Engineering Pipeline that Delivers Personalized Weekly Music Insights Using Spotify Data, Apache Kafka, Spark Streaming, and AI**

---

## 🎯 **What Makes This Project Special?**

This isn't just another data pipeline. it's a **production-ready, end-to-end Data Engineering system** that transforms raw Spotify listening data into personalized weekly insights using cutting-edge technologies. Think of it as "Spotify Wrapped" but delivered weekly with AI-powered recommendations!

### 🌟 **Key Highlights:**

- **🔬 Real-World Data Engineering:** Complete data pipeline from ingestion to AI-powered insights
- **⚡ Real-Time Processing:** Handles live data streams with Apache Kafka and Spark Streaming
- **🤖 AI Integration:** Leverages Google Gemini AI for personalized music recommendations
- **🏗️ Production Architecture:** Scalable microservices with Docker containerization
- **📊 Data Warehousing:** Implements Star Schema for efficient analytics
- **🔄 End-to-End Automation:** From data collection to email delivery

---

## ✨ **Core Features**

| Feature                    | Technology               | Description                                                        |
| -------------------------- | ------------------------ | ------------------------------------------------------------------ |
| 🎵 **Spotify Integration** | Flask + Spotify API      | Real-time data ingestion from user's listening history             |
| 📡 **Real-Time Streaming** | Apache Kafka             | Handles 4 different data streams (songs, albums, artists, history) |
| ⚡ **Stream Processing**   | Apache Spark Streaming   | Real-time data transformation and analytics                        |
| 🗄️ **Data Warehousing**    | PostgreSQL + Star Schema | Efficient storage with fact/dimension tables                       |
| 🤖 **AI-Powered Insights** | Google Gemini AI         | Generates personalized weekly recaps and recommendations           |
| 📧 **Automated Delivery**  | Email Service            | Sends AI-generated insights directly to users                      |
| 🐳 **Containerization**    | Docker                   | Scalable deployment with Kafka cluster                             |

---

## 🛠️ **Tech Stack**

### **Backend & APIs**

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.0+-green?style=for-the-badge&logo=flask)
![Spotify API](https://img.shields.io/badge/Spotify%20API-1.0+-green?style=for-the-badge&logo=spotify)

### **Data Engineering**

![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-3.0+-orange?style=for-the-badge&logo=apache-kafka)
![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.0+-red?style=for-the-badge&logo=apache-spark)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue?style=for-the-badge&logo=postgresql)

### **AI & ML**

![Google Gemini AI](https://img.shields.io/badge/Google%20Gemini%20AI-Latest-purple?style=for-the-badge&logo=google)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1.4+-red?style=for-the-badge)

### **DevOps & Deployment**

![Docker](https://img.shields.io/badge/Docker-20.0+-lightblue?style=for-the-badge&logo=docker)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2.0+-lightblue?style=for-the-badge&logo=docker)

---

## 🏗️ **Architecture Overview**

```mermaid
graph LR
    A[Spotify API] --> B[Flask Backend]
    B --> C[Apache Kafka]
    C --> D[Spark Streaming]
    D --> E[PostgreSQL]
    E --> F[Gemini AI]
    F --> G[Email Delivery]

    style A fill:#1DB954
    style C fill:#FF6B35
    style D fill:#FF6B35
    style E fill:#336791
    style F fill:#4285F4
```

---

## 📁 **Project Structure**

```
weekly-spotify-wrapped-pipeline/
├── 🐍 flask_backend/           # Flask web service for API integration
│   ├── app.py                  # Main Flask application
│   └── utils.py                # Utility functions
├── 🐳 kafka-clusters/          # Docker Compose for Kafka setup
│   └── docker-compose.yml      # Kafka & Control Center configuration
├── ⚡ prod-con/                # Producer & Consumer scripts
│   ├── producer.py             # Kafka producer for Spotify data
│   ├── models.py               # Database models (SQLAlchemy)
│   ├── spark-consumer-song.py  # Spark streaming for song data
│   ├── spark-consumer-album.py # Spark streaming for album data
│   ├── spark-consumer-artist.py # Spark streaming for artist data
│   └── spark-consumer-history.py # Spark streaming for history data
├── 📋 requirements.txt         # Python dependencies
└── 📖 README.md               # This file
```

---

## 🚀 **Quick Start Guide**

### **Prerequisites**

- Python 3.8+
- Docker & Docker Compose
- Apache Spark (for streaming consumers)
- PostgreSQL database

### **1. Clone & Setup**

```bash
git clone https://github.com/your-username/weekly-spotify-wrapped-pipeline.git
cd weekly-spotify-wrapped-pipeline
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### **2. Environment Configuration**

Create a `.env` file in the root directory:

```env
# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Email Configuration
GMAIL_APP_PASSWORD=your_gmail_app_password

# PostgreSQL Database
DATABASE_URL=postgresql://username:password@localhost:5432/spotify_wrapped
```

### **3. Start Kafka Cluster**

```bash
cd kafka-clusters
docker compose up -d --build
```

Access Confluent Control Center at `http://127.0.0.1:9021`

### **4. Run the Pipeline**

```bash
# Terminal 1: Start Flask backend
cd flask_backend
flask run --reload

# Terminal 2: Start Kafka producer
python prod-con/producer.py

# Terminal 3-6: Start Spark consumers (in separate terminals)
python prod-con/spark-consumer-song.py
python prod-con/spark-consumer-album.py
python prod-con/spark-consumer-artist.py
python prod-con/spark-consumer-history.py
```

### **5. Access the Application**

Visit `http://127.0.0.1:5000/login` to authenticate with Spotify and start receiving weekly insights!

---

## 🎯 **What You'll Learn**

This project demonstrates **real-world Data Engineering skills** including:

- **🔗 API Integration:** Building robust connections with external APIs (Spotify)
- **📊 Data Pipeline Design:** End-to-end data flow from ingestion to insights
- **⚡ Real-Time Processing:** Handling live data streams with Kafka and Spark
- **🗄️ Data Modeling:** Implementing Star Schema for analytics
- **🤖 AI Integration:** Leveraging LLMs for personalized content generation
- **🐳 Containerization:** Docker-based deployment and scaling
- **📧 Automation:** Scheduled data processing and delivery

---

## 🔮 **Future Roadmap**

- [ ] **Unified Spark Consumer:** Consolidate all consumers into a single, optimized streaming job
- [ ] **Data Quality Monitoring:** Implement real-time data validation and alerting
- [ ] **Full Containerization:** Dockerize the entire pipeline for easy deployment
- [ ] **Orchestration:** Integrate with Apache Airflow for workflow management
- [ ] **Cloud Deployment:** Migrate to AWS/GCP with managed services
- [ ] **Real-Time Dashboard:** Web-based analytics dashboard
- [ ] **Mobile App:** Native iOS/Android app for insights delivery

---

## 🤝 **Contributing**

Contributions are welcome! Please feel free to submit a Pull Request.

### **Development Setup**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**⭐ Star this repository if you found it helpful! ⭐**

_Built with ❤️ using cutting-edge Data Engineering technologies_

</div>
