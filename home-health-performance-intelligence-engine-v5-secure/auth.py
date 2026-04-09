from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request
from starlette.middleware.sessions import SessionMiddleware
import secrets
import hmac
import hashlib
from typing import Optional
import secure_auth
USER_CREDENTIALS = secure_auth.USER_CREDENTIALS

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = secrets.token_hex(32)
SESSION_COOKIE = "session"

# Add session middleware to app in main server file
# app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Simple user verification using secure_auth module
def verify_credentials(username: str, password: str) -> bool:
    return secure_auth.verify_user(username, password)

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not verify_credentials(form_data.username, form_data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    # In real app, generate a JWT or session token. Here use a simple secure cookie.
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(SESSION_COOKIE, form_data.username)
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE)
    return response

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[str]:
    # Simplified for demo: token is username
    # Validate token if implementing JWT
    return token

async def get_authenticated_user(request: Request) -> Optional[str]:
    user = request.cookies.get(SESSION_COOKIE)
    if user and secure_auth.USER_CREDENTIALS.get(user):
        return user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
