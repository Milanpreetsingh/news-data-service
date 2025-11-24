from fastapi import APIRouter, status, Response, Cookie, Depends
from typing import Optional
from app.models.schemas import UserSignup, UserLogin, Token, UserResponse, RefreshToken
from app.core.container import get_container, Container

# Create router for authentication endpoints with /auth prefix
# Tags help organize endpoints in Swagger UI documentation
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup, container: Container = Depends(get_container)):
    """
    User Registration Endpoint
    
    Flow:
    1. Receive email, username, password from client
    2. Validate data using UserSignup schema (Pydantic)
    3. Get auth_service from DI container
    4. Service checks if user exists, hashes password, creates user
    5. Return user data (without password)
    
    No authentication required - public endpoint
    """
    user = await container.auth_service.signup(user_data)
    return user

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin, 
    response: Response,
    container: Container = Depends(get_container)
):
    """
    User Login Endpoint
    
    Flow:
    1. Receive email and password
    2. Get auth_service from DI container
    3. Service validates credentials, generates tokens
    4. Set refresh token in HTTP-only cookie (secure, can't be accessed by JavaScript)
    5. Set Authorization header with access token
    6. Return access token in response body
    
    Returns:
    - Body: {"access_token": "...", "token_type": "bearer"}
    - Cookie: refresh_token (HTTP-only, 7-day expiry)
    - Header: Authorization: Bearer <access_token>
    """
    tokens = await container.auth_service.login(login_data)
    
    # Set refresh token in secure HTTP-only cookie
    # This prevents XSS attacks as JavaScript cannot access it
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,              # Cannot be accessed by JavaScript
        secure=True,                # Only sent over HTTPS (in production)
        samesite="lax",             # CSRF protection
        max_age=7 * 24 * 60 * 60   # 7 days in seconds
    )
    
    # Set Authorization header for easy client extraction
    response.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    
    # Return access token in body (client can use from body or header)
    return {
        "access_token": tokens["access_token"],
        "token_type": tokens["token_type"]
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    container: Container = Depends(get_container)
):
    """
    Token Refresh Endpoint
    
    Flow:
    1. Read refresh_token from HTTP-only cookie (automatically sent by browser)
    2. Validate refresh token (check signature, expiry, user status)
    3. Generate new access token
    4. Return new access token
    
    Use case: When access token expires (24 hours), use this to get a new one
    without asking user to login again. Refresh token is valid for 7 days.
    
    Returns:
    - Body: {"access_token": "...", "token_type": "bearer"}
    - Header: Authorization: Bearer <new_access_token>
    """
    # Check if refresh token cookie exists
    if not refresh_token:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    # Validate refresh token and generate new access token
    tokens = await container.auth_service.refresh_access_token(refresh_token)
    
    # Set new access token in Authorization header
    response.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    
    return tokens

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    """
    Logout Endpoint
    
    Flow:
    1. Delete refresh_token cookie from browser
    2. Client should also discard access token
    
    Note: Access tokens are stateless (JWT), so they remain valid until expiry.
    This endpoint only clears the refresh token to prevent getting new access tokens.
    """
    response.delete_cookie(key="refresh_token")
    return {"message": "Successfully logged out"}

