import streamlit as st
import pandas as pd
import json
import os

# --- Configuration ---
FAMILIES = ["Dhinakarans", "Davids", "Moses", "Benjamins"]
TEAMS = ["CSK", "RCB", "MI", "GT", "DC", "SRH", "LSG", "RR", "PBKS", "KKR"]
DATA_FILE = 'ipl_game_data.json'

# --- 1. Data Logic ---
def load_data():
    default_structure = {
        "scores": {f: 0 for f in FAMILIES}, 
        "current_match": None, 
        "team_selections": {f: "None" for f in FAMILIES}, 
        "picks_locked": False,
        "match_locked": False,
        "history": [],
        "last_win_msg": None 
    }
    if not os.path.exists(DATA_FILE):
        return default_structure
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    for key, value in default_structure.items():
        if key not in data: data[key] = value
    return data

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Initialize Session State (Using 'ipl_data' consistently)
if 'ipl_data' not in st.session_state:
    st.session_state.ipl_data = load_data()

data = st.session_state.ipl_data

st.set_page_config(page_title="Family IPL 2026", page_icon="🏏")
st.title("🏏 Family IPL Leaderboard")

# --- 2. Admin Sidebar ---
with st.sidebar:
    st.header("⚙️ Admin Controls")
    st.metric("Total Matches Played", len(data["history"]))
    
    if st.button("🆕 Start New Match Entry"):
        st.session_state.ipl_data["current_match"] = {"team1": "CSK", "team2": "MI"} 
        st.session_state.ipl_data["team_selections"] = {f: "None" for f in FAMILIES}
        st.session_state.ipl_data["picks_locked"] = False
        st.session_state.ipl_data["match_locked"] = False
        st.session_state.ipl_data["last_win_msg"] = None 
        save_data(st.session_state.ipl_data)
        st.rerun()
    
    if data["picks_locked"]:
        st.divider()
        if st.button("🔓 Unlock Family Picks"):
            st.session_state.ipl_data["picks_locked"] = False
            save_data(st.session_state.ipl_data)
            st.rerun()

# --- 3. Persistent Victory Popup ---
if data["last_win_msg"]:
    st.balloons()
    st.success(data["last_win_msg"])
    if st.button("Clear & View Standings"):
        st.session_state.ipl_data["last_win_msg"] = None
        save_data(st.session_state.ipl_data)
        st.rerun()

# --- 4. Steps Section (Only shows if a match is active) ---
if data["current_match"] is not None and data["last_win_msg"] is None:
    
    # --- Step 1: Set Matchup ---
    st.header("Step 1: Set Today's Match")
    t1_input = st.selectbox("Team 1", TEAMS, index=TEAMS.index(data["current_match"]["team1"]), disabled=data["match_locked"])
    t2_input = st.selectbox("Team 2", TEAMS, index=TEAMS.index(data["current_match"]["team2"]), disabled=data["match_locked"])

    if not data["match_locked"]:
        if st.button("Confirm Matchup"):
            st.session_state.ipl_data["current_match"] = {"team1": t1_input, "team2": t2_input}
            st.session_state.ipl_data["match_locked"] = True
            save_data(st.session_state.ipl_data)
            st.rerun()
    else:
        st.info(f"Confirmed Matchup: **{data['current_match']['team1']} vs {data['current_match']['team2']}**")
        if not data["picks_locked"]:
            if st.button("✏️ Edit Matchup"):
                st.session_state.ipl_data["match_locked"] = False
                save_data(st.session_state.ipl_data)
                st.rerun()

    # --- Step 2: Family Selection ---
    if data["match_locked"]:
        st.divider()
        t1_n, t2_n = data["current_match"]["team1"], data["current_match"]["team2"]
        st.header(f"Step 2: {t1_n} vs {t2_n}")
        
        match_options = [t1_n, t2_n]
        cols = st.columns(4)
        for i, family in enumerate(FAMILIES):
            with cols[i]:
                current_val = data["team_selections"][family]
                start_idx = match_options.index(current_val) if current_val in match_options else 0
                data["team_selections"][family] = st.radio(
                    f"**{family}**", match_options, index=start_idx, 
                    disabled=data["picks_locked"], key=f"radio_{family}"
                )

        if not data["picks_locked"]:
            if st.button("🔒 Finalize & Lock Picks"):
                st.session_state.ipl_data["picks_locked"] = True
                save_data(st.session_state.ipl_data) # Fixed the typo here
                st.rerun()

        # --- Step 3: Results ---
        if data["picks_locked"]:
            st.divider()
            st.header("Step 3: Award Points")
            winner = st.selectbox("Who won?", ["Select Winner", t1_n, t2_n])
            
            if st.button("Submit Result"):
                if winner != "Select Winner":
                    winners_list = [f for f, t in data["team_selections"].items() if t == winner]
                    count = len(winners_list)
                    pts = 4 if count == 1 else (1 if count == 4 else (2 if count > 0 else 0))
                    
                    if count > 0:
                        for f in winners_list: st.session_state.ipl_data["scores"][f] += pts
                    
                    st.session_state.ipl_data["history"].append({
                        "Match #": len(data["history"]) + 1,
                        "Matchup": f"{t1_n} vs {t2_n}",
                        "Winner": winner,
                        "Winners": ", ".join(winners_list),
                        "Pts": pts
                    })
                    
                    st.session_state.ipl_data["last_win_msg"] = f"🎉 {winner} Victory! {', '.join(winners_list)} earned {pts} points each."
                    st.session_state.ipl_data["current_match"] = None
                    st.session_state.ipl_data["picks_locked"] = False
                    st.session_state.ipl_data["match_locked"] = False
                    
                    save_data(st.session_state.ipl_data)
                    st.rerun()

# --- 5. Leaderboard & History Tabs ---
st.divider()
tab1, tab2 = st.tabs(["🏆 Standings", "📜 History"])
with tab1:
    df = pd.DataFrame([{"Family": f, "Points": data["scores"][f]} for f in FAMILIES]).sort_values("Points", ascending=False)
    df.index = range(1, len(df) + 1)
    st.table(df)
with tab2:
    if data["history"]:
        h_df = pd.DataFrame(data["history"])
        h_df.set_index("Match #", inplace=True)
        st.dataframe(h_df, use_container_width=True)
    else:
        st.info("No history yet. Start a new match in the sidebar!")
