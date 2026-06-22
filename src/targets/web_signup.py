import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from faker import Faker
import random
import json
import os
from datetime import datetime
from typing import Any
from config import REGION_CURRENT
from core.actions import (
    click_element as human_click,
    jitter_delay as human_delay,
    page_contains_any,
    safe_input,
    type_text as human_type,
)
from core.browser import (
    create_browser_session,
    print_browser_environment,
    resolve_browser_proxy,
)
from core.config_loader import load_yaml_file, resolve_project_path
from core.context import RunContext
from services.email_service import create_temp_email
from helpers.multilang import lang_selector


fake = Faker('en_US')
DEFAULT_TARGET_CONFIG_PATH = "config/targets/aws_builder_id.yaml"
TARGET_CONFIG_ENV = "WEB_SIGNUP_CONFIG"
LEGACY_TARGET_CONFIG_ENV = "AWS_BUILDER_CONFIG"
SUPPORTED_STEP_ACTIONS = {
    "open_start_page",
    "dismiss_cookies",
    "enter_signup_flow",
    "submit_email",
    "submit_name",
    "fetch_and_submit_otp",
    "set_password",
    "detect_result",
}
STEP_SELECTOR_REQUIREMENTS = {
    "submit_email": ("email_input_css", "primary_button_css"),
    "submit_name": ("name_input_css",),
    "fetch_and_submit_otp": ("otp_input_css",),
    "set_password": ("password_input_css",),
}


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_web_signup_config(config_path=None):
    """Load web signup target behavior from YAML."""

    selected_path = (
        config_path
        or os.environ.get(TARGET_CONFIG_ENV)
        or os.environ.get(LEGACY_TARGET_CONFIG_ENV)
        or DEFAULT_TARGET_CONFIG_PATH
    )
    path = resolve_project_path(selected_path)
    if not path.exists():
        raise FileNotFoundError(f"Web signup target config not found: {path}")
    target_config = load_yaml_file(path)
    _validate_web_signup_config(target_config, path)
    return target_config


def _validate_web_signup_config(target_config, path):
    selectors = _selectors(target_config)
    steps = _steps(target_config)
    missing = []
    if not isinstance(steps, list) or not steps:
        missing.append("steps")
    else:
        for index, raw_step in enumerate(steps, start=1):
            step = _normalize_step(raw_step, index)
            if not _step_enabled(step):
                continue

            action = step["action"]
            if action not in SUPPORTED_STEP_ACTIONS:
                raise ValueError(
                    f"Web signup target config {path} has unsupported step action "
                    f"at steps[{index}]: {action}"
                )

            if action == "open_start_page" and not (step.get("url") or target_config.get("start_url")):
                missing.append(f"start_url or steps[{index}].url")

            missing.extend(
                f"selectors.{key} for step {index} ({action})"
                for key in STEP_SELECTOR_REQUIREMENTS.get(action, ())
                if not selectors.get(key)
            )

    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Web signup target config {path} is missing: {missing_text}")


def _selectors(target_config):
    return target_config.get("selectors") or {}


def _markers(target_config, key):
    return _as_list((target_config.get("markers") or {}).get(key))


def _steps(target_config):
    return target_config.get("steps") or []


def _normalize_step(raw_step: Any, index: int) -> dict[str, Any]:
    if isinstance(raw_step, str):
        step = {"action": raw_step}
    elif isinstance(raw_step, dict):
        step = dict(raw_step)
    else:
        raise ValueError(f"Web signup step {index} must be a string or mapping")

    action = str(step.get("action", "")).strip()
    if not action:
        raise ValueError(f"Web signup step {index} is missing action")

    step["action"] = action.lower().replace("-", "_")
    return step


def _step_enabled(step):
    return step.get("enabled", True) is not False


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


def open_start_page(driver, target_config, step=None):
    """Open the target start URL and let the page settle."""

    step = step or {}
    start_url = step.get("url") or target_config.get("start_url")
    print("\nOpening start page...")
    driver.get(start_url)
    human_delay(2, 3)
    print(f"Page title: {driver.title}")


