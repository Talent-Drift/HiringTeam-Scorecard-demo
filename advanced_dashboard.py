"""
Advanced Team Scorecard Dashboard - Enhanced Design & Department Organization
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Talent Score", page_icon="🏆", layout="wide")

# ==================== CUSTOM STYLING ====================

def apply_custom_css():
    """Apply custom CSS for better design"""
    st.markdown("""
    <style>
        /* Import modern font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Global font */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        /* Fix text overflow issues */
        .stMarkdown, .stText {
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        
        /* Better button styling */
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Card-like containers */
        .stExpander {
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Better metrics */
        [data-testid="stMetricValue"] {
            font-size: 2em;
            font-weight: 700;
        }
        
        /* Department headers */
        .department-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            margin: 20px 0 10px 0;
            font-weight: 600;
            font-size: 1.2em;
        }
        
        /* Team role badges */
        .role-badge {
            display: inline-block;
            background: #f0f2f6;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
            color: #4a5568;
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
            recruiter_scores[['name', 'final_score', 'total_violations']],
            left_on='recruiter', right_on='name', how='left'
        ).rename(columns={'final_score': 'recruiter_score', 'total_violations': 'recruiter_violations'})
        
        team_data = team_data.merge(
            hm_scores[['name', 'final_score', 'total_violations']],
            left_on='hm', right_on='name', how='left'
        ).rename(columns={'final_score': 'hm_score', 'total_violations': 'hm_violations'})
        
        team_data['team_score'] = (team_data['recruiter_score'] + team_data['hm_score']) / 2
        team_data['total_violations'] = team_data['recruiter_violations'] + team_data['hm_violations']
        
        team_data = team_data[['department', 'role', 'recruiter', 'hm', 'recruiter_score', 'hm_score', 
                                'team_score', 'total_violations', 'roles', 'candidates']]
        
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
                <h1 style='font-size: 4em; margin: 0; color: #1f77b4;'>⭐</h1>
                <h1 style='font-size: 3em; margin: 10px 0; font-weight: bold;'>Talent Score</h1>
                <p style='font-size: 1.2em; color: #666;'>Performance tracking for recruiting teams</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align: center; margin: 30px 0;'>Select Your Role</h3>", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.markdown("""<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 40px 20px; border-radius: 15px; text-align: center; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 10px;'>
                    <h2 style='color: white; font-size: 2.5em; margin: 0;'>👥</h2>
                    <h3 style='color: white; margin: 15px 0 5px 0;'>Recruiter</h3>
                </div>""", unsafe_allow_html=True)
            if st.button("Sign in as Recruiter", use_container_width=True):
                st.session_state['role'] = 'recruiter'
                st.rerun()
        
        with col_b:
            st.markdown("""<div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                            padding: 40px 20px; border-radius: 15px; text-align: center; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 10px;'>
                    <h2 style='color: white; font-size: 2.5em; margin: 0;'>🎯</h2>
                    <h3 style='color: white; margin: 15px 0 5px 0;'>Hiring Team</h3>
                </div>""", unsafe_allow_html=True)
            if st.button("Sign in as Hiring Team", use_container_width=True):
                st.session_state['role'] = 'hiring_team'
                st.rerun()
        
        with col_c:
            st.markdown("""<div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                            padding: 40px 20px; border-radius: 15px; text-align: center; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 10px;'>
                    <h2 style='color: white; font-size: 2.5em; margin: 0;'>🏆</h2>
                    <h3 style='color: white; margin: 15px 0 5px 0;'>Leader</h3>
                </div>""", unsafe_allow_html=True)
            if st.button("Sign in as Leader", use_container_width=True):
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
        st.metric("🥇 Top Team", f"{best_team['department']} - {best_team['role'][:20]}...")
    with col4:
        st.metric("Top Score", f"{teams['team_score'].max():.0f}/100")
    
    st.markdown("---")
    
    with st.expander("ℹ️ How Scoring Works"):
        st.markdown("""
        **Team Score = Average of Recruiter + HM Scores**
        
        **Metrics:** 🕐 Feedback (40%) | ⚡ Velocity (35%) | 🤝 Engagement (25%)
        
        **Severity:** 🔴 High (-10 to -15) | 🟡 Medium (-5 to -7) | 🟢 Low (-2 to -3)
        """)
    
    st.markdown("---")
    st.subheader("🏅 Rankings by Department & Role")
    
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
        score_color = "🟢" if row['team_score'] >= 70 else "🟡" if row['team_score'] >= 50 else "🔴"
        
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1.5, 1.5, 1])
        
        with col1:
            st.markdown(f"**#{rank}**")
        
        with col2:
            # Role as main text, names on hover/click
            st.markdown(f"**{row['role']}**")
            with st.popover("👥 Team Members"):
                st.write(f"**Recruiter:** {row['recruiter']}")
                st.write(f"**Hiring Manager:** {row['hm']}")
        
        with col3:
            st.markdown(f"{score_color} **{row['team_score']:.0f}/100**")
        
        with col4:
            st.caption(f"🚩 {row['total_violations']} issues")
            st.caption(f"📋 {row['roles']} roles")
        
        with col5:
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
                    st.markdown(f"**🎯 HM: {row['hm']}**")
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
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"**{row['name']}**")
        with col2:
            if st.button(f"🚩 {row['total_violations']}", key=f"{person_type}_{idx}"):
                st.session_state[f"show_{person_type}_{idx}"] = not st.session_state.get(f"show_{person_type}_{idx}", False)
        with col3:
            score_color = "🟢" if row['final_score'] >= 70 else "🟡" if row['final_score'] >= 50 else "🔴"
            st.write(f"{score_color} {row['final_score']:.0f}/100")
        with col4:
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
