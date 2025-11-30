import streamlit as st
from utils.startup import initialize_database
from utils.utils import get_connection

def startup():
    initialize_database()
    return get_connection()

conn = startup()

st.title("A&R Bot – Artist Discovery")

st.write("This tool analyzes artists' tracks, extracts vocals, and prepares data for A&R evaluation.")