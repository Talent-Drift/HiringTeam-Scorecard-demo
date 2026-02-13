"""
Recruiter Scorecard Scoring Engine
Implements the three-metric scoring system with severity-based penalties
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ScorecardEngine:
    """
    Scoring engine for recruiter and hiring manager performance
    
    Metrics:
    1. Interview Feedback Timeliness (40%)
    2. Stage Progression Velocity (35%)
    3. Hiring Manager Engagement (25%)
    """
    
    # Metric weights
    WEIGHTS = {
        'feedback_timeliness': 0.40,
        'stage_velocity': 0.35,
        'hm_engagement': 0.25
    }
    
    # Severity penalties
    PENALTIES = {
        'low': -3,
        'medium': -10,
        'high': -25
    }
    
    def __init__(self, df):
        """Initialize with ATS export dataframe"""
        self.df = df.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        """Parse dates and prepare data for scoring"""
        date_columns = ['stage_entered_date', 'interview_completed_date', 'feedback_submitted_date']
        
        for col in date_columns:
            self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
        
        self.df['role_opened_date'] = pd.to_datetime(self.df['role_opened_date'])
    
    def calculate_feedback_timeliness(self):
        """
        Metric 1: Interview Feedback Timeliness
        Measures delay between interview completion and feedback submission
        
        Severity:
        - Low: ≤ 48 hours (-3 points)
        - Medium: 48-72 hours (-10 points)
        - High: > 72 hours (-25 points)
        """
        violations = []
        
        # Only score rows with both interview and feedback dates
        scored_interviews = self.df[
            (self.df['interview_completed_date'].notna()) & 
            (self.df['feedback_submitted_date'].notna())
        ].copy()
        
        scored_interviews['feedback_delay_hours'] = (
            scored_interviews['feedback_submitted_date'] - 
            scored_interviews['interview_completed_date']
        ).dt.total_seconds() / 3600
        
        for _, row in scored_interviews.iterrows():
            delay_hours = row['feedback_delay_hours']
            
            if delay_hours <= 48:
                severity = 'low'
                penalty = self.PENALTIES['low']
            elif delay_hours <= 72:
                severity = 'medium'
                penalty = self.PENALTIES['medium']
            else:
                severity = 'high'
                penalty = self.PENALTIES['high']
            
            violations.append({
                'requisition_id': row['requisition_id'],
                'stage': row['stage'],
                'metric': 'feedback_timeliness',
                'severity': severity,
                'penalty': penalty,
                'delay_hours': delay_hours,
                'recruiter_name': row['recruiter_name'],
                'hiring_manager_name': row['hiring_manager_name'],
                'is_hm_interview': row['is_hiring_manager_interview'],
                'responsible_party': row['hiring_manager_name'] if row['is_hiring_manager_interview'] else row['recruiter_name']
            })
        
        # Also penalize missing feedback
        missing_feedback = self.df[
            (self.df['interview_completed_date'].notna()) & 
            (self.df['feedback_submitted_date'].isna())
        ].copy()
        
        for _, row in missing_feedback.iterrows():
            violations.append({
                'requisition_id': row['requisition_id'],
                'stage': row['stage'],
                'metric': 'feedback_timeliness',
                'severity': 'high',
                'penalty': self.PENALTIES['high'],
                'delay_hours': 999,  # Marker for missing
                'recruiter_name': row['recruiter_name'],
                'hiring_manager_name': row['hiring_manager_name'],
                'is_hm_interview': row['is_hiring_manager_interview'],
                'responsible_party': row['hiring_manager_name'] if row['is_hiring_manager_interview'] else row['recruiter_name']
            })
        
        return pd.DataFrame(violations)
    
    def calculate_stage_velocity(self):
        """
        Metric 2: Stage Progression Velocity
        Measures time a candidate remains in the same stage
        
        Severity:
        - Low: ≤ 7 days (-3 points)
        - Medium: 7-14 days (-10 points)
        - High: > 14 days (-25 points)
        """
        violations = []
        
        # Get stage durations by looking at stage transitions
        stage_order = ['New', 'Phone Screen', 'Technical Interview', 'Final Interview', 'Offer', 'Hired']
        
        for req_id in self.df['requisition_id'].unique():
            req_data = self.df[self.df['requisition_id'] == req_id].sort_values('stage_entered_date')
            
            recruiter = req_data['recruiter_name'].iloc[0]
            hm = req_data['hiring_manager_name'].iloc[0]
            
            stages = req_data['stage'].unique()
            
            for i, stage in enumerate(stages[:-1]):  # Skip last stage (no transition)
                stage_data = req_data[req_data['stage'] == stage]
                if len(stage_data) == 0:
                    continue
                
                stage_entered = stage_data['stage_entered_date'].iloc[0]
                
                # Find next stage
                next_stages = req_data[req_data['stage_entered_date'] > stage_entered]
                if len(next_stages) > 0:
                    next_stage_entered = next_stages['stage_entered_date'].iloc[0]
                    days_in_stage = (next_stage_entered - stage_entered).days
                    
                    if days_in_stage <= 7:
                        severity = 'low'
                        penalty = self.PENALTIES['low']
                    elif days_in_stage <= 14:
                        severity = 'medium'
                        penalty = self.PENALTIES['medium']
                    else:
                        severity = 'high'
                        penalty = self.PENALTIES['high']
                    
                    violations.append({
                        'requisition_id': req_id,
                        'stage': stage,
                        'metric': 'stage_velocity',
                        'severity': severity,
                        'penalty': penalty,
                        'days_in_stage': days_in_stage,
                        'recruiter_name': recruiter,
                        'hiring_manager_name': hm,
                        'responsible_party': recruiter  # Primary ownership with recruiter
                    })
        
        return pd.DataFrame(violations)
    
    def calculate_hm_engagement(self):
        """
        Metric 3: Hiring Manager Engagement
        Measures responsiveness and participation
        
        Signals:
        - Missing interview feedback (high severity)
        - Delayed feedback > 72 hours (medium severity)
        - Multiple violations (compounds)
        """
        violations = []
        
        # Count engagement issues per HM per requisition
        for req_id in self.df['requisition_id'].unique():
            req_data = self.df[self.df['requisition_id'] == req_id]
            hm = req_data['hiring_manager_name'].iloc[0]
            recruiter = req_data['recruiter_name'].iloc[0]
            
            hm_interviews = req_data[req_data['is_hiring_manager_interview'] == True]
            
            if len(hm_interviews) == 0:
                continue
            
            # Count issues
            missing_feedback = len(hm_interviews[
                (hm_interviews['interview_completed_date'].notna()) & 
                (hm_interviews['feedback_submitted_date'].isna())
            ])
            
            delayed_feedback = 0
            for _, interview in hm_interviews.iterrows():
                if pd.notna(interview['interview_completed_date']) and pd.notna(interview['feedback_submitted_date']):
                    delay_hours = (interview['feedback_submitted_date'] - interview['interview_completed_date']).total_seconds() / 3600
                    if delay_hours > 72:
                        delayed_feedback += 1
            
            total_issues = missing_feedback + delayed_feedback
            
            if total_issues == 0:
                # Excellent engagement - no penalty but track it
                severity = 'low'
                penalty = 0
            elif total_issues <= 2:
                severity = 'medium'
                penalty = self.PENALTIES['medium']
            else:
                severity = 'high'
                penalty = self.PENALTIES['high'] * min(total_issues, 3)  # Cap at 3x
            
            if total_issues > 0:
                violations.append({
                    'requisition_id': req_id,
                    'stage': 'Overall',
                    'metric': 'hm_engagement',
                    'severity': severity,
                    'penalty': penalty,
                    'missing_feedback_count': missing_feedback,
                    'delayed_feedback_count': delayed_feedback,
                    'recruiter_name': recruiter,
                    'hiring_manager_name': hm,
                    'responsible_party': hm
                })
        
        return pd.DataFrame(violations)
    
    def calculate_scores(self):
        """Calculate all violations and compute scores"""
        
        # Calculate all violations
        feedback_violations = self.calculate_feedback_timeliness()
        velocity_violations = self.calculate_stage_velocity()
        engagement_violations = self.calculate_hm_engagement()
        
        # Combine all violations
        all_violations = pd.concat([
            feedback_violations,
            velocity_violations,
            engagement_violations
        ], ignore_index=True)
        
        return all_violations
    
    def score_by_recruiter(self, violations_df):
        """Calculate recruiter scores"""
        scores = []
        
        for recruiter in self.df['recruiter_name'].unique():
            recruiter_violations = violations_df[
                (violations_df['recruiter_name'] == recruiter)
            ]
            
            # Calculate metric-specific penalties
            feedback_penalty = recruiter_violations[
                (recruiter_violations['metric'] == 'feedback_timeliness') &
                (recruiter_violations['responsible_party'] == recruiter)
            ]['penalty'].sum()
            
            velocity_penalty = recruiter_violations[
                recruiter_violations['metric'] == 'stage_velocity'
            ]['penalty'].sum()
            
            # Recruiters also affected by HM engagement issues (partial responsibility)
            engagement_penalty = 0  # Recruiters not directly penalized for HM engagement
            
            # Calculate weighted score (start at 100)
            base_score = 100
            
            feedback_score = max(0, base_score + feedback_penalty)
            velocity_score = max(0, base_score + velocity_penalty)
            engagement_score = base_score  # Full points for recruiters on this metric
            
            final_score = (
                feedback_score * self.WEIGHTS['feedback_timeliness'] +
                velocity_score * self.WEIGHTS['stage_velocity'] +
                engagement_score * self.WEIGHTS['hm_engagement']
            )
            
            # Count violations by severity
            severity_counts = recruiter_violations['severity'].value_counts().to_dict()
            
            scores.append({
                'name': recruiter,
                'role_type': 'Recruiter',
                'final_score': round(final_score, 1),
                'feedback_score': round(feedback_score, 1),
                'velocity_score': round(velocity_score, 1),
                'engagement_score': round(engagement_score, 1),
                'total_violations': len(recruiter_violations),
                'high_severity': severity_counts.get('high', 0),
                'medium_severity': severity_counts.get('medium', 0),
                'low_severity': severity_counts.get('low', 0)
            })
        
        return pd.DataFrame(scores)
    
    def score_by_hiring_manager(self, violations_df):
        """Calculate hiring manager scores"""
        scores = []
        
        for hm in self.df['hiring_manager_name'].unique():
            hm_violations = violations_df[
                (violations_df['hiring_manager_name'] == hm)
            ]
            
            # Calculate metric-specific penalties
            feedback_penalty = hm_violations[
                (hm_violations['metric'] == 'feedback_timeliness') &
                (hm_violations['responsible_party'] == hm)
            ]['penalty'].sum()
            
            # HMs share some responsibility for velocity
            velocity_penalty = hm_violations[
                hm_violations['metric'] == 'stage_velocity'
            ]['penalty'].sum() * 0.5  # 50% responsibility
            
            engagement_penalty = hm_violations[
                hm_violations['metric'] == 'hm_engagement'
            ]['penalty'].sum()
            
            # Calculate weighted score
            base_score = 100
            
            feedback_score = max(0, base_score + feedback_penalty)
            velocity_score = max(0, base_score + velocity_penalty)
            engagement_score = max(0, base_score + engagement_penalty)
            
            final_score = (
                feedback_score * self.WEIGHTS['feedback_timeliness'] +
                velocity_score * self.WEIGHTS['stage_velocity'] +
                engagement_score * self.WEIGHTS['hm_engagement']
            )
            
            # Count violations by severity
            severity_counts = hm_violations['severity'].value_counts().to_dict()
            
            scores.append({
                'name': hm,
                'role_type': 'Hiring Manager',
                'final_score': round(final_score, 1),
                'feedback_score': round(feedback_score, 1),
                'velocity_score': round(velocity_score, 1),
                'engagement_score': round(engagement_score, 1),
                'total_violations': len(hm_violations),
                'high_severity': severity_counts.get('high', 0),
                'medium_severity': severity_counts.get('medium', 0),
                'low_severity': severity_counts.get('low', 0)
            })
        
        return pd.DataFrame(scores)
    
    def get_org_summary(self, recruiter_scores, hm_scores):
        """Calculate organization-level summary"""
        all_scores = pd.concat([recruiter_scores, hm_scores])
        
        summary = {
            'org_average_score': round(all_scores['final_score'].mean(), 1),
            'recruiter_average': round(recruiter_scores['final_score'].mean(), 1),
            'hm_average': round(hm_scores['final_score'].mean(), 1),
            'total_violations': int(all_scores['total_violations'].sum()),
            'high_severity_total': int(all_scores['high_severity'].sum()),
            'people_count': len(all_scores)
        }
        
        return summary

if __name__ == "__main__":
    # Test the scoring engine
    df = pd.read_csv('sample_ats_export.csv')
    
    print("Initializing scoring engine...")
    engine = ScorecardEngine(df)
    
    print("Calculating violations...")
    violations = engine.calculate_scores()
    
    print(f"✓ Found {len(violations)} total violations")
    print(f"\nViolation Breakdown:")
    print(violations.groupby(['metric', 'severity']).size())
    
    print("\n" + "="*60)
    print("Calculating Recruiter Scores...")
    recruiter_scores = engine.score_by_recruiter(violations)
    print(recruiter_scores.sort_values('final_score', ascending=False))
    
    print("\n" + "="*60)
    print("Calculating Hiring Manager Scores...")
    hm_scores = engine.score_by_hiring_manager(violations)
    print(hm_scores.sort_values('final_score', ascending=False))
    
    print("\n" + "="*60)
    print("Organization Summary:")
    summary = engine.get_org_summary(recruiter_scores, hm_scores)
    for key, value in summary.items():
        print(f"  {key}: {value}")
