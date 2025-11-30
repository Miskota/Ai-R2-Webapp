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

conn = sqlite3.connect(CONN_STR)
conn.execute("PRAGMA foreign_keys = ON")

artists_create_table = """
    CREATE TABLE "Artists" (
        "ArtistId" INTEGER PRIMARY KEY
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

# Todo: Extend with dataset columns
streaming_data_create_table = """
    CREATE TABLE "StreamingData" (
        "StreamingDataId" INTEGER PRIMARY KEY,
        "ArtistId" INTEGER,
        FOREIGN KEY("ArtistId") REFERENCES "Artists"("ArtistId")
    )
"""

potential_talents_create_table = """
    CREATE TABLE "Candidates" (
        "ArtistId" INTEGER,
        FOREIGN KEY ("ArtistId") REFERENCES "Artists"("ArtistId"),
        "SingingScore" REAL,
        "HitOrFlopChance" REAL,
        "OverallScore" REAL
    )
"""

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

for file, table in [
    ("/data/artists.csv", "Artists"),
    ("/data/tracks.csv", "Tracks"),
    ("/data/streaming_data.csv", "StreamingData")
]:
    df = pd.read_csv(file)
    df.to_sql(table, conn, if_exists="append", index=False)

print("Database initiated and filled successfully")
conn.close()