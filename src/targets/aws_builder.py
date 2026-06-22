import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Monkey-patch undetected_chromedriver.patcher.Patcher.auto() to prevent
# re-download of ChromeDriver on every launch (must precede any uc import).
import patch_uc  # noqa: F401

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from faker import Faker
import random
import time
import json
import os
from datetime import datetime
from config import HEADLESS, SLOW_MO
from core.config_loader import load_yaml_file, resolve_project_path
from core.context import RunContext
from services.email_service import create_temp_email, wait_for_verification_email
from selenium.webdriver.common.action_chains import ActionChains
from helpers.multilang import lang_selector


fake = Faker('en_US')
DEFAULT_TARGET_CONFIG_PATH = "config/targets/aws_builder.yaml"
REQUIRED_SELECTOR_KEYS = (
    "email_input_css",
    "primary_button_css",
    "name_input_css",
    "otp_input_css",
    "password_input_css",
)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_aws_builder_config(config_path=None):
    """Load AWS Builder target behavior from YAML."""

    selected_path = config_path or os.environ.get("AWS_BUILDER_CONFIG") or DEFAULT_TARGET_CONFIG_PATH
    path = resolve_project_path(selected_path)
    if not path.exists():
        raise FileNotFoundError(f"AWS Builder target config not found: {path}")
    target_config = load_yaml_file(path)
    _validate_aws_builder_config(target_config, path)
    return target_config


def _validate_aws_builder_config(target_config, path):
    selectors = _selectors(target_config)
    missing = []
    if not target_config.get("start_url"):
        missing.append("start_url")
    missing.extend(f"selectors.{key}" for key in REQUIRED_SELECTOR_KEYS if not selectors.get(key))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"AWS Builder target config {path} is missing: {missing_text}")


def _selectors(target_config):
    return target_config.get("selectors") or {}


def _markers(target_config, key):
    return _as_list((target_config.get("markers") or {}).get(key))


def generate_strong_password():
    """Generate a strong password."""
    import string
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choices(chars, k=16))
    # Ensure mix of upper, lower, digit, and symbol
    password = random.choice(string.ascii_uppercase) + random.choice(string.ascii_lowercase) + \
               random.choice(string.digits) + random.choice("!@#$%^&*") + password[4:]
    return password


def save_account(email, password, name, jwt_token="", status="registered", notes=None, output_file="accounts.jsonl"):
    """Append account row to accounts.jsonl."""
    account_info = {
        "email": email,
        "password": password,
        "name": name,
        "jwt_token": jwt_token,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status
    }

    if notes:
        account_info["notes"] = notes

    try:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(account_info, ensure_ascii=False) + "\n")
        print(f"✅ Account saved: {email}")
    except Exception as e:
        print(f"❌ Failed to save account: {e}")


def page_contains_any(driver, needles):
    """Best-effort page text check without failing the run."""
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    except Exception:
        page_text = ""

    haystack = " ".join([
        str(getattr(driver, "current_url", "")),
        str(getattr(driver, "title", "")),
        page_text,
    ]).lower()

    return any(needle.lower() in haystack for needle in needles)


def registration_has_blocking_error(driver, blocking_markers=None):
    """Return True when the page exposes an obvious failure state."""
    return page_contains_any(driver, blocking_markers or [])


def registration_looks_successful(driver, success_markers=None, blocking_markers=None):
    """Best-effort success detector used to avoid false registered rows."""
    return (
        page_contains_any(driver, success_markers or [])
        and not registration_has_blocking_error(driver, blocking_markers)
    )


