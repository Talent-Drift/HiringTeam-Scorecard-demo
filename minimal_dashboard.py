"""
Simple Recruiter Scorecard Dashboard - With Issue Flags
"""

import streamlit as st
import pandas as pd
import random

# Page config
st.set_page_config(page_title="Recruiter Scorecard", page_icon="📊", layout="wide")

# Simple scoring function
def calculate_score(violations):
    """Start at 100, subtract penalties"""
    return max(0, 100 - (violations * 5))

# Generate flags for each person's issues
def generate_flags(person_data, num_issues):
    """Generate top 3 issue flags with severity"""
    flags = []
    
    # Sample flag types
    flag_types = [
        ("Feedback delayed >72hrs", "🔴"),
        ("Stage stuck >7 days", "🔴"),
        ("Missing interview feedback", "🟡"),
        ("Slow candidate response", "🟡"),
        ("Scheduling conflicts", "🟢"),
        ("Profile incomplete", "🟢"),
    ]
    
    # Get top 3 (or however many issues exist)
    for i in range(min(3, num_issues)):
        flag = random.choice(flag_types)
        candidate = person_data['candidate_id'].iloc[min(i, len(person_data)-1)]
        flags.append({
            'severity': flag[1],
            'issue': flag[0],
            'candidate': candidate
        })
    
    # Sort by severity (red first, then yellow, then green)
    severity_order = {'🔴': 0, '🟡': 1, '🟢': 2}
    flags.sort(key=lambda x: severity_order[x['severity']])
    
    return flags

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('sample_ats_export.csv')
        
        # Calculate simple violation count per person
        recruiter_violations = df.groupby('recruiter_name').size().reset_index(name='violations')
        recruiter_violations['score'] = recruiter_violations['violations'].apply(calculate_score)
        
        hm_violations = df.groupby('hiring_manager_name').size().reset_index(name='violations')
        hm_violations['score'] = hm_violations['violations'].apply(calculate_score)
        
        return df, recruiter_violations, hm_violations
    except FileNotFoundError:
        st.error("❌ Please upload sample_ats_export.csv")
        return None, None, None

# Main app
def main():
    st.title("📊 Recruiter Scorecard")
    st.caption("Simple performance tracking dashboard")
    
    df, recruiters, hms = load_data()
    
    if df is None:
        return
    
    # Navigation
    page = st.sidebar.radio("View", ["Overview", "Recruiters", "Hiring Managers"])
    
    if page == "Overview":
        st.header("📈 Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Recruiter Score", f"{recruiters['score'].mean():.0f}/100")
        
        with col2:
            st.metric("Avg Manager Score", f"{hms['score'].mean():.0f}/100")
        
        with col3:
            st.metric("Total Candidates", len(df))
        
        st.markdown("---")
        
        # Simple bar charts using streamlit's built-in
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Recruiter Scores")
            chart_data = recruiters.set_index('recruiter_name')['score'].sort_values()
            st.bar_chart(chart_data)
        
        with col2:
            st.subheader("Hiring Manager Scores")
            chart_data = hms.set_index('hiring_manager_name')['score'].sort_values()
            st.bar_chart(chart_data)
    
    elif page == "Recruiters":
        st.header("👥 Recruiters")
        
        # Show table with clickable issues
        for idx, row in recruiters.sort_values('score', ascending=False).iterrows():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{row['recruiter_name']}**")
            
            with col2:
                # Make issues clickable
                if st.button(f"🚩 {row['violations']} issues", key=f"rec_{idx}"):
                    st.session_state[f"show_rec_{idx}"] = not st.session_state.get(f"show_rec_{idx}", False)
            
            with col3:
                score_color = "🟢" if row['score'] >= 70 else "🟡" if row['score'] >= 50 else "🔴"
                st.write(f"{score_color} {row['score']:.0f}/100")
            
            with col4:
                if st.button("Details", key=f"det_rec_{idx}"):
                    st.session_state['selected_recruiter'] = row['recruiter_name']
            
            # Show popup with top 3 flags if clicked
            if st.session_state.get(f"show_rec_{idx}", False):
                person_data = df[df['recruiter_name'] == row['recruiter_name']]
                flags = generate_flags(person_data, row['violations'])
                
                with st.expander("⚠️ Top Issues", expanded=True):
                    for i, flag in enumerate(flags, 1):
                        st.markdown(f"{flag['severity']} **{flag['issue']}** - Candidate: `{flag['candidate']}`")
            
            st.markdown("---")
        
        # Detail view if selected
        if 'selected_recruiter' in st.session_state:
            st.markdown("---")
            selected = st.session_state['selected_recruiter']
            st.subheader(f"Details: {selected}")
            
            recruiter_data = df[df['recruiter_name'] == selected]
            score = recruiters[recruiters['recruiter_name'] == selected]['score'].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Score", f"{score:.0f}/100")
            
            with col2:
                st.metric("Candidates", len(recruiter_data))
            
            with col3:
                st.metric("Roles", recruiter_data['requisition_id'].nunique())
            
            st.subheader("Recent Candidates")
            st.dataframe(
                recruiter_data[['candidate_id', 'job_title', 'current_stage', 'team']].head(10),
                use_container_width=True,
                hide_index=True
            )
    
    else:  # Hiring Managers
        st.header("🎯 Hiring Managers")
        
        # Show table with clickable issues
        for idx, row in hms.sort_values('score', ascending=False).iterrows():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{row['hiring_manager_name']}**")
            
            with col2:
                # Make issues clickable
                if st.button(f"🚩 {row['violations']} issues", key=f"hm_{idx}"):
                    st.session_state[f"show_hm_{idx}"] = not st.session_state.get(f"show_hm_{idx}", False)
            
            with col3:
                score_color = "🟢" if row['score'] >= 70 else "🟡" if row['score'] >= 50 else "🔴"
                st.write(f"{score_color} {row['score']:.0f}/100")
            
            with col4:
                if st.button("Details", key=f"det_hm_{idx}"):
                    st.session_state['selected_hm'] = row['hiring_manager_name']
            
            # Show popup with top 3 flags if clicked
            if st.session_state.get(f"show_hm_{idx}", False):
                person_data = df[df['hiring_manager_name'] == row['hiring_manager_name']]
                flags = generate_flags(person_data, row['violations'])
                
                with st.expander("⚠️ Top Issues", expanded=True):
                    for i, flag in enumerate(flags, 1):
                        st.markdown(f"{flag['severity']} **{flag['issue']}** - Candidate: `{flag['candidate']}`")
            
            st.markdown("---")
        
        # Detail view if selected
        if 'selected_hm' in st.session_state:
            st.markdown("---")
            selected = st.session_state['selected_hm']
            st.subheader(f"Details: {selected}")
            
            hm_data = df[df['hiring_manager_name'] == selected]
            score = hms[hms['hiring_manager_name'] == selected]['score'].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Score", f"{score:.0f}/100")
            
            with col2:
                st.metric("Candidates", len(hm_data))
            
            with col3:
                st.metric("Roles", hm_data['requisition_id'].nunique())
            
            st.subheader("Recent Candidates")
            st.dataframe(
                hm_data[['candidate_id', 'job_title', 'current_stage', 'team']].head(10),
                use_container_width=True,
                hide_index=True
            )

if __name__ == "__main__":
    main()
