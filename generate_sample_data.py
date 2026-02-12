"""
Generate realistic fake ATS data for recruiter scorecard demo
Mimics Workday/Greenhouse CSV export structure
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
random.seed(42)
np.random.seed(42)

# Configuration
NUM_ROLES = 50
START_DATE = datetime(2024, 11, 1)
END_DATE = datetime(2025, 1, 31)

# Team structure
TEAMS = ['Engineering', 'Sales', 'Marketing', 'Product', 'Customer Success']

RECRUITERS = {
    'Engineering': ['Sarah Chen', 'Mike Rodriguez'],
    'Sales': ['Jessica Williams', 'David Park'],
    'Marketing': ['Amanda Taylor', 'Chris Johnson'],
    'Product': ['Sarah Chen', 'Lisa Anderson'],  # Sarah covers multiple teams
    'Customer Success': ['Mike Rodriguez', 'Jessica Williams']
}

HIRING_MANAGERS = {
    'Engineering': ['Alex Kumar', 'Rachel Green', 'Tom Brady'],
    'Sales': ['Jennifer Lopez', 'Mark Watson'],
    'Marketing': ['Emily Davis', 'Robert Smith'],
    'Product': ['Priya Patel', 'James Wilson'],
    'Customer Success': ['Maria Garcia', 'Kevin Lee']
}

JOB_TITLES = {
    'Engineering': ['Senior Software Engineer', 'Frontend Developer', 'Backend Engineer', 'DevOps Engineer', 'Engineering Manager'],
    'Sales': ['Account Executive', 'Sales Development Rep', 'Sales Manager', 'Enterprise AE'],
    'Marketing': ['Content Marketing Manager', 'Growth Marketing Lead', 'Brand Designer', 'Marketing Analyst'],
    'Product': ['Product Manager', 'Senior Product Designer', 'Product Analyst', 'Associate PM'],
    'Customer Success': ['Customer Success Manager', 'Support Engineer', 'Implementation Specialist']
}

STAGES = ['New', 'Phone Screen', 'Technical Interview', 'Final Interview', 'Offer', 'Hired', 'Rejected']

def random_date(start, end):
    """Generate random datetime between start and end"""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)

def generate_realistic_progression(role_opened_date, is_fast_recruiter, is_engaged_hm):
    """
    Generate realistic stage progression with timing that reflects recruiter and HM performance
    """
    events = []
    current_date = role_opened_date
    
    # Determine role outcome
    outcome = random.choices(['Hired', 'Rejected', 'In Progress'], 
                            weights=[0.3, 0.4, 0.3])[0]
    
    current_stage = 'New'
    
    # Phone Screen Stage
    if is_fast_recruiter:
        days_to_screen = random.randint(2, 5)
    else:
        days_to_screen = random.randint(5, 12)
    
    phone_screen_date = current_date + timedelta(days=days_to_screen)
    events.append({
        'stage': 'Phone Screen',
        'stage_entered': phone_screen_date,
        'interview_date': phone_screen_date + timedelta(days=random.randint(0, 2)),
        'feedback_submitted': None
    })
    
    # Feedback timing (Metric 1)
    if is_engaged_hm:
        feedback_delay_hours = random.randint(4, 36)
    else:
        feedback_delay_hours = random.randint(48, 120)
    
    events[-1]['feedback_submitted'] = events[-1]['interview_date'] + timedelta(hours=feedback_delay_hours)
    
    if outcome == 'Rejected' and random.random() < 0.3:
        return events, 'Rejected'
    
    # Technical Interview Stage
    if is_engaged_hm:
        days_to_tech = random.randint(3, 7)
    else:
        days_to_tech = random.randint(7, 18)  # Metric 2: slow stage velocity
    
    tech_interview_date = events[-1]['feedback_submitted'] + timedelta(days=days_to_tech)
    events.append({
        'stage': 'Technical Interview',
        'stage_entered': tech_interview_date,
        'interview_date': tech_interview_date + timedelta(days=random.randint(0, 3)),
        'feedback_submitted': None
    })
    
    # Feedback timing
    if is_engaged_hm:
        feedback_delay_hours = random.randint(6, 48)
    else:
        # Metric 3: Some HMs don't submit feedback at all or are very delayed
        if random.random() < 0.2:
            feedback_delay_hours = None  # Missing feedback
        else:
            feedback_delay_hours = random.randint(72, 168)
    
    if feedback_delay_hours:
        events[-1]['feedback_submitted'] = events[-1]['interview_date'] + timedelta(hours=feedback_delay_hours)
    
    if outcome == 'Rejected' and random.random() < 0.4:
        return events, 'Rejected'
    
    if outcome == 'In Progress':
        return events, 'Technical Interview'
    
    # Final Interview Stage
    if is_engaged_hm:
        days_to_final = random.randint(4, 8)
    else:
        days_to_final = random.randint(10, 20)
    
    final_interview_date = events[-1]['feedback_submitted'] + timedelta(days=days_to_final) if events[-1]['feedback_submitted'] else events[-1]['interview_date'] + timedelta(days=days_to_final + 5)
    events.append({
        'stage': 'Final Interview',
        'stage_entered': final_interview_date,
        'interview_date': final_interview_date + timedelta(days=random.randint(0, 2)),
        'feedback_submitted': None
    })
    
    if is_engaged_hm:
        feedback_delay_hours = random.randint(12, 48)
    else:
        if random.random() < 0.15:
            feedback_delay_hours = None
        else:
            feedback_delay_hours = random.randint(60, 144)
    
    if feedback_delay_hours:
        events[-1]['feedback_submitted'] = events[-1]['interview_date'] + timedelta(hours=feedback_delay_hours)
    
    # Offer Stage
    if outcome == 'Hired':
        if is_engaged_hm:
            days_to_offer = random.randint(2, 5)
        else:
            days_to_offer = random.randint(6, 12)
        
        offer_date = events[-1]['feedback_submitted'] + timedelta(days=days_to_offer) if events[-1]['feedback_submitted'] else events[-1]['interview_date'] + timedelta(days=days_to_offer + 3)
        events.append({
            'stage': 'Offer',
            'stage_entered': offer_date,
            'interview_date': None,
            'feedback_submitted': None
        })
        
        # Hired
        hired_date = offer_date + timedelta(days=random.randint(3, 10))
        events.append({
            'stage': 'Hired',
            'stage_entered': hired_date,
            'interview_date': None,
            'feedback_submitted': None
        })
    
    final_stage = events[-1]['stage']
    return events, final_stage

def generate_ats_export():
    """Generate complete ATS export CSV"""
    
    roles_data = []
    
    for i in range(NUM_ROLES):
        # Select team
        team = random.choice(TEAMS)
        
        # Assign recruiter and hiring manager
        recruiter = random.choice(RECRUITERS[team])
        hiring_manager = random.choice(HIRING_MANAGERS[team])
        
        # Create performance profiles
        # Some recruiters are fast, some are slow
        recruiter_performance = {
            'Sarah Chen': 'fast',
            'Jessica Williams': 'fast',
            'Mike Rodriguez': 'medium',
            'David Park': 'medium',
            'Amanda Taylor': 'slow',
            'Chris Johnson': 'slow',
            'Lisa Anderson': 'fast'
        }
        
        # Some HMs are engaged, some are not
        hm_engagement = {
            'Alex Kumar': 'engaged',
            'Rachel Green': 'engaged',
            'Priya Patel': 'engaged',
            'Jennifer Lopez': 'medium',
            'Mark Watson': 'medium',
            'Emily Davis': 'medium',
            'Tom Brady': 'disengaged',
            'Robert Smith': 'disengaged',
            'James Wilson': 'disengaged',
            'Maria Garcia': 'medium',
            'Kevin Lee': 'engaged'
        }
        
        is_fast_recruiter = recruiter_performance[recruiter] == 'fast'
        is_engaged_hm = hm_engagement[hiring_manager] == 'engaged'
        
        # Generate role details
        role_opened = random_date(START_DATE, END_DATE - timedelta(days=30))
        requisition_id = f"REQ-2024-{1000 + i}"
        job_title = random.choice(JOB_TITLES[team])
        
        # Generate progression
        events, final_status = generate_realistic_progression(role_opened, is_fast_recruiter, is_engaged_hm)
        
        # Create rows for each stage/interview
        for event_idx, event in enumerate(events):
            row = {
                'requisition_id': requisition_id,
                'job_title': job_title,
                'team': team,
                'recruiter_name': recruiter,
                'hiring_manager_name': hiring_manager,
                'role_opened_date': role_opened.strftime('%Y-%m-%d'),
                'current_status': final_status,
                'stage': event['stage'],
                'stage_entered_date': event['stage_entered'].strftime('%Y-%m-%d %H:%M:%S'),
                'interview_completed_date': event['interview_date'].strftime('%Y-%m-%d %H:%M:%S') if event['interview_date'] else '',
                'feedback_submitted_date': event['feedback_submitted'].strftime('%Y-%m-%d %H:%M:%S') if event['feedback_submitted'] else '',
                'interviewer_name': hiring_manager if 'Interview' in event['stage'] else recruiter,
                'is_hiring_manager_interview': 'Interview' in event['stage']
            }
            roles_data.append(row)
    
    df = pd.DataFrame(roles_data)
    return df

if __name__ == "__main__":
    print("Generating realistic ATS export data...")
    df = generate_ats_export()
    
    output_file = "sample_ats_export.csv"
    df.to_csv(output_file, index=False)
    
    print(f"✓ Generated {len(df)} records across {df['requisition_id'].nunique()} roles")
    print(f"✓ Saved to: {output_file}")
    print(f"\nData Summary:")
    print(f"  - Teams: {df['team'].nunique()}")
    print(f"  - Recruiters: {df['recruiter_name'].nunique()}")
    print(f"  - Hiring Managers: {df['hiring_manager_name'].nunique()}")
    print(f"  - Date Range: {df['role_opened_date'].min()} to {df['role_opened_date'].max()}")
