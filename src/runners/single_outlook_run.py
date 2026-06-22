#!/usr/bin/env python3
"""
Single Outlook account runner.
Uses one configured Outlook account for a signup run.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from services.outlook_accounts import OUTLOOK_ACCOUNTS
from managers.proxy_manager import proxy_manager
from helpers.multilang import lang_selector


def single_outlook_run(account_index=0):
    """
    Run once with the Outlook account at the specified index.
    :param account_index: Account index.
    """
    
    if account_index >= len(OUTLOOK_ACCOUNTS):
        print(f"❌ Account index {account_index} is out of range; {len(OUTLOOK_ACCOUNTS)} accounts configured")
        return
    
    account = OUTLOOK_ACCOUNTS[account_index]
    
    print("\n" + "=" * 60)
    print("📧 Single Outlook account mode")
    print("=" * 60)
    print(f"Account: {account['email']}")
    print(f"Account index: {account_index + 1}/{len(OUTLOOK_ACCOUNTS)}")
    
    # Smart environment config based on proxy IP.
    proxy_region = "usa"
    
    if proxy_manager.use_proxy:
        print("\n🔄 Fetching proxy...")
        proxy_url = proxy_manager.get_proxy()
        
        if proxy_url and proxy_manager.proxy_location:
            proxy_region = proxy_manager.proxy_location.get('region', 'usa')
            country = proxy_manager.proxy_location.get('country', 'Unknown')
            print(f"📍 Proxy IP location: {country} -> Environment: {proxy_region.upper()}")
    
    # Update language selector.
    lang_selector.update_region(proxy_region)
    os.environ['AUTO_REGION'] = proxy_region
    
    print(f"\n🌍 Region environment: {proxy_region.upper()}")
    lang_selector.print_current_language()
    print("=" * 60)
    print("\n🚀 Starting run...\n")
    
    # Run main entry point.
    from runners.main import run
    run(fixed_account=account)


if __name__ == "__main__":
    # Defaults to the first account. Pass an index to select another one.
    # python single_outlook_run.py 0
    # python single_outlook_run.py 2
    
    account_idx = 0
    if len(sys.argv) > 1:
        try:
            account_idx = int(sys.argv[1])
        except ValueError:
            print("⚠️ Invalid argument; using default account index 0")
    
    try:
        single_outlook_run(account_idx)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
