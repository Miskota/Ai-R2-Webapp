import streamlit as st
from utils.startup import initialize_database
from utils.utils import get_connection, get_random_artists, hit_predictor
from utils.predict_mos import batch_predict_mos
from pathlib import Path
import pandas as pd

if "db_initialized" not in st.session_state:
    initialize_database()
    st.session_state.db_initialized = True

if "conn" not in st.session_state:
    st.session_state.conn = get_connection()

conn = st.session_state.conn

st.title("A&R Bot - Artist Discovery")
st.write("This tool analyzes artists' tracks, extracts vocals, and prepares data for A&R evaluation.")

# Todo
# Plan
# Press button -> Show dataframe (Dynamically updates between calculation stages)
# ArtistId | Name | Hit Chance (%) | Singing Performance | Overall Score |
# 1        | John |   Not Ready    |         Not Ready   |   Not Ready   |   
# 1        | John |      76.53     |         Not Ready   |   Not Ready   |
# 1        | John |      76.53     |          4.5        |   Not Ready   |
# 1        | John |      76.53     |          4.5        |      80       |

if st.button("Select 10 Random Aritsts"):
    df_artists = get_random_artists(conn, 10)

    st.subheader("Selected Artists & Tracks")
    st.dataframe(df_artists)

    streaming_features = [
        "danceability", "energy", "key", "loudness", "mode",
        "speechiness", "acousticness", "instrumentalness",
        "liveness", "valence", "tempo", "duration_ms",
        "time_signature", "chorus_hit", "sections"
    ]

    X_pred = df_artists[streaming_features]

    st.subheader("Streaming Features for Prediction")
    st.dataframe(X_pred)

    scores = hit_predictor(df_artists, streaming_features)
    print(scores)

    if "FileName" not in df_artists.columns:
        st.warning("df_artists does not have a 'FileName' column.")
    else:
        # Construct full paths if needed
        audio_base = Path("audio")  # change to your audio folder
        file_list = [audio_base / f for f in df_artists["FileName"]]

        # Batch predict MOS
        mos_dict = batch_predict_mos(file_list, base_dir=None)
        mos_dict = {Path(k).name: v for k, v in mos_dict.items()}
        print(mos_dict)
        # Add MOS to df_artists
        df_artists["Singing Performance"] = df_artists["FileName"].map(mos_dict)

        st.dataframe(df_artists[["ArtistId", "Name", "FileName", "Singing Performance"]])