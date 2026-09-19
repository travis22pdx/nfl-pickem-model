import streamlit as st
import json

st.set_page_config(page_title="Coffee Can Winner Model", layout="wide")
st.title("Coffee Can Winner Model — ATS Analysis")

# Key NFL Betting Margins
KEY_NUMBERS = [3, 5, 6, 7, 10, 14]

# 1. Load baseline Elo ratings
try:
    with open("teams_elo.json", "r") as f:
        elo_data = json.load(f)
except FileNotFoundError:
    elo_data = {"Minnesota Vikings": 1538, "Chicago Bears": 1554}

team_list = sorted(list(elo_data.keys()))

with st.form("matchup_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Away Team")
        away_team = st.selectbox("Select Away Team", team_list, index=team_list.index("Minnesota Vikings") if "Minnesota Vikings" in team_list else 0)
        away_base_elo = elo_data.get(away_team, 1500)
        away_elo = st.number_input(f"{away_team} Base Elo", value=int(away_base_elo), step=1)
        away_adj = st.number_input("Away Adjustments (Points)", value=0.0, step=0.5, 
                                   help="+ for boosts, - for key injuries/travel fatigue")

    with col2:
        st.subheader("Home Team")
        home_team = st.selectbox("Select Home Team", team_list, index=team_list.index("Chicago Bears") if "Chicago Bears" in team_list else 0)
        home_base_elo = elo_data.get(home_team, 1500)
        home_elo = st.number_input(f"{home_team} Base Elo", value=int(home_base_elo), step=1)
        home_adj = st.number_input("Home Adjustments (Points)", value=1.0, step=0.5, 
                                   help="Coaching upgrades, rest advantage, etc.")

    st.divider()
    st.subheader("Vegas Betting Market")
    
    col3, col4 = st.columns(2)
    with col3:
        favored_team = st.selectbox("Vegas Favored Team", [away_team, home_team], index=1)
    with col4:
        raw_spread = st.number_input("Vegas Line (Points)", value=5.5, min_value=0.0, step=0.5,
                                     help="Enter favorite's line as a positive number (e.g., 5.5 for a 5.5-point favorite).")

    hfa_points = st.number_input("Home Field Advantage (Points)", value=1.5, step=0.5)
    is_divisional = st.checkbox("Divisional Matchup (+1.5 pt ATS boost to Underdog)", value=True)
    
    submit_button = st.form_submit_button("Run Analysis")

if submit_button:
    # Convert Vegas selection into Home Perspective Spread
    # Example: If Bears are home favorites by 5.5 -> home_vegas_spread = -5.5
    if favored_team == home_team:
        home_vegas_spread = -raw_spread
        away_vegas_spread = raw_spread
    else:
        home_vegas_spread = raw_spread
        away_vegas_spread = -raw_spread

    # 1. Base Elo Difference (Home - Away)
    elo_diff = home_elo - away_elo
    base_spread = elo_diff / 25.0  # Negative = Away favored by Elo math
    
    # 2. Divisional Underdog Boost
    ats_adj = 0.0
    if is_divisional:
        if base_spread < 0:
            ats_adj += 1.5  # Home is underdog, boost Home
        else:
            ats_adj -= 1.5  # Away is underdog, boost Away

    # 3. Model Projected Line (Home Perspective)
    # Negative means Home team should be favored by X points
    projected_home_line = base_spread + hfa_points + home_adj - away_adj + ats_adj
    
    # Calculate Edge relative to Home Team (Projected Home Margin - Vegas Home Line)
    # Positive edge = Model is MORE bullish on Home Team than Vegas
    # Negative edge = Model is MORE bullish on Away Team than Vegas
    home_edge = projected_home_line - home_vegas_spread
    abs_edge = abs(home_edge)

    st.divider()
    st.header("📊 Model Analysis & Pick Recommendation")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Elo Difference", f"{elo_diff:+d} Elo")
    
    # Readable Model Projection
    if projected_home_line < 0:
        proj_str = f"{home_team} {projected_home_line:+.1f}"
    else:
        proj_str = f"{away_team} {-projected_home_line:+.1f}"
    c2.metric("Model Projected Spread", proj_str)
    
    # Readable Vegas Line
    if home_vegas_spread < 0:
        vegas_str = f"{home_team} {home_vegas_spread:+.1f}"
    else:
        vegas_str = f"{away_team} {away_vegas_spread:+.1f}"
    c3.metric("Vegas Line", vegas_str)

    # Determine ATS Pick Side
    # Note: If projected_home_line is less than home_vegas_spread (e.g. Proj -3.4 vs Vegas -5.5),
    # the model thinks Home will cover LESS than Vegas requires -> Pick Away Team!
    if projected_home_line > home_vegas_spread:
        recommended_team = home_team
        recommended_line = home_vegas_spread
        underdog_check = (favored_team != home_team)
    else:
        recommended_team = away_team
        recommended_line = away_vegas_spread
        underdog_check = (favored_team != away_team)

    st.subheader("🎯 Final Pick Recommendation")
    
    # Display clear pick recommendation
    if abs_edge >= 1.5:
        st.success(f"**RECOMMENDED ATS PICK:** **{recommended_team} ({recommended_line:+.1f})** | Model Edge: **{abs_edge:.1f} pts**")
    elif abs_edge >= 0.5 and underdog_check and raw_spread in [3.5, 4.5, 5.5, 7.5]:
        st.info(f"🐶 **VALUE UNDERDOG PICK:** **{recommended_team} ({recommended_line:+.1f})** | Edge: **{abs_edge:.1f} pts** (High value on key underdog hook margin)")
    else:
        st.warning(f"**NO ACTIONABLE EDGE:** Model projection matches Vegas line within 1.5 pts. (Edge: {abs_edge:.1f} pts)")

    # Key Number Crossing Details
    vegas_abs = abs(home_vegas_spread)
    proj_abs = abs(projected_home_line)
    lower_b = min(vegas_abs, proj_abs)
    upper_b = max(vegas_abs, proj_abs)
    crossed = [k for k in KEY_NUMBERS if lower_b < k < upper_b or (lower_b <= k <= upper_b and lower_b != upper_b)]
    
    if crossed:
        key_str = ", ".join([str(k) for k in crossed])
        st.caption(f"🔑 **Key Numbers Crossed:** Game edge spans key NFL betting margins ({key_str} pts).")
