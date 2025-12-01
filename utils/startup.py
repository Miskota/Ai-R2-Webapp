# dependecies:
# db-sqlite3
# dotenv
# pandas
import sqlite3
import os
import csv
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
CONN_STR = os.environ.get("CONN_STR")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
data_dir = os.path.join(PROJECT_DIR, "data")

conn = sqlite3.connect(CONN_STR)
conn.execute("PRAGMA foreign_keys = ON")

artists_create_table = """
    CREATE TABLE "Artists" (
        "ArtistId" INTEGER PRIMARY KEY,
        "Name" TEXT
    )
"""

tracks_create_table = """
    CREATE TABLE "Tracks" (
        "TrackId" INTEGER PRIMARY KEY,
        "FileName" TEXT,
        "ArtistId" INTEGER,
        FOREIGN KEY ("ArtistId") REFERENCES "Artists"("ArtistId")
    )
"""

streaming_data_create_table = """
    CREATE TABLE "StreamingData" (
        "StreamingDataId" INTEGER PRIMARY KEY,
        "ArtistId" INTEGER,
        "TrackId" INTEGER,
        "danceability" FLOAT,
        "energy" FLOAT,
        "key" INTEGER,
        "loudness" FLOAT,
        "mode" INTEGER,
        "speechiness" FLOAT,
        "acousticness" FLOAT,
        "instrumentalness" FLOAT,
        "liveness" FLOAT,
        "valence" FLOAT,
        "tempo" FLOAT,
        "duration_ms" INTEGER,
        "time_signature" INTEGER,
        "chorus_hit" FLOAT,
        "sections" INTEGER,
        FOREIGN KEY("ArtistId") REFERENCES "Artists"("ArtistId")
    )
"""

potential_talents_create_table = """
    CREATE TABLE "Candidates" (
        "ArtistId" INTEGER,
        "SingingScore" REAL,
        "HitOrFlopChance" REAL,
        "OverallScore" REAL,
        FOREIGN KEY ("ArtistId") REFERENCES "Artists"("ArtistId")
    )
"""
def initialize_database():
    try:
        cursor = conn.cursor()
        cursor.execute(artists_create_table)
        cursor.execute(tracks_create_table)
        cursor.execute(streaming_data_create_table)
        cursor.execute(potential_talents_create_table)
        conn.commit()
    except Exception as e:
        print(f"Error while creating tables: {e}")
    finally:
        cursor.close()

    for file_name, table in [
        ("Artists.csv", "Artists"),
        ("Tracks.csv", "Tracks"),
        ("StreamingData.csv", "StreamingData")
    ]:
        file_path = os.path.join(data_dir, file_name)
        df = pd.read_csv(file_path)
        df.to_sql(table, conn, if_exists="append", index=False)

    print("Database initiated and filled successfully")
    conn.close()

if __name__ == "__main__":
    initialize_database()