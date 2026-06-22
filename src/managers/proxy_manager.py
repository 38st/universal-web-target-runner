"""
Proxy management module.
Supports static proxies and dynamic proxy APIs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from config import (
    REGION_USE_PROXY,
    REGION_PROXY_MODE,
    REGION_PROXY_URL,
    REGION_PROXY_API,
    HTTP_TIMEOUT
)


class ProxyManager:
    """Proxy manager."""
    
    def __init__(self):
        self.use_proxy = REGION_USE_PROXY
        self.proxy_mode = REGION_PROXY_MODE
        self.static_proxy = REGION_PROXY_URL
        self.api_config = REGION_PROXY_API
        self.current_proxy = None
        self.proxy_location = None  # Stores proxy IP geolocation info.
    
    def get_proxy(self):
        """
        Get a proxy.
        
        Returns:
            str: Proxy URL, for example http://ip:port or socks5://ip:port.
            None: When proxy is disabled or unavailable.
        """
        if not self.use_proxy:
            return None
        
        if self.proxy_mode == "static":
            # Use a static proxy.
            self.current_proxy = self.static_proxy
            return self.static_proxy
        
        elif self.proxy_mode == "dynamic":
            # Fetch a dynamic proxy from API.
            return self._fetch_proxy_from_api()
        
        return None
    
    def _fetch_proxy_from_api(self):
        """Fetch a proxy IP from API."""
        if not self.api_config or not self.api_config.get('url'):
            print("⚠️  Proxy API is not configured")
            return None
        
        api_url = self.api_config['url']
        timeout = self.api_config.get('timeout', 10)
        protocol = self.api_config.get('protocol', 'http')
        auth_required = self.api_config.get('auth_required', False)
        
        try:
            print("🔄 Fetching proxy from API...")
            response = requests.get(api_url, timeout=timeout)
            
            if response.status_code == 200:
                # Get returned IP:PORT.
                proxy_text = response.text.strip()
                
                # Remove possible newlines and whitespace.
                proxy_text = proxy_text.replace('\n', '').replace('\r', '').strip()
                
                if not proxy_text:
                    print("⚠️  API returned empty content")
                    return None
                
                # Build full proxy URL.
                if auth_required:
                    username = self.api_config.get('username', '')
                    password = self.api_config.get('password', '')
                    proxy_url = f"{protocol}://{username}:{password}@{proxy_text}"
                else:
                    proxy_url = f"{protocol}://{proxy_text}"
                
                self.current_proxy = proxy_url
                print(f"✅ Proxy acquired: {proxy_text}")
                
                # Query proxy IP location.
                self._query_proxy_location(proxy_text.split(':')[0])
                
                return proxy_url
            else:
                print(f"⚠️  API request failed: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⚠️  API request timed out (>{timeout}s)")
            return None
        except Exception as e:
            print(f"⚠️  Proxy fetch failed: {e}")
            return None
    
    def _query_proxy_location(self, ip_address):
        """Query proxy IP geolocation."""
        try:
            from helpers.ip_location import get_region_config_from_ip
            self.proxy_location = get_region_config_from_ip(ip_address)
        except Exception as e:
            print(f"   IP location lookup failed: {e}")
            self.proxy_location = None
    
    def test_proxy(self, proxy_url=None):
        """
        Test whether a proxy is usable.
        
        Args:
            proxy_url: Proxy URL to test. Uses current proxy when None.
        
        Returns:
            bool: True when usable, otherwise False.
        """
        if proxy_url is None:
            proxy_url = self.current_proxy
        
        if not proxy_url:
            return False
        
        try:
            print("🔍 Testing proxy...")
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # Test against a lightweight endpoint.
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                ip_info = response.json()
                print(f"✅ Proxy test passed. Current IP: {ip_info.get('origin', 'Unknown')}")
                return True
            else:
                print(f"⚠️  Proxy test failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️  Proxy test failed: {e}")
            return False
    
    def get_current_proxy(self):
        """Get the current proxy."""
        return self.current_proxy
    
    def print_proxy_info(self):
        """Print proxy info."""
        if not self.use_proxy:
            print("🔒 Proxy: disabled")
            return
        
        print(f"🔒 Proxy mode: {self.proxy_mode.upper()}")
        
        if self.proxy_mode == "static" and self.static_proxy:
            print(f"   Static proxy: {self.static_proxy}")
        elif self.proxy_mode == "dynamic":
            if self.current_proxy:
                # Hide full proxy credentials and show only the host portion.
                display_proxy = self.current_proxy.split('@')[-1] if '@' in self.current_proxy else self.current_proxy
                print(f"   Dynamic proxy: {display_proxy}")
            else:
                print("   Dynamic proxy: waiting...")


# Global proxy manager instance.
proxy_manager = ProxyManager()


def get_proxy():
    """Convenience function for fetching a proxy."""
    return proxy_manager.get_proxy()


def test_current_proxy():
    """Convenience function for testing the current proxy."""
    return proxy_manager.test_proxy()
