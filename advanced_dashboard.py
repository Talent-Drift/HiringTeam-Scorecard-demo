"""
Advanced Team Scorecard Dashboard
With SLA-based scoring, role-based sign-in, and team competition
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from advanced_scoring_engine import ScorecardEngine

# Page config
st.set_page_config(page_title="Talent Score", page_icon="🏆", layout="wide")

# Load data and calculate scores using advanced engine
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('sample_ats_export.csv')
        
        # Initialize scoring engine
        engine = ScorecardEngine(df)
        violations = engine.calculate_scores()
        recruiter_scores = engine.score_by_recruiter(violations)
        hm_scores = engine.score_by_hiring_manager(violations)
        
        # Calculate TEAM scores (recruiter + HM pairs)
        team_data = df.groupby(['recruiter_name', 'hiring_manager_name']).agg({
            'requisition_id': 'nunique',
            'candidate_id': 'count'
        }).reset_index()
        
        team_data.columns = ['recruiter', 'hm', 'roles', 'candidates']
        
        # Add individual scores to teams
        team_data = team_data.merge(
            recruiter_scores[['name', 'final_score', 'total_violations']],
            left_on='recruiter',
            right_on='name',
            how='left'
        ).rename(columns={'final_score': 'recruiter_score', 'total_violations': 'recruiter_violations'})
        
        team_data = team_data.merge(
            hm_scores[['name', 'final_score', 'total_violations']],
            left_on='hm',
            right_on='name',
            how='left'
        ).rename(columns={'final_score': 'hm_score', 'total_violations': 'hm_violations'})
        
        # Calculate team score (average of recruiter + HM)
        team_data['team_score'] = (team_data['recruiter_score'] + team_data['hm_score']) / 2
        team_data['total_violations'] = team_data['recruiter_violations'] + team_data['hm_violations']
        
        # Create team name
        team_data['team_name'] = team_data['recruiter'].str.split().str[0] + " & " + team_data['hm'].str.split().str[0]
        
        # Clean up columns
        team_data = team_data[['team_name', 'recruiter', 'hm', 'recruiter_score', 'hm_score', 
                                'team_score', 'total_violations', 'roles', 'candidates']]
        
        return df, team_data, recruiter_scores, hm_scores, violations
        
    except FileNotFoundError:
        st.error("❌ Please upload sample_ats_export.csv")
        return None, None, None, None, None

# Get top flags from violations
def get_top_flags(violations, person_name, person_type='recruiter'):
    """Get top 3 violations for a person, sorted by severity"""
    if violations.empty:
        return []
    
    if person_type == 'recruiter':
        person_violations = violations[violations['recruiter_name'] == person_name]
    else:
        person_violations = violations[violations['hiring_manager_name'] == person_name]
    
    if person_violations.empty:
        return []
    
    # Sort by severity (high > medium > low) then by penalty
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    person_violations['severity_rank'] = person_violations['severity'].map(severity_order)
    sorted_violations = person_violations.sort_values(['severity_rank', 'penalty']).head(3)
    
    flags = []
    for _, viol in sorted_violations.iterrows():
        emoji = "🔴" if viol['severity'] == 'high' else "🟡" if viol['severity'] == 'medium' else "🟢"
        flags.append({
            'severity': emoji,
            'issue': viol['description'],
            'candidate': viol['candidate_id'],
            'metric': viol['metric']
        })
    
    return flags

# Sign-in page
def show_signin():
    """Display sign-in page with role selection"""
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
        st.markdown("<p style='text-align: center; color: #999; font-size: 0.9em;'>© 2026 Talent Score. Powered by SLA-based scoring.</p>", unsafe_allow_html=True)

# Team Leaderboard Page
def show_team_leaderboard(teams, df, violations):
    """Show team rankings with advanced metrics"""
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
    
    # Scoring methodology info
    with st.expander("ℹ️ How Scoring Works"):
        st.markdown("""
        **Team Score = Average of Recruiter + Hiring Manager Scores**
        
        Individual scores start at 100 and are reduced based on SLA violations:
        
        **Weighted Metrics:**
        - 🕐 Interview Feedback Timeliness (40%)
        - ⚡ Stage Progression Velocity (35%)
        - 🤝 Hiring Manager Engagement (25%)
        
        **Severity Levels:**
        - 🔴 High: -10 to -15 points
        - 🟡 Medium: -5 to -7 points
        - 🟢 Low: -2 to -3 points
        """)
    
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
                    
                    # Show recruiter flags
                    rec_flags = get_top_flags(violations, row['recruiter'], 'recruiter')
                    
                    if rec_flags:
                        st.markdown("**Top Issues:**")
                        for flag in rec_flags:
                            st.markdown(f"{flag['severity']} {flag['issue']}")
                    else:
                        st.success("✅ No violations - excellent performance!")
                
                with col2:
                    st.markdown(f"**🎯 Hiring Manager: {row['hm']}**")
                    st.write(f"Score: {row['hm_score']:.0f}/100")
                    
                    # Show HM flags
                    hm_flags = get_top_flags(violations, row['hm'], 'hm')
                    
                    if hm_flags:
                        st.markdown("**Top Issues:**")
                        for flag in hm_flags:
                            st.markdown(f"{flag['severity']} {flag['issue']}")
                    else:
                        st.success("✅ No violations - excellent performance!")
                
                st.markdown("---")
                st.write(f"**Team Stats:** {row['candidates']} candidates across {row['roles']} open roles")
        
        st.markdown("---")
    
    # Chart
    st.subheader("📊 Team Score Distribution")
    chart_data = sorted_teams.set_index('team_name')['team_score']
    st.bar_chart(chart_data)

# Individual performance pages
def show_recruiter_view(recruiters, teams, df, violations):
    """Show recruiter performance with detailed metrics"""
    st.header("👥 Recruiter Performance")
    
    for idx, row in recruiters.sort_values('final_score', ascending=False).iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"**{row['name']}**")
        
        with col2:
            if st.button(f"🚩 {row['total_violations']} issues", key=f"rec_{idx}"):
                st.session_state[f"show_rec_{idx}"] = not st.session_state.get(f"show_rec_{idx}", False)
        
        with col3:
            score_color = "🟢" if row['final_score'] >= 70 else "🟡" if row['final_score'] >= 50 else "🔴"
            st.write(f"{score_color} {row['final_score']:.0f}/100")
        
        with col4:
            rec_teams = teams[teams['recruiter'] == row['name']]['team_name'].tolist()
            st.caption(f"Teams: {len(rec_teams)}")
        
        if st.session_state.get(f"show_rec_{idx}", False):
            flags = get_top_flags(violations, row['name'], 'recruiter')
            
            with st.expander("⚠️ Top Issues & Metrics", expanded=True):
                # Show metric breakdown
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Feedback Score", f"{row['feedback_score']:.0f}/100", help="40% weight")
                with col2:
                    st.metric("Velocity Score", f"{row['velocity_score']:.0f}/100", help="35% weight")
                with col3:
                    st.metric("Engagement Score", f"{row['engagement_score']:.0f}/100", help="25% weight")
                
                st.markdown("---")
                
                if flags:
                    for flag in flags:
                        st.markdown(f"{flag['severity']} **{flag['issue']}** - Candidate: `{flag['candidate']}`")
                else:
                    st.success("✅ No violations - excellent performance!")
        
        st.markdown("---")

def show_hm_view(hms, teams, df, violations):
    """Show hiring manager performance with detailed metrics"""
    st.header("🎯 Hiring Manager Performance")
    
    for idx, row in hms.sort_values('final_score', ascending=False).iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"**{row['name']}**")
        
        with col2:
            if st.button(f"🚩 {row['total_violations']} issues", key=f"hm_{idx}"):
                st.session_state[f"show_hm_{idx}"] = not st.session_state.get(f"show_hm_{idx}", False)
        
        with col3:
            score_color = "🟢" if row['final_score'] >= 70 else "🟡" if row['final_score'] >= 50 else "🔴"
            st.write(f"{score_color} {row['final_score']:.0f}/100")
        
        with col4:
            hm_teams = teams[teams['hm'] == row['name']]['team_name'].tolist()
            st.caption(f"Teams: {len(hm_teams)}")
        
        if st.session_state.get(f"show_hm_{idx}", False):
            flags = get_top_flags(violations, row['name'], 'hm')
            
            with st.expander("⚠️ Top Issues & Metrics", expanded=True):
                # Show metric breakdown
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Feedback Score", f"{row['feedback_score']:.0f}/100", help="40% weight")
                with col2:
                    st.metric("Velocity Score", f"{row['velocity_score']:.0f}/100", help="35% weight")
                with col3:
                    st.metric("Engagement Score", f"{row['engagement_score']:.0f}/100", help="25% weight")
                
                st.markdown("---")
                
                if flags:
                    for flag in flags:
                        st.markdown(f"{flag['severity']} **{flag['issue']}** - Candidate: `{flag['candidate']}`")
                else:
                    st.success("✅ No violations - excellent performance!")
        
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
    df, teams, recruiters, hms, violations = load_data()
    
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
        page = st.sidebar.radio("View", ["🏆 Team Leaderboard", "👥 My Performance"])
        
        if page == "🏆 Team Leaderboard":
            show_team_leaderboard(teams, df, violations)
        else:
            show_recruiter_view(recruiters, teams, df, violations)
    
    elif role == 'hiring_team':
        page = st.sidebar.radio("View", ["🏆 Team Leaderboard", "🎯 My Performance"])
        
        if page == "🏆 Team Leaderboard":
            show_team_leaderboard(teams, df, violations)
        else:
            show_hm_view(hms, teams, df, violations)
    
    elif role == 'leader':
        page = st.sidebar.radio("View", ["🏆 Team Leaderboard", "👥 Recruiters", "🎯 Hiring Managers"])
        
        if page == "🏆 Team Leaderboard":
            show_team_leaderboard(teams, df, violations)
        elif page == "👥 Recruiters":
            show_recruiter_view(recruiters, teams, df, violations)
        else:
            show_hm_view(hms, teams, df, violations)

if __name__ == "__main__":
    main()
