from src.privacy import pseudonymize
from src.database import connect, init_db
from src.audit import log_event, get_audit_logs

def test_pseudonym_is_stable_and_masks_raw_id():
    assert pseudonymize('S1001') == pseudonymize('S1001')
    assert 'S1001' not in pseudonymize('S1001')

def test_audit_logging_records_sensitive_action(tmp_path):
    conn = connect(tmp_path / 'audit.sqlite3')
    init_db(conn)
    log_event(conn, {'email':'teacher@demo.school','role':'teacher'}, 'scoring', 'batch', '1', 'unit test')
    rows = get_audit_logs(conn)
    assert rows[0]['action'] == 'scoring'
