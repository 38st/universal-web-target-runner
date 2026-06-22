#!/usr/bin/env python3
"""
Proxy API test tool.
Checks whether the configured proxy API works.
"""

from proxy_manager import proxy_manager

print("=" * 60)
print("Proxy API test")
print("=" * 60)

# Show current config.
print("\n📋 Current config:")
print(f"   Proxy enabled: {proxy_manager.use_proxy}")
print(f"   Proxy mode: {proxy_manager.proxy_mode}")

if proxy_manager.use_proxy:
    print("\n" + "-" * 60)
    
    # Fetch proxy.
    proxy_url = proxy_manager.get_proxy()
    
    if proxy_url:
        print("\n✅ Proxy acquired")
        print(f"   Full URL: {proxy_url}")
        
        # Test proxy.
        print("\n" + "-" * 60)
        is_working = proxy_manager.test_proxy()
        
        if is_working:
            print("\n🎉 Proxy test passed")
        else:
            print("\n❌ Proxy test failed; check proxy settings")
    else:
        print("\n❌ Proxy fetch failed")
        print("   Check:")
        print("   1. Whether the API URL is correct")
        print("   2. Whether the API key is valid")
        print("   3. Whether network connectivity is working")
else:
    print("\n⚠️  Proxy is disabled")
    print("   To enable it, set use_proxy to true in config.yaml")

print("\n" + "=" * 60)
