import hashlib
import os
import unittest
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-only-secret-for-password-reset-123456"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.models import PasswordResetToken, User
from app.rate_limit import limiter
from app.routers.auth import router
from app.security import create_access_token, hash_password, verify_password
from app.services.password_reset_email import send_password_reset_email


class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.user = User(
            email="user@example.com",
            full_name="Test User",
            password_hash=hash_password("old-password-123"),
            role="institution",
            is_active=True,
        )
        with self.session_factory() as session:
            session.add(self.user)
            session.commit()
            self.user_id = self.user.id

        self.app = FastAPI()
        self.app.state.limiter = limiter
        self.app.include_router(router)

        def override_get_db():
            with self.session_factory() as session:
                yield session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)
        limiter.reset()
        self.smtp_values = (
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM,
            settings.FRONTEND_BASE_URL,
        )
        settings.SMTP_HOST = "smtp.example.test"
        settings.SMTP_PORT = "587"
        settings.SMTP_USER = ""
        settings.SMTP_PASSWORD = ""
        settings.SMTP_FROM = "support@example.test"
        settings.FRONTEND_BASE_URL = "https://nexora.example.test"

    def tearDown(self):
        (
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM,
            settings.FRONTEND_BASE_URL,
        ) = self.smtp_values
        limiter.reset()
        self.client.close()
        self.engine.dispose()

    def test_forgot_password_sends_a_hashed_single_use_token(self):
        with patch("app.routers.auth.send_password_reset_email") as send_email:
            response = self.client.post(
                "/api/auth/forgot-password",
                json={"email": "user@example.com"},
            )

        self.assertEqual(response.status_code, 202)
        self.assertNotIn("user@example.com", response.text)
        send_email.assert_called_once()
        recipient, reset_url = send_email.call_args.args
        self.assertEqual(recipient, "user@example.com")
        parsed_url = urlparse(reset_url)
        self.assertEqual(parsed_url.scheme, "https")
        self.assertEqual(parsed_url.netloc, "nexora.example.test")
        raw_token = parse_qs(parsed_url.query)["token"][0]

        with self.session_factory() as session:
            stored_token = session.query(PasswordResetToken).one()
            self.assertNotEqual(stored_token.token_hash, raw_token)
            self.assertEqual(stored_token.token_hash, hashlib.sha256(raw_token.encode()).hexdigest())
            self.assertEqual(stored_token.user_id, self.user_id)
            self.assertIsNone(stored_token.used_at)

    def test_reset_changes_password_and_cannot_reuse_token(self):
        raw_token = "test-reset-token-" + ("x" * 40)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        old_access_token = create_access_token(
            subject=self.user_id,
            role="institution",
            token_version=0,
        )
        with self.session_factory() as session:
            session.add(PasswordResetToken(
                user_id=self.user_id,
                token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=now + timedelta(minutes=30),
            ))
            session.commit()

        response = self.client.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "new_password": "new-password-456"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Password updated", response.json()["message"])
        with self.session_factory() as session:
            user = session.query(User).filter_by(id=self.user_id).one()
            reset_token = session.query(PasswordResetToken).one()
            self.assertTrue(verify_password("new-password-456", user.password_hash))
            self.assertEqual(user.token_version, 1)
            self.assertIsNotNone(reset_token.used_at)

        revoked_session = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {old_access_token}"},
        )
        self.assertEqual(revoked_session.status_code, 401)

        reuse_response = self.client.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "new_password": "another-password-789"},
        )
        self.assertEqual(reuse_response.status_code, 400)

    def test_expired_reset_token_is_rejected(self):
        raw_token = "expired-reset-token-" + ("y" * 40)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with self.session_factory() as session:
            session.add(PasswordResetToken(
                user_id=self.user_id,
                token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=now - timedelta(seconds=1),
            ))
            session.commit()

        response = self.client.post(
            "/api/auth/reset-password",
            json={"token": raw_token, "new_password": "new-password-456"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("expired", response.json()["detail"])

    def test_unknown_account_gets_same_generic_forgot_response(self):
        with patch("app.routers.auth.send_password_reset_email") as send_email:
            response = self.client.post(
                "/api/auth/forgot-password",
                json={"email": "unknown@example.com"},
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.json()["message"],
            "If an active account matches that email, password reset instructions will be sent.",
        )
        send_email.assert_not_called()

    def test_forgot_password_requires_email_configuration(self):
        settings.SMTP_HOST = ""
        response = self.client.post(
            "/api/auth/forgot-password",
            json={"email": "unknown@example.com"},
        )
        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.json()["detail"])

    def test_forgot_password_is_rate_limited(self):
        with patch("app.routers.auth.send_password_reset_email"):
            responses = [
                self.client.post(
                    "/api/auth/forgot-password",
                    json={"email": "unknown@example.com"},
                )
                for _ in range(4)
            ]
        self.assertEqual([response.status_code for response in responses], [202, 202, 202, 429])

    def test_password_reset_endpoint_is_rate_limited(self):
        response_codes = [
            self.client.post(
                "/api/auth/reset-password",
                json={
                    "token": "invalid-reset-token-" + ("z" * 40),
                    "new_password": "new-password-456",
                },
            ).status_code
            for _ in range(6)
        ]
        self.assertEqual(response_codes, [400, 400, 400, 400, 400, 429])

    @patch("app.services.password_reset_email.smtplib.SMTP")
    def test_reset_email_uses_starttls_and_sends_reset_link(self, smtp):
        server = smtp.return_value.__enter__.return_value

        send_password_reset_email(
            "user@example.com",
            "https://nexora.example.test/reset-password?token=sample",
        )

        server.starttls.assert_called_once()
        server.send_message.assert_called_once()
        message = server.send_message.call_args.args[0]
        self.assertEqual(message["To"], "user@example.com")
        self.assertIn("https://nexora.example.test/reset-password?token=sample", message.get_content())


if __name__ == "__main__":
    unittest.main()
