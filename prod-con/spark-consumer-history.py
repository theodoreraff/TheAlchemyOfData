from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, to_date, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType
from dotenv import load_dotenv
import os
import findspark
import time


def get_schemas():
    item_schema = StructType([
        StructField("song_id", StringType(), True),
        StructField("album_id", StringType(), True),
        StructField("artist_id", StringType(), True),
        StructField("played_at", StringType(), True)
    ])

    return {
        "item_topic": item_schema
    }


def write_to_postgres(batch_df, batch_id):
    properties = {
        "user": os.getenv('POSTGRES_USER'),
        "password": os.getenv('POSTGRES_PASSWORD'),
        "driver": "org.postgresql.Driver",
        'url': os.getenv('POSTGRES_URL'),
        "dbtable": "fact_history",
    }

    if not batch_df.isEmpty():
        time.sleep(
            5)  # Wait for 5 seconds before writing to Postgres fact table in case of late-arriving data on dim tables
        batch_df.write.format('jdbc').options(**properties).mode('append').save()


def create_spark_session():
    return SparkSession.builder \
        .appName("fact-history-topic-spark-consumer") \
        .config("spark.jars", jdbc_jar) \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2") \
        .getOrCreate()


def read_from_kafka(spark, kafka_bootstrap_servers, topics):
    return spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", topics) \
        .load()


def parse_json_data(df, schemas):
    item_df = df.filter(col("topic") == "item_topic") \
        .withColumn("parsed_data", from_json(col("json_value"), schemas["item_topic"])) \
        .select(col("parsed_data.*"))

    # Use to_timestamp instead of to_date
    item_df = item_df.withColumn("played_at", to_timestamp(col("played_at"), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"))

    return item_df


def main():
    schemas = get_schemas()
    spark = create_spark_session()
    kafka_bootstrap_servers = "localhost:9092"
    topics = "item_topic"  # Only consume

    df = read_from_kafka(spark, kafka_bootstrap_servers, topics)
    df = df.selectExpr("CAST(value AS STRING) as json_value", "topic")
    df = parse_json_data(df, schemas)

    def process_batch(batch_df, batch_id):
        batch_df.printSchema()
        batch_df.show()
        write_to_postgres(batch_df, batch_id)

    query = df.writeStream \
        .foreachBatch(process_batch) \
        .outputMode("append") \
        .start()

    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("Process interrupted by user.")
    finally:
        query.stop()
        print("Query stopped.")
        spark.stop()
        print("Spark session stopped.")


if __name__ == "__main__":
    spark_home = "your spark home directory"
    jdbc_jar = f"{spark_home}/jars/PostgreSQL-42.7.0.jar"
    findspark.init(spark_home)
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    main()