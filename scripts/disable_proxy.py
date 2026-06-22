#!/usr/bin/env python3
"""
Temporary config switch tool: disable proxy.
"""

import yaml
from pathlib import Path

config_path = Path(__file__).parent / "config.yaml"

# Read config.
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Disable proxy.
config['region']['use_proxy'] = False

# Save config.
with open(config_path, 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, sort_keys=False)

print("✅ Proxy temporarily disabled")
print("   To re-enable it, set use_proxy: true in config.yaml")
