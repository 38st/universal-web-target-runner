import yaml
from pathlib import Path

# Read config file.
config_path = Path(__file__).parent.parent / "config" / "config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    _config = yaml.safe_load(f)

# Email config.
EMAIL_WORKER_URL = _config["email"]["worker_url"]
EMAIL_DOMAIN = _config["email"]["domain"]
EMAIL_PREFIX_LENGTH = _config["email"]["prefix_length"]
EMAIL_WAIT_TIMEOUT = _config["email"]["wait_timeout"]
EMAIL_POLL_INTERVAL = _config["email"]["poll_interval"]
EMAIL_ADMIN_PASSWORD = _config["email"].get("admin_password", "")

# Browser config.
HEADLESS = _config["browser"]["headless"]
SLOW_MO = _config["browser"]["slow_mo"]

# Region config.
REGION_CURRENT = _config["region"]["current"]
DEVICE_TYPE = _config["region"].get("device_type", "desktop")
REGION_USE_PROXY = _config["region"].get("use_proxy", False)
REGION_PROXY_MODE = _config["region"].get("proxy_mode", "static")
REGION_PROXY_URL = _config["region"].get("proxy_url", "")
REGION_PROXY_API = _config["region"].get("proxy_api", {})
REGION_PROFILES = _config["region"]["profiles"]



# HTTP config.
HTTP_TIMEOUT = _config["http"]["timeout"]
