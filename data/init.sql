CREATE TABLE "Artists" (
        "ArtistId" INTEGER PRIMARY KEY,
        "Name" TEXT
);

CREATE TABLE "Tracks" (
        "TrackId" INTEGER PRIMARY KEY,
        "FileName" TEXT,
        "ArtistId" INTEGER,
        FOREIGN KEY ("ArtistId") REFERENCES "Artists"("ArtistId")
);

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
);

CREATE TABLE "Candidates" (
        "ArtistId" INTEGER,
        "SingingScore" REAL,
        "HitOrFlopChance" REAL,
        "OverallScore" REAL,
        FOREIGN KEY ("ArtistId") REFERENCES "Artists"("ArtistId")
);

COPY "Artists" ("ArtistId", "Name")
FROM '/docker-entrypoint-initdb.d/Artists.csv'
WITH (FORMAT csv, HEADER true);

COPY "Tracks" ("FileName", "ArtistId", "TrackId")
FROM '/docker-entrypoint-initdb.d/Tracks.csv'
WITH (FORMAT csv, HEADER true);

COPY "StreamingData" (
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "duration_ms",
    "time_signature",
    "chorus_hit",
    "sections",
    "TrackId",
    "StreamingDataId"
)
FROM '/docker-entrypoint-initdb.d/StreamingData.csv'
WITH (FORMAT csv, HEADER true);