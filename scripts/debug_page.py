#!/usr/bin/env python3
"""Debug script for inspecting page elements."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

def debug_page():
    print("🔍 Starting debug browser...")
    
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = uc.Chrome(options=options)
    
    try:
        print("📄 Opening AWS Builder page...")
        driver.get("https://builder.aws.com/start")
        time.sleep(5)
        
        print(f"\nPage title: {driver.title}")
        print(f"Page URL: {driver.current_url}")
        
        # Find buttons.
        print("\n=== Buttons ===")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for i, btn in enumerate(buttons[:10]):
            text = btn.text.strip()[:50] if btn.text else "(no text)"
            print(f"  [{i}] {text}")
        
        # Find links.
        print("\n=== Links ===")
        links = driver.find_elements(By.TAG_NAME, "a")
        for i, link in enumerate(links[:15]):
            text = link.text.strip()[:50] if link.text else "(no text)"
            href = link.get_attribute("href") or ""
            print(f"  [{i}] {text} -> {href[:60]}")
        
        # Find elements containing sign/register/builder.
        print("\n=== Keyword Elements ===")
        keywords = ["sign", "register", "builder", "create", "start"]
        for kw in keywords:
            els = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{kw}')]")
            if els:
                print(f"  '{kw}': found {len(els)}")
                for el in els[:3]:
                    print(f"    - <{el.tag_name}> {el.text[:40]}")
        
        print("\n⏸️  Browser remains open. Press Ctrl+C to close...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nClosing browser...")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_page()
