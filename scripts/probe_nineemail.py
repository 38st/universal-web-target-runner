from playwright.sync_api import sync_playwright
import time

def probe():
    with sync_playwright() as p:
        # Use headless mode for probing.
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "https://api.nineemail.com"
        print(f"Opening: {url}")
        
        try:
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")
            print(f"Page title: {page.title()}")
            
            # Print inputs and buttons on the page.
            print("--- Page element analysis ---")
            inputs = page.locator("input").all()
            for i, inp in enumerate(inputs):
                print(f"Input {i}: name='{inp.get_attribute('name')}', placeholder='{inp.get_attribute('placeholder')}', id='{inp.get_attribute('id')}'")
            
            buttons = page.locator("button").all()
            for i, btn in enumerate(buttons):
                print(f"Button {i}: text='{str(btn.text_content()).strip()}', type='{btn.get_attribute('type')}'")
                
            # Also inspect links because actions are sometimes anchors.
            links = page.locator("a").all()
            for i, link in enumerate(links):
                text = str(link.text_content()).strip()
                if "lookup" in text.lower() or "query" in text.lower():
                    print(f"Link {i}: text='{text}', href='{link.get_attribute('href')}'")
            
        except Exception as e:
            print(f"Error: {e}")
        
        browser.close()
        
        browser.close()

if __name__ == "__main__":
    probe()
