import requests  # For HTTP requests
import sqlite3   # For interacting with SQLite database
import pandas as pd  # For data manipulation
from bs4 import BeautifulSoup  # For parsing HTML content

# URL of archived webpage
url = 'https://web.archive.org/web/20230902185655/https://en.everybodywiki.com/100_Most_Highly-Ranked_Films'

# File and database configurations
db_name = 'Movies.db'  # SQLite database file
table_name = 'Top_50'  # Table name in the SQLite database
csv_path = 'top_50_films.csv'  # Path to save the CSV file

# Initialize empty DataFrame to store the top 50 films
df = pd.DataFrame(columns=["Average Rank", "Film", "Year"])
count = 0

# Fetch and parse HTML page
html_page = requests.get(url).text
data = BeautifulSoup(html_page, 'html.parser')

# Locate the table rows in the HTML
tables = data.find_all('tbody')
rows = tables[0].find_all('tr')

# Extract top 50 film data from the rows
for row in rows:
    if count < 50:
        col = row.find_all('td')
        if len(col) != 0:  # Ensure there are columns present
            # Create a dictionary with the extracted data
            data_dict = {
                "Average Rank": int(col[0].contents[0]),
                "Film": str(col[1].contents[0]),
                "Year": int(col[2].contents[0])
            }
            # Convert the dictionary to a DataFrame and append it to the main DataFrame
            df1 = pd.DataFrame(data_dict, index=[0])
            df = pd.concat([df, df1], ignore_index=True)
            count += 1
    else:
        break  # Exit the loop after extracting the top 50 films

# Display the scraped data
print(df)

# Save the data to a CSV file
df.to_csv(csv_path, index=False)

# Save the data to an SQLite database
conn = sqlite3.connect(db_name)
df.to_sql(table_name, conn, if_exists='replace', index=False)
conn.close()
