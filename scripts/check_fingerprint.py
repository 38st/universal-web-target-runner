#!/usr/bin/env python3
"""
Fingerprint check tool.
Opens fingerprint testing sites to inspect randomization behavior.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from fingerprint import fingerprint_randomizer
import time

def test_fingerprint():
    """Test fingerprint randomization behavior."""
    
    print("=" * 70)
    print("🎭 Browser fingerprint randomization test")
    print("=" * 70)
    
    # Configure browser.
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    
    # Start browser.
    print("\n🚀 Starting browser...")
    driver = uc.Chrome(options=options)
    
    # Inject fingerprint randomization.
    print("🎭 Injecting fingerprint randomization scripts...")
    fingerprint_randomizer.inject_to_driver(driver)
    
    # Test site list.
    test_sites = [
        {
            'name': 'BrowserLeaks - Canvas',
            'url': 'https://browserleaks.com/canvas',
            'desc': 'Canvas fingerprint test'
        },
        {
            'name': 'BrowserLeaks - WebGL',
            'url': 'https://browserleaks.com/webgl',
            'desc': 'WebGL fingerprint test'
        },
        {
            'name': 'CreepJS',
            'url': 'https://abrahamjuliot.github.io/creepjs/',
            'desc': 'Comprehensive fingerprint test'
        }
    ]
    
    print("\n📊 Available fingerprint test sites:")
    for i, site in enumerate(test_sites, 1):
        print(f"   {i}. {site['name']} - {site['desc']}")
    
    choice = input("\nSelect site (1-3, or press Enter for the first): ").strip() or "1"
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(test_sites):
            site = test_sites[idx]
            print(f"\n🔗 Opening: {site['name']}")
            print(f"   URL: {site['url']}")
            
            driver.get(site['url'])
            print("\n✅ Page loaded")
            print("📝 Inspect the fingerprint result in the browser")
            print("   Note: each run generates a different fingerprint")
            
            input("\nPress Enter to close the browser...")
        else:
            print("❌ Invalid selection")
    except ValueError:
        print("❌ Invalid input")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()
        print("\n✅ Test complete")


if __name__ == "__main__":
    test_fingerprint()
