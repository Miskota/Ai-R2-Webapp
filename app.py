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

st.title("Ai&R2 Bot - Artist Discovery")
st.write("This tool analyzes artists' tracks, extracts vocals, and prepares data for A&R evaluation.")

# Todo
# Plan
# Press button -> Show dataframe (Dynamically updates between calculation stages)
# ArtistId | Name | Hit Chance (%) | Singing Performance | Overall Score |
# 1        | John |   Not Ready    |         Not Ready   |   Not Ready   |   
# 1        | John |      76.53     |         Not Ready   |   Not Ready   |
# 1        | John |      76.53     |          4.5        |   Not Ready   |
# 1        | John |      76.53     |          4.5        |      80       |
table_placeholder = st.empty()

if st.button("Select 10 Random Artists"):
    df_artists = get_random_artists(conn, 10)

    df_artists_display = df_artists[["Name"]].copy()
    df_artists_display["Singing Performance"] = "Not ready"
    df_artists_display["Hit Chance (%)"] = "Not ready"
    df_artists_display["Overall Score"] = "Not ready"

    #st.subheader("Selected Artists & Tracks")
    table_placeholder.dataframe(df_artists_display)



    audio_base = Path("audio")
    file_list = [audio_base / f for f in df_artists["FileName"]]

    mos_dict = batch_predict_mos(file_list)
    mos_dict = {Path(k).name: round(v, 2) for k, v in mos_dict.items()}

    df_artists_display["Singing Performance"] = df_artists["FileName"].map(mos_dict)
    #st.subheader("After MOS Prediction")
    table_placeholder.dataframe(df_artists_display)




    streaming_features = [
        "danceability", "energy", "key", "loudness", "mode",
        "speechiness", "acousticness", "instrumentalness",
        "liveness", "valence", "tempo", "duration_ms",
        "time_signature", "chorus_hit", "sections"
    ]
    scores = hit_predictor(df_artists, streaming_features)
    scores_clean = {Path(f).name: score for f, score in zip(df_artists["FileName"], scores)}
    df_artists_display["Hit Chance (%)"] = df_artists["FileName"].map(scores_clean)
    df_artists_display["Hit Chance (%)"] = (df_artists_display["Hit Chance (%)"] * 100).round(2)
    #st.subheader("After Hit Chance Prediction")
    table_placeholder.dataframe(df_artists_display)



    normalized_mos = (df_artists_display["Singing Performance"]) / 5
    normalized_chance = df_artists_display["Hit Chance (%)"] / 100
    df_artists_display["Overall Score"] = (0.6 * normalized_mos + 0.4 * normalized_chance).round(2)

    # Sort ascending by overall score
    df_artists_display = df_artists_display.sort_values("Overall Score", ascending=False)
    table_placeholder.dataframe(df_artists_display)

    def highlight_top_10(val, df):
        # Ensure the column is numeric
        overall_scores = pd.to_numeric(df["Overall Score"], errors='coerce')
        threshold = overall_scores.quantile(0.9)
        return [
            "background-color: green" if pd.notna(v) and v >= threshold else ""
            for v in overall_scores
        ]
    

    #st.subheader("Final Results with Overall Score")
    table_placeholder.dataframe(
    df_artists_display.style
        .format({
            "Singing Performance": "{:.2f}",
            "Hit Chance (%)": "{:.2f}",
            "Overall Score": "{:.2f}"
        })
        .apply(lambda x: highlight_top_10(x, df_artists_display), axis=0)
)

    # streaming_features = [
    #     "danceability", "energy", "key", "loudness", "mode",
    #     "speechiness", "acousticness", "instrumentalness",
    #     "liveness", "valence", "tempo", "duration_ms",
    #     "time_signature", "chorus_hit", "sections"
    # ]

    # X_pred = df_artists[streaming_features]

    # st.subheader("Streaming Features for Prediction")
    # st.dataframe(X_pred)

    # scores = hit_predictor(df_artists, streaming_features)
    # print(scores)

    # if "FileName" not in df_artists.columns:
    #     st.warning("df_artists does not have a 'FileName' column.")
    # else:
    #     # Construct full paths if needed
    #     audio_base = Path("audio")  # change to your audio folder
    #     file_list = [audio_base / f for f in df_artists["FileName"]]

    #     # Batch predict MOS
    #     mos_dict = batch_predict_mos(file_list, base_dir=None)
    #     mos_dict = {Path(k).name: v for k, v in mos_dict.items()}
    #     print(mos_dict)
    #     # Add MOS to df_artists
    #     df_artists["Singing Performance"] = df_artists["FileName"].map(mos_dict)

    #     st.dataframe(df_artists[["ArtistId", "Name", "FileName", "Singing Performance"]])