from fastapi import APIRouter, Request, HTTPException
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from ..config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

oauth = OAuth()

if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
else:
    logger.warning("Google credentials not found. OAuth will not work.")

@router.get('/login')
async def login(request: Request):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google authentication is not configured.")
    
    # Determine redirect URI based on current host
    # For local dev: http://localhost:8000/auth/callback
    # For production: https://en-claro.onrender.com/auth/callback
    
    redirect_uri = request.url_for('auth_callback')
    
    # Robustly force HTTPS on Render
    # Render sets 'RENDER' env var, but checking domain is also safe
    if 'onrender.com' in str(redirect_uri) or settings.RENDER:
        redirect_uri = str(redirect_uri).replace('http://', 'https://')

    logger.info(f"redirect_uri: {redirect_uri}")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get('/callback')
async def auth_callback(request: Request):
    try:
        # Determine redirect URI (same logic as login)
        redirect_uri = request.url_for('auth_callback')
        if 'onrender.com' in str(redirect_uri) or settings.RENDER:
            redirect_uri = str(redirect_uri).replace('http://', 'https://')
            
        token = await oauth.google.authorize_access_token(request, redirect_uri=redirect_uri)
        user_info = token.get('userinfo')
        if not user_info:
             # Sometimes userinfo is inside 'id_token' claims
             user_info = token.get('user_info') or token.get('id_token')

        if user_info:
            request.session['user'] = dict(user_info)
            logger.info(f"User logged in: {user_info.get('email')}")
        
        # Redirect to frontend with a success flag
        # Ideally, we verify session on frontend. simple redirect to root for now.
        return RedirectResponse(url='/')
    except Exception as e:
        logger.error(f"Error during Google callback: {str(e)}")
        # Redirect to home with error details
        return RedirectResponse(url=f'/?error={str(e)}')

@router.get('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@router.get('/me')
async def get_current_user(request: Request):
    user = request.session.get('user')
    if user:
        return user
    return None
