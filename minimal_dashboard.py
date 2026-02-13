"""
Team Scorecard Dashboard - With Role-Based Sign-In
"""

import streamlit as st
import pandas as pd
import random

# Page config
st.set_page_config(page_title="Talent Score", page_icon="🏆", layout="wide")

# Simple scoring function
def calculate_score(violations):
    """Start at 100, subtract penalties"""
    return max(0, 100 - (violations * 5))

# Generate flags for each person's issues
def generate_flags(person_data, num_issues):
    """Generate top 3 issue flags with severity"""
    flags = []
    
    flag_types = [
        ("Feedback delayed >72hrs", "🔴"),
        ("Stage stuck >7 days", "🔴"),
        ("Missing interview feedback", "🟡"),
        ("Slow candidate response", "🟡"),
        ("Scheduling conflicts", "🟢"),
        ("Profile incomplete", "🟢"),
    ]
    
    for i in range(min(3, num_issues)):
        flag = random.choice(flag_types)
        candidate = person_data['candidate_id'].iloc[min(i, len(person_data)-1)]
        flags.append({
            'severity': flag[1],
            'issue': flag[0],
            'candidate': candidate
        })
    
    severity_order = {'🔴': 0, '🟡': 1, '🟢': 2}
    flags.sort(key=lambda x: severity_order[x['severity']])
    
    return flags

# Load data and calculate team scores
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('sample_ats_export.csv')
        
        # Calculate individual scores first
        recruiter_violations = df.groupby('recruiter_name').size().reset_index(name='violations')
        recruiter_violations['score'] = recruiter_violations['violations'].apply(calculate_score)
        
        hm_violations = df.groupby('hiring_manager_name').size().reset_index(name='violations')
        hm_violations['score'] = hm_violations['violations'].apply(calculate_score)
        
        # Calculate TEAM scores (recruiter + HM pairs)
        team_data = df.groupby(['recruiter_name', 'hiring_manager_name']).agg({
            'requisition_id': 'nunique',
            'candidate_id': 'count'
        }).reset_index()
        
        team_data.columns = ['recruiter', 'hm', 'roles', 'candidates']
        
        # Add individual scores to teams
        team_data = team_data.merge(
            recruiter_violations[['recruiter_name', 'score', 'violations']],
            left_on='recruiter',
            right_on='recruiter_name',
            how='left'
        ).rename(columns={'score': 'recruiter_score', 'violations': 'recruiter_violations'})
        
        team_data = team_data.merge(
            hm_violations[['hiring_manager_name', 'score', 'violations']],
            left_on='hm',
            right_on='hiring_manager_name',
            how='left'
        ).rename(columns={'score': 'hm_score', 'violations': 'hm_violations'})
        
        # Calculate team score (average of recruiter + HM)
        team_data['team_score'] = (team_data['recruiter_score'] + team_data['hm_score']) / 2
        team_data['total_violations'] = team_data['recruiter_violations'] + team_data['hm_violations']
        
        # Create team name
        team_data['team_name'] = team_data['recruiter'].str.split().str[0] + " & " + team_data['hm'].str.split().str[0]
        
        # Clean up columns
        team_data = team_data[['team_name', 'recruiter', 'hm', 'recruiter_score', 'hm_score', 
                                'team_score', 'total_violations', 'roles', 'candidates']]
        
        return df, team_data, recruiter_violations, hm_violations
        
    except FileNotFoundError:
        st.error("❌ Please upload sample_ats_export.csv")
        return None, None, None, None

