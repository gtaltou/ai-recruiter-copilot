"""Dépendances pour les routes web (auth via cookie JWT)."""
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from app.core.security import verify_token


async def get_current_user_from_cookie(request: Request) -> dict:
    """Extrait et vérifie le token JWT depuis le cookie 'access_token'."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return payload


async def require_auth(request: Request):
    """Redirige vers /login si non authentifié (pour les pages web)."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER,
                            headers={"Location": "/login"})

    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER,
                            headers={"Location": "/login"})