def dismiss_cookies(driver, selectors):
    """Best-effort cookie banner dismissal."""

    print("Checking cookie banner...")
    human_delay(3, 4)  # let modal render

    cookie_closed = False

    try:
        accept_selectors = _as_list(selectors.get("cookie_accept_xpaths"))

        for selector in accept_selectors:
            try:
                cookie_btn = driver.find_element(By.XPATH, selector)
                if cookie_btn and cookie_btn.is_displayed():
                    print("   Found cookie button; clicking...")
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
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            human_delay(1, 2)

    except Exception as e:
        print(f"   Cookie handler error: {e}")

    if cookie_closed:
        print("   Cookie banner handled")
    else:
        print("   ⚠️  Could not auto-dismiss cookie banner; continuing...")

    return cookie_closed


def enter_signup_flow(driver, selectors):
    """Navigate from the start page into the signup flow."""

    print("Clicking signup entrypoint...")
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
            key_texts = _as_list(selectors.get("signup_texts"))

            found_elements = []
            for text in key_texts:
                xpath = f"//span[contains(text(), '{text}')]"
                elements = driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        found_elements.append(el)

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

                    if tag_name not in ['a', 'button']:
                        parent = element
                        for _ in range(5):
                            try:
                                parent = parent.find_element(By.XPATH, "./..")
                                if (
                                    parent.tag_name in ['a', 'button']
                                    or parent.get_attribute('role') in ['button', 'link']
                                ):
                                    target_element = parent
                                    print(f"      Found clickable parent: <{parent.tag_name}>")
                                    break
                            except:
                                break

                    driver.execute_script(
                        "arguments[0].style.border='3px solid red'; "
                        "arguments[0].style.backgroundColor='yellow';",
                        target_element,
                    )

                    print("      👉 Trying click...")

                    human_click(driver, target_element)
                    human_delay(2, 3)

                    if driver.current_url != original_url:
                        print(f"✅ Navigated to: {driver.current_url}")
                        signup_clicked = True
                        break

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
                    if signup_clicked:
                        break
                except:
                    continue
        except:
            pass

    if not signup_clicked:
        print("❌ Could not enter signup flow")
        driver.save_screenshot("debug_failed_click.png")

    print(f"Current URL: {driver.current_url}")
    driver.save_screenshot("screenshot.png")
    print("Screenshot saved")
    return signup_clicked


def submit_email(driver, wait, selectors, email_address):
    """Submit the email address on the first signup form."""

    print(f"Typing email: {email_address}")

    safe_input(wait, (By.CSS_SELECTOR, selectors.get("email_input_css")), email_address)
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


def submit_name(driver, wait, selectors, name=None):
    """Submit a generated display name and wait for the OTP step."""

    random_name = name or fake.name()
    print(f"Typing name: {random_name}")

    driver.execute_script("window.scrollBy(0, 10)")
    human_delay(0.5, 1)

    name_input_success = False
    for name_attempt in range(3):
        try:
            name_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selectors.get("name_input_css")))
            )

            name_input.click()
            human_delay(0.3, 0.5)

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
            print("   Empty value; retrying...")

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
            continue_selectors.extend(
                (By.XPATH, xpath) for xpath in _as_list(selectors.get("continue_xpaths"))
            )
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
            print("   ✅ Page navigated")
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

                try:
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    human_delay(1, 2)
                except:
                    pass

                print("   🔄 Waiting before retry...")
                human_delay(2, 4)
                continue

        except Exception:
            pass

        if not error_found and not page_changed:
            print("   No navigation yet; retrying...")
            human_delay(1, 2)

    if not page_changed:
        print("⚠️ No navigation after retries; continuing...")

    driver.save_screenshot("screenshot.png")
    print(f"Page title: {driver.title}")

    return random_name


