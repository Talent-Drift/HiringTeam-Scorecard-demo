"""
Talent Score Platform - Matching Reference Design
Clean table-based view with sidebar drill-down
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scoring_engine import ScorecardEngine
from datetime import datetime
import json
import os

# Page config
st.set_page_config(
    page_title="Hiring Process Health - MVP",
    page_icon="📊",
    layout="wide"
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
        st.error("Data file not found")
        return None

def load_historical_data():
    """Load historical performance data"""
    try:
        if os.path.exists('historical_performance_data.json'):
            with open('historical_performance_data.json', 'r') as f:
                return json.load(f)
        else:
            return generate_sample_historical_data()
    except:
        return generate_sample_historical_data()

def generate_sample_historical_data():
    """Generate sample historical data"""
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

def get_score_color(score):
    """Return color for score badge"""
    if score >= 80:
        return "#10b981"  # Green
    elif score >= 65:
        return "#f59e0b"  # Orange
    else:
        return "#ef4444"  # Red

def format_score_badge(score):
    """Create HTML for score badge"""
    color = get_score_color(score)
    return f'<div style="background-color: {color}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: 600; text-align: center; display: inline-block;">{int(score)}</div>'

def login_screen():
    """Display login screen"""
    st.title("📊 Hiring Process Health - MVP")
    st.markdown("---")
    
    data = load_data()
    if not data:
        return
    
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

def render_recruiter_view(data, user_name):
    """Recruiter view matching the screenshot design"""
    
    # Logout in sidebar
    with st.sidebar:
        st.button("← Logout", key="logout", on_click=lambda: [st.session_state.pop('role'), st.session_state.pop('user_name')])
    
    # Title
    st.title("Hiring Process Health - MVP")
    st.caption(f"Logged in as: {user_name}")
    
    raw_data = data['raw_data']
    violations = data['violations']
    recruiter_scores = data['recruiter_scores']
    hm_scores = data['hm_scores']
    
    # Get my score
    my_score_data = recruiter_scores[recruiter_scores['name'] == user_name].iloc[0]
    my_score = my_score_data['final_score']
    
    # Get my roles
    my_roles = raw_data[raw_data['recruiter_name'] == user_name]['requisition_id'].unique()
    
    # Calculate trend (fake for now - would compare to last period)
    trend = 3  # +3 vs last 14 days
    
    # Top metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Avg Recruiter Score", int(my_score), delta=f"{trend} vs last 14 days")
    
    with col2:
        # Calculate avg HM score for my roles
        my_hms = raw_data[raw_data['recruiter_name'] == user_name]['hiring_manager_name'].unique()
        avg_hm_score = hm_scores[hm_scores['name'].isin(my_hms)]['final_score'].mean()
        hm_trend = -2
        st.metric("Avg Hiring Manager", int(avg_hm_score), delta=f"{hm_trend} vs last 14 days")
    
    with col3:
        st.metric("Open Roles", len(my_roles))
    
    st.markdown("---")
    
    # Main content area with sidebar
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_main:
        st.subheader("Role Performance - Last 14 Days")
        
        # Build table data
        table_data = []
        for req_id in my_roles:
            req_data = raw_data[raw_data['requisition_id'] == req_id].iloc[0]
            hm = req_data['hiring_manager_name']
            
            hm_score_data = hm_scores[hm_scores['name'] == hm]
            hm_score = hm_score_data['final_score'].iloc[0] if len(hm_score_data) > 0 else 0
            
            # Fake trend for demo
            trend = ["+6", "-5", "+3", "+3", "-7"][len(table_data) % 5]
            
            table_data.append({
                'Role': req_data['job_title'],
                'Department': req_data['team'],
                'Recruiter': user_name,
                'Rec. Score': int(my_score),
                'Hiring Manager': hm,
                'Mgr. Score': int(hm_score),
                'Trend': trend,
                'req_id': req_id
            })
        
        df_display = pd.DataFrame(table_data)
        
        # Custom styling for the table
        def style_score(val):
            if isinstance(val, int):
                color = get_score_color(val)
                return f'background-color: {color}; color: white; font-weight: bold; border-radius: 4px; padding: 4px 8px;'
            return ''
        
        def style_trend(val):
            if isinstance(val, str) and val.startswith('+'):
                return 'color: #10b981; font-weight: bold;'
            elif isinstance(val, str) and val.startswith('-'):
                return 'color: #ef4444; font-weight: bold;'
            return ''
        
        # Display table
        st.dataframe(
            df_display[['Role', 'Department', 'Recruiter', 'Rec. Score', 'Hiring Manager', 'Mgr. Score', 'Trend']],
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Click to select role
        selected_role_idx = st.selectbox(
            "Click on a role to view details:",
            range(len(df_display)),
            format_func=lambda x: df_display.iloc[x]['Role']
        )
    
    with col_sidebar:
        if selected_role_idx is not None:
            selected_row = df_display.iloc[selected_role_idx]
            selected_req_id = selected_row['req_id']
            
            st.markdown(f"### {selected_row['Role']}")
            st.caption(f"{selected_row['Department']} / {selected_row['Recruiter']}")
            
            st.markdown("---")
            
            st.markdown("**Recruiter Score**")
            score_color = get_score_color(selected_row['Rec. Score'])
            st.markdown(f'<div style="background: linear-gradient(to right, {score_color} 0%, {score_color} {selected_row["Rec. Score"]}%, #f3f4f6 {selected_row["Rec. Score"]}%); padding: 20px; border-radius: 8px; text-align: center; font-size: 32px; font-weight: bold; color: #1f2937;">{selected_row["Rec. Score"]}</div>', unsafe_allow_html=True)
            
            st.markdown("")
            st.markdown("**Hiring Manager Score**")
            hm_score_color = get_score_color(selected_row['Mgr. Score'])
            st.markdown(f'<div style="background: linear-gradient(to right, {hm_score_color} 0%, {hm_score_color} {selected_row["Mgr. Score"]}%, #f3f4f6 {selected_row["Mgr. Score"]}%); padding: 20px; border-radius: 8px; text-align: center; font-size: 32px; font-weight: bold; color: #1f2937;">{selected_row["Mgr. Score"]}</div>', unsafe_allow_html=True)
            
            st.markdown("")
            combined = int((selected_row['Rec. Score'] + selected_row['Mgr. Score']) / 2)
            combined_color = get_score_color(combined)
            st.markdown(f"**Combined Score** {combined} {selected_row['Trend']}")
            
            st.markdown("---")
            
            st.markdown("**Recent Violations (Last 14 Days)**")
            
            # Get violations for this role
            role_violations = violations[violations['requisition_id'] == selected_req_id]
            
            if len(role_violations) > 0:
                for _, v in role_violations.head(3).iterrows():
                    severity_emoji = "🔴" if v['severity'] == 'high' else "🟡"
                    
                    if v['metric'] == 'stage_velocity':
                        st.markdown(f"{severity_emoji} **Stage Delay (High)**")
                        st.caption(f"Owner ▶ {selected_row['Hiring Manager']}")
                        st.caption(f"{v.get('days_in_stage', 5)} days")
                    elif v['metric'] == 'feedback_timeliness':
                        st.markdown(f"{severity_emoji} **Interview Feedback Overdue**")
                        st.caption(f"Owner ▶ {selected_row['Hiring Manager']}")
                        st.caption(f"{int(v.get('delay_hours', 72) / 24)} days")
                    
                    st.markdown("")
            else:
                st.success("No violations!")
            
            st.caption("Worse than last period.")

def render_hiring_manager_view(data, user_name):
    """Hiring Manager view - same layout as recruiter"""
    
    # Logout in sidebar
    with st.sidebar:
        st.button("← Logout", key="logout", on_click=lambda: [st.session_state.pop('role'), st.session_state.pop('user_name')])
    
    st.title("Hiring Process Health - MVP")
    st.caption(f"Logged in as: {user_name}")
    
    raw_data = data['raw_data']
    violations = data['violations']
    recruiter_scores = data['recruiter_scores']
    hm_scores = data['hm_scores']
    
    # Get my score
    my_score_data = hm_scores[hm_scores['name'] == user_name].iloc[0]
    my_score = my_score_data['final_score']
    
    # Get my roles
    my_roles = raw_data[raw_data['hiring_manager_name'] == user_name]['requisition_id'].unique()
    
    # Top metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        my_recruiters = raw_data[raw_data['hiring_manager_name'] == user_name]['recruiter_name'].unique()
        avg_rec_score = recruiter_scores[recruiter_scores['name'].isin(my_recruiters)]['final_score'].mean()
        st.metric("Avg Recruiter Score", int(avg_rec_score), delta=f"+3 vs last 14 days")
    
    with col2:
        st.metric("Avg Hiring Manager", int(my_score), delta=f"-2 vs last 14 days")
    
    with col3:
        st.metric("Open Roles", len(my_roles))
    
    st.markdown("---")
    
    # Main content with sidebar
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_main:
        st.subheader("Role Performance - Last 14 Days")
        
        # Build table data
        table_data = []
        for req_id in my_roles:
            req_data = raw_data[raw_data['requisition_id'] == req_id].iloc[0]
            recruiter = req_data['recruiter_name']
            
            rec_score_data = recruiter_scores[recruiter_scores['name'] == recruiter]
            rec_score = rec_score_data['final_score'].iloc[0] if len(rec_score_data) > 0 else 0
            
            trend = ["+6", "-5", "+3", "+3", "-7"][len(table_data) % 5]
            
            table_data.append({
                'Role': req_data['job_title'],
                'Department': req_data['team'],
                'Recruiter': recruiter,
                'Rec. Score': int(rec_score),
                'Hiring Manager': user_name,
                'Mgr. Score': int(my_score),
                'Trend': trend,
                'req_id': req_id
            })
        
        df_display = pd.DataFrame(table_data)
        
        st.dataframe(
            df_display[['Role', 'Department', 'Recruiter', 'Rec. Score', 'Hiring Manager', 'Mgr. Score', 'Trend']],
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        selected_role_idx = st.selectbox(
            "Click on a role to view details:",
            range(len(df_display)),
            format_func=lambda x: df_display.iloc[x]['Role']
        )
    
    with col_sidebar:
        if selected_role_idx is not None:
            selected_row = df_display.iloc[selected_role_idx]
            selected_req_id = selected_row['req_id']
            
            st.markdown(f"### {selected_row['Role']}")
            st.caption(f"{selected_row['Department']} / {selected_row['Recruiter']}")
            
            st.markdown("---")
            
            st.markdown("**Recruiter Score**")
            score_color = get_score_color(selected_row['Rec. Score'])
            st.markdown(f'<div style="background: linear-gradient(to right, {score_color} 0%, {score_color} {selected_row["Rec. Score"]}%, #f3f4f6 {selected_row["Rec. Score"]}%); padding: 20px; border-radius: 8px; text-align: center; font-size: 32px; font-weight: bold; color: #1f2937;">{selected_row["Rec. Score"]}</div>', unsafe_allow_html=True)
            
            st.markdown("")
            st.markdown("**Hiring Manager Score**")
            hm_score_color = get_score_color(selected_row['Mgr. Score'])
            st.markdown(f'<div style="background: linear-gradient(to right, {hm_score_color} 0%, {hm_score_color} {selected_row["Mgr. Score"]}%, #f3f4f6 {selected_row["Mgr. Score"]}%); padding: 20px; border-radius: 8px; text-align: center; font-size: 32px; font-weight: bold; color: #1f2937;">{selected_row["Mgr. Score"]}</div>', unsafe_allow_html=True)
            
            st.markdown("")
            combined = int((selected_row['Rec. Score'] + selected_row['Mgr. Score']) / 2)
            st.markdown(f"**Combined Score** {combined} {selected_row['Trend']}")
            
            st.markdown("---")
            
            st.markdown("**Recent Violations (Last 14 Days)**")
            
            role_violations = violations[violations['requisition_id'] == selected_req_id]
            
            if len(role_violations) > 0:
                for _, v in role_violations.head(3).iterrows():
                    severity_emoji = "🔴" if v['severity'] == 'high' else "🟡"
                    
                    if v['metric'] == 'stage_velocity':
                        st.markdown(f"{severity_emoji} **Stage Delay (High)**")
                        st.caption(f"Owner ▶ Hiring Manager")
                        st.caption(f"{v.get('days_in_stage', 5)} days")
                    elif v['metric'] == 'feedback_timeliness':
                        st.markdown(f"{severity_emoji} **Interview Feedback Overdue**")
                        st.caption(f"Owner ▶ Hiring Manager")
                        st.caption(f"{int(v.get('delay_hours', 72) / 24)} days")
                    
                    st.markdown("")
            else:
                st.success("No violations!")
            
            st.caption("Worse than last period.")

def render_leadership_view(data):
    """Leadership view with org-wide trends"""
    
    with st.sidebar:
        st.button("← Logout", key="logout", on_click=lambda: [st.session_state.pop('role'), st.session_state.pop('user_name')])
    
    st.title("Hiring Process Health - MVP")
    st.caption("Leadership Dashboard")
    
    org_summary = data['org_summary']
    
    # Top metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Avg Recruiter Score", int(org_summary['recruiter_average']), delta="+3 vs last 14 days")
    
    with col2:
        st.metric("Avg Hiring Manager", int(org_summary['hm_average']), delta="-2 vs last 14 days")
    
    with col3:
        st.metric("Open Roles", len(data['raw_data']['requisition_id'].unique()))
    
    st.markdown("---")
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
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

def main():
    """Main app"""
    
    if 'role' not in st.session_state:
        login_screen()
        return
    
    data = load_data()
    if not data:
        return
    
    if st.session_state.role == "recruiter":
        render_recruiter_view(data, st.session_state.user_name)
    elif st.session_state.role == "hiring_manager":
        render_hiring_manager_view(data, st.session_state.user_name)
    elif st.session_state.role == "leadership":
        render_leadership_view(data)

if __name__ == "__main__":
    main()
