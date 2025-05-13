import os
import glob
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime

# File paths
log_file = "log_file.txt"
target_file = "sample_data/transformed_data.csv"

# Extract data from CSV
def extract_from_csv(file):
    return pd.read_csv(file)

# Extract data from JSON
def extract_from_json(file):
    return pd.read_json(file, lines=True)

# Extract data from XML
def extract_from_xml(file):
    dataframe = pd.DataFrame(columns=["name", "height", "weight"])
    tree = ET.parse(file)
    root = tree.getroot()
    for person in root:
        row = {"name": person.find("name").text,
               "height": float(person.find("height").text),
               "weight": float(person.find("weight").text)}
        dataframe = pd.concat([dataframe, pd.DataFrame([row])], ignore_index=True)
    return dataframe

# Main extract function
def extract():
    data = pd.DataFrame(columns=['name', 'height', 'weight'])
    for file in glob.glob("*.csv"):
        if file != os.path.basename(target_file):
            data = pd.concat([data, extract_from_csv(file)], ignore_index=True)
    for file in glob.glob("*.json"):
        data = pd.concat([data, extract_from_json(file)], ignore_index=True)
    for file in glob.glob("*.xml"):
        data = pd.concat([data, extract_from_xml(file)], ignore_index=True)
    return data

# Transform data (convert height and weight units)
def transform(data):
    data['height'] = round(data['height'] * 0.0254, 2)  # inches to meters
    data['weight'] = round(data['weight'] * 0.45359237, 2)  # pounds to kilograms
    return data

# Load transformed data to a CSV file
def load_data(data):
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    data.to_csv(target_file, index=False)

# Log progress
def log_progress(message):
    timestamp = datetime.now().strftime('%Y-%b-%d-%H:%M:%S')
    with open(log_file, "a") as f:
        f.write(f"{timestamp}, {message}\n")

# ETL Process
log_progress("ETL Job Started")
log_progress("Extract phase Started")
extracted_data = extract()
log_progress("Extract phase Ended")

log_progress("Transform phase Started")
transformed_data = transform(extracted_data)
log_progress("Transform phase Ended")

log_progress("Load phase Started")
load_data(transformed_data)
log_progress("Load phase Ended")

log_progress("ETL Job Ended")
