import numpy as np, pandas as pd
from .config import PASS_MARK, RECENT_DAYS

def _streak(vals):
    best=cur=0
    for v in vals:
        if not v: cur+=1; best=max(best,cur)
        else: cur=0
    return best

def _current_streak(vals):
    cur=0
    for v in vals[::-1]:
        if not v: cur+=1
        else: break
    return cur

def build_features(att, marks, previous_scores=None):
    att=att.copy(); marks=marks.copy(); att['date']=pd.to_datetime(att['date']); marks['date']=pd.to_datetime(marks['date'])
    max_date=max(att['date'].max(), marks['date'].max())
    rows=[]
    for sid in sorted(set(att.student_id)|set(marks.student_id)):
        a=att[att.student_id==sid].sort_values('date'); m=marks[marks.student_id==sid].sort_values('date')
        name=(a.student_name.iloc[-1] if len(a) else m.student_name.iloc[-1]); cls=(a.class_name.iloc[-1] if len(a) else m.class_name.iloc[-1]); sec=(a.section.iloc[-1] if 'section' in a and len(a) else (m.section.iloc[-1] if 'section' in m and len(m) else 'A'))
        recent_a=a[a.date>=max_date-pd.Timedelta(days=RECENT_DAYS)]; prior_a=a[(a.date<max_date-pd.Timedelta(days=RECENT_DAYS)) & (a.date>=max_date-pd.Timedelta(days=RECENT_DAYS*2))]
        att_pct=100*a.is_present.mean() if len(a) else 0; recent_att=100*recent_a.is_present.mean() if len(recent_a) else att_pct; prior_att=100*prior_a.is_present.mean() if len(prior_a) else att_pct
        vals=a.is_present.astype(bool).tolist(); unexplained=0
        if 'status' in a: unexplained=((recent_a.status.astype(str).str.lower().str.contains('unexplained|unknown|u')) & (recent_a.is_present==0)).sum()
        m['pct']=100*m.marks/m.max_marks; recent_m=m[m.date>=max_date-pd.Timedelta(days=RECENT_DAYS)]
        ordered=m.sort_values('date'); half=max(1, len(ordered)//2); early=ordered.head(half).pct.mean() if len(ordered) else 0; late=ordered.tail(half).pct.mean() if len(ordered) else early
        subj=m.groupby('subject').pct.mean() if len(m) else pd.Series(dtype=float)
        worst_subject=str(subj.idxmin()) if len(subj) else 'No assessments'; worst_gap=max(0, PASS_MARK-(subj.min() if len(subj) else 0))
        missing=max(0, m.subject.nunique()*m.term.nunique()-len(m.drop_duplicates(['subject','term']))) if len(m) else 0
        marks_pct=m.pct.mean() if len(m) else 0; recent_marks=recent_m.pct.mean() if len(recent_m) else marks_pct
        att_decl=max(0, prior_att-recent_att); marks_decl=max(0, early-late)
        prev=previous_scores.get(sid, 0) if previous_scores else 0
        rows.append(dict(student_id=sid, student_name=name, class_name=cls, section=sec, attendance_pct=att_pct, recent_attendance_pct=recent_att, attendance_decline=att_decl, absence_count=int((a.is_present==0).sum()) if len(a) else 0, longest_absence_streak=_streak(vals), current_absence_streak=_current_streak(vals), recent_unexplained_absences=int(unexplained), days_since_last_attendance=int((max_date-a.date.max()).days) if len(a) else 999, marks_pct=marks_pct, recent_marks_pct=recent_marks, marks_decline=marks_decl, failing_subject_count=int((subj<PASS_MARK).sum()) if len(subj) else 0, near_failing_subject_count=int((subj<50).sum()) if len(subj) else 0, worst_subject=worst_subject, worst_subject_gap=worst_gap, subject_variability=float(subj.std() if len(subj)>1 else 0), missing_assessments=int(missing), decline_interaction=att_decl*marks_decl/100, chronic_low_attendance=int(att_pct<75), recent_disengagement=int(recent_att<70 and recent_marks<50), data_quality_confidence_score=float(min(1, (len(a)/20+len(m)/8)/2)), previous_risk_score_delta=float(prev)))
    return pd.DataFrame(rows).fillna(0)
