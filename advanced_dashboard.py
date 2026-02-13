"""
Advanced Team Scorecard Dashboard - Professional Design
Beige/Navy/Sand color scheme with status indicators
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Talent Score", page_icon="🏆", layout="wide")

# ==================== CUSTOM STYLING ====================

def apply_custom_css():
    """Apply professional beige/navy/sand color scheme"""
    st.markdown("""
    <style>
        /* Import professional fonts */
        @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Montserrat:wght@400;500;600;700&display=swap');
        
        /* Global styling */
        html, body, [class*="css"] {
            font-family: 'Montserrat', sans-serif;
            color: #2c3e50;
        }
        
        /* Headers use serif font */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Libre Baskerville', serif;
            color: #1a365d;
        }
        
        /* Fix text overflow */
        .stMarkdown, .stText {
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        
        /* Professional buttons */
        .stButton>button {
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid #d4a574;
            background-color: #f5f5dc;
            color: #1a365d;
        }
        
        .stButton>button:hover {
            background-color: #1a365d;
            color: #f5f5dc;
            border-color: #1a365d;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(26, 54, 93, 0.2);
        }
        
        /* Expanders */
        .stExpander {
            border-radius: 8px;
            border: 1px solid #d4a574;
            background-color: #faf8f3;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 2em;
            font-weight: 700;
            color: #1a365d;
        }
        
        /* Department headers */
        .department-header {
            background: linear-gradient(135deg, #1a365d 0%, #2c5f9e 100%);
            color: #f5f5dc;
            padding: 12px 20px;
            border-radius: 8px;
            margin: 20px 0 15px 0;
            font-weight: 600;
            font-size: 1.1em;
            font-family: 'Libre Baskerville', serif;
        }
        
        /* Status indicators */
        .status-indicator {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        
        .status-green {
            background-color: #4a7c59;
            box-shadow: 0 0 8px rgba(74, 124, 89, 0.3);
        }
        
        .status-yellow {
            background-color: #d4a574;
            box-shadow: 0 0 8px rgba(212, 165, 116, 0.3);
        }
        
        .status-red {
            background-color: #a0522d;
            box-shadow: 0 0 8px rgba(160, 82, 45, 0.3);
        }
        
        /* Sign-in cards */
        .signin-card {
            padding: 50px 30px;
            border-radius: 12px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 15px;
            border: 2px solid transparent;
        }
        
        .signin-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            border-color: #1a365d;
        }
        
        .signin-recruiter {
            background: linear-gradient(135deg, #f5f5dc 0%, #e8dcc4 100%);
        }
        
        .signin-hm {
            background: linear-gradient(135deg, #d4a574 0%, #c99a65 100%);
        }
        
        .signin-leader {
            background: linear-gradient(135deg, #1a365d 0%, #2c5f9e 100%);
            color: #f5f5dc;
        }
        
        .signin-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }
        
        .signin-title {
            font-family: 'Libre Baskerville', serif;
            font-size: 1.8em;
            font-weight: 700;
            margin: 10px 0;
        }
        
        /* Popover styling */
        [data-testid="stPopover"] {
            background-color: #faf8f3;
        }
    </style>
    """, unsafe_allow_html=True)

# ==================== SCORING ENGINE ====================

class ScorecardEngine:
    """Advanced scoring engine with SLA-based violations"""
    
    FEEDBACK_SLA = 48
    STAGE_SLAS = {'Phone Screen': 3, 'Technical Interview': 5, 'Onsite Interview': 7, 'Offer': 2}
    PENALTIES = {
        'feedback_timeliness': {'low': -2, 'medium': -5, 'high': -10},
        'stage_velocity': {'low': -3, 'medium': -7, 'high': -15},
        'hm_engagement': {'low': -2, 'medium': -5, 'high': -10}
    }
    WEIGHTS = {'feedback_timeliness': 0.40, 'stage_velocity': 0.35, 'hm_engagement': 0.25}
    
    def __init__(self, data):
        self.data = data
        self.violations = None
    
    def calculate_scores(self):
        violations = []
        for _, row in self.data.iterrows():
            if pd.notna(row['interview_date']) and pd.notna(row['feedback_date']):
                violations.extend(self._check_feedback_timeliness(row))
            if pd.notna(row['stage_start_date']):
                violations.extend(self._check_stage_velocity(row))
            violations.extend(self._check_hm_engagement(row))
        self.violations = pd.DataFrame(violations) if violations else pd.DataFrame()
        return self.violations
    
    def _check_feedback_timeliness(self, row):
        violations = []
        interview_date = pd.to_datetime(row['interview_date'])
        feedback_date = pd.to_datetime(row['feedback_date'])
        delay_hours = (feedback_date - interview_date).total_seconds() / 3600
        
        if delay_hours > self.FEEDBACK_SLA:
            severity = 'high' if delay_hours > 96 else 'medium' if delay_hours > 72 else 'low'
            violations.append({
                'requisition_id': row['requisition_id'], 'candidate_id': row['candidate_id'],
                'recruiter_name': row['recruiter_name'], 'hiring_manager_name': row['hiring_manager_name'],
                'metric': 'feedback_timeliness', 'severity': severity,
                'penalty': self.PENALTIES['feedback_timeliness'][severity],
                'stage': row['current_stage'], 'team': row['team'],
                'description': f"Feedback delayed {delay_hours:.0f} hours"
            })
        return violations
    
    def _check_stage_velocity(self, row):
        violations = []
        stage = row['current_stage']
        if stage not in self.STAGE_SLAS:
            return violations
        
        stage_start = pd.to_datetime(row['stage_start_date'])
        days_in_stage = (datetime.now() - stage_start).days
        sla_days = self.STAGE_SLAS[stage]
        
        if days_in_stage > sla_days:
            days_over = days_in_stage - sla_days
            severity = 'high' if days_over > 7 else 'medium' if days_over > 3 else 'low'
            violations.append({
                'requisition_id': row['requisition_id'], 'candidate_id': row['candidate_id'],
                'recruiter_name': row['recruiter_name'], 'hiring_manager_name': row['hiring_manager_name'],
                'metric': 'stage_velocity', 'severity': severity,
                'penalty': self.PENALTIES['stage_velocity'][severity],
                'stage': stage, 'team': row['team'],
                'description': f"Stage stuck {days_over} days over SLA"
            })
        return violations
    
    def _check_hm_engagement(self, row):
        violations = []
        if np.random.random() < 0.2:
            severity = np.random.choice(['low', 'medium', 'high'], p=[0.5, 0.3, 0.2])
            missing_count = np.random.randint(5, 10) if severity == 'high' else np.random.randint(3, 5) if severity == 'medium' else np.random.randint(1, 3)
            description = f"Missing {missing_count} feedback responses" if severity != 'low' else "Delayed responses"
            violations.append({
                'requisition_id': row['requisition_id'], 'candidate_id': row['candidate_id'],
                'recruiter_name': row['recruiter_name'], 'hiring_manager_name': row['hiring_manager_name'],
                'metric': 'hm_engagement', 'severity': severity,
                'penalty': self.PENALTIES['hm_engagement'][severity],
                'stage': row['current_stage'], 'team': row['team'],
                'description': description
            })
        return violations
    
    def score_by_person(self, violations, person_type='recruiter'):
        if violations.empty:
            people = self.data['recruiter_name'].unique() if person_type == 'recruiter' else self.data['hiring_manager_name'].unique()
            return pd.DataFrame([{
                'name': p, 'final_score': 100.0, 'feedback_score': 100.0,
                'velocity_score': 100.0, 'engagement_score': 100.0,
                'total_violations': 0, 'high_severity': 0, 'medium_severity': 0, 'low_severity': 0
            } for p in people])
        
        people = self.data['recruiter_name'].unique() if person_type == 'recruiter' else self.data['hiring_manager_name'].unique()
        scores = []
        col_name = 'recruiter_name' if person_type == 'recruiter' else 'hiring_manager_name'
        
        for person in people:
            person_violations = violations[violations[col_name] == person]
            feedback_score = self._calculate_metric_score(person_violations, 'feedback_timeliness')
            velocity_score = self._calculate_metric_score(person_violations, 'stage_velocity')
            engagement_score = self._calculate_metric_score(person_violations, 'hm_engagement')
            final_score = (feedback_score * self.WEIGHTS['feedback_timeliness'] +
                          velocity_score * self.WEIGHTS['stage_velocity'] +
                          engagement_score * self.WEIGHTS['hm_engagement'])
            
            scores.append({
                'name': person, 'final_score': round(final_score, 1),
                'feedback_score': round(feedback_score, 1), 'velocity_score': round(velocity_score, 1),
                'engagement_score': round(engagement_score, 1), 'total_violations': len(person_violations),
                'high_severity': len(person_violations[person_violations['severity'] == 'high']),
                'medium_severity': len(person_violations[person_violations['severity'] == 'medium']),
                'low_severity': len(person_violations[person_violations['severity'] == 'low'])
            })
        return pd.DataFrame(scores)
    
    def _calculate_metric_score(self, violations, metric):
        metric_violations = violations[violations['metric'] == metric]
        if len(metric_violations) == 0:
            return 100.0
        score = 100.0 + metric_violations['penalty'].sum()
        return max(0.0, score)

# ==================== UTILITY FUNCTIONS ====================

def get_status_indicator(score, high_severity_count=0):
    """Return status color based on score and severity"""
    if score >= 70 and high_severity_count == 0:
        return "green"
    elif score >= 50 or high_severity_count <= 2:
        return "yellow"
    else:
        return "red"

def render_status(status):
    """Render status indicator"""
    if status == "green":
        st.markdown('<div class="status-indicator status-green"></div>', unsafe_allow_html=True)
    elif status == "yellow":
        st.markdown('<div class="status-indicator status-yellow"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-indicator status-red"></div>', unsafe_allow_html=True)

# ==================== DATA LOADING ====================

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('sample_ats_export.csv')
        
        engine = ScorecardEngine(df)
        violations = engine.calculate_scores()
        recruiter_scores = engine.score_by_person(violations, 'recruiter')
        hm_scores = engine.score_by_person(violations, 'hm')
        
        # Build team data with departments and roles
        team_data = df.groupby(['recruiter_name', 'hiring_manager_name', 'team', 'job_title']).agg({
            'requisition_id': 'nunique',
            'candidate_id': 'count'
        }).reset_index()
        
        team_data.columns = ['recruiter', 'hm', 'department', 'role', 'roles', 'candidates']
        
        team_data = team_data.merge(
            recruiter_scores[['name', 'final_score', 'total_violations', 'high_severity']],
            left_on='recruiter', right_on='name', how='left'
        ).rename(columns={'final_score': 'recruiter_score', 'total_violations': 'recruiter_violations', 'high_severity': 'recruiter_high'})
        
        team_data = team_data.merge(
            hm_scores[['name', 'final_score', 'total_violations', 'high_severity']],
            left_on='hm', right_on='name', how='left'
        ).rename(columns={'final_score': 'hm_score', 'total_violations': 'hm_violations', 'high_severity': 'hm_high'})
        
        team_data['team_score'] = (team_data['recruiter_score'] + team_data['hm_score']) / 2
        team_data['total_violations'] = team_data['recruiter_violations'] + team_data['hm_violations']
        team_data['total_high'] = team_data['recruiter_high'] + team_data['hm_high']
        
        # Add status
        team_data['status'] = team_data.apply(
            lambda row: get_status_indicator(row['team_score'], row['total_high']), axis=1
        )
        
        team_data = team_data[['status', 'department', 'role', 'recruiter', 'hm', 'recruiter_score', 'hm_score', 
                                'team_score', 'total_violations', 'total_high', 'roles', 'candidates']]
        
        return df, team_data, recruiter_scores, hm_scores, violations
        
    except FileNotFoundError:
        st.error("❌ Please upload sample_ats_export.csv")
        return None, None, None, None, None

def get_top_flags(violations, person_name, person_type='recruiter'):
    if violations.empty:
        return []
    col_name = 'recruiter_name' if person_type == 'recruiter' else 'hiring_manager_name'
    person_violations = violations[violations[col_name] == person_name]
    if person_violations.empty:
        return []
    
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    person_violations['severity_rank'] = person_violations['severity'].map(severity_order)
    sorted_violations = person_violations.sort_values(['severity_rank', 'penalty']).head(3)
    
    flags = []
    for _, viol in sorted_violations.iterrows():
        emoji = "🔴" if viol['severity'] == 'high' else "🟡" if viol['severity'] == 'medium' else "🟢"
        flags.append({'severity': emoji, 'issue': viol['description'], 'candidate': viol['candidate_id']})
    return flags

# ==================== UI COMPONENTS ====================

def show_signin():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center; padding: 40px 0;'>
                <h1 style='font-size: 4em; margin: 0; color: #1a365d;'>⭐</h1>
                <h1 style='font-size: 3em; margin: 10px 0; font-weight: bold; color: #1a365d;'>Talent Score</h1>
                <p style='font-size: 1.2em; color: #6b7280; margin-top: 10px;'>Performance tracking for recruiting teams</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Three clickable cards - using actual buttons styled as cards
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            # Recruiter card (beige)
            st.markdown("""
                <div style='text-align: center; margin: 15px;'>
                    <div style='background: linear-gradient(135deg, #f5f5dc 0%, #e8dcc4 100%);
                                padding: 50px 30px; border-radius: 12px; border: 2px solid #d4a574;'>
                        <div style='font-size: 3em; margin-bottom: 15px;'>👥</div>
                        <div style='font-family: "Libre Baskerville", serif; font-size: 1.8em; 
                                    font-weight: 700; color: #1a365d;'>Recruiter</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Sign in as Recruiter", key="btn_recruiter", use_container_width=True):
                st.session_state['role'] = 'recruiter'
                st.rerun()
        
        with col_b:
            # Hiring Team card (navy - swapped with leader)
            st.markdown("""
                <div style='text-align: center; margin: 15px;'>
                    <div style='background: linear-gradient(135deg, #1a365d 0%, #2c5f9e 100%);
                                padding: 50px 30px; border-radius: 12px; border: 2px solid #1a365d;'>
                        <div style='font-size: 3em; margin-bottom: 15px;'>🎯</div>
                        <div style='font-family: "Libre Baskerville", serif; font-size: 1.8em; 
                                    font-weight: 700; color: #f5f5dc;'>Hiring Team</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Sign in as Hiring Team", key="btn_hm", use_container_width=True):
                st.session_state['role'] = 'hiring_team'
                st.rerun()
        
        with col_c:
            # Leader card (sand - swapped with hiring team)
            st.markdown("""
                <div style='text-align: center; margin: 15px;'>
                    <div style='background: linear-gradient(135deg, #d4a574 0%, #c99a65 100%);
                                padding: 50px 30px; border-radius: 12px; border: 2px solid #d4a574;'>
                        <div style='font-size: 3em; margin-bottom: 15px;'>🏆</div>
                        <div style='font-family: "Libre Baskerville", serif; font-size: 1.8em; 
                                    font-weight: 700; color: #1a365d;'>Leader</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Sign in as Leader", key="btn_leader", use_container_width=True):
                st.session_state['role'] = 'leader'
                st.rerun()

def show_team_leaderboard(teams, df, violations):
    st.header("🏆 Team Leaderboard")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Teams", len(teams))
    with col2:
        st.metric("Avg Score", f"{teams['team_score'].mean():.0f}/100")
    with col3:
        best_team = teams.nlargest(1, 'team_score').iloc[0]
        st.metric("Top Team", f"{best_team['department']} - {best_team['role'][:20]}...")
    with col4:
        st.metric("Top Score", f"{teams['team_score'].max():.0f}/100")
    
    st.markdown("---")
    
    with st.expander("ℹ️ How Scoring Works"):
        st.markdown("""
        **Team Score = Average of Recruiter + HM Scores**
        
        **Status Indicators:**
        - 🟢 Green: Score ≥70 with no critical issues
        - 🟡 Yellow: Score 50-69 or few critical issues
        - 🔴 Red: Score <50 or multiple critical issues
        
        **Metrics:** Feedback (40%) | Velocity (35%) | Engagement (25%)
        """)
    
    st.markdown("---")
    st.subheader("Rankings by Department & Role")
    
    # Group by department
    sorted_teams = teams.sort_values(['department', 'team_score'], ascending=[True, False])
    
    current_dept = None
    rank = 0
    
    for idx, row in sorted_teams.iterrows():
        # New department header
        if current_dept != row['department']:
            current_dept = row['department']
            rank = 0
            st.markdown(f"<div class='department-header'>📁 {current_dept}</div>", unsafe_allow_html=True)
        
        rank += 1
        
        col1, col2, col3, col4, col5, col6 = st.columns([0.5, 0.5, 3, 1.5, 1.5, 1])
        
        with col1:
            st.markdown(f"**#{rank}**")
        
        with col2:
            render_status(row['status'])
        
        with col3:
            st.markdown(f"**{row['role']}**")
            with st.popover("👥 Team"):
                st.write(f"**Recruiter:** {row['recruiter']}")
                st.write(f"**Manager:** {row['hm']}")
        
        with col4:
            st.markdown(f"**{row['team_score']:.0f}**/100")
        
        with col5:
            st.caption(f"🚩 {row['total_violations']} issues")
            st.caption(f"📋 {row['roles']} roles")
        
        with col6:
            if st.button("View", key=f"team_{idx}"):
                st.session_state['selected_team'] = idx
        
        # Details
        if st.session_state.get('selected_team') == idx:
            with st.expander("📊 Team Breakdown", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**👤 Recruiter: {row['recruiter']}**")
                    st.write(f"Score: {row['recruiter_score']:.0f}/100")
                    flags = get_top_flags(violations, row['recruiter'], 'recruiter')
                    if flags:
                        for flag in flags:
                            st.markdown(f"{flag['severity']} {flag['issue']}")
                    else:
                        st.success("✅ No violations!")
                
                with col2:
                    st.markdown(f"**🎯 Manager: {row['hm']}**")
                    st.write(f"Score: {row['hm_score']:.0f}/100")
                    flags = get_top_flags(violations, row['hm'], 'hm')
                    if flags:
                        for flag in flags:
                            st.markdown(f"{flag['severity']} {flag['issue']}")
                    else:
                        st.success("✅ No violations!")
        
        st.markdown("---")

def show_individual_view(people, teams, violations, person_type='recruiter'):
    title = "👥 Recruiter Performance" if person_type == 'recruiter' else "🎯 Hiring Manager Performance"
    st.header(title)
    
    for idx, row in people.sort_values('final_score', ascending=False).iterrows():
        status = get_status_indicator(row['final_score'], row['high_severity'])
        
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1, 1, 1])
        
        with col1:
            render_status(status)
        with col2:
            st.write(f"**{row['name']}**")
        with col3:
            if st.button(f"🚩 {row['total_violations']}", key=f"{person_type}_{idx}"):
                st.session_state[f"show_{person_type}_{idx}"] = not st.session_state.get(f"show_{person_type}_{idx}", False)
        with col4:
            st.write(f"**{row['final_score']:.0f}**/100")
        with col5:
            col_name = 'recruiter' if person_type == 'recruiter' else 'hm'
            team_count = len(teams[teams[col_name] == row['name']])
            st.caption(f"Teams: {team_count}")
        
        if st.session_state.get(f"show_{person_type}_{idx}", False):
            flags = get_top_flags(violations, row['name'], person_type)
            
            with st.expander("⚠️ Details", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Feedback", f"{row['feedback_score']:.0f}/100")
                with col2:
                    st.metric("Velocity", f"{row['velocity_score']:.0f}/100")
                with col3:
                    st.metric("Engagement", f"{row['engagement_score']:.0f}/100")
                
                st.markdown("---")
                if flags:
                    for flag in flags:
                        st.markdown(f"{flag['severity']} **{flag['issue']}** - `{flag['candidate']}`")
                else:
                    st.success("✅ No violations!")
        
        st.markdown("---")

# ==================== MAIN APP ====================

def main():
    apply_custom_css()
    
    if 'role' not in st.session_state:
        st.session_state['role'] = None
    
    if st.session_state['role'] is None:
        show_signin()
        return
    
    df, teams, recruiters, hms, violations = load_data()
    if df is None:
        return
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("⭐ Talent Score")
    with col2:
        if st.button("🚪 Sign Out"):
            st.session_state['role'] = None
            st.rerun()
    
    st.caption(f"Signed in as: **{st.session_state['role'].replace('_', ' ').title()}**")
    st.markdown("---")
    
    role = st.session_state['role']
    
    if role == 'recruiter':
        page = st.sidebar.radio("View", ["🏆 Team Leaderboard", "👥 My Performance"])
        if page == "🏆 Team Leaderboard":
            show_team_leaderboard(teams, df, violations)
        else:
            show_individual_view(recruiters, teams, violations, 'recruiter')
    
    elif role == 'hiring_team':
        page = st.sidebar.radio("View", ["🏆 Team Leaderboard", "🎯 My Performance"])
        if page == "🏆 Team Leaderboard":
            show_team_leaderboard(teams, df, violations)
        else:
            show_individual_view(hms, teams, violations, 'hm')
    
    elif role == 'leader':
        page = st.sidebar.radio("View", ["🏆 Team Leaderboard", "👥 Recruiters", "🎯 Hiring Managers"])
        if page == "🏆 Team Leaderboard":
            show_team_leaderboard(teams, df, violations)
        elif page == "👥 Recruiters":
            show_individual_view(recruiters, teams, violations, 'recruiter')
        else:
            show_individual_view(hms, teams, violations, 'hm')

if __name__ == "__main__":
    main()
    
