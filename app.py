import streamlit as st
import json

st.set_page_config(page_title="Coffee Can Winner Model", layout="wide")

st.title("Coffee Can Winner Model")

# Key Numbers definition for NFL betting margins
KEY_NUMBERS = [3, 6, 7, 10, 14]

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
                                   help="+ for team boosts, - for key injuries/disadvantages/travel fatigue")

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
        raw_spread = st.number_input("Vegas Spread (Points)", value=3.5, min_value=0.0, step=0.5,
                                     help="Enter a positive number. E.g., if Rams are favored by 3.5, select Rams above and enter 3.5 here.")

    hfa_points = st.number_input("Home Field Advantage (Points)", value=1.5, step=0.5, 
                                 help="Set to 0.0 for international neutral-site games like Melbourne, London, or Munich.")
    is_divisional = st.checkbox("Divisional Matchup (+1.5 pt ATS boost to Underdog)", value=True)
    
    submit_button = st.form_submit_button("Run Analysis")

if submit_button:
    # Convert Vegas selection into standard Home Perspective Spread
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
    abs_edge = abs(edge)

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

    # Determine recommended side
    if edge > 0:
        rec_team = home_team
        rec_spread = home_vegas_spread
    else:
        rec_team = away_team
        rec_spread = -home_vegas_spread

    st.subheader("Pick Recommendation")
    if abs_edge >= 1.5:
        st.success(f"**RECOMMENDED PICK:** **{rec_team} ({rec_spread:+.1f})** | Model Edge: **{abs_edge:.2f} pts**")
    else:
        st.warning(f"**NO ACTIONABLE EDGE:** Model line matches Vegas within 1.5 pts threshold. Edge: **{abs_edge:.2f} pts**")

    # ---------------------------------------------------------
    # KEY NUMBERS & SPREAD VALUE ANALYSIS
    # ---------------------------------------------------------
    st.divider()
    st.subheader("🎯 Key Number & Hook Line Analysis")
    
    # Identify crossed key numbers between Vegas Line and Model Projected Line
    vegas_abs = abs(home_vegas_spread)
    proj_abs = abs(projected_line)
    lower_bound = min(vegas_abs, proj_abs)
    upper_bound = max(vegas_abs, proj_abs)
    
    crossed_keys = [k for k in KEY_NUMBERS if lower_bound < k < upper_bound or (lower_bound <= k and k <= upper_bound and lower_bound != upper_bound)]
    
    # Key Number Alerts
    if crossed_keys:
        key_str = ", ".join([str(k) for k in crossed_keys])
        st.info(f"🔑 **Key Numbers Crossed ({key_str} Points):** Your model edge spans across crucial NFL betting key numbers ({key_str}). Spanning a key number significantly increases win probability over market consensus.")
    
    # Half-Point "Hook" Value Check (+3.5, +7.5, -2.5, -6.5)
    if raw_spread in [3.5, 7.5, 10.5, 14.5]:
        if (favored_team != rec_team):
            st.success(f"⚡ **HIGH-VALUE HOOK ALERT:** You are taking an underdog at **+{raw_spread}**. The **+0.5 hook** protects against the most common NFL margins of victory ({int(raw_spread)})—converting potential pushes into outright wins!")
        else:
            st.warning(f"⚠️ **HOOK HAZARD:** You are laying points with a favorite at **-{raw_spread}**. Be aware that losing by exactly {int(raw_spread)} points results in a loss instead of a push. Consider waiting for a line move to -3.0 or buying a half-point.")
    elif raw_spread in [2.5, 6.5, 9.5, 13.5]:
        if (favored_team == rec_team):
            st.success(f"⚡ **HIGH-VALUE FAVORITE LINE:** You are laying **-{raw_spread}** with the favorite. Staying under the key number of {int(raw_spread) + 1} points provides critical protection if the favorite wins by a standard margin.")
