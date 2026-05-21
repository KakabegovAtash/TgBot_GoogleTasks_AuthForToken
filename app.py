import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google_auth_oauthlib.flow import Flow
from starlette.middleware.sessions import SessionMiddleware

# Load environment variables
load_dotenv()

app = FastAPI()

# Add session middleware for OAuth state
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "fallback-insecure-key-change-me")
)


# Setup templates and static files
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Google OAuth setup
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/login")
async def login(request: Request):
    if not os.path.exists(CLIENT_SECRETS_FILE):
        raise HTTPException(status_code=500, detail="Файл credentials.json не найден. Владелец должен добавить его в папку проекта.")
    
    # We dynamically determine the redirect URI based on the request URL
    # This allows it to work seamlessly with Cloudflare tunnels
    redirect_uri = str(request.url_for("auth_callback")).replace("http://", "https://")
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=redirect_uri
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )
    
    request.session['state'] = state
    request.session['code_verifier'] = flow.code_verifier
    return RedirectResponse(authorization_url)

@app.get("/callback", response_class=HTMLResponse)
async def auth_callback(request: Request):
    state = request.session.get('state')
    
    if not state or state != request.query_params.get('state'):
        return HTMLResponse("Ошибка: несовпадение состояний сессии. Попробуйте снова.", status_code=400)
    
    redirect_uri = str(request.url_for("auth_callback")).replace("http://", "https://")
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state, redirect_uri=redirect_uri
    )
    flow.code_verifier = request.session.get('code_verifier')
    
    authorization_response = str(request.url).replace("http://", "https://")
    
    try:
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        
        # Save the token
        with open('token.json', 'w') as token_file:
            token_file.write(credentials.to_json())
            
        return templates.TemplateResponse(request=request, name="success.html")
    except Exception as e:
        return HTMLResponse(f"Произошла ошибка при получении токена: {str(e)}", status_code=500)
