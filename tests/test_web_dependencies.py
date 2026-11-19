"""Tests pour app.web.dependencies — alignés sur le code réel."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request, HTTPException, status


@pytest.mark.asyncio
async def test_get_current_user_from_cookie_valid():
    """Token valide → retourne le payload."""
    from app.web.dependencies import get_current_user_from_cookie

    fake_payload = {"sub": "admin", "role": "admin"}

    mock_request = AsyncMock(spec=Request)
    mock_request.cookies.get.return_value = "valid_token"

    with patch("app.web.dependencies.verify_token", return_value=fake_payload):
        result = await get_current_user_from_cookie(mock_request)

    assert result == fake_payload
    mock_request.cookies.get.assert_called_once_with("access_token")


@pytest.mark.asyncio
async def test_get_current_user_from_cookie_no_token():
    """Pas de cookie → lève HTTPException 401."""
    from app.web.dependencies import get_current_user_from_cookie

    mock_request = AsyncMock(spec=Request)
    mock_request.cookies.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        await get_current_user_from_cookie(mock_request)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_from_cookie_invalid_token():
    """Token invalide → lève HTTPException 401."""
    from app.web.dependencies import get_current_user_from_cookie

    mock_request = AsyncMock(spec=Request)
    mock_request.cookies.get.return_value = "invalid_token"

    with patch("app.web.dependencies.verify_token", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await get_current_user_from_cookie(mock_request)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_require_auth_no_token():
    """Pas de cookie access_token → redirection 303 vers /login."""
    from app.web.dependencies import require_auth

    mock_request = AsyncMock(spec=Request)
    mock_request.cookies.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        await require_auth(mock_request)

    assert exc.value.status_code == status.HTTP_303_SEE_OTHER
    assert exc.value.headers["Location"] == "/login"


@pytest.mark.asyncio
async def test_require_auth_invalid_token():
    """Token invalide → redirection 303 vers /login."""
    from app.web.dependencies import require_auth

    mock_request = AsyncMock(spec=Request)
    mock_request.cookies.get.return_value = "bad_token"

    with patch("app.web.dependencies.verify_token", return_value=None):
        with pytest.raises(HTTPException) as exc:
            await require_auth(mock_request)

    assert exc.value.status_code == status.HTTP_303_SEE_OTHER
    assert exc.value.headers["Location"] == "/login"


@pytest.mark.asyncio
async def test_require_auth_valid():
    """Token valide → ne lève pas d'exception."""
    from app.web.dependencies import require_auth

    mock_request = AsyncMock(spec=Request)
    mock_request.cookies.get.return_value = "valid_token"

    with patch("app.web.dependencies.verify_token", return_value={"sub": "admin"}):
        # Ne doit pas lever d'exception
        await require_auth(mock_request)
