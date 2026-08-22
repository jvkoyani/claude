"""Interactive Fyers API Token Renewal Tool"""

import sys
from fyers_service.auth import FyersAuth


def main():
    """Interactive token generation"""
    print("\n" + "=" * 50)
    print("VolHedge Pro - Fyers API Token Generator")
    print("=" * 50 + "\n")

    auth = FyersAuth()

    if auth.is_authenticated():
        print("✓ Valid access token already saved")
        print(f"  Token: {auth.get_access_token()[:50]}...\n")

        response = input("Do you want to generate a new token? (y/n): ").strip().lower()
        if response != 'y':
            print("Exiting...")
            return

    print("\nStep 1: Verify Credentials")
    print("-" * 50)

    app_id = auth.config.get('app_id', '')
    print(f"Saved App ID: {app_id}")

    if not app_id or input("Update App ID? (y/n): ").strip().lower() == 'y':
        app_id = input("Enter Fyers App ID: ").strip()
        auth.config['app_id'] = app_id

    secret_key = auth.config.get('secret_key', '')
    print(f"Saved Secret Key: {secret_key}")

    if not secret_key or input("Update Secret Key? (y/n): ").strip().lower() == 'y':
        secret_key = input("Enter Fyers Secret Key: ").strip()
        auth.config['secret_key'] = secret_key

    auth.save_config()

    print("\nStep 2: OAuth Login")
    print("-" * 50)
    print("Opening Fyers OAuth login page in your default browser...")
    print("Please authorize the application.\n")

    auth.open_oauth_login()

    print("After authorization, the browser will show the redirect URL")
    print("Example: https://www.google.com/?s=ok&code=200&auth_code=...")

    callback_url = input("\nPaste the complete redirect URL here: ").strip()

    if not callback_url:
        print("No URL provided. Exiting.")
        return

    auth_code = auth.extract_auth_code(callback_url)

    if not auth_code:
        print("✗ Failed to extract auth code from URL")
        print("Make sure you copied the complete URL from the browser address bar")
        return

    print(f"\n✓ Auth code extracted: {auth_code[:30]}...")

    print("\nStep 3: Exchange for Access Token")
    print("-" * 50)
    print("Exchanging auth code for access token...")

    token = auth.exchange_code_for_token(auth_code)

    if token:
        print("\n" + "=" * 50)
        print("✓ SUCCESS!")
        print("=" * 50)
        print(f"Access token: {token[:50]}...")
        print(f"Token saved to config.json\n")
        print("You can now use VolHedge Pro to trade!")
        return True
    else:
        print("\n✗ Failed to get access token")
        print("Please verify your App ID and Secret Key")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
