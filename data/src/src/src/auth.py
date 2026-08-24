from .config import DEMO_USERS, ROLE_PERMISSIONS

def authenticate(email: str, password: str):
    user = DEMO_USERS.get(email.strip().lower())
    if user and user["password"] == password:
        return {"email": email.strip().lower(), "role": user["role"], "name": user["name"]}
    return None

def can(user: dict, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(user.get("role", ""), set())