def save_account_info(email, password, name, jwt_token):
    """Write account to legacy accounts.json array."""
    accounts_file = "accounts.json"
    accounts = []

    if os.path.exists(accounts_file):
        with open(accounts_file, 'r', encoding='utf-8') as f:
            accounts = json.load(f)

    account = {
        "email": email,
        "password": password,
        "name": name,
        "jwt_token": jwt_token,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active"
    }
    accounts.append(account)

    with open(accounts_file, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

    print(f"Account info saved to {accounts_file}")


def human_delay(min_sec=0.5, max_sec=2.0):
    """Random delay to mimic human pacing."""
    # Occasionally a longer “thinking” pause
    if random.random() < 0.15:  # 15% chance of longer pause
        time.sleep(random.uniform(2.5, 5.0))
    time.sleep(random.uniform(min_sec, max_sec))


def human_type(element, text):
    """Human-like typing with jitter."""
    # Per-user-ish speed factor
    speed_factor = random.uniform(0.7, 1.3)

    for char in text:
        element.send_keys(char)
        # Base delay + jitter
        delay = random.uniform(0.04, 0.15) * speed_factor

        # Occasional typing gap
        if random.random() < 0.05:
            delay += random.uniform(0.2, 0.5)

        time.sleep(delay)


def human_click(driver, element):
    """Human-like click with move + short hold."""
    try:
        # 1) Move near element with small offset
        action = ActionChains(driver)
        # Small jitter around center
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)

        action.move_to_element_with_offset(element, offset_x, offset_y)
        action.perform()

        # 2) Brief hover
        time.sleep(random.uniform(0.1, 0.4))

        # 3) Click with short hold/release
        action.click_and_hold().pause(random.uniform(0.05, 0.15)).release().perform()

    except Exception as e:
        # Fallback if ActionChains fails
        print(f"⚠️ ActionChains click failed; using plain click: {e}")
        try:
            element.click()
        except:
            driver.execute_script("arguments[0].click();", element)


