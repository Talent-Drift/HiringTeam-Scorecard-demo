"""
Recruiter Scorecard Dashboard - Role-Based Views with Visual Cards
Login as Recruiter, Hiring Manager, or Leadership to see personalized dashboards
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scoring_engine import ScorecardEngine
from datetime import datetime
import json
import os

# Page config
st.set_page_config(
    page_title="Talent Score Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def load_data():
    """Load and process current data"""
    try:
        df = pd.read_csv('sample_ats_export.csv')
        engine = ScorecardEngine(df)
        violations = engine.calculate_scores()
        recruiter_scores = engine.score_by_recruiter(violations)
        hm_scores = engine.score_by_hiring_manager(violations)
        org_summary = engine.get_org_summary(recruiter_scores, hm_scores)
        
        return {
            'raw_data': df,
            'violations': violations,
            'recruiter_scores': recruiter_scores,
            'hm_scores': hm_scores,
            'org_summary': org_summary,
            'engine': engine
        }
    except FileNotFoundError:
        st.error("Data file not found. Please ensure sample_ats_export.csv is uploaded.")
        return None

def load_historical_data():
    """Load historical performance data"""
    try:
        if os.path.exists('historical_performance_data.json'):
            with open('historical_performance_data.json', 'r') as f:
                return json.load(f)
        else:
            return generate_sample_historical_data()
    except Exception as e:
        return generate_sample_historical_data()

def generate_sample_historical_data():
    """Generate sample historical data if JSON file is missing"""
    dates = ['2024-11-01', '2024-11-15', '2024-11-29', '2024-12-13', '2024-12-27', '2025-01-10']
    base_scores = [39.8, 44.6, 49.6, 54.6, 58.4, 64.2]
    
    sample_data = {
        'snapshots': [],
        'metadata': {'start_date': dates[0], 'end_date': dates[-1], 'num_snapshots': 6, 'cadence': 'biweekly'}
    }
    
    for i in range(6):
        snapshot = {
            'snapshot_num': i,
            'snapshot_date': dates[i],
            'org_summary': {
                'org_average_score': base_scores[i],
                'recruiter_average': 37.4 + i * 4,
                'hm_average': 41.3 + i * 4.1
            }
        }
        sample_data['snapshots'].append(snapshot)
    
    return sample_data

def get_score_emoji(score):
    """Return emoji based on score"""
    if score >= 70:
        return "🟢"
    elif score >= 50:
        return "🟡"
    else:
        return "🔴"

def render_role_card(role_data, violations_data, is_recruiter_view=True):
    """Render a role card using native Streamlit components"""
    
    # Determine score order based on view
    if is_recruiter_view:
        primary_score = role_data['my_score']
        primary_label = "My Score"
        secondary_score = role_data['partner_score']
        secondary_label = f"{role_data['partner_name']}"
    else:
        primary_score = role_data['my_score']
        primary_label = "My Score"
        secondary_score = role_data['partner_score']
        secondary_label = f"{role_data['partner_name']}"
    
    combined_score = role_data['combined_score']
    
    # Role violations
    role_violations = violations_data[violations_data['requisition_id'] == role_data['req_id']]
    high_count = len(role_violations[role_violations['severity'] == 'high'])
    medium_count = len(role_violations[role_violations['severity'] == 'medium'])
    low_count = len(role_violations[role_violations['severity'] == 'low'])
    
    # Create container for card
    with st.container():
        # Card border styling
        if high_count > 0:
            st.markdown(f"### 🔴 {role_data['job_title']}")
        elif medium_count > 0:
            st.markdown(f"### 🟡 {role_data['job_title']}")
        else:
            st.markdown(f"### 🟢 {role_data['job_title']}")
        
        st.caption(f"{role_data['department']} • {role_data['status']} • {role_data['days_open']} days open")
        
        # Score badges in columns
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(primary_label, f"{primary_score:.0f}", delta=None)
        
        with col2:
            st.metric(f"{secondary_label}", f"{secondary_score:.0f}", delta=None)
        
        with col3:
            st.metric("Combined", f"{combined_score:.0f}", delta=None)
        
        with col4:
            st.metric("Critical", high_count, delta=None, delta_color="inverse")
        
        with col5:
            st.metric("Total Issues", high_count + medium_count + low_count, delta=None)
        
        # Expandable section to view violations
        with st.expander(f"🔍 View Details & Violations", expanded=False):
            if len(role_violations) == 0:
                st.success("✅ No violations! This role is on track.")
            else:
                # Group by metric
                col1, col2, col3 = st.columns(3)
                
                feedback_vios = role_violations[role_violations['metric'] == 'feedback_timeliness']
                velocity_vios = role_violations[role_violations['metric'] == 'stage_velocity']
                engagement_vios = role_violations[role_violations['metric'] == 'hm_engagement']
                
                with col1:
                    st.markdown("**📧 Feedback Timeliness**")
                    if len(feedback_vios) > 0:
                        for _, v in feedback_vios.iterrows():
                            severity_emoji = "🔴" if v['severity'] == 'high' else "🟡" if v['severity'] == 'medium' else "🟢"
                            delay_hours = v.get('delay_hours', 0)
                            st.write(f"{severity_emoji} {v['stage']}: {delay_hours:.0f}hrs ({v['penalty']} pts)")
                    else:
                        st.success("✅ On time")
                
                with col2:
                    st.markdown("**⏱️ Stage Velocity**")
                    if len(velocity_vios) > 0:
                        for _, v in velocity_vios.iterrows():
                            severity_emoji = "🔴" if v['severity'] == 'high' else "🟡" if v['severity'] == 'medium' else "🟢"
                            days = v.get('days_in_stage', 0)
                            st.write(f"{severity_emoji} {v['stage']}: {days:.0f}d ({v['penalty']} pts)")
                    else:
                        st.success("✅ Good pace")
                
                with col3:
                    st.markdown("**👥 Engagement**")
                    if len(engagement_vios) > 0:
                        for _, v in engagement_vios.iterrows():
                            missing = v.get('missing_feedback_count', 0)
                            delayed = v.get('delayed_feedback_count', 0)
                            st.write(f"🔴 Missing: {missing}, Delayed: {delayed}")
                    else:
                        st.success("✅ Engaged")
        
        st.markdown("---")

def login_screen():
    """Display login/role selection screen"""
    st.title("📊 Talent Score Platform")
    st.markdown("---")
    
    data = load_data()
    if not data:
        return None, None
    
    st.subheader("Select Your Role")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 👤 Recruiter")
        recruiter_names = sorted(data['recruiter_scores']['name'].unique())
        selected_recruiter = st.selectbox("Select your name:", [""] + recruiter_names, key="rec_login")
        if selected_recruiter and st.button("Login as Recruiter", key="rec_btn", use_container_width=True):
            st.session_state.role = "recruiter"
            st.session_state.user_name = selected_recruiter
            st.rerun()
    
    with col2:
        st.markdown("### 🎯 Hiring Manager")
        hm_names = sorted(data['hm_scores']['name'].unique())
        selected_hm = st.selectbox("Select your name:", [""] + hm_names, key="hm_login")
        if selected_hm and st.button("Login as Hiring Manager", key="hm_btn", use_container_width=True):
            st.session_state.role = "hiring_manager"
            st.session_state.user_name = selected_hm
            st.rerun()
    
    with col3:
        st.markdown("### 👔 Leadership")
        st.write("")
        st.write("")
        if st.button("Login as Leadership", key="lead_btn", use_container_width=True):
            st.session_state.role = "leadership"
            st.session_state.user_name = "Leadership"
            st.rerun()
    
    return None, None

def render_recruiter_view(data, user_name):
    """Recruiter-specific view: Only their roles with visual cards"""
    st.title(f"📊 My Performance Dashboard")
    st.caption(f"Logged in as: {user_name} (Recruiter)")
    
    # Logout button
    if st.button("← Logout", key="logout_rec"):
        del st.session_state.role
        del st.session_state.user_name
        st.rerun()
    
    raw_data = data['raw_data']
    violations = data['violations']
    recruiter_scores = data['recruiter_scores']
    hm_scores = data['hm_scores']
    
    # Get recruiter's score
    my_score_data = recruiter_scores[recruiter_scores['name'] == user_name].iloc[0]
    my_score = my_score_data['final_score']
    
    # Show recruiter's overall score prominently
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    score_emoji = get_score_emoji(my_score)
    
    with col1:
        st.metric("Your Overall Score", f"{score_emoji} {my_score:.0f}/100")
    
    with col2:
        st.metric("Total Violations", my_score_data['total_violations'])
    
    with col3:
        st.metric("Feedback Score", f"{my_score_data['feedback_score']:.0f}/100")
    
    with col4:
        st.metric("Velocity Score", f"{my_score_data['velocity_score']:.0f}/100")
    
    st.markdown("---")
    
    # Get roles assigned to this recruiter
    my_roles = raw_data[raw_data['recruiter_name'] == user_name]['requisition_id'].unique()
    
    st.subheader(f"My Open Roles ({len(my_roles)} roles)")
    
    # Build role data for cards
    for req_id in my_roles:
        req_data = raw_data[raw_data['requisition_id'] == req_id].iloc[0]
        hm = req_data['hiring_manager_name']
        
        # Get HM score
        hm_score_data = hm_scores[hm_scores['name'] == hm]
        hm_score = hm_score_data['final_score'].iloc[0] if len(hm_score_data) > 0 else 0
        
        # Combined score
        combined_score = (my_score * 0.5 + hm_score * 0.5)
        
        # Days open
        role_opened = pd.to_datetime(req_data['role_opened_date'])
        days_open = (datetime.now() - role_opened).days
        
        role_card_data = {
            'req_id': req_id,
            'job_title': req_data['job_title'],
            'department': req_data['team'],
            'my_score': my_score,
            'partner_name': hm,
            'partner_score': hm_score,
            'combined_score': combined_score,
            'days_open': days_open,
            'status': req_data['current_status']
        }
        
        render_role_card(role_card_data, violations, is_recruiter_view=True)
    
    # Show score trend
    st.markdown("---")
    st.subheader("📈 My Score Trend")
    
    historical_data = load_historical_data()
    if historical_data and 'snapshots' in historical_data:
        dates = [s['snapshot_date'] for s in historical_data['snapshots']]
        scores = [s['org_summary']['recruiter_average'] for s in historical_data['snapshots']]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            line=dict(color='#10b981', width=3),
            marker=dict(size=10),
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.1)'
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Score",
            yaxis=dict(range=[0, 100]),
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        if len(scores) >= 2:
            improvement = scores[-1] - scores[0]
            if improvement > 0:
                st.success(f"📈 +{improvement:.1f} point improvement over {len(scores)} periods!")
            else:
                st.warning(f"📉 {improvement:.1f} point change - let's work on improving this together")

def render_hiring_manager_view(data, user_name):
    """Hiring Manager-specific view: Only their roles with visual cards"""
    st.title(f"📊 My Performance Dashboard")
    st.caption(f"Logged in as: {user_name} (Hiring Manager)")
    
    # Logout button
    if st.button("← Logout", key="logout_hm"):
        del st.session_state.role
        del st.session_state.user_name
        st.rerun()
    
    raw_data = data['raw_data']
    violations = data['violations']
    recruiter_scores = data['recruiter_scores']
    hm_scores = data['hm_scores']
    
    # Get HM's score
    my_score_data = hm_scores[hm_scores['name'] == user_name].iloc[0]
    my_score = my_score_data['final_score']
    
    # Show HM's overall score prominently
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    score_emoji = get_score_emoji(my_score)
    
    with col1:
        st.metric("Your Overall Score", f"{score_emoji} {my_score:.0f}/100")
    
    with col2:
        st.metric("Total Violations", my_score_data['total_violations'])
    
    with col3:
        st.metric("Feedback Score", f"{my_score_data['feedback_score']:.0f}/100")
    
    with col4:
        st.metric("Engagement Score", f"{my_score_data['engagement_score']:.0f}/100")
    
    st.markdown("---")
    
    # Get roles assigned to this HM
    my_roles = raw_data[raw_data['hiring_manager_name'] == user_name]['requisition_id'].unique()
    
    st.subheader(f"My Open Roles ({len(my_roles)} roles)")
    
    # Build role data for cards
    for req_id in my_roles:
        req_data = raw_data[raw_data['requisition_id'] == req_id].iloc[0]
        recruiter = req_data['recruiter_name']
        
        # Get recruiter score
        rec_score_data = recruiter_scores[recruiter_scores['name'] == recruiter]
        rec_score = rec_score_data['final_score'].iloc[0] if len(rec_score_data) > 0 else 0
        
        # Combined score
        combined_score = (my_score * 0.5 + rec_score * 0.5)
        
        # Days open
        role_opened = pd.to_datetime(req_data['role_opened_date'])
        days_open = (datetime.now() - role_opened).days
        
        role_card_data = {
            'req_id': req_id,
            'job_title': req_data['job_title'],
            'department': req_data['team'],
            'my_score': my_score,
            'partner_name': recruiter,
            'partner_score': rec_score,
            'combined_score': combined_score,
            'days_open': days_open,
            'status': req_data['current_status']
        }
        
        render_role_card(role_card_data, violations, is_recruiter_view=False)
    
    # Show score trend
    st.markdown("---")
    st.subheader("📈 My Score Trend")
    
    historical_data = load_historical_data()
    if historical_data and 'snapshots' in historical_data:
        dates = [s['snapshot_date'] for s in historical_data['snapshots']]
        scores = [s['org_summary']['hm_average'] for s in historical_data['snapshots']]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            line=dict(color='#f59e0b', width=3),
            marker=dict(size=10),
            fill='tozeroy',
            fillcolor='rgba(245, 158, 11, 0.1)'
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Score",
            yaxis=dict(range=[0, 100]),
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        if len(scores) >= 2:
            improvement = scores[-1] - scores[0]
            if improvement > 0:
                st.success(f"📈 +{improvement:.1f} point improvement over {len(scores)} periods!")
            else:
                st.warning(f"📉 {improvement:.1f} point change - let's work on improving this together")

def render_leadership_view(data):
    """Leadership view: See everything with visual cards + simplified trends"""
    st.title("📊 Leadership Dashboard")
    st.caption("Organization-Wide Performance Overview")
    
    # Logout button
    if st.button("← Logout", key="logout_lead"):
        del st.session_state.role
        del st.session_state.user_name
        st.rerun()
    
    raw_data = data['raw_data']
    violations = data['violations']
    recruiter_scores = data['recruiter_scores']
    hm_scores = data['hm_scores']
    org_summary = data['org_summary']
    
    # Top metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    org_score = org_summary['org_average_score']
    score_emoji = get_score_emoji(org_score)
    
    with col1:
        st.metric("Organization Score", f"{score_emoji} {org_score:.0f}/100")
    
    with col2:
        st.metric("Recruiter Average", f"{org_summary['recruiter_average']:.0f}/100")
    
    with col3:
        st.metric("Manager Average", f"{org_summary['hm_average']:.0f}/100")
    
    with col4:
        st.metric("Critical Issues", org_summary['high_severity_total'])
    
    st.markdown("---")
    
    # Score trend over time
    st.subheader("📈 Organization Score Trend")
    
    historical_data = load_historical_data()
    if historical_data and 'snapshots' in historical_data:
        dates = [s['snapshot_date'] for s in historical_data['snapshots']]
        org_scores = [s['org_summary']['org_average_score'] for s in historical_data['snapshots']]
        rec_scores = [s['org_summary']['recruiter_average'] for s in historical_data['snapshots']]
        hm_scores_hist = [s['org_summary']['hm_average'] for s in historical_data['snapshots']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates, y=org_scores, mode='lines+markers', name='Organization',
            line=dict(color='#3b82f6', width=3), marker=dict(size=10)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates, y=rec_scores, mode='lines+markers', name='Recruiters',
            line=dict(color='#10b981', width=2), marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates, y=hm_scores_hist, mode='lines+markers', name='Hiring Managers',
            line=dict(color='#f59e0b', width=2), marker=dict(size=8)
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Score",
            yaxis=dict(range=[0, 100]),
            height=400,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        if len(org_scores) >= 2:
            improvement = org_scores[-1] - org_scores[0]
            col1, col2 = st.columns(2)
            
            with col1:
                if improvement > 0:
                    st.success(f"📈 **+{improvement:.1f} point improvement** over {len(org_scores)} periods")
                else:
                    st.warning(f"📉 {improvement:.1f} point change")
            
            with col2:
                st.info(f"**Current Trajectory:** {'Improving' if improvement > 0 else 'Needs Attention'}")
    
    st.markdown("---")
    
    # All roles as cards
    st.subheader("All Open Roles")
    
    all_req_ids = raw_data['requisition_id'].unique()
    
    for req_id in all_req_ids:
        req_data = raw_data[raw_data['requisition_id'] == req_id].iloc[0]
        recruiter = req_data['recruiter_name']
        hm = req_data['hiring_manager_name']
        
        # Get scores
        rec_score_data = recruiter_scores[recruiter_scores['name'] == recruiter]
        rec_score = rec_score_data['final_score'].iloc[0] if len(rec_score_data) > 0 else 0
        
        hm_score_data = hm_scores[hm_scores['name'] == hm]
        hm_score = hm_score_data['final_score'].iloc[0] if len(hm_score_data) > 0 else 0
        
        combined_score = (rec_score * 0.5 + hm_score * 0.5)
        
        # Days open
        role_opened = pd.to_datetime(req_data['role_opened_date'])
        days_open = (datetime.now() - role_opened).days
        
        # Role violations
        role_violations = violations[violations['requisition_id'] == req_id]
        high_count = len(role_violations[role_violations['severity'] == 'high'])
        
        # Leadership sees both scores
        with st.container():
            if high_count > 0:
                st.markdown(f"### 🔴 {req_data['job_title']}")
            else:
                st.markdown(f"### 🟢 {req_data['job_title']}")
            
            st.caption(f"{req_data['team']} • {recruiter} + {hm} • {days_open} days open")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Recruiter", f"{rec_score:.0f}")
            
            with col2:
                st.metric("Manager", f"{hm_score:.0f}")
            
            with col3:
                st.metric("Combined", f"{combined_score:.0f}")
            
            with col4:
                st.metric("Critical", high_count, delta_color="inverse")
            
            st.markdown("---")

def main():
    """Main app logic"""
    
    # Check if user is logged in
    if 'role' not in st.session_state:
        login_screen()
        return
    
    # Load data
    data = load_data()
    if not data:
        return
    
    # Route to appropriate view
    if st.session_state.role == "recruiter":
        render_recruiter_view(data, st.session_state.user_name)
    elif st.session_state.role == "hiring_manager":
        render_hiring_manager_view(data, st.session_state.user_name)
    elif st.session_state.role == "leadership":
        render_leadership_view(data)

if __name__ == "__main__":
    main()
