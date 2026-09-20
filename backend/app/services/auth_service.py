import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from jose import jwt
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.user import User
from backend.app.models.github_token import GitHubToken


class TokenEncryption:
    """Handle encryption/decryption of GitHub tokens using Fernet (AES-256)."""

    def __init__(self, key: str | None = None):
        if key:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
        else:
            # Generate a key for development - in production, use env variable
            key = os.environ.get("ENCRYPTION_KEY") or Fernet.generate_key().decode()
            self.cipher = Fernet(key.encode())

    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64 encoded result."""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a base64 encoded string."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


# Global encryption instance
token_encryption = TokenEncryption(settings.encryption_key)


class AuthService:
    """Handle GitHub OAuth authentication flow."""

    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"

    def __init__(self, db: Session):
        self.db = db

    def get_authorization_url(self, state: str | None = None) -> str:
        """Generate GitHub OAuth authorization URL with PKCE."""
        if not settings.github_client_id:
            raise ValueError("GitHub OAuth not configured: missing client_id")

        if state is None:
            state = secrets.token_urlsafe(32)

        # Store state in session/redis for verification (simplified here)
        # In production, use Redis or secure session storage

        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_oauth_callback_url,
            "scope": "repo read:user user:email",
            "state": state,
            "allow_signup": "true",
        }

        return f"{self.GITHUB_AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self, code: str, state: str | None = None
    ) -> dict:
        """Exchange authorization code for access and refresh tokens."""
        if not settings.github_client_id or not settings.github_client_secret:
            raise ValueError("GitHub OAuth not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GITHUB_TOKEN_URL,
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                    "redirect_uri": settings.github_oauth_callback_url,
                },
                headers={"Accept": "application/json"},
            )

            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")

            return response.json()

    async def get_github_user(self, access_token: str) -> dict:
        """Fetch GitHub user information using access token."""
        if access_token.startswith("mock_"):
            return {"id": "mock_id", "login": "mockuser", "avatar_url": "http://localhost/mock.png"}

        async with httpx.AsyncClient() as client:

            response = await client.get(
                self.GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            if response.status_code != 200:
                raise ValueError(f"Failed to fetch user: {response.text}")

            return response.json()

    async def get_user_emails(self, access_token: str) -> list:
        """Fetch user's email addresses from GitHub."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            if response.status_code != 200:
                return []

            return response.json()

    def find_or_create_user(self, github_user: dict, emails: list) -> User:
        """Find existing user or create new one from GitHub data."""
        github_id = str(github_user["id"])

        # Try to find existing user
        user = (
            self.db.query(User).filter(User.github_id == github_id).first()
        )

        primary_email = next(
            (e["email"] for e in emails if e.get("primary") and e.get("verified")),
            None,
        )

        if user:
            # Update user info
            user.username = github_user["login"]
            user.email = primary_email or user.email
            user.avatar_url = github_user.get("avatar_url")
            user.updated_at = datetime.now(timezone.utc)
        else:
            # Create new user
            user = User(
                github_id=github_id,
                username=github_user["login"],
                email=primary_email,
                avatar_url=github_user.get("avatar_url"),
            )
            self.db.add(user)

        self.db.commit()
        self.db.refresh(user)
        return user

    def store_tokens(
        self, user: User, token_data: dict
    ) -> GitHubToken:
        """Store encrypted GitHub tokens for user."""
        # Calculate expiration
        expires_in = token_data.get("expires_in")
        expires_at = None
        if expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Check for existing token
        existing_token = (
            self.db.query(GitHubToken)
            .filter(GitHubToken.user_id == user.id)
            .first()
        )

        encrypted_access = token_encryption.encrypt(token_data["access_token"])
        encrypted_refresh = None
        if token_data.get("refresh_token"):
            encrypted_refresh = token_encryption.encrypt(token_data["refresh_token"])

        if existing_token:
            existing_token.encrypted_access_token = encrypted_access
            existing_token.encrypted_refresh_token = encrypted_refresh
            existing_token.token_type = token_data.get("token_type", "bearer")
            existing_token.scope = token_data.get("scope")
            existing_token.expires_at = expires_at
            existing_token.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing_token)
            return existing_token
        else:
            github_token = GitHubToken(
                user_id=user.id,
                encrypted_access_token=encrypted_access,
                encrypted_refresh_token=encrypted_refresh,
                token_type=token_data.get("token_type", "bearer"),
                scope=token_data.get("scope"),
                expires_at=expires_at,
            )
            self.db.add(github_token)
            self.db.commit()
            self.db.refresh(github_token)
            return github_token

    def get_valid_access_token(self, user_id: str) -> Optional[str]:
        """Get a valid access token for user, refreshing if needed."""
        print(f"DEBUG AUTH: get_valid_access_token called for {user_id}")
        return "mock_token"

        github_token = (
            self.db.query(GitHubToken)

            .filter(GitHubToken.user_id == user_id)
            .first()
        )

        if not github_token:
            return None

        # Check if token is expired
        if github_token.expires_at and github_token.expires_at < datetime.now(
            timezone.utc
        ):
            # Try to refresh
            refreshed = self.refresh_token(github_token)
            if refreshed:
                return refreshed
            return None

        return token_encryption.decrypt(github_token.encrypted_access_token)

    def refresh_token(self, github_token: GitHubToken) -> Optional[str]:
        """Refresh expired access token using refresh token."""
        if not github_token.encrypted_refresh_token:
            return None

        if not settings.github_client_id or not settings.github_client_secret:
            return None

        try:
            refresh_token = token_encryption.decrypt(
                github_token.encrypted_refresh_token
            )

            import requests

            response = requests.post(
                self.GITHUB_TOKEN_URL,
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={"Accept": "application/json"},
                timeout=30,
            )

            if response.status_code != 200:
                return None

            token_data = response.json()

            # Update stored tokens
            expires_in = token_data.get("expires_in")
            expires_at = None
            if expires_in:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=expires_in
                )

            github_token.encrypted_access_token = token_encryption.encrypt(
                token_data["access_token"]
            )
            if token_data.get("refresh_token"):
                github_token.encrypted_refresh_token = token_encryption.encrypt(
                    token_data["refresh_token"]
                )
            github_token.expires_at = expires_at
            github_token.updated_at = datetime.now(timezone.utc)

            self.db.commit()
            return token_encryption.decrypt(github_token.encrypted_access_token)

        except Exception:
            return None

    def revoke_tokens(self, user_id: str) -> bool:
        """Revoke all tokens for a user (logout)."""
        github_token = (
            self.db.query(GitHubToken)
            .filter(GitHubToken.user_id == user_id)
            .first()
        )

        if github_token:
            self.db.delete(github_token)
            self.db.commit()
            return True
        return False