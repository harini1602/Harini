from datetime import date, timedelta

def urgency(score):
    return 'Critical' if score>=85 else 'High' if score>=70 else 'Moderate' if score>=50 else 'Monitor'

def recommended_action(row):
    if row.get('current_absence_streak',0)>=5: return 'Call parent/guardian today and confirm reason for recent absences.'
    if row.get('failing_subject_count',0)>=2: return f"Schedule remediation and review {row.get('worst_subject','the lowest subject')} assessment."
    if row.get('attendance_decline',0)>10: return 'Assign attendance check-in for the next 5 school days.'
    if row.get('risk_score',0)>=85: return 'Refer to counsellor if absence streak or distress signals continue.'
    return 'Monitor weekly and celebrate the next positive attendance or learning step.'

def message_template(display_id, reason):
    return f"Hello, this is a supportive check-in from school about {display_id}. We noticed recent changes: {reason}. We would like to work together early and understand if any support is needed. Could we schedule a short conversation this week?"

def default_due_date(): return (date.today()+timedelta(days=3)).isoformat()
