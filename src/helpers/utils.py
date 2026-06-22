import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
import random
import requests
from config import REGION_CURRENT, REGION_PROFILES, DEVICE_TYPE

# Shared HTTP session.
http_session = requests.Session()


def get_region_config():
    """Get the current region config."""
    return REGION_PROFILES.get(REGION_CURRENT, REGION_PROFILES.get("usa"))


def get_user_agent():
    """Get a random User-Agent for the current region and device type."""
    region_config = get_region_config()
    
    # Pick the User-Agent list based on device type.
    if DEVICE_TYPE == "mobile":
        user_agents = region_config.get("mobile_user_agents", [])
        # Fall back to desktop User-Agents when mobile ones are unavailable.
        if not user_agents:
            user_agents = region_config.get("desktop_user_agents", [])
    else:
        user_agents = region_config.get("desktop_user_agents", [])
    
    # Default fallback.
    if not user_agents:
        user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
            if DEVICE_TYPE == "mobile" else
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
    
    return random.choice(user_agents)


def is_mobile():
    """Return True when the current device mode is mobile."""
    return DEVICE_TYPE == "mobile"


def get_locale():
    """Get the current region locale."""
    region_config = get_region_config()
    return region_config.get("locale", "en-US")


def get_timezone():
    """Get the current region timezone."""
    region_config = get_region_config()
    return region_config.get("timezone", "America/New_York")


def get_accept_language():
    """Get the current region Accept-Language value."""
    region_config = get_region_config()
    return region_config.get("accept_language", "en-US,en;q=0.9")



def extract_verification_code(text: str):
    """
    Extract a 6-digit verification code from text.
    """
    if not text:
        return None
    
    # Match common 6-digit code formats.
    patterns = [
        r'\b(\d{6})\b',
        r'code[:\s]+(\d{6})',  # code: 123456
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


# === Dynamic region config support ===

def get_region_config_by_name(region_name):
    """Get config for a region name."""
    return REGION_PROFILES.get(region_name, REGION_PROFILES.get("usa"))


def get_user_agent_for_region(region_name):
    """Get a User-Agent for a region using Windows with a dynamic Chrome version."""
    
    # Generate a dynamic Chrome version to avoid a fixed fingerprint list.
    major = random.randint(119, 124)
    build = random.randint(6000, 6999)
    patch = random.randint(100, 200)
    
    version = f"{major}.0.{build}.{patch}"
    
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"


def get_locale_for_region(region_name):
    """Get locale for a region."""
    region_config = get_region_config_by_name(region_name)
    return region_config.get("locale", "en-US")


def get_timezone_for_region(region_name):
    """Get timezone for a region."""
    region_config = get_region_config_by_name(region_name)
    return region_config.get("timezone", "America/New_York")


def get_accept_language_for_region(region_name):
    """Get Accept-Language for a region."""
    region_config = get_region_config_by_name(region_name)
    return region_config.get("accept_language", "en-US,en;q=0.9")
