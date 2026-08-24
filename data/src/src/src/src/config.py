from pathlib import Path
import os
APP_NAME = "Drop-Out Early-Warning Copilot"
TAGLINE = "Predict • Explain • Intervene — before absence becomes dropout"
DATA_DIR = Path(os.getenv("DROPOUT_DATA_DIR", ".data")); DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "dropout_copilot.sqlite3"
PSEUDONYM_SALT = os.getenv("DROPOUT_PSEUDONYM_SALT", "demo-only-change-in-production")
ENCRYPTION_READY = {"database_encryption": os.getenv("DATABASE_ENCRYPTION_KEY", "configure-in-production"), "object_storage": os.getenv("OBJECT_STORAGE_URL", "local-sqlite-default")}
PASS_MARK = 40.0
RECENT_DAYS = 30
DEMO_USERS = {
    "teacher@demo.school": {"password": "teacher123", "role": "teacher", "name": "Ms. Rivera"},
    "leader@demo.school": {"password": "leader123", "role": "school_leader", "name": "Principal Chen"},
    "admin@demo.school": {"password": "admin123", "role": "admin", "name": "System Admin"},
}
ROLE_PERMISSIONS = {
    "teacher": {"upload", "score", "view_assigned", "edit_interventions", "export"},
    "school_leader": {"view_aggregate", "view_details", "export"},
    "admin": {"upload", "score", "view_assigned", "view_aggregate", "view_details", "edit_interventions", "audit", "reveal_identity", "export"},
}