def fetch_and_submit_otp(driver, wait, selectors, *, fixed_account, email_filters, jwt_token):
    """Fetch a verification code and submit it when available."""

    from services.outlook_service import get_verification_code_from_outlook

    print("Waiting for verification code...")
    human_delay(3, 5)

    try:
        if fixed_account:
            verification_code = get_verification_code_from_outlook(
                fixed_account,
                filters=email_filters,
            )
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
                except:
                    continue

            if not verify_clicked:
                print("⚠️  No obvious button; sending Enter")
                code_input.send_keys(Keys.ENTER)

            print("Waiting for navigation (proxy may be slow)...")
            human_delay(8, 12)

        except Exception as e:
            print(f"⚠️  OTP step failed: {e}")
    else:
        print("❌ No verification code received")

    return verification_code


def set_password(driver, selectors, password=None):
    """Generate and submit a password when the password step is present."""

    print("Preparing password step...")
    human_delay(5, 8)
    driver.save_screenshot("screenshot.png")
    print(f"Current URL: {driver.current_url}")

    password = password or generate_strong_password()
    password_submitted = False
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
                        except:
                            continue
                except:
                    pass

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
                except:
                    continue

        else:
            print("⚠️  No password fields; flow may differ")

    except Exception as e:
        print(f"⚠️  Password step error: {e}")

    return password, password_submitted


def detect_result(
    driver,
    *,
    email_address,
    password,
    random_name,
    jwt_token,
    verification_code,
    password_submitted,
    success_markers,
    blocking_markers,
    output_file,
):
    """Detect the final registration outcome and persist account data."""

    human_delay(5, 8)
    print(f"Final title: {driver.title}")
    print(f"Final URL: {driver.current_url}")
    driver.save_screenshot("final_success.png")

    if registration_looks_successful(driver, success_markers, blocking_markers):
        save_account(
            email_address,
            password,
            random_name,
            jwt_token,
            status="registered",
            output_file=output_file,
        )
        print(f"\n✅ Run finished; registered row appended to {output_file}")
        return "registered"

    if password_submitted and verification_code:
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
        return "submitted_unconfirmed"

    print("\n❌ Run finished without confirmed registration; no account row saved")
    return "unconfirmed"


def execute_web_signup_steps(driver, wait, target_config, runtime):
    """Execute semantic web signup steps defined by target YAML."""

    selectors = _selectors(target_config)
    steps = _steps(target_config)

    for index, raw_step in enumerate(steps, start=1):
        step = _normalize_step(raw_step, index)
        if not _step_enabled(step):
            print(f"\nSkipping disabled workflow step {index}/{len(steps)}: {step['action']}")
            continue

        action = step["action"]
        print(f"\nWorkflow step {index}/{len(steps)}: {action}")

        try:
            if action == "open_start_page":
                open_start_page(driver, target_config, step=step)
            elif action == "dismiss_cookies":
                runtime["cookie_closed"] = dismiss_cookies(driver, selectors)
            elif action == "enter_signup_flow":
                runtime["signup_clicked"] = enter_signup_flow(driver, selectors)
            elif action == "submit_email":
                email_address = runtime.get("email_address")
                if not email_address:
                    raise ValueError("submit_email requires runtime email_address")
                submit_email(driver, wait, selectors, email_address)
            elif action == "submit_name":
                runtime["random_name"] = submit_name(
                    driver,
                    wait,
                    selectors,
                    name=step.get("value") or step.get("name"),
                )
            elif action == "fetch_and_submit_otp":
                runtime["verification_code"] = fetch_and_submit_otp(
                    driver,
                    wait,
                    selectors,
                    fixed_account=runtime.get("fixed_account"),
                    email_filters=runtime.get("email_filters") or {},
                    jwt_token=runtime.get("jwt_token"),
                )
            elif action == "set_password":
                password, password_submitted = set_password(
                    driver,
                    selectors,
                    password=step.get("value") or step.get("password"),
                )
                runtime["password"] = password
                runtime["password_submitted"] = password_submitted
            elif action == "detect_result":
                runtime["status"] = detect_result(
                    driver,
                    email_address=runtime.get("email_address"),
                    password=runtime.get("password"),
                    random_name=runtime.get("random_name"),
                    jwt_token=runtime.get("jwt_token"),
                    verification_code=runtime.get("verification_code"),
                    password_submitted=runtime.get("password_submitted", False),
                    success_markers=runtime.get("success_markers") or [],
                    blocking_markers=runtime.get("blocking_markers") or [],
                    output_file=runtime.get("output_file", "accounts.jsonl"),
                )
            else:
                raise ValueError(f"Unsupported web signup step action: {action}")
        except Exception as e:
            if step.get("optional") is True:
                print(f"⚠️ Optional workflow step failed ({action}): {e}")
                continue
            raise

    return runtime


