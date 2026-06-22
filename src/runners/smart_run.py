#!/usr/bin/env python3
"""
Smart launch script.
Automatically configures the environment from proxy IP geolocation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from managers.proxy_manager import proxy_manager
from helpers.multilang import lang_selector

def auto_configure_environment():
    """Automatically configure environment from proxy IP."""
    
    print("\n" + "=" * 60)
    print("🤖 Smart environment configuration")
    print("=" * 60)
    
    # Fetch proxy.
    proxy_url = None
    proxy_region = "usa"
    
    if proxy_manager.use_proxy:
        print("\n🔄 Fetching proxy...")
        proxy_url = proxy_manager.get_proxy()
        
        if not proxy_url:
            print("⚠️  Proxy fetch failed; using default USA environment")
        elif proxy_manager.proxy_location:
            # Use proxy IP geolocation.
            proxy_region = proxy_manager.proxy_location.get('region', 'usa')
            country = proxy_manager.proxy_location.get('country', 'Unknown')
            
            print("\n📍 Proxy IP location detected:")
            print(f"   Country: {country}")
            print(f"   Environment: {proxy_region.upper()}")
    else:
        print("\n⚠️  Proxy is disabled; using default USA environment")
    
    # Update multilingual selector.
    lang_selector.update_region(proxy_region)
    
    print("\n✅ Environment configuration complete")
    print(f"   Region: {proxy_region.upper()}")
    lang_selector.print_current_language()
    
    print("=" * 60)
    print("\n🚀 Starting main runner...\n")
    
    # Save config to env for main.py.
    import os
    os.environ['AUTO_REGION'] = proxy_region
    
    # Import and run the main entry point.
    from runners.main import run
    run()


if __name__ == "__main__":
    try:
        auto_configure_environment()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
