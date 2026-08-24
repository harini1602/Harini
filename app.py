import json
import sys
from pathlib import Path
from datetime import datetime

# Streamlit Cloud can launch from a working directory that is not the repo root;
# keep local src imports deterministic after merges/deploys.
APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import pandas as pd
import streamlit as st
from src.config import APP_NAME, TAGLINE, ENCRYPTION_READY
from src.auth import authenticate, can
from src.audit import log_event, get_audit_logs
from src.database import connect, init_db, insert_batch, latest_batch_id
from src.features import build_features
from src.ingestion import read_spreadsheet, normalize_attendance, normalize_marks, standardize_columns
from src.interventions import recommended_action, message_template, default_due_date
from src.model import train_calibrated_model, score_students, persist_model_metadata
from src.explainability import explain_students
from src.privacy import pseudonymize
from src.sample_data import generate_demo_data
from src.validation import validate_attendance, validate_marks, cross_file_warnings
from src import visualizations as viz

st.set_page_config(APP_NAME, layout='wide')
st.markdown('''<style>.stApp{background:#f8fafc;color:#0f172a}.hero{padding:1.4rem;border-radius:24px;background:linear-gradient(135deg,#0f172a,#0f766e);color:white}.card{padding:1rem;border-radius:18px;background:white;box-shadow:0 10px 25px rgba(15,23,42,.08);border:1px solid #e2e8f0}.risk{font-size:2rem;font-weight:800}.muted{color:#64748b}.badge{padding:.2rem .55rem;border-radius:999px;background:#ccfbf1;color:#134e4a;font-weight:700}</style>''', unsafe_allow_html=True)
conn=connect(); init_db(conn)

