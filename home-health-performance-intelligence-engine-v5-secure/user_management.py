from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from auth import verify_credentials, USER_CREDENTIALS
import secure_auth

router = APIRouter()

BASE_DIR = __import__('pathlib').Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / 'templates'
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get('/users', include_in_schema=False)
async def list_users(request: Request):
    users = list(USER_CREDENTIALS.keys())
    return templates.TemplateResponse('users.html', {'request': request, 'users': users})

@router.get('/users/add', include_in_schema=False)
async def add_user_form(request: Request):
    return templates.TemplateResponse('add_user.html', {'request': request})

@router.post('/users/add', include_in_schema=False)
async def add_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username in USER_CREDENTIALS:
        return templates.TemplateResponse('add_user.html', {'request': request, 'error': 'User already exists'})
    # Use secure_auth to create user
    import secure_auth
    secure_auth.create_user(username, password)
    return RedirectResponse(url='/users', status_code=status.HTTP_303_SEE_OTHER)

@router.get('/users/delete/{username}', include_in_schema=False)
async def delete_user(request: Request, username: str):
    if username in USER_CREDENTIALS:
        del USER_CREDENTIALS[username]
    return RedirectResponse(url='/users', status_code=status.HTTP_303_SEE_OTHER)

@router.get('/users/login', include_in_schema=False)
async def login_form(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})
