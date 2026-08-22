import json
import os
import webbrowser
from urllib.parse import parse_qs, urlparse
import requests
from pathlib import Path


class FyersAuth:
    """OAuth Authentication & Token Manager for Fyers API v3"""

    CONFIG_FILE = "config.json"

    def __init__(self, config_file=None):
        self.config_file = config_file or self.CONFIG_FILE
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)

        return {
            'app_id': '',
            'secret_key': '',
            'redirect_uri': 'https://www.google.com/',
            'access_token': '',
            'use_mock_feed': False,
            'host': '127.0.0.1',
            'port': 8000
        }

    def save_config(self):
        """Save configuration to JSON file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def set_credentials(self, app_id, secret_key, redirect_uri=None):
        """Set API credentials"""
        self.config['app_id'] = app_id
        self.config['secret_key'] = secret_key
        if redirect_uri:
            self.config['redirect_uri'] = redirect_uri
        self.save_config()

    def get_oauth_url(self):
        """Generate OAuth login URL"""
        app_id = self.config.get('app_id', '')
        redirect_uri = self.config.get('redirect_uri', '')
        state = 'volhedge_pro'

        oauth_url = f"https://api-t2.fyers.in/api/v3/auth/login?client_id={app_id}&redirect_uri={redirect_uri}&state={state}&response_type=code"
        return oauth_url

    def open_oauth_login(self):
        """Open browser for OAuth login"""
        oauth_url = self.get_oauth_url()
        webbrowser.open(oauth_url)
        return oauth_url

    def extract_auth_code(self, callback_url):
        """Extract auth code from callback URL"""
        try:
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)
            auth_code = params.get('auth_code', [None])[0]
            return auth_code
        except:
            return None

    def exchange_code_for_token(self, auth_code):
        """Exchange auth code for access token"""
        try:
            url = "https://api-t2.fyers.in/api/v3/auth/token"
            payload = {
                "client_id": self.config['app_id'],
                "client_secret": self.config['secret_key'],
                "code": auth_code,
                "grant_type": "authorization_code",
                "state": "volhedge_pro"
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token', '')
                self.config['access_token'] = access_token
                self.save_config()
                return access_token
            else:
                return None
        except Exception as e:
            print(f"Error exchanging code: {e}")
            return None

    def get_access_token(self):
        """Get current access token"""
        return self.config.get('access_token', '')

    def is_authenticated(self):
        """Check if access token exists"""
        return bool(self.get_access_token())

    def renew_token(self):
        """Placeholder for token renewal (Fyers tokens expire daily)"""
        return self.is_authenticated()

    def interactive_token_generation(self):
        """Interactive flow to generate and save token"""
        print("\n=== Fyers API v3 Token Generator ===\n")

        app_id = self.config.get('app_id', '')
        print(f"Saved App ID: {app_id}")
        input("Press Enter to continue...")

        secret_key = self.config.get('secret_key', '')
        print(f"Saved Secret Key: {secret_key}")
        input("Press Enter to proceed with OAuth...")

        print("\nOpening Fyers OAuth login page in browser...")
        self.open_oauth_login()

        callback_url = input("\nEnter the complete redirect URL from browser: ").strip()

        auth_code = self.extract_auth_code(callback_url)

        if not auth_code:
            print("Failed to extract auth code from URL")
            return False

        print("Exchanging auth code for access token...")
        token = self.exchange_code_for_token(auth_code)

        if token:
            print(f"\n✓ Access token saved successfully!")
            print(f"Token: {token[:50]}...")
            return True
        else:
            print("\n✗ Failed to get access token")
            return False
