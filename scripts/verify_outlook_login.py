from outlook_service import get_access_token
from outlook_accounts import OUTLOOK_ACCOUNTS
import re

def test_oauth_login():
    print("🚀 Testing Outlook OAuth login...")
    
    # Test the first account.
    account = OUTLOOK_ACCOUNTS[0]
    email = account['email']
    raw_token_url = account['api_url']
    
    print(f"📧 Test mailbox: {email}")
    
    # Extract token.
    token = raw_token_url
    if "token=" in raw_token_url:
        match = re.search(r'token=([^&]+)', raw_token_url)
        if match:
            token = match.group(1)
            
    print(f"🔑 Extracted token: {token}")
    print(f"📏 Token length: {len(token)}")
    
    if len(token) < 50:
        print("⚠️ Warning: token length looks short. Microsoft refresh tokens are usually long.")
        print("   If the request fails, this may be a platform key rather than a refresh_token.")
    
    # Try to get Access Token.
    print("\n🔄 Requesting Microsoft OAuth...")
    access_token = get_access_token(token)
    
    if access_token:
        print("\n✅ Access Token acquired")
        print(f"🎫 Access Token (first 20 chars): {access_token[:20]}...")
        print("🎉 Mailbox verification path passed.")
    else:
        print("\n❌ Failed to get Access Token.")
        print("💡 Possible reason: provided token is not a valid Microsoft refresh token.")
        
        print("\n🕵️‍♀️ Trying token URLs directly to inspect response...")
        import requests
        try:
            # Try original URL and alternate URL shapes.
            urls_to_try = [
                f"https://api.nineemail.com/index.php?token={token}",
                f"https://www.appleemail.top/index.php?token={token}",
                f"http://api.nineemail.com/token={token}"
            ]
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            for url in urls_to_try:
                print(f"👉 Trying GET request: {url}")
                try:
                    r = requests.get(url, timeout=10, headers=headers, proxies={"http": None, "https": None}, verify=False)
                    print(f"   Status code: {r.status_code}")
                    print(f"   Content (first 200 chars): {r.text[:200]}")
                    if "refresh_token" in r.text or "access_token" in r.text:
                        print("   ✨ Found token keywords. The real token may be in this response.")
                except Exception as e:
                    print(f"   Request error: {e}")
                    
        except Exception as e:
            print(f"Probe error: {e}")

if __name__ == "__main__":
    test_oauth_login()
