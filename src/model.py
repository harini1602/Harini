import json, numpy as np, pandas as pd
from datetime import datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import recall_score, precision_score, roc_auc_score, average_precision_score, brier_score_loss
from sklearn.model_selection import train_test_split
FEATURE_COLUMNS=['attendance_pct','recent_attendance_pct','attendance_decline','absence_count','longest_absence_streak','current_absence_streak','recent_unexplained_absences','days_since_last_attendance','marks_pct','recent_marks_pct','marks_decline','failing_subject_count','near_failing_subject_count','worst_subject_gap','subject_variability','missing_assessments','decline_interaction','chronic_low_attendance','recent_disengagement','data_quality_confidence_score','previous_risk_score_delta']

def synthetic_labels(df):
    risk=(df.attendance_pct<75)|(df.recent_attendance_pct<65)|(df.marks_pct<45)|((df.attendance_decline>12)&(df.marks_decline>10))|(df.current_absence_streak>=5)|(df.failing_subject_count>=2)
    return risk.astype(int)

def train_calibrated_model(features, labels=None):
    X=features[FEATURE_COLUMNS].astype(float); y=synthetic_labels(features) if labels is None else labels.astype(int)
    if y.nunique()<2: y=synthetic_labels(features)
    base=GradientBoostingClassifier(random_state=42, n_estimators=80, max_depth=3)
    cv=3 if min(np.bincount(y))>=3 and len(y)>=12 else 2
    model=CalibratedClassifierCV(base, method='sigmoid', cv=cv).fit(X,y)
    p=model.predict_proba(X)[:,1]
    thresholds=np.linspace(.25,.75,21); best=.5; best_recall=-1
    for t in thresholds:
        r=recall_score(y, p>=t, zero_division=0)
        if r>best_recall: best_recall=r; best=t
    pred=p>=best
    metrics={'recall_high_risk':float(recall_score(y,pred,zero_division=0)),'false_negative_rate':float(1-recall_score(y,pred,zero_division=0)),'precision':float(precision_score(y,pred,zero_division=0)),'brier_score':float(brier_score_loss(y,p)),'mode':'synthetic-label' if labels is None else 'labeled'}
    if y.nunique()>1: metrics.update({'roc_auc':float(roc_auc_score(y,p)),'pr_auc':float(average_precision_score(y,p))})
    meta={'model_version':'gb-calibrated-'+datetime.utcnow().strftime('%Y%m%d%H%M%S'),'trained_at':datetime.utcnow().isoformat(),'feature_list':FEATURE_COLUMNS,'calibration_status':'CalibratedClassifierCV sigmoid','threshold':float(best),'metrics':metrics}
    return model, meta

def score_students(model, features):
    X=features[FEATURE_COLUMNS].astype(float); out=features.copy(); out['risk_score']=(model.predict_proba(X)[:,1]*100).round(1)
    out['urgency']=pd.cut(out.risk_score, [-1,49.9,69.9,84.9,100], labels=['Monitor','Moderate','High','Critical']).astype(str)
    return out.sort_values('risk_score', ascending=False)

def persist_model_metadata(conn, meta):
    conn.execute('INSERT INTO model_metadata(model_version,trained_at,feature_list,calibration_status,threshold,metrics_json) VALUES(?,?,?,?,?,?)',(meta['model_version'],meta['trained_at'],json.dumps(meta['feature_list']),meta['calibration_status'],meta['threshold'],json.dumps(meta['metrics']))); conn.commit()
