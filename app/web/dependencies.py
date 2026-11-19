import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from app.core.config import settings

templates = Jinja2Templates(directory="app/web/templates")

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM

def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

async def require_auth(request: Request):
    print(f"\n[DEBUG require_auth] cookies: {dict(request.cookies)}")
    print(f"[DEBUG require_auth] token: {request.cookies.get('access_token')}")
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER,
                            headers={"Location": "/login"})
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER,
                            headers={"Location": "/login"})

print('[DEBUG MODULE] dependencies.py loaded')

async def get_current_user_from_cookie(request: Request) -> dict:
    """Extract and verify JWT from the access_token cookie."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = verify_token(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Correction de la fonction pour gérer le retour None de verify_token
def get_current_user_from_cookie_sync(request: Request) -> dict:
    """Extract and verify JWT from the access_token cookie (sync version)."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

async def get_current_user_from_cookie(request: Request) -> dict:
    """Async wrapper for get_current_user_from_cookie_sync."""
    return get_current_user_from_cookie_sync(request)
