from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.config import settings
from backend.app.services.auth_service import AuthService
from backend.app.schemas.auth import (
    AuthUrlResponse,
    UserResponse,
    AuthStatusResponse,
    LogoutResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.get("/github/login", response_model=AuthUrlResponse)
async def github_login(auth_service: AuthService = Depends(get_auth_service)):
    """Initiate GitHub OAuth login flow."""
    state = auth_service.get_authorization_url()
    # Extract state from URL
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(state)
    state_param = parse_qs(parsed.query).get("state", [""])[0]

    return AuthUrlResponse(url=state, state=state_param)


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str | None = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Handle GitHub OAuth callback."""
    try:
        # Exchange code for tokens
        token_data = await auth_service.exchange_code_for_tokens(code, state)

        # Get GitHub user info
        github_user = await auth_service.get_github_user(token_data["access_token"])

        # Get user emails
        emails = await auth_service.get_user_emails(token_data["access_token"])

        # Find or create user
        user = auth_service.find_or_create_user(github_user, emails)

        # Store tokens
        auth_service.store_tokens(user, token_data)

        # Redirect to frontend with success
        frontend_url = settings.frontend_url
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?success=true&user_id={user.id}"
        )

    except Exception as e:
        # Redirect to frontend with error
        frontend_url = settings.frontend_url
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?success=false&error={str(e)}"
        )


@router.get("/me", response_model=AuthStatusResponse)
async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current authenticated user from session."""
    # For now, check for user_id in query params or headers
    # In production, use proper session/JWT
    user_id = request.headers.get("X-User-ID") or request.query_params.get("user_id")

    if not user_id:
        return AuthStatusResponse(authenticated=False)

    # Get valid token to verify user is still authenticated
    token = auth_service.get_valid_access_token(user_id)
    if not token:
        return AuthStatusResponse(authenticated=False)

    user = auth_service.db.query(auth_service.db.query.__self__.__class__.__module__)

    # Re-query user
    from backend.app.models.user import User

    user = auth_service.db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        return AuthStatusResponse(authenticated=False)

    return AuthStatusResponse(
        authenticated=True,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout user and revoke tokens."""
    user_id = request.headers.get("X-User-ID") or request.query_params.get("user_id")

    if user_id:
        auth_service.revoke_tokens(user_id)

    return LogoutResponse(success=True, message="Logged out successfully")