"""Tests for app/core/security.py"""

from __future__ import annotations

import time
from unittest import mock

import jwt
import pytest

from app.core.security import (
    RateLimiter,
    SecuritySettings,
    rate_limiter,
    security_settings,
    verify_jwt_token,
)


class TestSecuritySettings:
    """Tests for SecuritySettings configuration."""

    def test_default_values(self):
        """Vérifie les valeurs par défaut du modèle."""
        settings = SecuritySettings()
        assert settings.jwt_secret_key == "super-secret-key-change-in-production"
        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_expiration_minutes == 30
        assert settings.rate_limit_requests == 100
        assert settings.rate_limit_window_seconds == 60
        assert settings.allowed_origins == ["*"]

    @mock.patch.dict(
        "os.environ",
        {
            "JWT_SECRET_KEY": "custom-secret",
            "JWT_ALGORITHM": "HS512",
            "JWT_EXPIRATION_MINUTES": "60",
            "RATE_LIMIT_REQUESTS": "200",
            "RATE_LIMIT_WINDOW_SECONDS": "120",
            "ALLOWED_ORIGINS": '["https://example.com"]',
        },
    )
    def test_env_override(self):
        """Vérifie que les variables d'environnement surchargent les défauts."""
        settings = SecuritySettings()
        assert settings.jwt_secret_key == "custom-secret"
        assert settings.jwt_algorithm == "HS512"
        assert settings.jwt_expiration_minutes == 60
        assert settings.rate_limit_requests == 200
        assert settings.rate_limit_window_seconds == 120
        assert settings.allowed_origins == ["https://example.com"]

    def test_singleton_instance_exists(self):
        """Vérifie que l'instance globale est bien un SecuritySettings."""
        assert isinstance(security_settings, SecuritySettings)
        assert hasattr(security_settings, "jwt_secret_key")


class TestRateLimiter:
    """Tests pour le RateLimiter avec sliding window."""

    def test_initialization_default(self):
        """Vérifie les valeurs par défaut du RateLimiter."""
        rl = RateLimiter()
        assert rl.max_requests == 100
        assert rl.window_seconds == 60
        assert rl.requests == {}

    def test_initialization_custom(self):
        """Vérifie l'initialisation avec des valeurs personnalisées."""
        rl = RateLimiter(max_requests=10, window_seconds=5)
        assert rl.max_requests == 10
        assert rl.window_seconds == 5

    def test_check_first_request_allowed(self):
        """Vérifie qu'une première requête est autorisée."""
        rl = RateLimiter(max_requests=5, window_seconds=60)
        assert rl.check("192.168.1.1") is True

    def test_check_multiple_requests_under_limit(self):
        """Vérifie que les requêtes sous la limite sont autorisées."""
        rl = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert rl.check("192.168.1.1") is True

    def test_check_exceeds_limit(self):
        """Vérifie que les requêtes au-delà de la limite sont refusées."""
        rl = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            rl.check("192.168.1.1")
        assert rl.check("192.168.1.1") is False

    def test_different_ips_independent_limits(self):
        """Vérifie que chaque IP a son propre compteur."""
        rl = RateLimiter(max_requests=2, window_seconds=60)
        assert rl.check("IP-A") is True
        assert rl.check("IP-A") is True
        assert rl.check("IP-A") is False  # IP-A a atteint la limite

        assert rl.check("IP-B") is True  # IP-B est encore libre
        assert rl.check("IP-B") is True
        assert rl.check("IP-B") is False  # IP-B a atteint la limite

    def test_window_sliding_allows_after_expiry(self):
        """Vérifie que les requêtes sont à nouveau autorisées après la fenêtre."""
        rl = RateLimiter(max_requests=1, window_seconds=1)

        assert rl.check("192.168.1.1") is True  # 1ère requête à t=0
        assert rl.check("192.168.1.1") is False  # Refusé, limite atteinte

        # Simuler l'attente de la fenêtre
        with mock.patch("time.time", return_value=time.time() + 2):
            assert rl.check("192.168.1.1") is True  # À nouveau autorisé

    def test_cleanup_expired_timestamps(self):
        """Vérifie que les timestamps expirés sont nettoyés."""
    rl = RateLimiter(max_requests=2, window_seconds=10)
    fixed_now = 1000.0

    with mock.patch("time.time", return_value=fixed_now):
        rl.check("IP-A")  # timestamp à 1000

    with mock.patch("time.time", return_value=fixed_now + 5):
        rl.check("IP-A")  # timestamp à 1005

    # À t=1011 : fenêtre [1001, 1011]
    #   1000 ≤ 1001 → expiré, nettoyé
    #   1005 > 1001 → conservé
    with mock.patch("time.time", return_value=fixed_now + 11):
        # 1er appel : nettoie 1000, garde 1005, ajoute 1011 → [1005, 1011]
        assert rl.check("IP-A") is True   # 1 requête < 2

        # 2e appel  : [1005, 1011] → 2 requêtes >= 2 → refusé
        assert rl.check("IP-A") is False  # Limite atteinte

        # Vérifie que le timestamp expiré (1000) a bien été supprimé
        assert len(rl.requests["IP-A"]) == 2


    def test_global_rate_limiter_instance(self):
        """Vérifie que l'instance globale rate_limiter est bien un RateLimiter."""
        assert isinstance(rate_limiter, RateLimiter)
        assert rate_limiter.max_requests == security_settings.rate_limit_requests
        assert rate_limiter.window_seconds == security_settings.rate_limit_window_seconds


