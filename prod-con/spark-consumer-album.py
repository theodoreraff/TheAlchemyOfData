from pyspark.sql import SparkSession # Core Spark SQL library
from pyspark.sql.functions import from_json, col, when, to_date # Spark SQL functions for data manipulation
from pyspark.sql.types import StructType, StructField, StringType, IntegerType # Spark SQL data types for defining schemas
from dotenv import load_dotenv # To load environment variables from a .env file
import os # For interacting with the operating system (e.g., environment variables)
import findspark # To locate Spark installation

# Load environment variables from the .env file located in the parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_schemas():
    """
    Defines the Spark SQL schema for the 'album_topic' data.
    This schema is used to parse incoming JSON data from Kafka.
    """
    album_schema = StructType([
        StructField("album_id", StringType(), True),
        StructField("title", StringType(), True),
        StructField("total_tracks", IntegerType(), True),
        StructField("release_date", StringType(), True),
        StructField("external_url", StringType(), True),
        StructField("image_url", StringType(), True),
        StructField("label", StringType(), True),
        StructField("popularity", IntegerType(), True)
    ])

    return {
        "album_topic": album_schema
    }


def write_to_postgres(batch_df, batch_id):
    """
    Writes a Spark DataFrame batch to the PostgreSQL 'dim_album' table.
    Uses JDBC connection properties loaded from environment variables.
    """
    properties = {
        "user": os.getenv('PSQL_DB_USER'),
        "password": os.getenv('PSQL_DB_PASSWORD'),
        "driver": "org.postgresql.Driver", # JDBC driver for PostgreSQL
        'url': os.getenv('PSQL_DB_LINK'), # Database connection URL
        "dbtable": "dim_album", # Target table in PostgreSQL
    }

    # Only write if the DataFrame batch is not empty
    if not batch_df.isEmpty():
        batch_df.write.format('jdbc').options(**properties).mode('append').save()


def create_spark_session():
    """
    Creates and configures a SparkSession for the consumer application.
    Configures the PostgreSQL JDBC driver and Kafka package for Spark SQL.
    """
    return SparkSession.builder \
        .appName("album-topic-spark-consumer") \
        .config("spark.jars", jdbc_jar) \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2") \
        .getOrCreate()


def read_from_kafka(spark_session, kafka_bootstrap_servers, topics):
    """
    Reads a streaming DataFrame from specified Kafka topics.
    """
    return spark_session.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", topics) \
        .load()


def parse_json_data(df, schemas):
    """
    Parses JSON data from the Kafka stream into a structured DataFrame
    based on the defined schema for 'album_topic'.
    """
    album_df = df.filter(col("topic") == "album_topic") \
                 .withColumn("parsed_data", from_json(col("json_value"), schemas["album_topic"])) \
                 .select(col("parsed_data.*"))

    # Convert 'release_date' string to a proper DateType
    album_df = album_df.withColumn("release_date", to_date(col("release_date")))

    return album_df


def main():
    """
    Main function to set up and run the Spark Streaming consumer for album data.
    It reads from Kafka, parses data, and writes processed data to PostgreSQL.
    """
    schemas = get_schemas() # Get the defined schemas
    spark = create_spark_session() # Create SparkSession
    kafka_bootstrap_servers = "localhost:9092" # Kafka broker address
    topics = "album_topic"  # Topic to subscribe to

    # Read streaming data from Kafka
    df = read_from_kafka(spark, kafka_bootstrap_servers, topics)
    # Cast Kafka value to string and select topic column for filtering
    df = df.selectExpr("CAST(value AS STRING) as json_value", "topic")
    # Parse the JSON string into structured DataFrame
    df = parse_json_data(df, schemas)

    def process_batch(batch_df, batch_id):
        """Function to process each micro-batch of the streaming data."""
        print(f"--- Processing Batch ID: {batch_id} ---")
        batch_df.printSchema() # Print schema of the batch
        batch_df.show(truncate=False) # Show sample data in the batch
        write_to_postgres(batch_df, batch_id) # Write batch to PostgreSQL

    # Start the Spark Streaming query
    query = df.writeStream \
        .foreachBatch(process_batch) \
        .outputMode("append") \
        .start()

    try:
        query.awaitTermination() # Wait for the streaming query to terminate
    except KeyboardInterrupt:
        print("Process interrupted by user.") # Handle graceful shutdown
    finally:
        query.stop() # Stop the streaming query
        print("Query stopped.")
        spark.stop() # Stop the Spark session
        print("Spark session stopped.")


if __name__ == "__main__":
    # Initialize findspark to locate Spark installation
    spark_home = os.getenv("SPARK_HOME") # Get SPARK_HOME from environment variable
    if not spark_home:
        print("Error: SPARK_HOME environment variable not set. Please set it to your Spark installation directory.")
        exit(1) # Exit if SPARK_HOME is not set

    # Path to PostgreSQL JDBC driver JAR file
    jdbc_jar = f"{spark_home}/jars/postgresql-42.7.0.jar" # Ensure this path is correct for your setup
    findspark.init(spark_home) # Initialize findspark

    # Load environment variables before running main
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

    main() # Run the main consumer logic