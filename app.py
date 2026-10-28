import streamlit as st
#from utils.startup import initialize_database
from utils.utils import get_connection, get_random_artists, hit_predictor, get_all_artists, export_to_table
from utils.predict_mos import batch_predict_mos
import math
import time
from pathlib import Path
import pandas as pd

if "db_initialized" not in st.session_state:
    #initialize_database()
    st.session_state.db_initialized = True

if "df_artists_selected" not in st.session_state:
    st.session_state.df_artists_selected = None

if "conn" not in st.session_state:
    st.session_state.conn = get_connection()


conn = st.session_state.conn

st.set_page_config(
    page_title="Ai&R2 Artist Discovery",
    page_icon="🎵",
    layout="wide"
)

with st.sidebar:
    st.header("⚙️ Controls")

    run_random_button = st.button("🎲 Select Random Artists")
    show_all_button = st.button("📚 Show Full Database")
    export_button = st.button("📋 Create Reporting Table")
    view_report = st.button("📖 View Last Report")

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
subheader_placeholder = st.empty()
table_placeholder = st.empty()
progress = st.progress(0)

if show_all_button:
    df_all = get_all_artists(conn)

    subheader_placeholder.subheader("📚 Full Artist Database")
    table_placeholder.dataframe(
        df_all,
        use_container_width=True,
        hide_index=True
    )

if run_random_button:
    start = time.time()
    subheader_placeholder.subheader("Selected Artists & Tracks")
    progress.progress(20, text=" Selecting artists...")
    df_artists = get_random_artists(conn, 10)

    df_artists_display = df_artists[["ArtistId", "Name"]].copy()
    df_artists_display["Singing Performance"] = "Not ready"
    df_artists_display["Hit Chance (%)"] = "Not ready"
    df_artists_display["Overall Score"] = "Not ready"

    #st.subheader("Selected Artists & Tracks")
    table_placeholder.dataframe(df_artists_display)



    audio_base = Path("audio")
    file_list = [audio_base / f for f in df_artists["FileName"]]

    progress.progress(45, text=" Running MOS vocal quality prediction...")
    mos_dict = batch_predict_mos(file_list)
    mos_dict = {Path(k).name: v for k, v in mos_dict.items()}

    df_artists_display["Singing Performance"] = df_artists["FileName"].map(mos_dict)
    #st.subheader("After MOS Prediction")
    table_placeholder.dataframe(df_artists_display)




    streaming_features = [
        "danceability", "energy", "key", "loudness", "mode",
        "speechiness", "acousticness", "instrumentalness",
        "liveness", "valence", "tempo", "duration_ms",
        "time_signature", "chorus_hit", "sections"
    ]
    progress.progress(75, text=" Predicting hit chance...")
    scores = hit_predictor(df_artists, streaming_features)
    scores_clean = {Path(f).name: score for f, score in zip(df_artists["FileName"], scores)}
    df_artists_display["Hit Chance (%)"] = df_artists["FileName"].map(scores_clean)
    df_artists_display["Hit Chance (%)"] = df_artists_display["Hit Chance (%)"] * 100
    #st.subheader("After Hit Chance Prediction")
    table_placeholder.dataframe(df_artists_display)


    progress.progress(100, text=" Finalizing scores...")
    normalized_mos = df_artists_display["Singing Performance"].clip(1, 5) / 5
    normalized_chance = df_artists_display["Hit Chance (%)"] / 100
    # Unrounded scores for ranking; rounding is display-only
    df_artists_display["Overall Score"] = 0.6 * normalized_mos + 0.4 * normalized_chance

    # Sort descending by overall score, ties -> higher singing score
    df_artists_display = df_artists_display.sort_values(["Overall Score", "Singing Performance"], ascending=False)
    n_top = math.ceil(len(df_artists_display) * 0.1)
    selected = df_artists_display.head(n_top)


    #st.subheader("Final Results with Overall Score")
    table_placeholder.dataframe(
    df_artists_display.style
        .format({
            "Singing Performance": "{:.2f}",
            "Hit Chance (%)": "{:.2f}",
            "Overall Score": "{:.2f}"
        })
        .apply(lambda row: ["background-color: green" if row.name in selected.index else ""] * len(row), axis=1)
    )
    elapsed = round(time.time() - start, 2)
    progress.progress(100, text=f"Done! ({elapsed}s)")

    st.session_state.df_artists_selected = selected

if export_button:
    if st.session_state.df_artists_selected is not None and len(st.session_state.df_artists_selected) > 0:
        export_to_table(st.session_state.df_artists_selected, conn)
        subheader_placeholder.subheader("Data exported successfully.")
    else:
        subheader_placeholder.subheader("No data to export. Run a talent search first.")

if view_report:
    df = pd.read_sql(
        sql="""SELECT * FROM "Candidates";""",
        con=conn
    )
    subheader_placeholder.subheader("Last report's results")
    table_placeholder.dataframe(df)
    