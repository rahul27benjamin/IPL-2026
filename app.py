import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("Final System Check")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # This reads the WHOLE sheet, ignoring tab names.
    data = conn.read(ttl=0) 
    st.success("✅ THE CONNECTION IS ALIVE!")
    st.write("I found these tabs:", list(data.keys()) if isinstance(data, dict) else "Data Found!")
    st.dataframe(data)
except Exception as e:
    st.error("❌ THE CONNECTION IS BROKEN")
    st.code(str(e)) # This will print the RAW error from Google
