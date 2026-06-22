#!/usr/bin/env python3
"""
Region switch tool.
Quickly switches between configured runtime regions.
"""

import yaml
import sys
from pathlib import Path


def switch_region(region: str):
    """Switch region config."""
    valid_regions = ['germany', 'japan', 'usa']
    
    if region not in valid_regions:
        print(f"❌ Invalid region: {region}")
        print(f"✅ Available regions: {', '.join(valid_regions)}")
        return False
    
    config_path = Path(__file__).parent / "config.yaml"
    
    # Read config.
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Update region.
    old_region = config['region']['current']
    config['region']['current'] = region
    
    # Save config.
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    
    print(f"✅ Region switched: {old_region} -> {region}")
    
    # Show current config.
    profile = config['region']['profiles'][region]
    print("\n📍 Current region config:")
    print(f"  Locale: {profile['locale']}")
    print(f"  Timezone: {profile['timezone']}")
    print(f"  Accept-Language: {profile['accept_language']}")
    print(f"  User-Agent count: {len(profile['user_agents'])}")
    
    return True


def show_current():
    """Show current region config."""
    config_path = Path(__file__).parent / "config.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    current = config['region']['current']
    profile = config['region']['profiles'][current]
    
    print(f"📍 Current region: {current.upper()}")
    print(f"  Locale: {profile['locale']}")
    print(f"  Timezone: {profile['timezone']}")
    print(f"  Accept-Language: {profile['accept_language']}")
    print(f"  Proxy: {'enabled' if config['region'].get('use_proxy') else 'disabled'}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Show current config: python switch_region.py show")
        print("  Switch region: python switch_region.py [germany|japan|usa]")
        print()
        show_current()
    elif sys.argv[1] == "show":
        show_current()
    else:
        switch_region(sys.argv[1].lower())
