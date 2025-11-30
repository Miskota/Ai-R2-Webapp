import streamlit as st

# Title of the app
st.title("Ai&R2 - Seeking hidden talents")

# Display text
st.write("Hello, World!")

# Optional: user input example
name = st.text_input("Enter your name")
if name:
    st.write(f"Hello, {name}!")