def run(fixed_account=None, target_config_path=None):
    target_config = load_web_signup_config(target_config_path)
    email_filters = target_config.get("email") or {}
    output_file = target_config.get("output_file", "accounts.jsonl")
    success_markers = _markers(target_config, "success")
    blocking_markers = _markers(target_config, "blocking_errors")

    # AUTO_REGION from smart_run, else config
    detected_region = os.environ.get('AUTO_REGION', REGION_CURRENT)

    lang_selector.update_region(detected_region)
    print_browser_environment(detected_region)

    # Resolve proxy (optional probe)
    try:
        proxy_url = resolve_browser_proxy(probe_proxy=True)
    except RuntimeError as e:
        print(f"❌ {e}")
        print("=" * 50)
        return
    if proxy_url:
        print("=" * 50)

    # Step 1: mailbox
    if fixed_account:
        email_address = fixed_account['email']
        jwt_token = "OUTLOOK_API"
        print(f"📧 Fixed Outlook mailbox: {email_address}")
    else:
        print("📧 Creating disposable mailbox...")
        email_address, jwt_token = create_temp_email()

    if not email_address:
        print("Mailbox creation failed; exiting")
        return

    runtime = {
        "fixed_account": fixed_account,
        "email_address": email_address,
        "jwt_token": jwt_token,
        "email_filters": email_filters,
        "password": None,
        "random_name": None,
        "verification_code": None,
        "password_submitted": False,
        "success_markers": success_markers,
        "blocking_markers": blocking_markers,
        "output_file": output_file,
    }

    profile_prefix = target_config.get("profile_prefix", "web_signup_")
    session = None

    print("\nLaunching browser...")
    try:
        session = create_browser_session(
            region_name=detected_region,
            profile_prefix=profile_prefix,
            proxy_url=proxy_url,
            use_configured_proxy=False,
            timeout=30,
        )
        driver = session.driver
        wait = session.wait
    except Exception as e:
        print(f"❌ Browser failed to start: {e}")
        return

    try:
        execute_web_signup_steps(driver, wait, target_config, runtime)

    except Exception as e:
        print(f"Run error: {e}")
        try:
            driver.save_screenshot("error_screenshot.png")
            if runtime.get("email_address") and runtime.get("password"):
                save_account(
                    runtime["email_address"],
                    runtime["password"],
                    runtime.get("random_name") or "Unknown",
                    runtime.get("jwt_token") or "",
                    status="partial_error",
                    notes=str(e),
                    output_file=runtime.get("output_file", "accounts.jsonl"),
                )
                print("⚠️  Partial error row saved")
        except: pass

    finally:
        try:
            if session:
                session.close()
                print("🧹 Removed temp profile")
        except: pass


class WebSignupTarget:
    name = "web_signup"
    description = "Configurable web signup flow"

    def run(self, context: RunContext):
        return run(
            fixed_account=context.fixed_account,
            target_config_path=context.options.get("target_config"),
        )


TARGET = WebSignupTarget()


if __name__ == "__main__":
    run()
