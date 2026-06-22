"""
IP geolocation lookup module.
Detects an appropriate runtime region from a proxy IP.
"""

import requests


def get_ip_location(ip_address):
    """
    Query geolocation for an IP address.
    
    Args:
        ip_address: IP address string.
    
    Returns:
        dict with country code, country name, timezone, and other metadata.
        Returns None on failure.
    """
    # Try multiple free IP lookup services.
    services = [
        {
            'name': 'ip-api.com',
            'url': f'http://ip-api.com/json/{ip_address}',
            'parser': parse_ipapi
        },
        {
            'name': 'ipapi.co',
            'url': f'https://ipapi.co/{ip_address}/json/',
            'parser': parse_ipapico
        },
        {
            'name': 'ipwhois.app',
            'url': f'http://ipwhois.app/json/{ip_address}',
            'parser': parse_ipwhois
        }
    ]
    
    for service in services:
        try:
            print(f"🔍 Querying IP location ({service['name']})...")
            response = requests.get(service['url'], timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                result = service['parser'](data)
                
                if result and result.get('country_code'):
                    print(f"✅ IP location: {result.get('country')} ({result.get('country_code')})")
                    return result
        except Exception as e:
            print(f"   Skipping {service['name']}: {e}")
            continue
    
    print("⚠️  Could not query IP location; using defaults")
    return None


def parse_ipapi(data):
    """Parse ip-api.com response data."""
    if data.get('status') != 'success':
        return None
    
    return {
        'country_code': data.get('countryCode', ''),
        'country': data.get('country', ''),
        'timezone': data.get('timezone', ''),
        'city': data.get('city', ''),
        'region': data.get('regionName', ''),
        'isp': data.get('isp', '')
    }


def parse_ipapico(data):
    """Parse ipapi.co response data."""
    return {
        'country_code': data.get('country_code', ''),
        'country': data.get('country_name', ''),
        'timezone': data.get('timezone', ''),
        'city': data.get('city', ''),
        'region': data.get('region', ''),
        'isp': data.get('org', '')
    }


def parse_ipwhois(data):
    """Parse ipwhois.app response data."""
    if not data.get('success'):
        return None
    
    return {
        'country_code': data.get('country_code', ''),
        'country': data.get('country', ''),
        'timezone': data.get('timezone', ''),
        'city': data.get('city', ''),
        'region': data.get('region', ''),
        'isp': data.get('isp', '')
    }


def map_country_to_region(country_code):
    """
    Map a country code to a configured region.
    
    Args:
        country_code: Two-letter country code, such as US, DE, or JP.
    
    Returns:
        Region name. Unknown countries map to 'usa'.
    """
    # Country code to region mapping.
    mapping = {
        # Germany and German-speaking regions.
        'DE': 'germany',
        'AT': 'germany',
        'CH': 'germany',
        
        # Japan.
        'JP': 'japan',
        
        # United States and English-speaking regions.
        'US': 'usa',
        'CA': 'usa',
        'GB': 'usa',
        'AU': 'usa',
        'NZ': 'usa',
        'IE': 'usa',
    }
    
    region = mapping.get(country_code.upper(), 'usa')
    return region


def get_region_config_from_ip(ip_address):
    """
    Get recommended region config from an IP address.
    
    Args:
        ip_address: IP address.
    
    Returns:
        dict: {
            'region': region name,
            'country_code': country code,
            'country': country name,
            'timezone': timezone,
            ...
        }
    """
    location = get_ip_location(ip_address)
    
    if not location:
        return {
            'region': 'usa',
            'country_code': 'US',
            'country': 'United States',
            'timezone': 'America/New_York'
        }
    
    country_code = location.get('country_code', 'US')
    region = map_country_to_region(country_code)
    
    return {
        'region': region,
        'country_code': country_code,
        'country': location.get('country', ''),
        'timezone': location.get('timezone', ''),
        'city': location.get('city', ''),
        'isp': location.get('isp', '')
    }


def extract_ip_from_proxy_url(proxy_url):
    """
    Extract an IP address from a proxy URL.
    
    Args:
        proxy_url: Proxy URL, such as http://1.2.3.4:8080 or http://user:pass@1.2.3.4:8080.
    
    Returns:
        IP address, or None on failure.
    """
    try:
        # Remove protocol prefix.
        url = proxy_url
        if '://' in url:
            url = url.split('://')[1]
        
        # Remove auth info.
        if '@' in url:
            url = url.split('@')[1]
        
        # Extract IP and strip port.
        ip = url.split(':')[0]
        
        return ip
    except:
        return None
