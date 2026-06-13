import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Google OAuth Scopes for Docs writes and Gmail compose/drafts
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.compose'
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')

def get_google_credentials():
    """
    Retrieves Google OAuth 2.0 credentials.
    Loads from token.json if present, refreshes if expired,
    and falls back to browser redirect flow if needed.
    """
    # Load credentials.json from env if available
    if "GOOGLE_CREDENTIALS_JSON" in os.environ and not os.path.exists(CREDENTIALS_PATH):
        try:
            with open(CREDENTIALS_PATH, "w") as f:
                f.write(os.environ["GOOGLE_CREDENTIALS_JSON"])
            print("Successfully populated credentials.json from env.")
        except Exception as e:
            print(f"Error writing credentials.json: {e}")
            
    # Load token.json from env if available
    if "GOOGLE_TOKEN_JSON" in os.environ and not os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, "w") as f:
                f.write(os.environ["GOOGLE_TOKEN_JSON"])
            print("Successfully populated token.json from env.")
        except Exception as e:
            print(f"Error writing token.json: {e}")

    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            print(f"Error loading existing token.json: {e}. Re-authenticating.")
            creds = None
            
    # Authenticate or refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired Google credentials token...")
                creds.refresh(Request())
                with open(TOKEN_PATH, 'w') as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                print(f"Token refresh failed: {e}. Forcing interactive login.")
                if os.path.exists(TOKEN_PATH):
                    os.remove(TOKEN_PATH)
                creds = None
                
        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"\n[Error] Google Cloud credentials file not found at: {CREDENTIALS_PATH}\n"
                    "Please download OAuth 2.0 Desktop Client credentials from the Google Cloud Console "
                    "and place them in the google-mcp-server/ folder as 'credentials.json'."
                )
            print("No valid credentials found. Launching browser for Google OAuth login...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save token
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
            print(f"Successfully authenticated and saved token.json to {TOKEN_PATH}")
            
    return creds
