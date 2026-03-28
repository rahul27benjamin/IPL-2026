import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- Configuration ---
# PASTE YOUR FULL GOOGLE SHEET URL HERE
# Ensure "Anyone with the link" is an "Editor" in the Share settings
# SHEET_URL = "https://docs.google.com/spreadsheets/d/1jbzcb-3qgMN0VCorXNxmNVnuNEd3X-XifCqPDwDoSZ8/edit"
FAMILIES = ["Dhinakarans", "Davids", "Moses", "Benjamins"]
TEAMS = ["CSK", "RCB", "MI", "GT", "DC", "SRH", "LSG", "RR", "PBKS", "KKR"]

st.set_page_config(page_title="Family IPL 2026", page_icon="🏏")
st.title("🏏 Family IPL Leaderboard")

# --- 1. Connection Logic ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # Use a short TTL for development, then 0 for live
        s_df = conn.read(worksheet="Scores", ttl=0)
        h_df = conn.read(worksheet="History", ttl=0)
        return s_df, h_df
    except Exception as e:
        # THIS IS THE IMPORTANT PART: It will show the REAL error on your screen
        st.error(f"❌ Actual Google Error: {e}")
        
        # Create empty data so the rest of the app doesn't crash
        s_err = pd.DataFrame(columns=["Family", "Points"])
        h_err = pd.DataFrame(columns=["Match #", "Matchup", "Winner", "Winners", "Pts"])
        return s_err, h_err

scores_df, history_df = get_data()

# --- 5. Standings & History (SAFE VERSION) ---
st.divider()
tab1, tab2 = st.tabs(["🏆 Standings", "📜 History"])

with tab1:
    if not scores_df.empty and "Points" in scores_df.columns:
        # Sort and display
        display_df = scores_df.sort_values("Points", ascending=False).set_index("Family")
        st.table(display_df)
    else:
        st.warning("Waiting for data from Google Sheets... Check your 'Scores' tab headers.")

with tab2:
    if not history_df.empty:
        st.dataframe(history_df.set_index("Match #"), use_container_width=True)
    else:
        st.info("No match history found in the Google Sheet.")

scores_df, history_df = get_data()

# Initialize Session State variables if not present
if "current_match" not in st.session_state: st.session_state.current_match = None
if "match_locked" not in st.session_state: st.session_state.match_locked = False
if "picks_locked" not in st.session_state: st.session_state.picks_locked = False
if "last_win_msg" not in st.session_state: st.session_state.last_win_msg = None
if "team_selections" not in st.session_state: st.session_state.team_selections = {f: "None" for f in FAMILIES}

# --- 2. Admin Sidebar ---
with st.sidebar:
    st.header("⚙️ Admin Controls")
    st.metric("Total Matches Played", len(history_df))
    
    if st.button("🆕 Start New Match Entry"):
        st.session_state.current_match = {"team1": "CSK", "team2": "MI"}
        st.session_state.match_locked = False
        st.session_state.picks_locked = False
        st.session_state.last_win_msg = None
        st.session_state.team_selections = {f: "None" for f in FAMILIES}
        st.rerun()
    
    if st.session_state.picks_locked:
        if st.button("🔓 Unlock Family Picks"):
            st.session_state.picks_locked = False
            st.rerun()

# --- 3. Victory Popup ---
if st.session_state.last_win_msg:
    st.balloons()
    st.success(st.session_state.last_win_msg)
    if st.button("Clear & View Standings"):
        st.session_state.last_win_msg = None
        st.rerun()

# --- 4. Steps Section ---
if st.session_state.current_match and not st.session_state.last_win_msg:
    st.header("Step 1: Set Today's Match")
    t1 = st.selectbox("Team 1", TEAMS, index=TEAMS.index(st.session_state.current_match["team1"]), disabled=st.session_state.match_locked)
    t2 = st.selectbox("Team 2", TEAMS, index=TEAMS.index(st.session_state.current_match["team2"]), disabled=st.session_state.match_locked)

    if not st.session_state.match_locked:
        if st.button("Confirm Matchup"):
            st.session_state.current_match = {"team1": t1, "team2": t2}
            st.session_state.match_locked = True
            st.rerun()
    else:
        st.info(f"Match: **{t1} vs {t2}**")
        if not st.session_state.picks_locked:
            if st.button("✏️ Edit Matchup"):
                st.session_state.match_locked = False
                st.rerun()

    if st.session_state.match_locked:
        st.divider()
        st.header("Step 2: Family Picks")
        cols = st.columns(4)
        match_options = [t1, t2]
        for i, family in enumerate(FAMILIES):
            with cols[i]:
                st.session_state.team_selections[family] = st.radio(
                    f"**{family}**", match_options, 
                    disabled=st.session_state.picks_locked, key=f"r_{family}"
                )

        if not st.session_state.picks_locked:
            if st.button("🔒 Lock All Picks"):
                st.session_state.picks_locked = True
                st.rerun()
        
        if st.session_state.picks_locked:
            st.divider()
            st.header("Step 3: Award Points")
            winner = st.selectbox("Who won?", ["Select Winner"] + match_options)
            if st.button("Submit Result"):
                if winner != "Select Winner":
                    winners = [f for f, t in st.session_state.team_selections.items() if t == winner]
                    pts = 4 if len(winners)==1 else (1 if len(winners)==4 else (2 if len(winners)>0 else 0))
                    
                    # Update Scores in DataFrame
                    for f in winners:
                        scores_df.loc[scores_df['Family'] == f, 'Points'] += pts
                    
                    # Update History
                    new_row = pd.DataFrame([{
                        "Match #": len(history_df) + 1,
                        "Matchup": f"{t1} vs {t2}",
                        "Winner": winner,
                        "Winners": ", ".join(winners),
                        "Pts": pts
                    }])
                    updated_history = pd.concat([history_df, new_row], ignore_index=True)
                    
                    # WRITE TO GOOGLE SHEETS
                    conn.update(spreadsheet=SHEET_URL, worksheet="Scores", data=scores_df)
                    conn.update(spreadsheet=SHEET_URL, worksheet="History", data=updated_history)
                    
                    st.session_state.last_win_msg = f"🎉 {winner} Won! {', '.join(winners)} get {pts} pts."
                    st.session_state.current_match = None
                    st.rerun()

# --- 5. Standings & History ---
st.divider()
tab1, tab2 = st.tabs(["🏆 Standings", "📜 History"])
with tab1:
    st.table(scores_df.sort_values("Points", ascending=False).set_index("Family"))
with tab2:
    if not history_df.empty:
        st.dataframe(history_df.set_index("Match #"), use_container_width=True)
