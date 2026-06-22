#!/usr/bin/env python3
"""
Device type switch tool.
Quickly switches between desktop and mobile device profiles.
"""

import yaml
import sys
from pathlib import Path


def switch_device(device_type: str):
    """Switch device type."""
    valid_devices = ['desktop', 'mobile']
    
    if device_type not in valid_devices:
        print(f"❌ Invalid device type: {device_type}")
        print(f"✅ Available types: {', '.join(valid_devices)}")
        return False
    
    config_path = Path(__file__).parent / "config.yaml"
    
    # Read config.
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Update device type.
    old_device = config['region'].get('device_type', 'desktop')
    config['region']['device_type'] = device_type
    
    # Save config.
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
    
    emoji = "📱" if device_type == "mobile" else "💻"
    print(f"{emoji} Device type switched: {old_device} -> {device_type}")
    
    # Show current config.
    region = config['region']['current']
    profile = config['region']['profiles'][region]
    
    ua_key = f"{device_type}_user_agents"
    user_agents = profile.get(ua_key, [])
    
    print("\n📱 Current config:")
    print(f"  Device type: {device_type.upper()}")
    print(f"  Region: {region.upper()}")
    print(f"  User-Agent count: {len(user_agents)}")
    if user_agents:
        print(f"  Example UA: {user_agents[0][:80]}...")
    
    return True


def show_current():
    """Show current device config."""
    config_path = Path(__file__).parent / "config.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    device_type = config['region'].get('device_type', 'desktop')
    region = config['region']['current']
    profile = config['region']['profiles'][region]
    
    emoji = "📱" if device_type == "mobile" else "💻"
    print(f"{emoji} Current device type: {device_type.upper()}")
    print(f"📍 Region: {region.upper()}")
    
    ua_key = f"{device_type}_user_agents"
    user_agents = profile.get(ua_key, [])
    print(f"🔧 User-Agent count: {len(user_agents)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Show current config: python switch_device.py show")
        print("  Switch device type: python switch_device.py [desktop|mobile]")
        print()
        show_current()
    elif sys.argv[1] == "show":
        show_current()
    else:
        switch_device(sys.argv[1].lower())