class TestVerifyJwtToken:
    """Tests pour la fonction verify_jwt_token()."""

    VALID_PAYLOAD = {"sub": "user-123", "role": "admin"}

    def _create_token(self, payload: dict | None = None, secret: str | None = None,
                      algorithm: str | None = None, expire: bool = False) -> str:
        """Helper pour créer un token JWT de test."""
        pld = dict(payload or self.VALID_PAYLOAD)
        if expire:
            pld["exp"] = int(time.time()) - 3600  # expiré il y a 1h
        else:
            pld["exp"] = int(time.time()) + 3600  # expire dans 1h

        return jwt.encode(
            pld,
            secret or security_settings.jwt_secret_key,
            algorithm=algorithm or security_settings.jwt_algorithm,
        )

    def test_verify_valid_token(self):
        """Vérifie qu'un token valide retourne le payload."""
        token = self._create_token()
        result = verify_jwt_token(token)
        assert result is not None
        assert result["sub"] == "user-123"
        assert result["role"] == "admin"
        assert "exp" in result

        @mock.patch(
            "app.core.security.security_settings.jwt_secret_key",
            "another-secret-key-that-is-long-enough-123456",   # 45 octets, ≥ 32
        )
        def test_verify_wrong_secret(self):
            """Vérifie qu'un token signé avec un mauvais secret retourne None."""
            token = self._create_token(secret="different-secret-key-that-is-long-enough-654321")
            result = verify_jwt_token(token)
            assert result is None


    
        

    def test_verify_expired_token(self):
        """Vérifie qu'un token expiré retourne None."""
        token = self._create_token(expire=True)
        result = verify_jwt_token(token)
        assert result is None

    def test_verify_malformed_token(self):
        """Vérifie qu'un token malformé retourne None."""
        result = verify_jwt_token("not.a.jwt")
        assert result is None

    def test_verify_empty_token(self):
        """Vérifie qu'un token vide retourne None."""
        result = verify_jwt_token("")
        assert result is None

    def test_verify_none_token(self):
        """Vérifie que None comme token retourne None."""
        result = verify_jwt_token(None)  # type: ignore[arg-type]
        assert result is None

    def test_verify_token_with_extra_claims(self):
        """Vérifie qu'un token avec des claims supplémentaires fonctionne."""
        payload = {"sub": "candidate-456", "role": "viewer", "department": "engineering"}
        token = self._create_token(payload=payload)
        result = verify_jwt_token(token)
        assert result is not None
        assert result["department"] == "engineering"

    @mock.patch("jwt.decode", side_effect=jwt.PyJWTError("Unexpected error"))
    def test_verify_jwt_decode_raises_pyjwterror(self, mock_decode):
        """Vérifie que toute PyJWTError renvoie None."""
        result = verify_jwt_token("some-token")
        assert result is None


class TestSecuritySettingsEdgeCases:
    """Tests aux limites pour SecuritySettings."""

    def test_allowed_origins_empty_list(self):
        """Vérifie qu'une liste d'origins vide est acceptée."""
        settings = SecuritySettings(allowed_origins=[])
        assert settings.allowed_origins == []

    def test_jwt_expiration_zero(self):
        """Vérifie qu'une expiration à 0 est acceptée (token immédiatement expiré)."""
        settings = SecuritySettings(jwt_expiration_minutes=0)
        assert settings.jwt_expiration_minutes == 0

    def test_rate_limit_zero(self):
        """Vérifie qu'un rate limit à 0 bloque toutes les requêtes."""
        rl = RateLimiter(max_requests=0, window_seconds=60)
        assert rl.check("192.168.1.1") is False


class TestRateLimiterEdgeCases:
    """Tests aux limites pour RateLimiter."""

    def test_large_window(self):
        """Vérifie qu'une grande fenêtre fonctionne."""
        rl = RateLimiter(max_requests=1000, window_seconds=86400)  # 24h
        for _ in range(1000):
            assert rl.check("IP-A") is True
        assert rl.check("IP-A") is False

    def test_zero_window(self):
        """Vérifie qu'une fenêtre de 0 seconde expire immédiatement."""
        rl = RateLimiter(max_requests=1, window_seconds=0)
        assert rl.check("IP-A") is True

        with mock.patch("time.time", return_value=time.time() + 1):
            assert rl.check("IP-A") is True  # Fenêtre de 0, donc aucun timestamp retenu

    def test_many_ips_no_interference(self):
        """Vérifie qu'un grand nombre d'IP ne s'affectent pas mutuellement."""
        rl = RateLimiter(max_requests=1, window_seconds=60)
        for i in range(100):
            ip = f"192.168.1.{i}"
            assert rl.check(ip) is True, f"Échec pour {ip} à la 1ère requête"
            assert rl.check(ip) is False, f"Échec pour {ip} à la 2ème requête"

    def test_request_dict_structure(self):
        """Vérifie la structure interne du dictionnaire requests."""
        rl = RateLimiter(max_requests=3, window_seconds=60)
        rl.check("IP-A")
        rl.check("IP-B")
        assert "IP-A" in rl.requests
        assert "IP-B" in rl.requests
        assert isinstance(rl.requests["IP-A"], list)
        assert all(isinstance(t, float) for t in rl.requests["IP-A"])
