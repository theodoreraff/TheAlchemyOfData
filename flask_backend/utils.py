import psycopg2
import os
from dotenv import load_dotenv
import json
from genai import generate_content
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import google.generativeai as genai

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_db_connection():
    connection = psycopg2.connect(
        dbname=os.getenv('PSQL_DB_NAME'),
        user=os.getenv('PSQL_DB_USER'),
        password=os.getenv('PSQL_DB_PASSWORD'),
        host=os.getenv('PSQL_DB_HOST'),
        port=5432
    )
    return connection

def generate_content(html_body):
    api_key = os.getenv('GENAI_API_KEY')

    system_instruction = """
    You are an expert music and/or song analyst.
    Given an html body, I need you to generate a weekly recap summary, mood recap, and recommendations. 
    You are to start and end your response with a fun and engaging opening and closing statement.
    Your responses should be engaging and fun to read, also use emojis where necessary.
    For song name, and artist name in the recaps, wrap it inside '' as I don't want you to return a markdown.
    Your response should be returned in json format like this:
    {
        "opening_statement": opening_statement,
        "weekly_recap": weekly_recap,
        "mood_recap": mood_recap,
        "recommendations": recommendations,
        "closing_statement": closing_statement
    }
    """

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name='gemini-1.5-pro-latest',
        system_instruction=system_instruction
    )
    try:
        response = model.generate_content(html_body)
        response_text = response.text
        if '```json' in response_text:
            response_text = response_text.replace('```json', '')
        if '```' in response_text:
            response_text = response_text.replace('```', '')
        print(response_text)
        return response_text
    except Exception as e:
        print("error: ", e)
        return {"error": str(e)}

