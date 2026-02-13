"""
Generate realistic ATS data with varied performance trends
Some people improving, some declining, realistic patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
random.seed(42)
np.random.seed(42)

# Configuration
NUM_ROLES = 60
START_DATE = datetime(2024, 11, 1)
END_DATE = datetime(2025, 2, 13)

# Team structure
TEAMS = ['Engineering', 'Sales', 'Marketing', 'Product', 'Customer Success', 'Operations']

# Define realistic performance profiles
RECRUITERS = {
    'Engineering': [
        {'name': 'Sarah Chen', 'trend': 'improving', 'base_score': 55},  # Started rough, getting better
        {'name': 'Mike Rodriguez', 'trend': 'stable_good', 'base_score': 78},  # Consistently good
    ],
    'Sales': [
        {'name': 'Jessica Williams', 'trend': 'declining', 'base_score': 82},  # Burning out
        {'name': 'David Park', 'trend': 'improving', 'base_score': 48},  # New hire, learning fast
    ],
    'Marketing': [
        {'name': 'Amanda Taylor', 'trend': 'stable_poor', 'base_score': 35},  # Struggling consistently
        {'name': 'Chris Johnson', 'trend': 'improving', 'base_score': 52},  # Responding to coaching
    ],
    'Product': [
        {'name': 'Lisa Anderson', 'trend': 'stable_good', 'base_score': 75},
    ],
    'Customer Success': [
        {'name': 'Alex Morgan', 'trend': 'improving', 'base_score': 60},
    ],
    'Operations': [
        {'name': 'Jordan Kim', 'trend': 'declining', 'base_score': 70},  # Was good, now slipping
    ]
}

HIRING_MANAGERS = {
    'Engineering': [
        {'name': 'Alex Kumar', 'trend': 'stable_good', 'base_score': 80},
        {'name': 'Rachel Green', 'trend': 'improving', 'base_score': 58},
        {'name': 'Tom Brady', 'trend': 'dramatically_improving', 'base_score': 28},  # Success story!
    ],
    'Sales': [
        {'name': 'Jennifer Lopez', 'trend': 'stable_poor', 'base_score': 45},
        {'name': 'Mark Watson', 'trend': 'improving', 'base_score': 50},
    ],
    'Marketing': [
        {'name': 'Emily Davis', 'trend': 'declining', 'base_score': 75},
        {'name': 'Robert Smith', 'trend': 'improving', 'base_score': 42},
    ],
    'Product': [
        {'name': 'Priya Patel', 'trend': 'stable_good', 'base_score': 72},
        {'name': 'James Wilson', 'trend': 'stable_poor', 'base_score': 40},
    ],
    'Customer Success': [
        {'name': 'Maria Garcia', 'trend': 'improving', 'base_score': 55},
        {'name': 'Kevin Lee', 'trend': 'stable_good', 'base_score': 78},
    ],
    'Operations': [
        {'name': 'Taylor Brooks', 'trend': 'declining', 'base_score': 68},
        {'name': 'Morgan Hayes', 'trend': 'improving', 'base_score': 62},
    ]
}

JOB_TITLES = {
    'Engineering': ['Senior Software Engineer', 'Frontend Developer', 'Backend Engineer', 'DevOps Engineer', 'Engineering Manager', 'Staff Engineer'],
    'Sales': ['Account Executive', 'Sales Development Rep', 'Sales Manager', 'Enterprise AE', 'Regional Sales Director'],
    'Marketing': ['Content Marketing Manager', 'Growth Marketing Lead', 'Brand Designer', 'Marketing Analyst', 'Product Marketing Manager'],
    'Product': ['Product Manager', 'Senior Product Designer', 'Product Analyst', 'Associate PM', 'Principal Product Manager'],
    'Customer Success': ['Customer Success Manager', 'Support Engineer', 'Implementation Specialist', 'CSM Lead'],
    'Operations': ['Operations Manager', 'Business Analyst', 'Program Manager', 'Operations Coordinator']
}

STAGES = ['New', 'Phone Screen', 'Technical Interview', 'Final Interview', 'Offer', 'Hired', 'Rejected']

def get_current_performance(person, days_since_start):
    """Calculate current performance based on trend and time elapsed"""
    base_score = person['base_score']
    trend = person['trend']
    
    # Calculate how much time has passed (0 to 1, where 1 = 100 days)
    progress = min(days_since_start / 100.0, 1.0)
    
    if trend == 'improving':
        # Improving 20-30 points over 100 days
        improvement = random.uniform(20, 30) * progress
        return min(100, base_score + improvement)
    
    elif trend == 'dramatically_improving':
        # Major turnaround - 40+ points
        improvement = random.uniform(40, 50) * progress
        return min(100, base_score + improvement)
    
    elif trend == 'declining':
        # Getting worse - losing 15-25 points
        decline = random.uniform(15, 25) * progress
        return max(20, base_score - decline)
    
    elif trend == 'stable_good':
        # Stays good with small variations
        return base_score + random.uniform(-3, 3)
    
    elif trend == 'stable_poor':
        # Stays poor with small variations
        return base_score + random.uniform(-5, 5)
    
    return base_score

def generate_violations_for_performance(current_score):
    """Generate realistic violations based on current score"""
    # Lower scores = more violations
    if current_score >= 80:
        high = random.randint(0, 2)
        medium = random.randint(1, 3)
        low = random.randint(2, 5)
    elif current_score >= 65:
        high = random.randint(1, 4)
        medium = random.randint(2, 5)
        low = random.randint(3, 6)
    elif current_score >= 50:
        high = random.randint(3, 6)
        medium = random.randint(4, 7)
        low = random.randint(2, 4)
    else:
        high = random.randint(5, 10)
        medium = random.randint(3, 6)
        low = random.randint(1, 3)
    
    return high, medium, low

def create_violation_events(high_count, medium_count, low_count, req_id, recruiter, hm):
    """Create specific violation events"""
    events = []
    
    # High severity - feedback delays > 72hrs or stage stuck > 14 days
    for i in range(high_count):
        if random.random() < 0.5:
            events.append({
                'requisition_id': req_id,
                'stage': random.choice(['Phone Screen', 'Technical Interview', 'Final Interview']),
                'metric': 'feedback_timeliness',
                'severity': 'high',
                'penalty': -25,
                'delay_hours': random.randint(73, 168),
                'recruiter_name': recruiter,
                'hiring_manager_name': hm,
                'is_hm_interview': True,
                'responsible_party': hm
            })
        else:
            events.append({
                'requisition_id': req_id,
                'stage': random.choice(['Phone Screen', 'Technical Interview']),
                'metric': 'stage_velocity',
                'severity': 'high',
                'penalty': -25,
                'days_in_stage': random.randint(15, 30),
                'recruiter_name': recruiter,
                'hiring_manager_name': hm,
                'responsible_party': recruiter
            })
    
    # Medium severity
    for i in range(medium_count):
        if random.random() < 0.5:
            events.append({
                'requisition_id': req_id,
                'stage': random.choice(['Phone Screen', 'Technical Interview']),
                'metric': 'feedback_timeliness',
                'severity': 'medium',
                'penalty': -10,
                'delay_hours': random.randint(49, 72),
                'recruiter_name': recruiter,
                'hiring_manager_name': hm,
                'is_hm_interview': random.choice([True, False]),
                'responsible_party': hm if random.random() < 0.6 else recruiter
            })
        else:
            events.append({
                'requisition_id': req_id,
                'stage': random.choice(['Phone Screen', 'Technical Interview']),
                'metric': 'stage_velocity',
                'severity': 'medium',
                'penalty': -10,
                'days_in_stage': random.randint(8, 14),
                'recruiter_name': recruiter,
                'hiring_manager_name': hm,
                'responsible_party': recruiter
            })
    
    # Low severity
    for i in range(low_count):
        events.append({
            'requisition_id': req_id,
            'stage': random.choice(['Phone Screen', 'Technical Interview', 'Final Interview']),
            'metric': 'feedback_timeliness',
            'severity': 'low',
            'penalty': -3,
            'delay_hours': random.randint(24, 48),
            'recruiter_name': recruiter,
            'hiring_manager_name': hm,
            'is_hm_interview': False,
            'responsible_party': recruiter
        })
    
    return events

def generate_realistic_ats_data():
    """Generate complete realistic dataset"""
    
    all_roles = []
    all_violations = []
    
    days_since_start = (END_DATE - START_DATE).days
    
    for i in range(NUM_ROLES):
        # Select team
        team = random.choice(TEAMS)
        
        # Select recruiter and HM from that team
        recruiter_profile = random.choice(RECRUITERS[team])
        hm_profile = random.choice(HIRING_MANAGERS[team])
        
        recruiter_name = recruiter_profile['name']
        hm_name = hm_profile['name']
        
        # Calculate current performance for both
        rec_current_score = get_current_performance(recruiter_profile, days_since_start)
        hm_current_score = get_current_performance(hm_profile, days_since_start)
        
        # Average their performance for role health
        avg_score = (rec_current_score + hm_current_score) / 2
        
        # Generate violations based on combined performance
        high, medium, low = generate_violations_for_performance(avg_score)
        
        # Create role
        req_id = f"REQ-2025-{1000 + i}"
        job_title = random.choice(JOB_TITLES[team])
        
        role_opened = START_DATE + timedelta(days=random.randint(0, days_since_start - 20))
        days_open = (END_DATE - role_opened).days
        
        status = random.choices(
            ['Phone Screen', 'Technical Interview', 'Final Interview', 'Offer', 'Hired'],
            weights=[0.3, 0.25, 0.2, 0.15, 0.1]
        )[0]
        
        # Main role record
        all_roles.append({
            'requisition_id': req_id,
            'job_title': job_title,
            'team': team,
            'recruiter_name': recruiter_name,
            'hiring_manager_name': hm_name,
            'role_opened_date': role_opened.strftime('%Y-%m-%d'),
            'current_status': status,
            'stage': status,
            'stage_entered_date': (role_opened + timedelta(days=random.randint(1, days_open))).strftime('%Y-%m-%d %H:%M:%S'),
            'interview_completed_date': '',
            'feedback_submitted_date': '',
            'interviewer_name': recruiter_name,
            'is_hiring_manager_interview': False
        })
        
        # Generate violation events
        violation_events = create_violation_events(high, medium, low, req_id, recruiter_name, hm_name)
        all_violations.extend(violation_events)
    
    # Create DataFrames
    roles_df = pd.DataFrame(all_roles)
    violations_df = pd.DataFrame(all_violations)
    
    return roles_df, violations_df

if __name__ == "__main__":
    print("Generating realistic ATS data with performance trends...")
    print("=" * 70)
    
    roles_df, violations_df = generate_realistic_ats_data()
    
    # Save
    roles_df.to_csv('sample_ats_export.csv', index=False)
    violations_df.to_csv('violations_data.csv', index=False)
    
    print(f"✓ Generated {len(roles_df)} roles")
    print(f"✓ Generated {len(violations_df)} violations")
    
    # Show some stats
    print("\n📊 PERFORMANCE BREAKDOWN")
    print("=" * 70)
    
    # Count by team
    print("\nRoles by Team:")
    print(roles_df['team'].value_counts())
    
    print("\nViolations by Severity:")
    print(violations_df['severity'].value_counts())
    
    print("\n⭐ REALISTIC TRENDS BUILT IN:")
    print("=" * 70)
    print("Improving: Sarah Chen, David Park, Chris Johnson, Alex Morgan, Rachel Green, Tom Brady (dramatic!)")
    print("Declining: Jessica Williams, Jordan Kim, Emily Davis, Taylor Brooks")
    print("Stable Good: Mike Rodriguez, Lisa Anderson, Alex Kumar, Priya Patel, Kevin Lee")
    print("Stable Poor: Amanda Taylor, Jennifer Lopez, James Wilson")
