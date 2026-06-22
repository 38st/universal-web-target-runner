"""
Proxy whitelist management utilities.
Automatically add the current IP to a proxy whitelist.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import hashlib
from config import REGION_PROXY_API


def get_public_ip():
    """Get the current public IP."""
    try:
        # Try multiple IP lookup services.
        services = [
            'https://api.ipify.org',
            'https://ifconfig.me/ip',
            'http://icanhazip.com',
            'https://ident.me'
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    ip = response.text.strip()
                    print(f"✅ Current public IP: {ip}")
                    return ip
            except:
                continue
        
        print("⚠️  Could not get public IP")
        return None
    except Exception as e:
        print(f"⚠️  Public IP lookup failed: {e}")
        return None


def generate_sign(key, brand, ip):
    """
    Generate an API signature.
    Some proxy APIs require a provider-specific signing algorithm.
    Return an empty string when no sign parameter is required.
    """
    # Implement provider-specific signing here if required.
    return ""


def add_to_whitelist(key, ip=None, brand=2):
    """
    Add an IP to the whitelist.
    
    Args:
        key: API key.
        ip: IP to add. Uses current public IP when None.
        brand: Brand identifier. Defaults to 2.
    
    Returns:
        bool: True on success, otherwise False.
    """
    if ip is None:
        ip = get_public_ip()
        if not ip:
            return False
    
    # Generate a signature if needed.
    sign = generate_sign(key, brand, ip)
    
    # Build API URL.
    if sign:
        url = f"http://your-proxy-api.com/white/add?key={key}&brand={brand}&sign={sign}&ip={ip}"
    else:
        # Try without the sign parameter.
        url = f"http://your-proxy-api.com/white/add?key={key}&brand={brand}&ip={ip}"
    
    try:
        print("🔄 Adding IP to whitelist...")
        print(f"   IP: {ip}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.text.strip()
            print(f"📝 API response: {result}")
            
            # Adjust this condition to match the provider response format.
            if "success" in result.lower() or "ok" in result.lower():
                print("✅ IP added to whitelist")
                return True
            else:
                print("⚠️  Whitelist add may have failed; check response")
                return False
        else:
            print(f"⚠️  API request failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  Whitelist add failed: {e}")
        return False


def delete_from_whitelist(key, ip=None, brand=2):
    """Delete an IP from the whitelist."""
    if ip is None:
        ip = get_public_ip()
        if not ip:
            return False
    
    sign = generate_sign(key, brand, ip)
    
    if sign:
        url = f"http://your-proxy-api.com/white/delete?key={key}&brand={brand}&sign={sign}&ip={ip}"
    else:
        url = f"http://your-proxy-api.com/white/delete?key={key}&brand={brand}&ip={ip}"
    
    try:
        print("🔄 Deleting IP from whitelist...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ IP deleted from whitelist")
            print(f"📝 Response: {response.text}")
            return True
        else:
            print(f"⚠️  Delete failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  Whitelist delete failed: {e}")
        return False


def fetch_whitelist(key, brand=2):
    """Fetch the whitelist."""
    sign = generate_sign(key, brand, "")
    
    if sign:
        url = f"http://your-proxy-api.com/white/fetch?key={key}&brand={brand}&sign={sign}"
    else:
        url = f"http://your-proxy-api.com/white/fetch?key={key}&brand={brand}"
    
    try:
        print("🔄 Fetching whitelist...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("📋 Current whitelist:")
            print(response.text)
            return True
        else:
            print(f"⚠️  Query failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  Whitelist query failed: {e}")
        return False


def extract_key_from_url(api_url):
    """Extract the key parameter from an API URL."""
    try:
        # Extract the key parameter from the URL.
        if 'key=' in api_url:
            key = api_url.split('key=')[1].split('&')[0]
            return key
        return None
    except:
        return None


def auto_add_whitelist():
    """Automatically add the current IP to the whitelist."""
    print("=" * 60)
    print("Auto-add IP to proxy whitelist")
    print("=" * 60)
    
    # Get API info from config.
    api_url = REGION_PROXY_API.get('url', '')
    
    if not api_url:
        print("⚠️  Proxy API config not found")
        return False
    
    # Extract key.
    key = extract_key_from_url(api_url)
    
    if not key:
        print("⚠️  Could not extract key from API URL")
        print(f"   URL: {api_url}")
        return False
    
    print(f"🔑 API Key: {key}")
    print("-" * 60)
    
    # Add to whitelist.
    success = add_to_whitelist(key)
    
    if success:
        print("-" * 60)
        print("🎉 Whitelist configuration complete")
        print("💡 Tip: run python check_proxy.py to test the proxy")
    
    return success


if __name__ == "__main__":
    auto_add_whitelist()
