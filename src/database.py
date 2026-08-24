import json, sqlite3
from datetime import datetime
from pathlib import Path
from .config import DB_PATH

def connect(path: Path = DB_PATH):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS upload_batches(id INTEGER PRIMARY KEY, school_id TEXT, source TEXT, created_at TEXT, summary TEXT);
    CREATE TABLE IF NOT EXISTS students(student_id TEXT PRIMARY KEY, pseudonym_id TEXT, student_name TEXT, class_name TEXT, section TEXT, school_id TEXT);
    CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY, batch_id INTEGER, student_id TEXT, student_name TEXT, class_name TEXT, section TEXT, date TEXT, status TEXT, is_present INTEGER);
    CREATE TABLE IF NOT EXISTS marks(id INTEGER PRIMARY KEY, batch_id INTEGER, student_id TEXT, student_name TEXT, class_name TEXT, section TEXT, date TEXT, subject TEXT, marks REAL, max_marks REAL, term TEXT);
    CREATE TABLE IF NOT EXISTS risk_scores(id INTEGER PRIMARY KEY, batch_id INTEGER, student_id TEXT, pseudonym_id TEXT, risk_score REAL, urgency TEXT, reason TEXT, features_json TEXT, model_version TEXT, score_delta REAL, created_at TEXT);
    CREATE TABLE IF NOT EXISTS shap_explanations(id INTEGER PRIMARY KEY, batch_id INTEGER, student_id TEXT, top_drivers_json TEXT, explanation TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS interventions(id INTEGER PRIMARY KEY, batch_id INTEGER, student_id TEXT, pseudonym_id TEXT, status TEXT, message TEXT, notes TEXT, due_date TEXT, outcome TEXT, updated_by TEXT, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY, ts TEXT, user_email TEXT, role TEXT, action TEXT, entity_type TEXT, entity_id TEXT, details TEXT);
    CREATE TABLE IF NOT EXISTS model_metadata(id INTEGER PRIMARY KEY, model_version TEXT, trained_at TEXT, feature_list TEXT, calibration_status TEXT, threshold REAL, metrics_json TEXT);
    '''); conn.commit()

def insert_batch(conn, school_id, source, summary):
    cur = conn.execute("INSERT INTO upload_batches(school_id,source,created_at,summary) VALUES(?,?,?,?)", (school_id, source, datetime.utcnow().isoformat(), json.dumps(summary)))
    conn.commit(); return cur.lastrowid

def latest_batch_id(conn):
    row = conn.execute("SELECT id FROM upload_batches ORDER BY id DESC LIMIT 1").fetchone(); return row[0] if row else None