def get_insight():
    conn = get_db_connection()
    cursor = conn.cursor()

    queries = [
        {
            'name': 'Top 10 Songs', 'query': """
                SELECT 
                    ds.title AS song_name,
                    da.title AS album,
                    dar.name AS artist,
                    da.image_url AS album_art,
                    FLOOR(SUM(ds.duration_ms) / (1000 * 60)) AS total_minute_listened
                FROM 
                    fact_history fh
                JOIN 
                    dim_song ds ON fh.song_id = ds.song_id
                JOIN 
                    dim_album da ON fh.album_id = da.album_id
                JOIN 
                    dim_artist dar ON fh.artist_id = dar.artist_id
                WHERE 
                    fh.played_at >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) + 1 DAY) + INTERVAL '00:01:00' HOUR_SECOND
                    AND fh.played_at < DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) - 5 DAY), INTERVAL '08:59:00' HOUR_SECOND)
                GROUP BY 
                    ds.title, da.title, dar.name, da.image_url
                ORDER BY 
                    total_minute_listened DESC
                LIMIT 10;
            """
        },
        {
            'name': 'Top 5 Albums', 'query': """
                SELECT 
                    da.title AS album,
                    dar.name AS artist,
                    da.image_url AS album_art,
                    FLOOR(SUM(ds.duration_ms) / (1000 * 60)) AS total_minute_listened
                FROM 
                    fact_history fh
                JOIN 
                    dim_album da ON fh.album_id = da.album_id
                JOIN 
                    dim_artist dar ON fh.artist_id = dar.artist_id
                JOIN 
                    dim_song ds ON fh.song_id = ds.song_id
                WHERE 
                    fh.played_at >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) + 1 DAY) + INTERVAL '00:01:00' HOUR_SECOND
                    AND fh.played_at < DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) - 5 DAY), INTERVAL '08:59:00' HOUR_SECOND)
                GROUP BY 
                    da.title, dar.name, da.image_url
                ORDER BY 
                    total_minute_listened DESC
                LIMIT 5;
            """
        },
        {
            'name': 'Top 5 Artists', 'query': """
                SELECT 
                    dar.name AS artist,
                    FLOOR(SUM(ds.duration_ms) / (1000 * 60)) AS total_minute_listened
                FROM 
                    fact_history fh
                JOIN 
                    dim_artist dar ON fh.artist_id = dar.artist_id
                JOIN 
                    dim_song ds ON fh.song_id = ds.song_id
                WHERE 
                    fh.played_at >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) + 1 DAY) + INTERVAL '00:01:00' HOUR_SECOND
                    AND fh.played_at < DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) - 5 DAY), INTERVAL '08:59:00' HOUR_SECOND)
                GROUP BY 
                    dar.name
                ORDER BY 
                    total_minute_listened DESC
                LIMIT 5;
            """
        },
        {
            'name': 'Songs you haven\'t listened to in a while', 'query': """
            SELECT 
                ds.title AS song_name,
                da.image_url AS album_art,
                MAX(fh.played_at) AS last_played,
                DATEDIFF(NOW(), MAX(fh.played_at)) AS days_ago
            FROM 
                fact_history fh
            JOIN 
                dim_song ds ON fh.song_id = ds.song_id
            JOIN 
                dim_album da ON fh.album_id = da.album_id
            GROUP BY 
                ds.title, da.image_url
            ORDER BY 
                days_ago DESC
            LIMIT 10;
            """
        }
    ]

    for query in queries:
        cursor.execute(query['query'])
        results = cursor.fetchall()
        data = []
        for row in results:
            data.append(row)
        query['data'] = data

    body = ""

    for query in queries:
        if query['data']:
            body += f"<h3>{query['name']}</h3>"
            body += "<div class='card-container'>"
            for row in query['data']:
                if query['name'] == 'Top 10 Songs':
                    body += f"<div class='album-card' style='background-image: url({row['album_art']});'>"
                    body += f"<div class='album-content'><div class='title'>{row['song_name']}</div>"
                    body += f"<div class='subtitle'>by {row['artist']}</div><p>{row['total_minute_listened']}m listened</p></div>"
                elif query['name'] == 'Top 5 Albums':
                    body += f"<div class='album-card' style='background-image: url({row['album_art']});'>"
                    body += f"<div class='album-content'><div class='title'>{row['album']}</div>"
                    body += f"<div class='subtitle'>by {row['artist']}</div><p>{row['total_minute_listened']}m listened</p></div>"
                elif query['name'] == 'Top 5 Artists':
                    body += "<div class='card'>"
                    body += f"<div class='artist-title'>{row['artist']}</div>"
                    body += f"<p>{row['total_minute_listened']}m listened</p>"
                elif query['name'] == 'Songs you haven\'t listened to in a while':
                    body += f"<div class='album-card' style='background-image: url({row['album_art']});'>"
                    body += f"<div class='album-content'><div class='title'>{row['song_name']}</div>"
                    body += f"<div class='subtitle'>was played {row['days_ago']} days ago</div></div>"
                body += "</div>"
            body += "</div>"
        else:
            body += f"<h3>{query['name']}</h3>"
            body += "<p>No data available</p>"

    ai_response = json.loads(generate_content(body))
    opening_statement = ai_response['opening_statement']
    closing_statement = ai_response['closing_statement']
    weekly_recap = ai_response['weekly_recap']
    mood_recap = ai_response['mood_recap']
    recommendations = ai_response['recommendations']

    html_string = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weekly Wrap</title>
        <style>
            body {{
                font-family: 'Roboto', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f4f4f4;
                color: #333;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background-color: #fff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .hero {{
                text-align: justify;
                margin-bottom: 40px;
            }}
            h1 {{
                color: #007bff;
                margin-bottom: 10px;
            }}
            h2 {{
                color: #555;
                margin-top: 40px;
                border-bottom: 2px solid #007bff;
                padding-bottom: 5px;
            }}
            h3 {{
                margin-top: 20px;
                color: #333;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }}
            .card-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 20px;
                justify-content: space-around;
            }}
            .card {{
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                padding: 15px;
                width: calc(33.333% - 20px);
                box-sizing: border-box;
                transition: transform 0.3s, box-shadow 0.3s;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                text-align: center;
            }}
            .card:hover, .album-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
            }}
            .card-image img {{
                max-width: 100%;
                border-radius: 5px;
            }}
            .card-content {{
                margin-top: 10px;
                font-size: 14px;
            }}
            .album-card {{
                background-size: cover;
                background-position: center;
                border-radius: 8px;
                color: #fff;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                padding: 20px;
                position: relative;
                width: calc(33.333% - 20px);
                box-sizing: border-box;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s, box-shadow 0.3s;
                overflow: hidden;
                margin-bottom: 20px;
            }}
            .album-card::after {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                border-radius: 8px;
            }}
            .album-content {{
                position: relative;
                z-index: 1;
                font-size: 14px;
            }}
            .title {{
                font-size: 18px;
                font-weight: bold;
                color: #fff;
                text-align: center;
                margin: 5px 0;
            }}
            .artist-title {{
                font-size: 18px;
                font-weight: bold;
                color: #000;
                text-align: center;
                margin: 5px 0;
            }}
            .subtitle {{
                font-size: 16px;
                color: #ddd;
                text-align: center;
                margin: 5px 0;
            }}
            .recap, .recommendations, .riddle {{
                padding: 15px;
                border-left: 4px solid;
                margin-bottom: 20px;
                font-size: 16px;
            }}
            .recap {{
                background-color: #e9f7ef;
                border-color: #28a745;
            }}
            .recommendations {{
                background-color: #e3f2fd;
                border-color: #007bff;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>Hey 👋</h1>
                <p>{opening_statement}</p>
            </div>

            <h2>Recaps</h2>
            <div class="recap">
                <p>{weekly_recap}</p>
                <p>{mood_recap}</p>
            </div>
    """

    html_string += body

    html_string += f"""
            <h2>Recommendations</h2>
            <div class="recommendations">
                <p>{recommendations}</p>
            </div>
            <p>{closing_statement}</p>
        </div>
    </body>
    </html>
    """

    cursor.close()
    conn.close()
    send_email(html_string)
    return 'Success'

def send_email(html_content):
    # Email configuration
    sender_email = "Sender email address"
    receiver_email = "Receiver email address"
    password = os.getenv("GOOGLE_APP_PASSWORD")
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Your Weekly Listening Wrap"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Create the HTML part of the message
    html_part = MIMEText(html_content, 'html')

    # Attach HTML content to the email
    msg.attach(html_part)

    # Connect to SMTP server and send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Secure the connection
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())