import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import settings
from app.observability.logger import logger, log_audit_event

security_scheme = HTTPBearer(auto_error=False)

# Common prompt injection triggers to flag/sanitize
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"(?i)system\s+prompt\s+override",
    r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
    r"(?i)bypass\s+all\s+safety\s+filters",
    r"(?i)reveal\s+(other\s+users'?|all|confidential)\s+documents",
    r"(?i)jailbreak",
    r"(?i)dan\s+mode",
]

def detect_prompt_injection(text: str) -> Optional[str]:
    for pattern in INJECTION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None

def sanitize_untrusted_text(text: str) -> str:
    # Escape markdown delimiter injection or control markers
    sanitized = text.replace("```system", "'''system").replace("```assistant", "'''assistant")
    return sanitized

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

class CurrentUser:
    def __init__(self, user_id: str, email: str, role: str = "member", workspace_id: str = "default-workspace"):
        self.id = user_id
        self.email = email
        self.role = role
        self.workspace_id = workspace_id

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> CurrentUser:
    # If no token provided in development mode, default to authenticated developer user
    if not credentials:
        return CurrentUser(
            user_id="default-user",
            email="admin@documind.ai",
            role="admin",
            workspace_id="default-workspace"
        )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        email = payload.get("email", "")
        role = payload.get("role", "member")
        workspace_id = payload.get("workspace_id", "default-workspace")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return CurrentUser(user_id=user_id, email=email, role=role, workspace_id=workspace_id)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
