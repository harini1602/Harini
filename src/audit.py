from datetime import datetime

def log_event(conn, user, action, entity_type="system", entity_id="", details=""):
    conn.execute("INSERT INTO audit_logs(ts,user_email,role,action,entity_type,entity_id,details) VALUES(?,?,?,?,?,?,?)", (datetime.utcnow().isoformat(), user.get('email','anonymous'), user.get('role',''), action, entity_type, str(entity_id), details))
    conn.commit()

def get_audit_logs(conn, limit=200):
    return conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
