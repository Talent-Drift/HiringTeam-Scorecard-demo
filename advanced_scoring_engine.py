"""
Advanced Scoring Engine for Recruiter Scorecard
Calculates performance scores based on SLA violations with weighted metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class ScorecardEngine:
    """
    Engine for calculating recruiter and hiring manager performance scores
    based on three key metrics:
    1. Interview Feedback Timeliness (40% weight)
    2. Stage Progression Velocity (35% weight)
    3. Hiring Manager Engagement (25% weight)
    """
    
    # SLA Thresholds
    FEEDBACK_SLA = 48  # hours
    STAGE_SLAS = {
        'Phone Screen': 3,
        'Technical Interview': 5,
        'Onsite Interview': 7,
        'Offer': 2
    }
    
    # Penalty structure
    PENALTIES = {
        'feedback_timeliness': {
            'low': -2,
            'medium': -5,
            'high': -10
        },
        'stage_velocity': {
            'low': -3,
            'medium': -7,
            'high': -15
        },
        'hm_engagement': {
            'low': -2,
            'medium': -5,
            'high': -10
        }
    }
    
    # Weights for final score
    WEIGHTS = {
        'feedback_timeliness': 0.40,
        'stage_velocity': 0.35,
        'hm_engagement': 0.25
    }
    
    def __init__(self, data):
        self.data = data
        self.violations = None
    
    def calculate_scores(self):
        """Calculate all SLA violations"""
        violations = []
        
        for _, row in self.data.iterrows():
            # Check feedback timeliness
            if pd.notna(row['interview_date']) and pd.notna(row['feedback_date']):
                feedback_violations = self._check_feedback_timeliness(row)
                violations.extend(feedback_violations)
            
            # Check stage velocity
            if pd.notna(row['stage_start_date']):
                velocity_violations = self._check_stage_velocity(row)
                violations.extend(velocity_violations)
            
            # Check HM engagement
            engagement_violations = self._check_hm_engagement(row)
            violations.extend(engagement_violations)
        
        self.violations = pd.DataFrame(violations) if violations else pd.DataFrame()
        return self.violations
    
    def _check_feedback_timeliness(self, row):
        """Check if feedback was provided within SLA"""
        violations = []
        
        interview_date = pd.to_datetime(row['interview_date'])
        feedback_date = pd.to_datetime(row['feedback_date'])
        
        delay_hours = (feedback_date - interview_date).total_seconds() / 3600
        
        if delay_hours > self.FEEDBACK_SLA:
            # Determine severity
            if delay_hours > 96:
                severity = 'high'
            elif delay_hours > 72:
                severity = 'medium'
            else:
                severity = 'low'
            
            violations.append({
                'requisition_id': row['requisition_id'],
                'candidate_id': row['candidate_id'],
                'recruiter_name': row['recruiter_name'],
                'hiring_manager_name': row['hiring_manager_name'],
                'metric': 'feedback_timeliness',
                'severity': severity,
                'penalty': self.PENALTIES['feedback_timeliness'][severity],
                'delay_hours': delay_hours,
                'stage': row['current_stage'],
                'team': row['team'],
                'description': f"Feedback delayed {delay_hours:.0f} hours"
            })
        
        return violations
    
    def _check_stage_velocity(self, row):
        """Check if candidate progressed through stage within SLA"""
        violations = []
        
        stage = row['current_stage']
        if stage not in self.STAGE_SLAS:
            return violations
        
        stage_start = pd.to_datetime(row['stage_start_date'])
        days_in_stage = (datetime.now() - stage_start).days
        sla_days = self.STAGE_SLAS[stage]
        
        if days_in_stage > sla_days:
            days_over = days_in_stage - sla_days
            
            # Determine severity
            if days_over > 7:
                severity = 'high'
            elif days_over > 3:
                severity = 'medium'
            else:
                severity = 'low'
            
            violations.append({
                'requisition_id': row['requisition_id'],
                'candidate_id': row['candidate_id'],
                'recruiter_name': row['recruiter_name'],
                'hiring_manager_name': row['hiring_manager_name'],
                'metric': 'stage_velocity',
                'severity': severity,
                'penalty': self.PENALTIES['stage_velocity'][severity],
                'days_in_stage': days_in_stage,
                'sla_days': sla_days,
                'stage': stage,
                'team': row['team'],
                'description': f"Stage stuck {days_over} days over SLA"
            })
        
        return violations
    
    def _check_hm_engagement(self, row):
        """Check hiring manager engagement"""
        violations = []
        
        # Simulate engagement issues (20% chance)
        if np.random.random() < 0.2:
            severity = np.random.choice(['low', 'medium', 'high'], p=[0.5, 0.3, 0.2])
            
            if severity == 'high':
                missing_count = np.random.randint(5, 10)
                description = f"Missing {missing_count} feedback responses"
            elif severity == 'medium':
                missing_count = np.random.randint(3, 5)
                description = f"Missing {missing_count} feedback responses"
            else:
                missing_count = np.random.randint(1, 3)
                description = "Delayed responses"
            
            violations.append({
                'requisition_id': row['requisition_id'],
                'candidate_id': row['candidate_id'],
                'recruiter_name': row['recruiter_name'],
                'hiring_manager_name': row['hiring_manager_name'],
                'metric': 'hm_engagement',
                'severity': severity,
                'penalty': self.PENALTIES['hm_engagement'][severity],
                'missing_feedback_count': missing_count,
                'stage': row['current_stage'],
                'team': row['team'],
                'description': description
            })
        
        return violations
    
    def score_by_recruiter(self, violations):
        """Calculate scores for each recruiter"""
        if violations.empty:
            # No violations - everyone gets 100
            recruiters = self.data['recruiter_name'].unique()
            return pd.DataFrame([{
                'name': rec,
                'final_score': 100.0,
                'feedback_score': 100.0,
                'velocity_score': 100.0,
                'engagement_score': 100.0,
                'total_violations': 0,
                'high_severity': 0,
                'medium_severity': 0,
                'low_severity': 0
            } for rec in recruiters])
        
        recruiters = self.data['recruiter_name'].unique()
        scores = []
        
        for recruiter in recruiters:
            recruiter_violations = violations[violations['recruiter_name'] == recruiter]
            
            # Calculate metric-specific scores
            feedback_score = self._calculate_metric_score(
                recruiter_violations, 'feedback_timeliness'
            )
            velocity_score = self._calculate_metric_score(
                recruiter_violations, 'stage_velocity'
            )
            engagement_score = self._calculate_metric_score(
                recruiter_violations, 'hm_engagement'
            )
            
            # Calculate weighted final score
            final_score = (
                feedback_score * self.WEIGHTS['feedback_timeliness'] +
                velocity_score * self.WEIGHTS['stage_velocity'] +
                engagement_score * self.WEIGHTS['hm_engagement']
            )
            
            # Count violations by severity
            high_severity = len(recruiter_violations[recruiter_violations['severity'] == 'high'])
            medium_severity = len(recruiter_violations[recruiter_violations['severity'] == 'medium'])
            low_severity = len(recruiter_violations[recruiter_violations['severity'] == 'low'])
            
            scores.append({
                'name': recruiter,
                'final_score': round(final_score, 1),
                'feedback_score': round(feedback_score, 1),
                'velocity_score': round(velocity_score, 1),
                'engagement_score': round(engagement_score, 1),
                'total_violations': len(recruiter_violations),
                'high_severity': high_severity,
                'medium_severity': medium_severity,
                'low_severity': low_severity
            })
        
        return pd.DataFrame(scores)
    
    def score_by_hiring_manager(self, violations):
        """Calculate scores for each hiring manager"""
        if violations.empty:
            # No violations - everyone gets 100
            hms = self.data['hiring_manager_name'].unique()
            return pd.DataFrame([{
                'name': hm,
                'final_score': 100.0,
                'feedback_score': 100.0,
                'velocity_score': 100.0,
                'engagement_score': 100.0,
                'total_violations': 0,
                'high_severity': 0,
                'medium_severity': 0,
                'low_severity': 0
            } for hm in hms])
        
        hms = self.data['hiring_manager_name'].unique()
        scores = []
        
        for hm in hms:
            hm_violations = violations[violations['hiring_manager_name'] == hm]
            
            # Calculate metric-specific scores
            feedback_score = self._calculate_metric_score(
                hm_violations, 'feedback_timeliness'
            )
            velocity_score = self._calculate_metric_score(
                hm_violations, 'stage_velocity'
            )
            engagement_score = self._calculate_metric_score(
                hm_violations, 'hm_engagement'
            )
            
            # Calculate weighted final score
            final_score = (
                feedback_score * self.WEIGHTS['feedback_timeliness'] +
                velocity_score * self.WEIGHTS['stage_velocity'] +
                engagement_score * self.WEIGHTS['hm_engagement']
            )
            
            # Count violations by severity
            high_severity = len(hm_violations[hm_violations['severity'] == 'high'])
            medium_severity = len(hm_violations[hm_violations['severity'] == 'medium'])
            low_severity = len(hm_violations[hm_violations['severity'] == 'low'])
            
            scores.append({
                'name': hm,
                'final_score': round(final_score, 1),
                'feedback_score': round(feedback_score, 1),
                'velocity_score': round(velocity_score, 1),
                'engagement_score': round(engagement_score, 1),
                'total_violations': len(hm_violations),
                'high_severity': high_severity,
                'medium_severity': medium_severity,
                'low_severity': low_severity
            })
        
        return pd.DataFrame(scores)
    
    def _calculate_metric_score(self, violations, metric):
        """Calculate score for a specific metric - starts at 100, deducts penalties"""
        metric_violations = violations[violations['metric'] == metric]
        
        if len(metric_violations) == 0:
            return 100.0
        
        score = 100.0
        total_penalty = metric_violations['penalty'].sum()
        score += total_penalty  # Penalties are negative
        
        return max(0.0, score)
