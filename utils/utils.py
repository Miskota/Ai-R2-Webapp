# dependencies
# Demucs
# Torchaudio
import sqlite3
import os
import joblib
import subprocess
from pathlib import Path
from demucs import pretrained
from demucs.apply import apply_model
from transformers import AutoProcessor, WavLMModel
import torchaudio
import io
import pandas as pd
from tensorflow.keras.models import load_model
import torch
from dotenv import load_dotenv
load_dotenv()

CONN_STR = os.environ.get("CONN_STR")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models", "hit-or-flop")

def get_connection():
    conn = sqlite3.connect(CONN_STR, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def execute_query(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    conn.commit()
    cursor.close()
    conn.close()

def fetch_all(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_one(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def get_random_artists(conn, limit=10):
    query = f"""
        SELECT a.ArtistId, a.Name, t.TrackId, t.FileName,
               s.danceability, s.energy, s.key, s.loudness, s.mode,
               s.speechiness, s.acousticness, s.instrumentalness,
               s.liveness, s.valence, s.tempo, s.duration_ms,
               s.time_signature, s.chorus_hit, s.sections
        FROM Artists a
        INNER JOIN Tracks t ON t.ArtistId = a.ArtistId
        INNER JOIN StreamingData s ON s.TrackId = t.TrackId
        ORDER BY RANDOM()
        LIMIT {limit}
    """
    return pd.read_sql_query(query, conn)

def get_all_artists(conn):
    query = """
        SELECT a.ArtistId, a.Name, t.TrackId, t.FileName,
               s.danceability, s.energy, s.key, s.loudness, s.mode,
               s.speechiness, s.acousticness, s.instrumentalness,
               s.liveness, s.valence, s.tempo, s.duration_ms,
               s.time_signature, s.chorus_hit, s.sections
        FROM Artists a
        INNER JOIN Tracks t ON t.ArtistId = a.ArtistId
        INNER JOIN StreamingData s ON s.TrackId = t.TrackId
        ORDER BY a.Name ASC;
    """
    return pd.read_sql_query(query, conn)

def hit_predictor(df: pd.DataFrame, feature_columns: list):
    scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
    scaler = joblib.load(scaler_path)
    
    model_path = os.path.join(MODELS_DIR, "hit_or_flop_classifier.keras")
    model = load_model(model_path)

    X = df[feature_columns].values
    X_scaled = scaler.transform(X)

    predictions = model.predict(X_scaled)
    if predictions.shape[1] == 1:
        predictions = predictions.flatten()
    
    pred_percent = predictions * 100
    pred_percent = pred_percent.round(2)

    #return pred_percent
    return predictions