"""
Recruiter Scorecard Dashboard
Interactive web interface for viewing performance scores and metrics
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
    page_title="Recruiter Scorecard Demo",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .score-high {
        color: #00cc00;
        font-weight: bold;
        font-size: 2em;
    }
    .score-medium {
        color: #ff9900;
        font-weight: bold;
        font-size: 2em;
    }
    .score-low {
        color: #cc0000;
        font-weight: bold;
        font-size: 2em;
    }
    </style>
""", unsafe_allow_html=True)

def get_score_color(score):
    """Return color class based on score"""
    if score >= 70:
        return "score-high"
    elif score >= 50:
        return "score-medium"
    else:
        return "score-low"

def load_data():
    """Load and process data"""
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
        return None

def load_historical_data():
    """Load historical performance data"""
    try:
        if os.path.exists('historical_performance_data.json'):
            with open('historical_performance_data.json', 'r') as f:
                return json.load(f)
        else:
            # Generate sample data on the fly if JSON is missing
            st.warning("⚠️ Historical data file not found. Generating sample trend data for demo purposes.")
            return generate_sample_historical_data()
    except Exception as e:
        st.error(f"Error loading historical data: {e}")
        return generate_sample_historical_data()

def generate_sample_historical_data():
    """Generate sample historical data if JSON file is missing"""
    dates = ['2024-11-01', '2024-11-15', '2024-11-29', '2024-12-13', '2024-12-27', '2025-01-10']
    
    # Sample data showing improvement
    sample_data = {
        'snapshots': [],
        'metadata': {
            'start_date': dates[0],
            'end_date': dates[-1],
            'num_snapshots': 6,
            'cadence': 'biweekly'
        }
    }
    
    # Generate 6 snapshots with improving scores
    base_scores = [39.8, 44.6, 49.6, 54.6, 58.4, 64.2]
    rec_scores = [37.4, 42.0, 47.0, 52.0, 56.5, 61.4]
    hm_scores = [41.3, 46.0, 51.0, 56.0, 59.8, 66.0]
    violations = [46, 40, 35, 28, 23, 19]
    
    for i in range(6):
        snapshot = {
            'snapshot_num': i,
            'snapshot_date': dates[i],
            'recruiters': [
                {'name': 'Sarah Chen', 'role_type': 'Recruiter', 'final_score': 45 + i*4, 'total_violations': 10 - i},
                {'name': 'Mike Rodriguez', 'role_type': 'Recruiter', 'final_score': 52 + i*3, 'total_violations': 8 - i},
                {'name': 'Jessica Williams', 'role_type': 'Recruiter', 'final_score': 38 + i*5, 'total_violations': 12 - i*2},
            ],
            'hiring_managers': [
                {'name': 'Tom Brady', 'role_type': 'Hiring Manager', 'final_score': 27 + i*8, 'total_violations': 15 - i*2},
                {'name': 'Alex Kumar', 'role_type': 'Hiring Manager', 'final_score': 55 + i*3, 'total_violations': 7 - i},
                {'name': 'Mark Watson', 'role_type': 'Hiring Manager', 'final_score': 36 + i*6, 'total_violations': 11 - i*2},
            ],
            'org_summary': {
                'org_average_score': base_scores[i],
                'recruiter_average': rec_scores[i],
                'hm_average': hm_scores[i],
                'total_violations': violations[i] * 2,
                'high_severity_total': violations[i],
                'people_count': 18
            }
        }
        sample_data['snapshots'].append(snapshot)
    
    return sample_data

