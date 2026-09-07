import streamlit as st
import json

st.set_page_config(page_title="Coffee Can Winner Model", layout="wide")

st.title("Coffee Can Winner Model")

# Load baseline Elo ratings from teams_elo.json
try:
    with open("teams_elo.json", "r") as f:
        elo_data = json.load(f)
except FileNotFoundError:
    elo_data = {"Dallas Cowboys": 1548, "New York Giants": 1452}

team_list = sorted(list(elo_data.keys()))

with st.form("matchup_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Away Team")
        away_team = st.selectbox("Select Away Team", team_list, index=0 if "Dallas Cowboys" in team_list else 0)
        away_base_elo = elo_data.get(away_team, 1500)
        away_elo = st.number_input(f"{away_team} Elo Rating", value=int(away_base_elo), step=1)
        away_adj = st.number_input("Away Adjustments (Points)", value=0.0, step=0.5, 
                                   help="+ for team boosts, - for key injuries/disadvantages")

    with col2:
        st.subheader("Home Team")
        home_team = st.selectbox("Select Home Team", team_list, index=1 if "New York Giants" in team_list else 0)
        home_base_elo = elo_data.get(home_team, 1500)
        home_elo = st.number_input(f"{home_team} Elo Rating", value=int(home_base_elo), step=1)
        home_adj = st.number_input("Home Adjustments (Points)", value=1.0, step=0.5, 
                                   help="Coaching upgrades, rest advantage, etc.")

    st.divider()
    
    st.subheader("Vegas Betting Market")
    col3, col4 = st.columns(2)
    
    with col3:
        # User explicitly selects the favorite
        favored_team = st.selectbox("Vegas Favored Team", [away_team, home_team])
    with col4:
        # Enter a positive spread number (e.g., 3.5 for 3.5-point favorite)
        raw_spread = st.number_input("Vegas Spread (Points)", value=2.5, min_value=0.0, step=0.5,
                                     help="Enter a positive number. E.g., if Ravens are favored by 3.5, select Ravens above and enter 3.5 here.")

    hfa_points = st.number_input("Home Field Advantage (Points)", value=1.5, step=0.5)
    is_divisional = st.checkbox("Divisional Matchup (+1.5 pt ATS boost to Underdog)", value=True)
    
    submit_button = st.form_submit_button("Run Analysis")

if submit_button:
    # Convert Vegas selection into standard Home Perspective Spread
    # If Home is favored, home_vegas_spread is negative (e.g., -3.5)
    # If Away is favored, home_vegas_spread is positive (e.g., +3.5)
    if favored_team == home_team:
        home_vegas_spread = -raw_spread
    else:
        home_vegas_spread = raw_spread

    # 1. Base Elo Difference (Home - Away)
    elo_diff = home_elo - away_elo
    base_spread = elo_diff / 25.0  # Negative means Away is favored by raw Elo
    
    # 2. Divisional Underdog Boost
    ats_adj = 0.0
    if is_divisional:
        if base_spread < 0:
            ats_adj += 1.5  # Boost Home Team
        else:
            ats_adj -= 1.5  # Boost Away Team

    # 3. Model Projected Line (from Home Perspective)
    projected_line = base_spread + hfa_points + home_adj - away_adj + ats_adj
    
    # Edge Calculation
    edge = projected_line - home_vegas_spread

    st.divider()
    st.header("📊 Model Analysis")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Elo Difference", f"{elo_diff:+d} Elo")
    
    # Display human-readable projected spread
    if projected_line < 0:
        proj_str = f"{home_team} {projected_line:+.2f}"
    else:
        proj_str = f"{away_team} {-projected_line:+.2f}"
    c2.metric("Model Projected Spread", proj_str)
    
    # Display human-readable Vegas line
    if home_vegas_spread < 0:
        vegas_str = f"{home_team} {home_vegas_spread:+.1f}"
    else:
        vegas_str = f"{away_team} {-home_vegas_spread:+.1f}"
    c3.metric("Vegas Line", vegas_str)

    st.subheader("Pick Recommendation")
    if abs(edge) >= 1.5:
        if edge > 0:
            # Value is on the Home Team
            st.success(f"**RECOMMENDED PICK:** **{home_team} ({home_vegas_spread:+.1f})** | Model Edge: **{abs(edge):.2f} pts**")
        else:
            # Value is on the Away Team
            st.success(f"**RECOMMENDED PICK:** **{away_team} ({-home_vegas_spread:+.1f})** | Model Edge: **{abs(edge):.2f} pts**")
    else:
        st.warning(f"**NO ACTIONABLE EDGE:** Model line matches Vegas within 1.5 pts threshold. Edge: **{abs(edge):.2f} pts**")