# Sign-in page
def show_signin():
    """Display sign-in page with role selection"""
    
    # Center content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Logo/Title
        st.markdown("""
            <div style='text-align: center; padding: 40px 0;'>
                <h1 style='font-size: 4em; margin: 0; color: #1f77b4;'>⭐</h1>
                <h1 style='font-size: 3em; margin: 10px 0; font-weight: bold;'>Talent Score</h1>
                <p style='font-size: 1.2em; color: #666; margin-top: 10px;'>
                    Performance tracking for recruiting teams
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Role selection
        st.markdown("<h3 style='text-align: center; margin-bottom: 30px;'>Select Your Role</h3>", unsafe_allow_html=True)
        
        # Create three big buttons
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.markdown("""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 40px 20px; border-radius: 15px; text-align: center; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 10px;'>
                    <h2 style='color: white; font-size: 2.5em; margin: 0;'>👥</h2>
                    <h3 style='color: white; margin: 15px 0 5px 0;'>Recruiter</h3>
                    <p style='color: rgba(255,255,255,0.8); font-size: 0.9em;'>
                        View your performance and team scores
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Sign in as Recruiter", key="btn_recruiter", use_container_width=True):
                st.session_state['role'] = 'recruiter'
                st.rerun()
        
        with col_b:
            st.markdown("""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                            padding: 40px 20px; border-radius: 15px; text-align: center; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 10px;'>
                    <h2 style='color: white; font-size: 2.5em; margin: 0;'>🎯</h2>
                    <h3 style='color: white; margin: 15px 0 5px 0;'>Hiring Team</h3>
                    <p style='color: rgba(255,255,255,0.8); font-size: 0.9em;'>
                        Track hiring manager metrics
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Sign in as Hiring Team", key="btn_hm", use_container_width=True):
                st.session_state['role'] = 'hiring_team'
                st.rerun()
        
        with col_c:
            st.markdown("""
                <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                            padding: 40px 20px; border-radius: 15px; text-align: center; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 10px;'>
                    <h2 style='color: white; font-size: 2.5em; margin: 0;'>🏆</h2>
                    <h3 style='color: white; margin: 15px 0 5px 0;'>Leader</h3>
                    <p style='color: rgba(255,255,255,0.8); font-size: 0.9em;'>
                        Full team analytics and insights
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Sign in as Leader", key="btn_leader", use_container_width=True):
                st.session_state['role'] = 'leader'
                st.rerun()
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #999; font-size: 0.9em;'>© 2026 Talent Score. Demo version.</p>", unsafe_allow_html=True)

# Team Leaderboard Page
def show_team_leaderboard(teams, df):
    """Show team rankings"""
    st.header("🏆 Team Leaderboard")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Teams Competing", len(teams))
    
    with col2:
        st.metric("Avg Team Score", f"{teams['team_score'].mean():.0f}/100")
    
    with col3:
        top_team = teams.nlargest(1, 'team_score')['team_name'].iloc[0]
        st.metric("🥇 Top Team", top_team)
    
    with col4:
        top_score = teams.nlargest(1, 'team_score')['team_score'].iloc[0]
        st.metric("Top Score", f"{top_score:.0f}/100")
    
    st.markdown("---")
    
    # Leaderboard
    st.subheader("🏅 Rankings")
    
    sorted_teams = teams.sort_values('team_score', ascending=False).reset_index(drop=True)
    
    for idx, row in sorted_teams.iterrows():
        # Medal for top 3
        if idx == 0:
            medal = "🥇"
        elif idx == 1:
            medal = "🥈"
        elif idx == 2:
            medal = "🥉"
        else:
            medal = f"#{idx + 1}"
        
        # Score color
        score = row['team_score']
        if score >= 70:
            score_color = "🟢"
        elif score >= 50:
            score_color = "🟡"
        else:
            score_color = "🔴"
        
        # Team card
        col1, col2, col3, col4, col5 = st.columns([1, 3, 1.5, 1.5, 1])
        
        with col1:
            st.markdown(f"### {medal}")
        
        with col2:
            st.markdown(f"**{row['team_name']}**")
            st.caption(f"👥 {row['recruiter']} + {row['hm']}")
        
        with col3:
            st.markdown(f"{score_color} **{score:.0f}/100**")
            st.caption("Team Score")
        
        with col4:
            st.write(f"🚩 {row['total_violations']} issues")
            st.caption(f"📋 {row['roles']} roles")
        
        with col5:
            if st.button("View", key=f"team_{idx}"):
                st.session_state['selected_team'] = idx
        
        # Show details if selected
        if st.session_state.get('selected_team') == idx:
            with st.expander("📊 Team Breakdown", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**👤 Recruiter: {row['recruiter']}**")
                    st.write(f"Score: {row['recruiter_score']:.0f}/100")
                    
                    rec_data = df[df['recruiter_name'] == row['recruiter']]
                    rec_flags = generate_flags(rec_data, int(row['recruiter_violations']))
                    
                    if rec_flags:
                        st.markdown("**Top Issues:**")
                        for flag in rec_flags:
                            st.markdown(f"{flag['severity']} {flag['issue']}")
                
                with col2:
                    st.markdown(f"**🎯 Hiring Manager: {row['hm']}**")
                    st.write(f"Score: {row['hm_score']:.0f}/100")
                    
                    hm_data = df[df['hiring_manager_name'] == row['hm']]
                    hm_flags = generate_flags(hm_data, int(row['hm_violations']))
                    
                    if hm_flags:
                        st.markdown("**Top Issues:**")
                        for flag in hm_flags:
                            st.markdown(f"{flag['severity']} {flag['issue']}")
                
                st.markdown("---")
                st.write(f"**Team Stats:** {row['candidates']} candidates across {row['roles']} open roles")
        
        st.markdown("---")
    
    # Chart
    st.subheader("📊 Team Score Distribution")
    chart_data = sorted_teams.set_index('team_name')['team_score']
    st.bar_chart(chart_data)

# Individual performance pages
def show_recruiter_view(recruiters, teams, df):
    """Show recruiter performance"""
    st.header("👥 Recruiter Performance")
    
    for idx, row in recruiters.sort_values('score', ascending=False).iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"**{row['recruiter_name']}**")
        
        with col2:
            if st.button(f"🚩 {row['violations']} issues", key=f"rec_{idx}"):
                st.session_state[f"show_rec_{idx}"] = not st.session_state.get(f"show_rec_{idx}", False)
        
        with col3:
            score_color = "🟢" if row['score'] >= 70 else "🟡" if row['score'] >= 50 else "🔴"
            st.write(f"{score_color} {row['score']:.0f}/100")
        
        with col4:
            rec_teams = teams[teams['recruiter'] == row['recruiter_name']]['team_name'].tolist()
            st.caption(f"Teams: {len(rec_teams)}")
        
        if st.session_state.get(f"show_rec_{idx}", False):
            person_data = df[df['recruiter_name'] == row['recruiter_name']]
            flags = generate_flags(person_data, row['violations'])
            
            with st.expander("⚠️ Top Issues", expanded=True):
                for flag in flags:
                    st.markdown(f"{flag['severity']} **{flag['issue']}** - Candidate: `{flag['candidate']}`")
        
        st.markdown("---")

def show_hm_view(hms, teams, df):
    """Show hiring manager performance"""
    st.header("🎯 Hiring Manager Performance")
    
    for idx, row in hms.sort_values('score', ascending=False).iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"**{row['hiring_manager_name']}**")
        
        with col2:
            if st.button(f"🚩 {row['violations']} issues", key=f"hm_{idx}"):
                st.session_state[f"show_hm_{idx}"] = not st.session_state.get(f"show_hm_{idx}", False)
        
        with col3:
            score_color = "🟢" if row['score'] >= 70 else "🟡" if row['score'] >= 50 else "🔴"
            st.write(f"{score_color} {row['score']:.0f}/100")
        
        with col4:
            hm_teams = teams[teams['hm'] == row['hiring_manager_name']]['team_name'].tolist()
            st.caption(f"Teams: {len(hm_teams)}")
        
        if st.session_state.get(f"show_hm_{idx}", False):
            person_data = df[df['hiring_manager_name'] == row['hiring_manager_name']]
            flags = generate_flags(person_data, row['violations'])
            
            with st.expander("⚠️ Top Issues", expanded=True):
                for flag in flags:
                    st.markdown(f"{flag['severity']} **{flag['issue']}** - Candidate: `{flag['candidate']}`")
        
        st.markdown("---")

# Main app
def main():
    # Initialize session state
    if 'role' not in st.session_state:
        st.session_state['role'] = None
    
    # Show sign-in if no role selected
    if st.session_state['role'] is None:
        show_signin()
        return
    
    # Load data
    df, teams, recruiters, hms = load_data()
    
    if df is None:
        return
    
    # Header with role and sign-out
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("⭐ Talent Score")
    with col2:
        if st.button("🚪 Sign Out"):
            st.session_state['role'] = None
            st.rerun()
    
    role = st.session_state['role']
    st.caption(f"Signed in as: **{role.replace('_', ' ').title()}**")
    st.markdown("---")
    
    # Role-based navigation
    if role == 'recruiter':
        # Recruiter sees: Team Leaderboard + Recruiter Performance
        page = st.sidebar.radio("View", ["🏆 Team Leaderboard", "👥 My Performance"])
        
        if page == "🏆 Team Leaderboard":
            show_team_leaderboard(teams, df)
        else:
            show_recruiter_view(recruiters, teams, df)
    
    elif role == 'hiring_team':
        # HM sees: Team Leaderboard + HM Performance
        page = st.sidebar.radio("View", ["🏆 Team Leaderboard", "🎯 My Performance"])
        
        if page == "🏆 Team Leaderboard":
            show_team_leaderboard(teams, df)
        else:
            show_hm_view(hms, teams, df)
    
    elif role == 'leader':
        # Leader sees: Everything
        page = st.sidebar.radio("View", ["🏆 Team Leaderboard", "👥 Recruiters", "🎯 Hiring Managers"])
        
        if page == "🏆 Team Leaderboard":
            show_team_leaderboard(teams, df)
        elif page == "👥 Recruiters":
            show_recruiter_view(recruiters, teams, df)
        else:
            show_hm_view(hms, teams, df)

if __name__ == "__main__":
    main()
