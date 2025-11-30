# dependencies
# Demucs
# Torchaudio
import sqlite3
import os
import subprocess
from pathlib import Path
from demucs import pretrained
from demucs.apply import apply_model
import torchaudio
import torch
from dotenv import load_dotenv
load_dotenv()

CONN_STR = os.environ.get("CONN_STR")

def get_connection():
    conn = sqlite3.connect(CONN_STR)
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

def extract_vocals(input_wav: str, output_dir: str = "./vocals") -> str:
    input_wav = Path(input_wav)
    output_dir = Path(output_dir)

    if not input_wav.exists():
        raise FileNotFoundError(f"Input file not found: {input_wav}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load audio
    wav, sr = torchaudio.load(input_wav)

    # Load pre-trained model
    model = pretrained.get_model("htdemucs")
    model.to("cuda" if torch.cuda.is_available() else "cpu")
    model.eval()

    # Apply model
    with torch.no_grad():
        results = apply_model(model, wav.unsqueeze(0), sr)

    # Extract vocals track
    vocals = results[0][model.sources.index("vocals")]

    # Save file
    output_path = output_dir / f"{input_wav.stem}_vocals.wav"
    torchaudio.save(output_path, vocals.cpu(), sr)

    return str(output_path)
