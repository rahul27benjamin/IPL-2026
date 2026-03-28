import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("IPL Connection Test")

# This will pull the URL from your "Secrets"
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(worksheet="Scores", ttl=0)
    st.write("✅ Connection Successful! Here is your data:")
    st.dataframe(df)
except Exception as e:
    st.error(f"❌ Connection Failed: {e}")
    st.info("Check your Secrets and Tab names.")
