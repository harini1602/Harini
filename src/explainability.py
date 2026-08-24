import numpy as np, pandas as pd, shap
from .model import FEATURE_COLUMNS
FRIENDLY={'attendance_pct':'overall attendance is low','recent_attendance_pct':'recent attendance is low','attendance_decline':'attendance fell compared with the prior period','absence_count':'many absences are recorded','longest_absence_streak':'a long absence streak appears','current_absence_streak':'the current absence streak is concerning','marks_pct':'overall marks are low','recent_marks_pct':'recent marks are low','marks_decline':'marks declined across assessments','failing_subject_count':'subjects are below the passing mark','worst_subject_gap':'largest subject gap is below pass level','missing_assessments':'recent assessments are missing','recent_disengagement':'recent attendance and marks both signal disengagement'}

def _estimator(model):
    cc=model.calibrated_classifiers_[0]
    return getattr(cc, 'estimator', getattr(cc, 'base_estimator', cc))

def explain_students(model, features):
    X=features[FEATURE_COLUMNS].astype(float)
    explainer=shap.TreeExplainer(_estimator(model))
    vals=explainer.shap_values(X)
    if isinstance(vals, list): vals=vals[-1]
    rows=[]
    for i, sid in enumerate(features.student_id):
        impacts=pd.Series(vals[i], index=FEATURE_COLUMNS).sort_values(ascending=False)
        top=impacts.head(3)
        drivers=[{'feature':f,'label':FRIENDLY.get(f,f.replace('_',' ')),'impact':float(v),'value':float(X.iloc[i][f])} for f,v in top.items()]
        labels=', '.join(d['label'] for d in drivers)
        rows.append({'student_id':sid,'top_drivers':drivers,'explanation':f"Model signal increased mainly because {labels}. Teacher judgement and context should guide the final action."})
    return rows