def run(fixed_account=None, target_config_path=None):
    import undetected_chromedriver as uc

    # Late imports (keeps module import light)
    import os
    from config import REGION_CURRENT, DEVICE_TYPE
    from helpers.utils import (
        get_user_agent_for_region, get_locale_for_region,
        get_timezone_for_region, get_accept_language_for_region, is_mobile
    )
    from services.outlook_service import get_verification_code_from_outlook
    from managers.proxy_manager import proxy_manager

    target_config = load_aws_builder_config(target_config_path)
    selectors = _selectors(target_config)
    email_filters = target_config.get("email") or {}
    output_file = target_config.get("output_file", "accounts.jsonl")
    success_markers = _markers(target_config, "success")
    blocking_markers = _markers(target_config, "blocking_errors")

    # AUTO_REGION from smart_run, else config
    detected_region = os.environ.get('AUTO_REGION', REGION_CURRENT)

    lang_selector.update_region(detected_region)

    device_emoji = "📱" if is_mobile() else "💻"
    print(f"\n{device_emoji} === Environment ===")
    print(f"📍 Region: {detected_region.upper()}")
    print(f"🖥️  Device: {DEVICE_TYPE.upper()}")
    print(f"🌐 Locale: {get_locale_for_region(detected_region)}")
    print(f"🕐 Timezone: {get_timezone_for_region(detected_region)}")
    lang_selector.print_current_language()
    proxy_manager.print_proxy_info()
    print("=" * 50)

    # Resolve proxy (optional probe)
    proxy_url = None
    if proxy_manager.use_proxy:
        max_proxy_attempts = 3
        for proxy_attempt in range(max_proxy_attempts):
            proxy_url = proxy_manager.get_proxy()
            if not proxy_url:
                print("⚠️  Failed to obtain proxy")
                continue

            print("🔍 Probing proxy...")
            try:
                from helpers.utils import probe_proxy_connection
                ok, egress = probe_proxy_connection(proxy_url, timeout=8)
                if ok:
                    print(f"✅ Proxy OK; egress IP: {egress}")
                    break
                print(f"⚠️  Proxy probe failed (attempt {proxy_attempt + 1}/{max_proxy_attempts}); retrying...")
                proxy_url = None
            except Exception as e:
                print(f"⚠️  Proxy probe error: {e}")
                proxy_url = None

        if not proxy_url:
            print("❌ All proxy attempts failed")
            print("   Set region.use_proxy: false in config.yaml to skip proxy")
            print("=" * 50)
            return
        print("=" * 50)

    # Step 1: mailbox
    if fixed_account:
        email_address = fixed_account['email']
        jwt_token = "OUTLOOK_API"
        print(f"📧 Fixed Outlook mailbox: {email_address}")
    else:
        print("📧 Creating disposable mailbox...")
        email_address, jwt_token = create_temp_email()
        email_api_url = None

    if not email_address:
        print("Mailbox creation failed; exiting")
        return

    password = None
    random_name = None
    verification_code = None
    password_submitted = False

    # Chrome options / isolation
    options = uc.ChromeOptions()

    if HEADLESS:
        options.add_argument('--headless=new')

    if is_mobile():
        options.add_argument('--window-size=375,812')  # iPhone-ish viewport
        options.add_argument('--touch-events=enabled')
    else:
        # Random desktop window size
        common_resolutions = [
            "1920,1080", "1366,768", "1536,864", "1440,900", "1280,720"
        ]
        chosen_res = random.choice(common_resolutions)
        options.add_argument(f'--window-size={chosen_res}')
        options.add_argument('--start-maximized')

    # Optional Sec-Ch-Ua platform noise
    # options.add_argument(f'--sec-ch-ua-platform="{random.choice(["Windows", "macOS", "Linux"])}"')

    options.add_argument(f'--lang={get_locale_for_region(detected_region)}')
    options.add_argument(f'--accept-lang={get_accept_language_for_region(detected_region)}')

    # Anti-automation flags
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    options.add_argument('--disable-site-isolation-trials')

    # WebGL / Canvas
    options.add_argument('--enable-webgl')
    options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')

    # Audio
    options.add_argument('--autoplay-policy=no-user-gesture-required')

    # Privacy-ish toggles
    # Reduce WebRTC local IP leak
    options.add_argument('--force-webrtc-ip-handling-policy=default_public_interface_only')
    options.add_argument('--disable-features=WebRtcHideLocalIpsWithMdns')


    # User-Agent for region
    user_agent = get_user_agent_for_region(detected_region)
    options.add_argument(f'--user-agent={user_agent}')
    print(f"User-Agent: {user_agent[:80]}...")

    if proxy_url:
        options.add_argument(f'--proxy-server={proxy_url}')
        print(f"✅ Proxy applied to Chrome")


    # Launch browser
    import tempfile
    import shutil

    profile_prefix = target_config.get("profile_prefix", "aws_reg_")
    user_data_dir = tempfile.mkdtemp(prefix=f"{profile_prefix}{random.randint(1000, 9999)}_")
    print(f"📁 Temp Chrome profile: {user_data_dir}")

    options.add_argument(f"--user-data-dir={user_data_dir}")

    print("\nLaunching browser...")
    try:
        driver = uc.Chrome(options=options, user_data_dir=user_data_dir)
        wait = WebDriverWait(driver, 30)

        # Vary hardwareConcurrency / deviceMemory
        cores = random.choice([4, 8, 12, 16])
        memory = random.choice([4, 8, 16, 32])

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": f"""
                Object.defineProperty(navigator, 'hardwareConcurrency', {{
                    get: () => {cores}
                }});
                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => {memory}
                }});
                // WebGL vendor/renderer noise (best-effort)
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    // 37445 = UNMASKED_VENDOR_WEBGL
                    // 37446 = UNMASKED_RENDERER_WEBGL
                    if (parameter === 37445) {{
                        return 'Intel Inc.';
                    }}
                    if (parameter === 37446) {{
                        return 'Intel Iris OpenGL Engine';
                    }}
                    return getParameter(parameter);
                }};
            """
        })


    except Exception as e:
        print(f"❌ Browser failed to start: {e}")
        # Remove temp profile on failure
        try:
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except: pass
        return

    # Fingerprint injector (disabled while debugging)
    # print("🎭 Injecting fingerprint script...")
    # from fingerprint import fingerprint_randomizer
    # fingerprint_randomizer.inject_to_driver(driver)

    # Timezone override
    try:
        driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
            'timezoneId': get_timezone_for_region(detected_region)
        })
        print(f"Timezone: {get_timezone_for_region(detected_region)}")
    except Exception as e:
        print(f"Timezone override failed (non-fatal): {e}")

    try:
        # Approximate coords per region
        geo_locations = {
            'germany': {'latitude': 52.52, 'longitude': 13.405, 'accuracy': 100},
            'japan': {'latitude': 35.6762, 'longitude': 139.6503, 'accuracy': 100},
            'usa': {'latitude': 40.7128, 'longitude': -74.0060, 'accuracy': 100}
        }
        location = geo_locations.get(detected_region, geo_locations['usa'])
        driver.execute_cdp_cmd('Emulation.setGeolocationOverride', location)
        print(f"Geolocation override applied")
    except Exception as e:
        print(f"Geolocation override failed (non-fatal): {e}")

    try:
        print("\nOpening AWS Builder...")
        driver.get(target_config.get("start_url"))
        human_delay(2, 3)
        print(f"Page title: {driver.title}")

        print("Checking cookie banner...")
        human_delay(3, 4)  # let modal render

        cookie_closed = False

        # Cookie banner: try several dismiss strategies
        try:
            # Method 1: common Accept buttons
            accept_selectors = _as_list(selectors.get("cookie_accept_xpaths"))

            for selector in accept_selectors:
                try:
                    cookie_btn = driver.find_element(By.XPATH, selector)
                    if cookie_btn and cookie_btn.is_displayed():
                        print(f"   Found cookie button; clicking...")
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        human_delay(1, 1.5)

                        driver.execute_script("arguments[0].style.border='3px solid red'", cookie_btn)
                        human_delay(0.5, 1)

                        human_click(driver, cookie_btn)
                        print("✅ Cookie banner dismissed")
                        cookie_closed = True
                        human_delay(2, 3)  # wait for overlay to go
                        break
                except:
                    continue

            if not cookie_closed:
                print("   Trying ESC...")
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                human_delay(1, 2)

        except Exception as e:
            print(f"   Cookie handler error: {e}")

        if cookie_closed:
            print("   Cookie banner handled")
        else:
            print("   ⚠️  Could not auto-dismiss cookie banner; continuing...")

        print("Clicking Sign up with Builder ID...")
        human_delay(4, 6)  # let page settle

        signup_clicked = False
        original_url = driver.current_url

        for scan_attempt in range(3):
            if signup_clicked:
                break

            if scan_attempt > 0:
                print(f"   🔄 Rescan ({scan_attempt + 1}/3)...")
                human_delay(3, 5)

            try:
                print("   🔍 Scanning DOM...")
                # Text may live in descendants; XPath uses .//
                key_texts = _as_list(selectors.get("signup_texts"))

                found_elements = []
                for text in key_texts:
                    # Prefer span matches
                    xpath = f"//span[contains(text(), '{text}')]"
                    elements = driver.find_elements(By.XPATH, xpath)
                    for el in elements:
                        if el.is_displayed():
                            found_elements.append(el)

                    # Then any element with text
                    if not found_elements:
                        xpath = f"//*[contains(., '{text}')]"
                        elements = driver.find_elements(By.XPATH, xpath)
                        for el in elements:
                            if el.is_displayed() and el.tag_name in ['a', 'button', 'span', 'div']:
                                found_elements.append(el)

                print(f"   Found {len(found_elements)} candidate element(s)")

                for i, element in enumerate(found_elements):
                    try:
                        tag_name = element.tag_name
                        text_content = element.text
                        print(f"   Element {i+1}: <{tag_name}> '{text_content[:20]}...'")

                        target_element = element

                        # Walk up to clickable parent (max 5)
                        if tag_name not in ['a', 'button']:
                            parent = element
                            for _ in range(5):
                                try:
                                    parent = parent.find_element(By.XPATH, "./..")
                                    if parent.tag_name in ['a', 'button'] or parent.get_attribute('role') in ['button', 'link']:
                                        target_element = parent
                                        print(f"      Found clickable parent: <{parent.tag_name}>")
                                        break
                                except:
                                    break

                        driver.execute_script("arguments[0].style.border='3px solid red'; arguments[0].style.backgroundColor='yellow';", target_element)

                        print(f"      👉 Trying click...")

                        human_click(driver, target_element)
                        human_delay(2, 3)

                        if driver.current_url != original_url:
                            print(f"✅ Navigated to: {driver.current_url}")
                            signup_clicked = True
                            break

                        # If still no nav, try ActionChains click
                        from selenium.webdriver.common.action_chains import ActionChains
                        ActionChains(driver).move_to_element(target_element).click().perform()
                        human_delay(2, 3)

                        if driver.current_url != original_url:
                            print(f"✅ Navigated to: {driver.current_url}")
                            signup_clicked = True
                            break

                    except Exception as e:
                        print(f"      Click failed: {e}")
                        continue

                    if signup_clicked:
                        break

            except Exception as e:
                print(f"   Scan error: {e}")

        if not signup_clicked:
            print("⚠️  Heuristic scan failed; trying CSS fallbacks...")
            try:
                # Common AWS-ish selectors
                css_selectors = _as_list(selectors.get("signup_fallback_css"))
                required_text = selectors.get("signup_required_text", "")
                for css in css_selectors:
                    try:
                        els = driver.find_elements(By.CSS_SELECTOR, css)
                        for el in els:
                            if el.is_displayed() and (not required_text or required_text in el.text):
                                human_click(driver, el)
                                human_delay(2, 3)
                                if driver.current_url != original_url:
                                    signup_clicked = True
                                    break
                        if signup_clicked: break
                    except: continue
            except: pass

        if not signup_clicked:
            print("❌ Could not enter signup flow")
            driver.save_screenshot("debug_failed_click.png")
            pass

        print(f"Current URL: {driver.current_url}")

        driver.save_screenshot("screenshot.png")
        print("Screenshot saved")

        print(f"Typing email: {email_address}")

        def safe_input(selector, value, max_retries=3):
            """Input with stale-element retries."""
            for attempt in range(max_retries):
                try:
                    element = wait.until(EC.presence_of_element_located(selector))
                    element.click()
                    human_delay(0.3, 0.8)
                    element.clear()
                    human_type(element, value)
                    return True
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"   Input retry {attempt + 1}/{max_retries}...")
                        human_delay(1, 2)
                    else:
                        raise e
            return False

        safe_input((By.CSS_SELECTOR, selectors.get("email_input_css")), email_address)
        driver.save_screenshot("screenshot.png")
        print("Email entered")

        human_delay(1, 2)
        print("Clicking Continue...")
        continue_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selectors.get("primary_button_css")))
        )
        continue_btn.click()

        human_delay(3, 5)
        print(f"Current URL: {driver.current_url}")
        driver.save_screenshot("screenshot.png")

        random_name = fake.name()
        print(f"Typing name: {random_name}")

        driver.execute_script("window.scrollBy(0, 10)")
        human_delay(0.5, 1)

        # Robust name field fill
        name_input_success = False
        for name_attempt in range(3):
            try:
                name_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selectors.get("name_input_css"))))

                name_input.click()
                human_delay(0.3, 0.5)

                # Ctrl+A + delete (clear() flaky)
                from selenium.webdriver.common.keys import Keys
                name_input.send_keys(Keys.CONTROL + "a")
                human_delay(0.1, 0.2)
                name_input.send_keys(Keys.DELETE)
                human_delay(0.2, 0.4)

                human_type(name_input, random_name)
                human_delay(0.5, 1)

                actual_value = name_input.get_attribute('value')
                if actual_value and len(actual_value) > 0:
                    print(f"   Field value: '{actual_value}'")
                    name_input_success = True
                    break
                else:
                    print(f"   Empty value; retrying...")

            except Exception as e:
                print(f"   Name input retry {name_attempt + 1}/3: {e}")
                human_delay(1, 2)

        if not name_input_success:
            print("⚠️ Name step may have failed; continuing...")

        driver.save_screenshot("screenshot.png")
        print("Name step done")

        max_continue_attempts = 5
        page_changed = False
        original_url = driver.current_url

        for continue_attempt in range(max_continue_attempts):
            human_delay(1, 2)
            print(f"Clicking Continue... ({continue_attempt + 1}/{max_continue_attempts})")

            try:
                continue_btn = None
                continue_selectors = [
                    lang_selector.get_by_xpath('continue', 'button'),
                ]
                continue_selectors.extend((By.XPATH, xpath) for xpath in _as_list(selectors.get("continue_xpaths")))
                primary_button_css = selectors.get("primary_button_css")
                if primary_button_css:
                    continue_selectors.append((By.CSS_SELECTOR, primary_button_css))

                for selector in continue_selectors:
                    try:
                        continue_btn = driver.find_element(*selector)
                        if continue_btn and continue_btn.is_displayed():
                            break
                    except:
                        continue

                if continue_btn:
                    driver.execute_script("arguments[0].scrollIntoView(true);", continue_btn)
                    human_delay(0.3, 0.5)

                    try:
                        human_click(driver, continue_btn)
                    except:
                        driver.execute_script("arguments[0].click();", continue_btn)
                else:
                    print("   ⚠️ Continue button not found")
                    continue

            except Exception as e:
                print(f"   Click error: {e}")
                continue

            human_delay(3, 5)

            current_url = driver.current_url
            if current_url != original_url or 'verification' in current_url.lower() or 'code' in driver.title.lower():
                print(f"   ✅ Page navigated")
                page_changed = True
                break

            error_found = False
            try:
                error_selectors = _as_list(selectors.get("page_error_xpaths"))

                for error_xpath in error_selectors:
                    try:
                        error_elements = driver.find_elements(By.XPATH, error_xpath)
                        for el in error_elements:
                            if el.is_displayed():
                                error_text = el.text.strip()
                                if error_text and len(error_text) > 5:
                                    if 'required' not in error_text.lower():
                                        error_found = True
                                        print(f"   ⚠️ Error text: {error_text[:60]}...")
                                        break
                        if error_found:
                            break
                    except:
                        continue

                if error_found:
                    # Try closing error dialog
                    try:
                        close_selectors = _as_list(selectors.get("close_error_xpaths"))
                        for close_xpath in close_selectors:
                            try:
                                close_btn = driver.find_element(By.XPATH, close_xpath)
                                if close_btn.is_displayed():
                                    close_btn.click()
                                    human_delay(1, 2)
                                    break
                            except:
                                continue
                    except:
                        pass

                    # ESC to dismiss
                    try:
                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        human_delay(1, 2)
                    except:
                        pass

                    print(f"   🔄 Waiting before retry...")
                    human_delay(2, 4)
                    continue

            except Exception as e:
                pass

            if not error_found and not page_changed:
                print(f"   No navigation yet; retrying...")
                human_delay(1, 2)

        if not page_changed:
            print("⚠️ No navigation after retries; continuing...")

        driver.save_screenshot("screenshot.png")
        print(f"Page title: {driver.title}")

        print("Waiting for verification code...")
        human_delay(3, 5)

        try:
            if fixed_account:
                verification_code = get_verification_code_from_outlook(fixed_account, filters=email_filters)
            else:
                from services.email_service import wait_for_verification_email
                verification_code = wait_for_verification_email(jwt_token, filters=email_filters)
        except Exception as e:
            print(f"⚠️  OTP fetch error: {e}")
            verification_code = None

        if verification_code:
            print(f"Verification code: {verification_code}")

            try:
                print("Looking for OTP field...")
                human_delay(4, 6)

                code_input = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selectors.get("otp_input_css")))
                )

                human_delay(1, 2)
                code_input.click()
                human_delay(0.5, 1)

                human_type(code_input, verification_code)
                print("OTP entered")

                human_delay(1.5, 2.5)

                # Often "Continue" rather than "Verify"
                verify_clicked = False
                verify_selectors = _as_list(selectors.get("verify_xpaths"))

                print("Looking for Verify/Continue...")
                for xpath in verify_selectors:
                    try:
                        verify_btn = driver.find_element(By.XPATH, xpath)
                        if verify_btn.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView(true);", verify_btn)
                            human_delay(0.5, 1)
                            driver.execute_script("arguments[0].click();", verify_btn)
                            verify_clicked = True
                            print(f"Clicked: {xpath}")
                            break
                    except: continue

                if not verify_clicked:
                    print("⚠️  No obvious button; sending Enter")
                    from selenium.webdriver.common.keys import Keys
                    code_input.send_keys(Keys.ENTER)

                print("Waiting for navigation (proxy may be slow)...")
                human_delay(8, 12)

            except Exception as e:
                    print(f"⚠️  OTP step failed: {e}")
        else:
            print("❌ No verification code received")

        print("Preparing password step...")
        human_delay(5, 8)
        driver.save_screenshot("screenshot.png")
        print(f"Current URL: {driver.current_url}")

        password = generate_strong_password()
        print("Generated password: [redacted]")

        try:
            password_inputs = driver.find_elements(By.CSS_SELECTOR, selectors.get("password_input_css"))

            if len(password_inputs) >= 1:
                print(f"Found {len(password_inputs)} password field(s)")

                human_delay(0.5, 1)
                password_inputs[0].click()
                human_type(password_inputs[0], password)
                print("Primary password filled")

                if len(password_inputs) >= 2:
                    human_delay(0.5, 1)
                    password_inputs[1].click()
                    human_type(password_inputs[1], password)
                    print("Confirm password filled")
                else:
                     try:
                        confirm_selectors = _as_list(selectors.get("confirm_password_css"))
                        for sel in confirm_selectors:
                            try:
                                confirm_input = driver.find_element(By.CSS_SELECTOR, sel)
                                if confirm_input.is_displayed() and confirm_input != password_inputs[0]:
                                    human_delay(0.5, 1)
                                    confirm_input.click()
                                    human_type(confirm_input, password)
                                    print("Confirm password filled (fallback selector)")
                                    break
                            except: continue
                     except: pass

                driver.save_screenshot("screenshot.png")

                human_delay(1, 2)
                print("Clicking submit / create...")

                submit_selectors = _as_list(selectors.get("submit_xpaths"))

                for xpath in submit_selectors:
                    try:
                        btn = driver.find_element(By.XPATH, xpath)
                        if btn.is_displayed():
                            human_click(driver, btn)
                            password_submitted = True
                            break
                    except: continue

            else:
                print("⚠️  No password fields; flow may differ")

        except Exception as e:
            print(f"⚠️  Password step error: {e}")

        human_delay(5, 8)
        print(f"Final title: {driver.title}")
        print(f"Final URL: {driver.current_url}")
        driver.save_screenshot("final_success.png")

        if registration_looks_successful(driver, success_markers, blocking_markers):
            save_account(email_address, password, random_name, jwt_token, status="registered", output_file=output_file)
            print(f"\n✅ Run finished; registered row appended to {output_file}")
        elif password_submitted and verification_code:
            save_account(
                email_address,
                password,
                random_name,
                jwt_token,
                status="submitted_unconfirmed",
                notes="Password form was submitted, but no definitive success page was detected.",
                output_file=output_file,
            )
            print(f"\n⚠️ Run finished; submitted_unconfirmed row appended to {output_file}")
        else:
            print("\n❌ Run finished without confirmed registration; no account row saved")

    except Exception as e:
        print(f"Run error: {e}")
        try:
            driver.save_screenshot("error_screenshot.png")
            if email_address and password:
                save_account(
                    email_address,
                    password,
                    random_name or "Unknown",
                    jwt_token if 'jwt_token' in locals() else "",
                    status="partial_error",
                    notes=str(e),
                    output_file=output_file if 'output_file' in locals() else "accounts.jsonl",
                )
                print("⚠️  Partial error row saved")
        except: pass

    finally:
        # Avoid WinError 6 on Windows teardown
        try:
            if 'driver' in locals() and driver:
                try:
                    driver.quit()
                except: pass

                driver.quit = lambda: None

                try:
                    if hasattr(driver, 'service') and driver.service.process:
                        driver.service.process = None
                except: pass
        except: pass

        try:
            if 'user_data_dir' in locals() and os.path.exists(user_data_dir):
                import shutil
                time.sleep(1)
                shutil.rmtree(user_data_dir, ignore_errors=True)
                print(f"🧹 Removed temp profile")
        except: pass


class AwsBuilderTarget:
    name = "aws_builder"
    description = "AWS Builder ID signup flow"

    def run(self, context: RunContext):
        return run(
            fixed_account=context.fixed_account,
            target_config_path=context.options.get("target_config"),
        )


TARGET = AwsBuilderTarget()


if __name__ == "__main__":
    run()
