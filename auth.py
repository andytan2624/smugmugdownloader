import os
import sys

import requests
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv

load_dotenv()

REQUEST_TOKEN_URL = 'https://api.smugmug.com/services/oauth/1.0a/getRequestToken'
AUTHORIZE_URL    = 'https://api.smugmug.com/services/oauth/1.0a/authorize'
ACCESS_TOKEN_URL = 'https://api.smugmug.com/services/oauth/1.0a/getAccessToken'


def get_session():
    api_key    = os.getenv('SMUGMUG_API_KEY')
    api_secret = os.getenv('SMUGMUG_API_SECRET')

    if not api_key or not api_secret:
        print("Error: SMUGMUG_API_KEY and SMUGMUG_API_SECRET must be set in .env")
        print("Copy .env.example → .env and fill in your credentials.")
        sys.exit(1)

    access_token  = os.getenv('SMUGMUG_ACCESS_TOKEN')
    access_secret = os.getenv('SMUGMUG_ACCESS_SECRET')

    if access_token and access_secret:
        return OAuth1Session(api_key, api_secret, access_token, access_secret)

    # API-key-only fallback (works for public albums)
    session = requests.Session()
    session.params = {'APIKey': api_key}
    return session


def run_oauth_flow():
    api_key    = os.getenv('SMUGMUG_API_KEY')
    api_secret = os.getenv('SMUGMUG_API_SECRET')

    if not api_key or not api_secret:
        print("Error: Set SMUGMUG_API_KEY and SMUGMUG_API_SECRET in .env first.")
        sys.exit(1)

    oauth = OAuth1Session(api_key, api_secret, callback_uri='oob')

    print("Requesting token from SmugMug...")
    resp = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    request_token  = resp['oauth_token']
    request_secret = resp['oauth_token_secret']

    auth_url = f"{AUTHORIZE_URL}?oauth_token={request_token}&Access=Full&Permissions=Read"
    print(f"\n1. Open this URL in your browser:\n   {auth_url}\n")
    print("2. Click 'Allow' to grant access.")
    verifier = input("3. Paste the 6-digit verifier code shown by SmugMug: ").strip()

    oauth = OAuth1Session(
        api_key, api_secret,
        request_token, request_secret,
        verifier=verifier,
    )
    tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)

    print("\nSuccess! Add these two lines to your .env file:\n")
    print(f"SMUGMUG_ACCESS_TOKEN={tokens['oauth_token']}")
    print(f"SMUGMUG_ACCESS_SECRET={tokens['oauth_token_secret']}")