def process(att, marks, user, source='demo'):
    ae,aw=validate_attendance(att); me,mw=validate_marks(marks); warnings=aw+mw+cross_file_warnings(att,marks)
    log_event(conn,user,'validation','upload',source,f'errors={ae+me}; warnings={warnings}')
    if ae or me: return None, ae+me, warnings
    batch=insert_batch(conn,'demo-school',source,{'attendance_rows':len(att),'marks_rows':len(marks)})
    for df,table in [(att,'attendance'),(marks,'marks')]: df.assign(batch_id=batch).to_sql(table, conn, if_exists='append', index=False)
    for _,r in pd.concat([att[['student_id','student_name','class_name','section']], marks[['student_id','student_name','class_name','section']]]).drop_duplicates('student_id').iterrows():
        conn.execute('INSERT OR REPLACE INTO students VALUES(?,?,?,?,?,?)',(r.student_id,pseudonymize(r.student_id),r.student_name,r.class_name,r.section,'demo-school'))
    prev={r['student_id']:r['risk_score'] for r in conn.execute('SELECT student_id,risk_score FROM risk_scores WHERE batch_id=(SELECT MAX(id) FROM upload_batches WHERE id<?)',(batch,)).fetchall()}
    feats=build_features(att,marks,prev); model,meta=train_calibrated_model(feats); scored=score_students(model,feats); explanations=explain_students(model,scored); emap={e['student_id']:e for e in explanations}
    persist_model_metadata(conn,meta)
    for _,r in scored.iterrows():
        pseudo=pseudonymize(r.student_id); exp=emap[r.student_id]; reason=exp['explanation']; delta=r.risk_score-prev.get(r.student_id, r.risk_score)
        conn.execute('INSERT INTO risk_scores(batch_id,student_id,pseudonym_id,risk_score,urgency,reason,features_json,model_version,score_delta,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(batch,r.student_id,pseudo,float(r.risk_score),r.urgency,reason,r.drop(labels=['student_name']).to_json(),meta['model_version'],float(delta),datetime.utcnow().isoformat()))
        conn.execute('INSERT INTO shap_explanations(batch_id,student_id,top_drivers_json,explanation,created_at) VALUES(?,?,?,?,?)',(batch,r.student_id,json.dumps(exp['top_drivers']),reason,datetime.utcnow().isoformat()))
        if r.risk_score>=50: conn.execute('INSERT INTO interventions(batch_id,student_id,pseudonym_id,status,message,notes,due_date,outcome,updated_by,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(batch,r.student_id,pseudo,'planned',message_template(pseudo, reason),'',default_due_date(),'Pending',user['email'],datetime.utcnow().isoformat()))
    conn.commit(); log_event(conn,user,'scoring','batch',batch,meta['model_version']); st.session_state.batch_id=batch; st.cache_data.clear(); return batch, [], warnings

@st.cache_data(ttl=2)
def load_scored(batch): return pd.read_sql_query('SELECT * FROM risk_scores WHERE batch_id=? ORDER BY risk_score DESC', conn, params=(batch,)) if batch else pd.DataFrame()

def login():
    st.markdown(f"<div class='hero'><h1>{APP_NAME}</h1><h3>{TAGLINE}</h3><p>Teacher-first explainable intervention operating system: Risk → Reason → Recommended Action → Outcome Tracking.</p></div>", unsafe_allow_html=True)
    with st.form('login'):
        email=st.selectbox('Demo account',['teacher@demo.school','leader@demo.school','admin@demo.school']); pwd=st.text_input('Password',value='teacher123',type='password')
        if st.form_submit_button('Start secure demo session'):
            u=authenticate(email,pwd)
            if u: st.session_state.user=u; log_event(conn,u,'login/session start'); st.rerun()
            else: st.error('Invalid credentials')
if 'user' not in st.session_state: login(); st.stop()
user=st.session_state.user
st.sidebar.markdown(f"**{user['name']}**  \nRole: `{user['role']}`"); page=st.sidebar.radio('Workspace',['Overview','Upload & Validate','Action Queue','Student Detail / Action Card','Model & Equity Monitor','Audit & Privacy'])
if 'batch_id' not in st.session_state: st.session_state.batch_id=latest_batch_id(conn)
if st.sidebar.button('Run built-in demo pipeline'):
    a,m=generate_demo_data(); process(a,m,user,'built-in demo'); st.rerun()
batch=st.session_state.batch_id; scored=load_scored(batch)
st.markdown(f"<div class='hero'><h1>{APP_NAME}</h1><p>{TAGLINE}</p><span class='badge'>Model signal ≠ final judgement</span></div>", unsafe_allow_html=True)
if page=='Upload & Validate':
    st.header('Upload & Validate'); st.info('CSV/XLSX spreadsheets are standardized through schema mapping before the data-quality gate.')
    af=st.file_uploader('Attendance CSV/XLSX',type=['csv','xlsx','xls']); mf=st.file_uploader('Marks CSV/XLSX',type=['csv','xlsx','xls']); of=st.file_uploader('Optional historical dropout outcome CSV',type=['csv'])
    if st.button('Use generated demo spreadsheets'): a,m=generate_demo_data(); st.session_state.preview=(a,m)
    if af and mf: st.session_state.preview=(normalize_attendance(read_spreadsheet(af)), normalize_marks(read_spreadsheet(mf))); log_event(conn,user,'file upload','upload','attendance+marks')
    if 'preview' in st.session_state:
        a,m=st.session_state.preview; st.write('Attendance mapping preview', standardize_columns(a)[1]); st.dataframe(a.head()); st.write('Marks mapping preview', standardize_columns(m)[1]); st.dataframe(m.head())
        errs,warns=validate_attendance(a)[0]+validate_marks(m)[0], validate_attendance(a)[1]+validate_marks(m)[1]+cross_file_warnings(a,m)
        [st.error(e) for e in errs]; [st.warning(w) for w in warns]
        if st.button('Process, score, explain, and refresh queue', disabled=bool(errs)): process(a,m,user,'uploaded/demo'); st.success('New batch scored and action queue refreshed.'); st.rerun()
elif scored.empty:
    st.info('No scored batch yet. Use the sidebar demo pipeline or Upload & Validate.')
elif page=='Overview':
    c=st.columns(6); vals=[len(scored),(scored.risk_score>=70).sum(),(scored.urgency=='Critical').sum(),round(pd.read_sql_query('SELECT AVG(json_extract(features_json,"$.attendance_pct")) a FROM risk_scores WHERE batch_id=?',conn,params=(batch,)).iloc[0,0],1),round(scored.risk_score.mean(),1),len(pd.read_sql_query('SELECT * FROM interventions WHERE batch_id=? AND status!=?',conn,params=(batch,'completed')))]
    labs=['Students','High risk','Critical','Avg attendance','Avg risk','Pending actions']
    for col,lab,val in zip(c,labs,vals): col.markdown(f"<div class='card'><div class='muted'>{lab}</div><div class='risk'>{val}</div></div>", unsafe_allow_html=True)
    st.plotly_chart(viz.risk_distribution(scored), use_container_width=True); st.plotly_chart(viz.risk_by_class(scored), use_container_width=True)
    st.subheader('What changed since previous review?'); st.write(f"Newly critical: {(scored.urgency=='Critical').sum()} • Improved ≥10 points: {(scored.score_delta<=-10).sum()} • Increased ≥10 points: {(scored.score_delta>=10).sum()}.")
elif page=='Action Queue':
    st.header('Prioritized Action Queue'); urg=st.multiselect('Urgency filter', ['Critical','High','Moderate','Monitor'], default=['Critical','High','Moderate']); q=scored[scored.urgency.isin(urg)]
    st.download_button('Bulk export for weak-connectivity follow-up', q.to_csv(index=False), 'action_queue.csv'); log_event(conn,user,'export','batch',batch)
    for _,r in q.iterrows(): st.markdown(f"<div class='card'><b>{r.pseudonym_id}</b> <span class='badge'>{r.urgency}</span><div class='risk'>{r.risk_score}/100</div><p>{r.reason}</p><b>Next:</b> {recommended_action(json.loads(r.features_json)|{'risk_score':r.risk_score})}</div><br>", unsafe_allow_html=True)
elif page=='Student Detail / Action Card':
    sid=st.selectbox('Select student', scored.pseudonym_id); r=scored[scored.pseudonym_id==sid].iloc[0]; feats=json.loads(r.features_json); log_event(conn,user,'student detail view','student',sid)
    st.plotly_chart(viz.gauge(r.risk_score), use_container_width=True); st.write(r.reason); drivers=json.loads(pd.read_sql_query('SELECT top_drivers_json FROM shap_explanations WHERE batch_id=? AND student_id=?',conn,params=(batch,r.student_id)).iloc[0,0]); st.plotly_chart(viz.shap_bar(drivers), use_container_width=True)
    if can(user,'reveal_identity') and st.button('Reveal identity (audited)'): st.warning(pd.read_sql_query('SELECT student_name FROM students WHERE student_id=?',conn,params=(r.student_id,)).iloc[0,0]); log_event(conn,user,'identity reveal','student',sid)
    with st.form('intervention'):
        msg=st.text_area('Editable parent/mentor message', message_template(sid,r.reason)); status=st.selectbox('Intervention status',['planned','contacted','completed','needs escalation']); notes=st.text_area('Notes'); due=st.date_input('Due/follow-up date'); outcome=st.text_input('Outcome tracking','Pending')
        if st.form_submit_button('Save intervention update'):
            conn.execute('UPDATE interventions SET status=?,message=?,notes=?,due_date=?,outcome=?,updated_by=?,updated_at=? WHERE batch_id=? AND student_id=?',(status,msg,notes,str(due),outcome,user['email'],datetime.utcnow().isoformat(),batch,r.student_id)); conn.commit(); log_event(conn,user,'intervention update','student',sid,status); st.success('Saved and audited.')
elif page=='Model & Equity Monitor':
    st.header('Model & Equity Monitor'); meta=pd.read_sql_query('SELECT * FROM model_metadata ORDER BY id DESC LIMIT 1',conn); st.dataframe(meta); st.caption('Threshold is selected to prioritize recall and reduce false negatives. Drift placeholders compare current feature and score distributions between upload batches. Equity review is aggregate-first to identify blind spots without unnecessary identity exposure.'); st.plotly_chart(viz.risk_by_class(scored), use_container_width=True)
else:
    st.header('Audit & Privacy'); st.write(f"Current user: {user['email']} ({user['role']})"); st.json(ENCRYPTION_READY); st.caption('Student identifiers are salted SHA-256 pseudonyms. Production should move secrets to a vault, enable database encryption, and use PostgreSQL/object storage adapters.'); st.dataframe(pd.DataFrame([dict(x) for x in get_audit_logs(conn)]))
