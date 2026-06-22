#!/usr/bin/env python3
"""
Manual proxy whitelist setup tool.
Tests and configures whitelist parameters.
"""

import requests
import sys


def test_whitelist_api():
    """Test several whitelist API parameter combinations."""
    
    print("=" * 70)
    print("Proxy whitelist API test tool")
    print("=" * 70)
    
    # Get current IP.
    print("\n1️⃣  Fetching current public IP...")
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text.strip()
        print(f"   ✅ Current IP: {ip}")
    except:
        print("   ⚠️  IP fetch failed")
        ip = input("   Enter your public IP manually: ").strip()
    
    # Input API key.
    print("\n2️⃣  Enter API config:")
    key = input("   API Key: ").strip()
    if not key:
        print("   ❌ API Key cannot be empty")
        return False
    brand = input("   Brand (default: 2): ").strip() or "2"
    
    # Test several API call styles.
    print("\n3️⃣  Testing API...")
    print("-" * 70)
    
    # Test 1: without sign.
    print("\n📝 Test 1: without sign parameter")
    url1 = f"http://your-proxy-api.com/white/add?key={key}&brand={brand}&ip={ip}"
    print(f"   URL: {url1}")
    try:
        resp = requests.get(url1, timeout=10)
        print(f"   Status code: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        if resp.status_code == 200:
            print("   ✅ Success")
            return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 2: empty sign.
    print("\n📝 Test 2: empty sign parameter")
    url2 = f"http://your-proxy-api.com/white/add?key={key}&brand={brand}&sign=&ip={ip}"
    print(f"   URL: {url2}")
    try:
        resp = requests.get(url2, timeout=10)
        print(f"   Status code: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        if resp.status_code == 200:
            print("   ✅ Success")
            return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 3: fetch whitelist without IP parameter.
    print("\n📝 Test 3: fetch current whitelist")
    url3 = f"http://your-proxy-api.com/white/fetch?key={key}&brand={brand}"
    print(f"   URL: {url3}")
    try:
        resp = requests.get(url3, timeout=10)
        print(f"   Status code: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 4: alternate brand value.
    print("\n📝 Test 4: try brand=1")
    url4 = f"http://your-proxy-api.com/white/add?key={key}&brand=1&ip={ip}"
    print(f"   URL: {url4}")
    try:
        resp = requests.get(url4, timeout=10)
        print(f"   Status code: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        if resp.status_code == 200:
            print("   ✅ Success")
            return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n" + "=" * 70)
    print("💡 Suggestions:")
    print("   1. Check the API docs for correct parameters")
    print("   2. Confirm the key is correct")
    print("   3. Contact the proxy provider to confirm whitelist API usage")
    print("=" * 70)
    
    return False


def manual_add():
    """Manually add an IP to the whitelist."""
    print("\n" + "=" * 70)
    print("Manually add IP to whitelist")
    print("=" * 70)
    
    url = input("\nEnter the full API URL: ").strip()
    
    if not url:
        print("❌ URL cannot be empty")
        return
    
    try:
        print("\n🔄 Calling API...")
        print(f"   URL: {url}")
        
        resp = requests.get(url, timeout=10)
        print("\n📊 Result:")
        print(f"   Status code: {resp.status_code}")
        print("   Response:")
        print(f"   {resp.text}")
        
        if resp.status_code == 200:
            print("\n✅ Request succeeded. Check response above to confirm.")
        else:
            print(f"\n⚠️  Request returned status code {resp.status_code}")
    
    except Exception as e:
        print(f"\n❌ Request failed: {e}")


if __name__ == "__main__":
    print("\nChoose an action:")
    print("1. Automatically test whitelist API")
    print("2. Manually test full URL")
    
    choice = input("\nSelect (1/2, default 1): ").strip() or "1"
    
    if choice == "1":
        test_whitelist_api()
    elif choice == "2":
        manual_add()
    else:
        print("Invalid selection")