def render_trends_dashboard():
    """Render leadership view with historical trends and improvement metrics"""
    st.header("📈 Trends & Progress (Leadership View)")
    st.caption("Track team improvement over time and identify success stories")
    
    # Load historical data
    historical_data = load_historical_data()
    
    if not historical_data or 'snapshots' not in historical_data:
        st.error("Unable to load historical data. Please check that historical_performance_data.json is uploaded to your GitHub repo.")
        return
    
    snapshots = historical_data['snapshots']
    
    if len(snapshots) == 0:
        st.error("No snapshot data available.")
        return
    
    # Extract trend data
    dates = [s['snapshot_date'] for s in snapshots]
    org_scores = [s['org_summary']['org_average_score'] for s in snapshots]
    rec_scores = [s['org_summary']['recruiter_average'] for s in snapshots]
    hm_scores = [s['org_summary']['hm_average'] for s in snapshots]
    high_violations = [s['org_summary']['high_severity_total'] for s in snapshots]
    
    # Calculate improvements
    first_snapshot = snapshots[0]['org_summary']
    last_snapshot = snapshots[-1]['org_summary']
    
    org_improvement = last_snapshot['org_average_score'] - first_snapshot['org_average_score']
    rec_improvement = last_snapshot['recruiter_average'] - first_snapshot['recruiter_average']
    hm_improvement = last_snapshot['hm_average'] - first_snapshot['hm_average']
    violation_reduction = first_snapshot['high_severity_total'] - last_snapshot['high_severity_total']
    
    # Top-level summary metrics
    st.subheader("🎯 3-Month Impact Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Organization Score",
            f"{last_snapshot['org_average_score']}/100",
            delta=f"+{org_improvement:.1f} pts",
            delta_color="normal"
        )
        st.caption(f"Started at {first_snapshot['org_average_score']}")
    
    with col2:
        st.metric(
            "Recruiter Average",
            f"{last_snapshot['recruiter_average']}/100",
            delta=f"+{rec_improvement:.1f} pts",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "Manager Average",
            f"{last_snapshot['hm_average']}/100",
            delta=f"+{hm_improvement:.1f} pts",
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            "Critical Issues",
            last_snapshot['high_severity_total'],
            delta=f"-{violation_reduction}",
            delta_color="inverse"
        )
        st.caption(f"Down from {first_snapshot['high_severity_total']}")
    
    st.markdown("---")
    
    # Main trend charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Overall Performance Trend")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=org_scores,
            mode='lines+markers',
            name='Organization',
            line=dict(color='#4299e1', width=3),
            marker=dict(size=10)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=rec_scores,
            mode='lines+markers',
            name='Recruiters',
            line=dict(color='#48bb78', width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=hm_scores,
            mode='lines+markers',
            name='Hiring Managers',
            line=dict(color='#ed8936', width=2),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Average Score",
            yaxis=dict(range=[0, 100]),
            hovermode='x unified',
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Critical Issues Reduction")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=dates,
            y=high_violations,
            marker=dict(
                color=high_violations,
                colorscale='Reds_r',
                showscale=False
            ),
            text=high_violations,
            textposition='auto'
        ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of High Severity Issues",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Individual improvement tracking
    st.subheader("⭐ Individual Performance Tracking")
    
    # Get all people from first and last snapshot
    first_people_rec = {p['name']: p['final_score'] for p in snapshots[0]['recruiters']}
    last_people_rec = {p['name']: p['final_score'] for p in snapshots[-1]['recruiters']}
    
    first_people_hm = {p['name']: p['final_score'] for p in snapshots[0]['hiring_managers']}
    last_people_hm = {p['name']: p['final_score'] for p in snapshots[-1]['hiring_managers']}
    
    # Calculate improvements
    rec_improvements = {name: last_people_rec[name] - first_people_rec[name] for name in first_people_rec}
    hm_improvements = {name: last_people_hm[name] - first_people_hm[name] for name in first_people_hm}
    
    all_improvements = {**rec_improvements, **hm_improvements}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏆 Top 5 Most Improved")
        top_improvers = sorted(all_improvements.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for i, (name, improvement) in enumerate(top_improvers, 1):
            if name in first_people_rec:
                role = "Recruiter"
                start_score = first_people_rec[name]
                end_score = last_people_rec[name]
            else:
                role = "Hiring Manager"
                start_score = first_people_hm[name]
                end_score = last_people_hm[name]
            
            st.success(f"**{i}. {name}** ({role})")
            st.caption(f"   {start_score:.1f} → {end_score:.1f} (+{improvement:.1f} points)")
    
    with col2:
        st.markdown("#### ⚠️ Needs Additional Support")
        bottom_improvers = sorted(all_improvements.items(), key=lambda x: x[1])[:5]
        
        for i, (name, improvement) in enumerate(bottom_improvers, 1):
            if name in first_people_rec:
                role = "Recruiter"
                start_score = first_people_rec[name]
                end_score = last_people_rec[name]
            else:
                role = "Hiring Manager"
                start_score = first_people_hm[name]
                end_score = last_people_hm[name]
            
            if improvement < 15:  # Less than expected improvement
                st.warning(f"**{i}. {name}** ({role})")
                st.caption(f"   {start_score:.1f} → {end_score:.1f} (+{improvement:.1f} points)")
            else:
                st.info(f"**{i}. {name}** ({role})")
                st.caption(f"   {start_score:.1f} → {end_score:.1f} (+{improvement:.1f} points)")
    
    st.markdown("---")
    
    # Detailed person-by-person trends
    st.subheader("📊 Individual Trend Lines")
    
    tab1, tab2 = st.tabs(["Recruiters", "Hiring Managers"])
    
    with tab1:
        # Get all recruiter names
        recruiter_names = list(first_people_rec.keys())
        
        # Create trend data for each recruiter
        recruiter_trends = {}
        for name in recruiter_names:
            scores = [s['final_score'] for s in [p for snap in snapshots for p in snap['recruiters'] if p['name'] == name]]
            recruiter_trends[name] = scores
        
        fig = go.Figure()
        
        for name, scores in recruiter_trends.items():
            fig.add_trace(go.Scatter(
                x=dates,
                y=scores,
                mode='lines+markers',
                name=name,
                line=dict(width=2),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Score",
            yaxis=dict(range=[0, 100]),
            hovermode='x unified',
            height=500,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Get all HM names
        hm_names = list(first_people_hm.keys())
        
        # Create trend data for each HM
        hm_trends = {}
        for name in hm_names:
            scores = [s['final_score'] for s in [p for snap in snapshots for p in snap['hiring_managers'] if p['name'] == name]]
            hm_trends[name] = scores
        
        fig = go.Figure()
        
        for name, scores in hm_trends.items():
            fig.add_trace(go.Scatter(
                x=dates,
                y=scores,
                mode='lines+markers',
                name=name,
                line=dict(width=2),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Score",
            yaxis=dict(range=[0, 100]),
            hovermode='x unified',
            height=500,
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Key insights and recommendations
    st.subheader("💡 Key Insights & Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✅ What's Working")
        st.success(f"**Overall improvement of +{org_improvement:.1f} points** in 3 months demonstrates the platform is driving behavioral change.")
        st.success(f"**{violation_reduction} fewer critical issues** - team is becoming more responsive and following SLAs.")
        
        # Find best performer
        best_name = max(all_improvements.items(), key=lambda x: x[1])[0]
        best_improvement = all_improvements[best_name]
        st.success(f"**{best_name}** is your star performer with +{best_improvement:.1f} point improvement. Consider having them share best practices.")
    
    with col2:
        st.markdown("#### 🎯 Areas for Focus")
        
        # Find slowest improver
        slowest_name = min(all_improvements.items(), key=lambda x: x[1])[0]
        slowest_improvement = all_improvements[slowest_name]
        
        if slowest_improvement < 15:
            st.warning(f"**{slowest_name}** needs additional coaching - only +{slowest_improvement:.1f} point improvement.")
        
        # Check if any group is lagging
        if hm_improvement < rec_improvement:
            st.warning("**Hiring Managers** improving slower than Recruiters - consider additional training on feedback timeliness.")
        
        st.info("**Recommendation:** Continue biweekly check-ins. Target org score of 75+ by next quarter.")

def render_open_roles_dashboard(data):
    """Render role-centric dashboard showing recruiter + HM partnerships"""
    st.header("📋 Open Roles Dashboard")
    
    # Calculate role-level scores
    raw_data = data['raw_data']
    violations = data['violations']
    recruiter_scores = data['recruiter_scores']
    hm_scores = data['hm_scores']
    
    # Get unique requisitions
    requisitions = []
    for req_id in raw_data['requisition_id'].unique():
        req_data = raw_data[raw_data['requisition_id'] == req_id].iloc[0]
        
        recruiter = req_data['recruiter_name']
        hm = req_data['hiring_manager_name']
        
        # Get scores
        rec_score = recruiter_scores[recruiter_scores['name'] == recruiter]['final_score'].iloc[0] if len(recruiter_scores[recruiter_scores['name'] == recruiter]) > 0 else 0
        hm_score = hm_scores[hm_scores['name'] == hm]['final_score'].iloc[0] if len(hm_scores[hm_scores['name'] == hm]) > 0 else 0
        
        # Combined score (weighted average)
        combined_score = (rec_score * 0.5 + hm_score * 0.5)
        
        # Get violations for this req
        req_violations = violations[violations['requisition_id'] == req_id]
        high_violations = len(req_violations[req_violations['severity'] == 'high'])
        
        # Calculate days open
        role_opened = pd.to_datetime(req_data['role_opened_date'])
        days_open = (datetime.now() - role_opened).days
        
        # Determine action items
        action_items = []
        if high_violations > 0:
            action_items.append(f"{high_violations} critical issue{'s' if high_violations > 1 else ''}")
        
        feedback_violations = req_violations[req_violations['metric'] == 'feedback_timeliness']
        if len(feedback_violations) > 0:
            action_items.append("Feedback overdue")
        
        velocity_violations = req_violations[req_violations['metric'] == 'stage_velocity']
        if len(velocity_violations[velocity_violations['severity'] == 'high']) > 0:
            action_items.append("Stage delay")
        
        requisitions.append({
            'req_id': req_id,
            'job_title': req_data['job_title'],
            'team': req_data['team'],
            'recruiter': recruiter,
            'rec_score': round(rec_score, 0),
            'hiring_manager': hm,
            'hm_score': round(hm_score, 0),
            'combined_score': round(combined_score, 0),
            'days_open': days_open,
            'status': req_data['current_status'],
            'action_items': ', '.join(action_items) if action_items else 'On track',
            'high_violations': high_violations
        })
    
    req_df = pd.DataFrame(requisitions)
    
    # Top metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    team_score = req_df['combined_score'].mean()
    
    with col1:
        score_color = "🟢" if team_score >= 70 else "🟡" if team_score >= 50 else "🔴"
        st.metric("Team Score", f"{score_color} {round(team_score, 0)}/100")
    
    with col2:
        st.metric("Open Roles", len(req_df))
    
    with col3:
        st.metric("Avg Recruiter Score", round(req_df['rec_score'].mean(), 0))
    
    with col4:
        st.metric("Avg Manager Score", round(req_df['hm_score'].mean(), 0))
    
    with col5:
        # Calculate avg feedback time from violations
        feedback_vios = violations[violations['metric'] == 'feedback_timeliness']
        if len(feedback_vios) > 0:
            avg_feedback_hrs = feedback_vios['delay_hours'].mean()
            st.metric("Avg Time to Feedback", f"{round(avg_feedback_hrs, 0)}hrs")
        else:
            st.metric("Avg Time to Feedback", "N/A")
    
    with col6:
        # Calculate avg stage time from violations
        velocity_vios = violations[violations['metric'] == 'stage_velocity']
        if len(velocity_vios) > 0:
            avg_stage_days = velocity_vios['days_in_stage'].mean()
            st.metric("Avg Stage Time", f"{round(avg_stage_days, 1)} days")
        else:
            st.metric("Avg Stage Time", "N/A")
    
    st.markdown("---")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        team_filter = st.multiselect(
            "Filter by Team",
            options=['All'] + sorted(req_df['team'].unique().tolist()),
            default=['All']
        )
    
    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            options=['All', 'Critical (Score < 50)', 'Needs Attention (50-70)', 'Good (70+)']
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            options=['Combined Score (Low to High)', 'Combined Score (High to Low)', 'Days Open', 'Critical Issues']
        )
    
    # Apply filters
    filtered_df = req_df.copy()
    
    if 'All' not in team_filter:
        filtered_df = filtered_df[filtered_df['team'].isin(team_filter)]
    
    if status_filter == 'Critical (Score < 50)':
        filtered_df = filtered_df[filtered_df['combined_score'] < 50]
    elif status_filter == 'Needs Attention (50-70)':
        filtered_df = filtered_df[(filtered_df['combined_score'] >= 50) & (filtered_df['combined_score'] < 70)]
    elif status_filter == 'Good (70+)':
        filtered_df = filtered_df[filtered_df['combined_score'] >= 70]
    
    # Apply sorting
    if sort_by == 'Combined Score (Low to High)':
        filtered_df = filtered_df.sort_values('combined_score', ascending=True)
    elif sort_by == 'Combined Score (High to Low)':
        filtered_df = filtered_df.sort_values('combined_score', ascending=False)
    elif sort_by == 'Days Open':
        filtered_df = filtered_df.sort_values('days_open', ascending=False)
    elif sort_by == 'Critical Issues':
        filtered_df = filtered_df.sort_values('high_violations', ascending=False)
    
    # Display table
    st.subheader(f"Open Roles ({len(filtered_df)} roles)")
    
    # Format the dataframe for display
    display_df = filtered_df[[
        'job_title', 'team', 'recruiter', 'rec_score', 
        'hiring_manager', 'hm_score', 'combined_score', 
        'days_open', 'action_items'
    ]].copy()
    
    display_df.columns = [
        'Role', 'Department', 'Recruiter', 'Rec. Score',
        'Hiring Manager', 'Mgr. Score', 'Combined Score',
        'Open Since (days)', 'Action Items'
    ]
    
    # Color code the scores
    def color_score(val):
        if isinstance(val, (int, float)):
            if val >= 70:
                return 'background-color: #d4edda; color: #155724; font-weight: bold'
            elif val >= 50:
                return 'background-color: #fff3cd; color: #856404; font-weight: bold'
            else:
                return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
        return ''
    
    styled_df = display_df.style.applymap(
        color_score,
        subset=['Rec. Score', 'Mgr. Score', 'Combined Score']
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Key insights
    st.markdown("---")
    st.subheader("Key Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔴 Roles Needing Immediate Attention")
        critical_roles = filtered_df[filtered_df['combined_score'] < 50].head(5)
        if len(critical_roles) > 0:
            for _, role in critical_roles.iterrows():
                st.error(f"**{role['job_title']}** ({role['team']}) - Score: {role['combined_score']} - {role['action_items']}")
        else:
            st.success("No critical roles!")
    
    with col2:
        st.markdown("#### ⭐ Best Performing Partnerships")
        top_roles = filtered_df[filtered_df['combined_score'] >= 70].head(5)
        if len(top_roles) > 0:
            for _, role in top_roles.iterrows():
                st.success(f"**{role['job_title']}** ({role['team']}) - Score: {role['combined_score']} - {role['recruiter']} + {role['hiring_manager']}")
        else:
            st.info("No roles scoring above 70 yet")

def render_org_dashboard(data):
    """Render organization-level scorecard"""
    st.header("🏢 Organization Scorecard")
    
    summary = data['org_summary']
    
    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Organization Score", 
            f"{summary['org_average_score']}/100",
            delta=None
        )
    
    with col2:
        st.metric(
            "Recruiter Average",
            f"{summary['recruiter_average']}/100"
        )
    
    with col3:
        st.metric(
            "Hiring Manager Average",
            f"{summary['hm_average']}/100"
        )
    
    with col4:
        st.metric(
            "High Severity Issues",
            summary['high_severity_total'],
            delta=None,
            delta_color="inverse"
        )
    
    st.markdown("---")
    
    # Team distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recruiter Performance Distribution")
        recruiter_df = data['recruiter_scores'].sort_values('final_score', ascending=True)
        
        fig = go.Figure(go.Bar(
            x=recruiter_df['final_score'],
            y=recruiter_df['name'],
            orientation='h',
            marker=dict(
                color=recruiter_df['final_score'],
                colorscale='RdYlGn',
                cmin=0,
                cmax=100
            ),
            text=recruiter_df['final_score'],
            textposition='auto',
        ))
        fig.update_layout(
            xaxis_title="Score",
            yaxis_title="",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Hiring Manager Performance Distribution")
        hm_df = data['hm_scores'].sort_values('final_score', ascending=True)
        
        fig = go.Figure(go.Bar(
            x=hm_df['final_score'],
            y=hm_df['name'],
            orientation='h',
            marker=dict(
                color=hm_df['final_score'],
                colorscale='RdYlGn',
                cmin=0,
                cmax=100
            ),
            text=hm_df['final_score'],
            textposition='auto',
        ))
        fig.update_layout(
            xaxis_title="Score",
            yaxis_title="",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Violation breakdown
    st.subheader("Violation Breakdown by Severity")
    
    severity_data = data['violations'].groupby(['severity', 'metric']).size().reset_index(name='count')
    
    fig = px.bar(
        severity_data,
        x='metric',
        y='count',
        color='severity',
        barmode='group',
        color_discrete_map={
            'low': '#90EE90',
            'medium': '#FFD700',
            'high': '#FF6B6B'
        },
        labels={
            'metric': 'Metric',
            'count': 'Number of Violations',
            'severity': 'Severity'
        }
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def render_recruiter_cards(data):
    """Render individual recruiter performance cards"""
    st.header("👥 Recruiter Performance Cards")
    
    recruiter_scores = data['recruiter_scores'].sort_values('final_score', ascending=False)
    violations = data['violations']
    
    # Filter selector
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_recruiter = st.selectbox(
            "Select Recruiter",
            options=recruiter_scores['name'].tolist(),
            index=0
        )
    
    with col2:
        st.write("")  # Spacing
    
    # Get recruiter data
    recruiter_data = recruiter_scores[recruiter_scores['name'] == selected_recruiter].iloc[0]
    recruiter_violations = violations[violations['recruiter_name'] == selected_recruiter]
    
    # Display card
    st.markdown("---")
    
    # Score overview
    col1, col2, col3, col4 = st.columns(4)
    
    score = recruiter_data['final_score']
    score_class = get_score_color(score)
    
    with col1:
        st.markdown(f"### Overall Score")
        st.markdown(f'<p class="{score_class}">{score}/100</p>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Total Violations")
        st.markdown(f"**{recruiter_data['total_violations']}**")
        st.caption(f"🔴 {recruiter_data['high_severity']} High")
    
    with col3:
        st.markdown("### Feedback Score")
        st.markdown(f"**{recruiter_data['feedback_score']}/100**")
        st.caption("40% weight")
    
    with col4:
        st.markdown("### Velocity Score")
        st.markdown(f"**{recruiter_data['velocity_score']}/100**")
        st.caption("35% weight")
    
    # Metric breakdown
    st.markdown("---")
    st.subheader("Performance Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Metric Scores")
        
        metrics_data = pd.DataFrame({
            'Metric': ['Interview Feedback', 'Stage Velocity', 'HM Engagement'],
            'Score': [
                recruiter_data['feedback_score'],
                recruiter_data['velocity_score'],
                recruiter_data['engagement_score']
            ],
            'Weight': ['40%', '35%', '25%']
        })
        
        fig = go.Figure(go.Bar(
            x=metrics_data['Metric'],
            y=metrics_data['Score'],
            marker=dict(
                color=metrics_data['Score'],
                colorscale='RdYlGn',
                cmin=0,
                cmax=100
            ),
            text=metrics_data['Score'],
            textposition='auto',
        ))
        fig.update_layout(
            yaxis_title="Score",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Violations by Severity")
        
        severity_data = recruiter_violations['severity'].value_counts().reset_index()
        severity_data.columns = ['Severity', 'Count']
        
        fig = px.pie(
            severity_data,
            values='Count',
            names='Severity',
            color='Severity',
            color_discrete_map={
                'low': '#90EE90',
                'medium': '#FFD700',
                'high': '#FF6B6B'
            },
            hole=0.4
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed violations
    st.markdown("---")
    st.subheader("Recent Violations")
    
    # Show top violations
    display_violations = recruiter_violations[
        ['requisition_id', 'metric', 'severity', 'penalty', 'stage']
    ].sort_values('penalty', ascending=True).head(10)
    
    display_violations['metric'] = display_violations['metric'].replace({
        'feedback_timeliness': 'Feedback Timeliness',
        'stage_velocity': 'Stage Velocity',
        'hm_engagement': 'HM Engagement'
    })
    
    st.dataframe(
        display_violations,
        use_container_width=True,
        hide_index=True,
        column_config={
            'requisition_id': 'Requisition',
            'metric': 'Metric',
            'severity': st.column_config.Column('Severity', width='small'),
            'penalty': st.column_config.Column('Penalty Points', width='small'),
            'stage': 'Stage'
        }
    )

def render_hm_cards(data):
    """Render individual hiring manager performance cards"""
    st.header("🎯 Hiring Manager Performance Cards")
    
    hm_scores = data['hm_scores'].sort_values('final_score', ascending=False)
    violations = data['violations']
    
    # Filter selector
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_hm = st.selectbox(
            "Select Hiring Manager",
            options=hm_scores['name'].tolist(),
            index=0
        )
    
    with col2:
        st.write("")  # Spacing
    
    # Get HM data
    hm_data = hm_scores[hm_scores['name'] == selected_hm].iloc[0]
    hm_violations = violations[violations['hiring_manager_name'] == selected_hm]
    
    # Display card
    st.markdown("---")
    
    # Score overview
    col1, col2, col3, col4 = st.columns(4)
    
    score = hm_data['final_score']
    score_class = get_score_color(score)
    
    with col1:
        st.markdown(f"### Overall Score")
        st.markdown(f'<p class="{score_class}">{score}/100</p>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Total Violations")
        st.markdown(f"**{hm_data['total_violations']}**")
        st.caption(f"🔴 {hm_data['high_severity']} High")
    
    with col3:
        st.markdown("### Feedback Score")
        st.markdown(f"**{hm_data['feedback_score']}/100**")
        st.caption("40% weight")
    
    with col4:
        st.markdown("### Engagement Score")
        st.markdown(f"**{hm_data['engagement_score']}/100**")
        st.caption("25% weight")
    
    # Metric breakdown
    st.markdown("---")
    st.subheader("Performance Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Metric Scores")
        
        metrics_data = pd.DataFrame({
            'Metric': ['Interview Feedback', 'Stage Velocity', 'HM Engagement'],
            'Score': [
                hm_data['feedback_score'],
                hm_data['velocity_score'],
                hm_data['engagement_score']
            ],
            'Weight': ['40%', '35%', '25%']
        })
        
        fig = go.Figure(go.Bar(
            x=metrics_data['Metric'],
            y=metrics_data['Score'],
            marker=dict(
                color=metrics_data['Score'],
                colorscale='RdYlGn',
                cmin=0,
                cmax=100
            ),
            text=metrics_data['Score'],
            textposition='auto',
        ))
        fig.update_layout(
            yaxis_title="Score",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Violations by Severity")
        
        severity_data = hm_violations['severity'].value_counts().reset_index()
        severity_data.columns = ['Severity', 'Count']
        
        fig = px.pie(
            severity_data,
            values='Count',
            names='Severity',
            color='Severity',
            color_discrete_map={
                'low': '#90EE90',
                'medium': '#FFD700',
                'high': '#FF6B6B'
            },
            hole=0.4
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Engagement metrics specific to HMs
    st.markdown("---")
    st.subheader("Engagement Metrics")
    
    engagement_violations = hm_violations[hm_violations['metric'] == 'hm_engagement']
    
    if len(engagement_violations) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            missing_feedback = engagement_violations['missing_feedback_count'].sum()
            st.metric("Missing Interview Feedback", int(missing_feedback))
        
        with col2:
            delayed_feedback = engagement_violations['delayed_feedback_count'].sum()
            st.metric("Delayed Feedback (>72hrs)", int(delayed_feedback))
    else:
        st.success("✅ Excellent engagement - no violations!")
    
    # Detailed violations
    st.markdown("---")
    st.subheader("Recent Violations")
    
    display_violations = hm_violations[
        ['requisition_id', 'metric', 'severity', 'penalty', 'stage']
    ].sort_values('penalty', ascending=True).head(10)
    
    display_violations['metric'] = display_violations['metric'].replace({
        'feedback_timeliness': 'Feedback Timeliness',
        'stage_velocity': 'Stage Velocity',
        'hm_engagement': 'HM Engagement'
    })
    
    st.dataframe(
        display_violations,
        use_container_width=True,
        hide_index=True,
        column_config={
            'requisition_id': 'Requisition',
            'metric': 'Metric',
            'severity': st.column_config.Column('Severity', width='small'),
            'penalty': st.column_config.Column('Penalty Points', width='small'),
            'stage': 'Stage'
        }
    )

# Main app
def main():
    # Title
    st.title("📊 Recruiter Scorecard Dashboard")
    st.caption("Performance tracking based on SLA violations across key hiring metrics")
    
    # Load data
    data = load_data()
    
    if data is None:
        st.error("Please generate sample data first by running: `python generate_sample_data.py`")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["Open Roles Dashboard", "Trends & Progress (Leadership)", "Organization Overview", "Recruiter Cards", "Hiring Manager Cards"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Data Summary")
    st.sidebar.metric("Total Recruiters", len(data['recruiter_scores']))
    st.sidebar.metric("Total Hiring Managers", len(data['hm_scores']))
    st.sidebar.metric("Total Violations", len(data['violations']))
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About This Demo")
    st.sidebar.info("""
    This dashboard tracks recruiter and hiring manager performance across three key metrics:
    
    1. **Interview Feedback Timeliness** (40%)
    2. **Stage Progression Velocity** (35%)
    3. **Hiring Manager Engagement** (25%)
    
    Scores start at 100 and decrease based on SLA violations.
    """)
    
    # Render selected page
    if page == "Open Roles Dashboard":
        render_open_roles_dashboard(data)
    elif page == "Trends & Progress (Leadership)":
        render_trends_dashboard()
    elif page == "Organization Overview":
        render_org_dashboard(data)
    elif page == "Recruiter Cards":
        render_recruiter_cards(data)
    elif page == "Hiring Manager Cards":
        render_hm_cards(data)

if __name__ == "__main__":
    main()
