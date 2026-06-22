import random
import shutil
import tempfile
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class BrowserSession:
    driver: Any
    wait: Any
    user_data_dir: str
    region_name: str
    proxy_url: str | None = None

    def close(self) -> None:
        """Close the browser and remove the temporary profile."""

        try:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                try:
                    self.driver.quit = lambda: None
                    if hasattr(self.driver, "service") and self.driver.service.process:
                        self.driver.service.process = None
                except Exception:
                    pass
        finally:
            if self.user_data_dir:
                time.sleep(1)
                shutil.rmtree(self.user_data_dir, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


def create_browser_session(
    *,
    region_name: str | None = None,
    profile_prefix: str = "web_auto_",
    proxy_url: str | None = None,
    use_configured_proxy: bool = True,
    probe_proxy: bool = False,
    max_proxy_attempts: int = 3,
    timeout: int = 30,
) -> BrowserSession:
    """
    Create a Selenium browser session using the project's configured environment.

    Browser-driver imports stay inside this function so target discovery and tests
    do not require driver dependencies.
    """

    import patch_uc  # noqa: F401
    import undetected_chromedriver as uc
    from selenium.webdriver.support.ui import WebDriverWait

    from config import HEADLESS, REGION_CURRENT
    from helpers.utils import (
        get_accept_language_for_region,
        get_locale_for_region,
        get_user_agent_for_region,
        is_mobile,
    )

    detected_region = region_name or REGION_CURRENT
    options = uc.ChromeOptions()

    if HEADLESS:
        options.add_argument("--headless=new")

    if is_mobile():
        options.add_argument("--window-size=375,812")
        options.add_argument("--touch-events=enabled")
    else:
        chosen_res = random.choice(["1920,1080", "1366,768", "1536,864", "1440,900", "1280,720"])
        options.add_argument(f"--window-size={chosen_res}")
        options.add_argument("--start-maximized")

    options.add_argument(f"--lang={get_locale_for_region(detected_region)}")
    options.add_argument(f"--accept-lang={get_accept_language_for_region(detected_region)}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--enable-webgl")
    options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_argument("--force-webrtc-ip-handling-policy=default_public_interface_only")
    options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")
    user_agent = get_user_agent_for_region(detected_region)
    options.add_argument(f"--user-agent={user_agent}")
    print(f"User-Agent: {user_agent[:80]}...")

    resolved_proxy = proxy_url
    if not resolved_proxy:
        resolved_proxy = resolve_browser_proxy(
            use_configured_proxy=use_configured_proxy,
            probe_proxy=probe_proxy,
            max_proxy_attempts=max_proxy_attempts,
        )
    if resolved_proxy:
        options.add_argument(f"--proxy-server={resolved_proxy}")
        print("✅ Proxy applied to Chrome")

    user_data_dir = tempfile.mkdtemp(prefix=f"{profile_prefix}{random.randint(1000, 9999)}_")
    print(f"📁 Temp Chrome profile: {user_data_dir}")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    try:
        driver = uc.Chrome(options=options, user_data_dir=user_data_dir)
        wait = WebDriverWait(driver, timeout)
        inject_hardware_noise(driver)
        apply_timezone_override(driver, detected_region)
        apply_geolocation_override(driver, detected_region)
        return BrowserSession(
            driver=driver,
            wait=wait,
            user_data_dir=user_data_dir,
            region_name=detected_region,
            proxy_url=resolved_proxy,
        )
    except Exception:
        shutil.rmtree(user_data_dir, ignore_errors=True)
        raise


def print_browser_environment(region_name: str) -> None:
    """Print the configured browser environment for a region."""

    from config import DEVICE_TYPE
    from helpers.multilang import lang_selector
    from helpers.utils import (
        get_accept_language_for_region,
        get_locale_for_region,
        get_timezone_for_region,
        is_mobile,
    )
    from managers.proxy_manager import proxy_manager

    device_emoji = "📱" if is_mobile() else "💻"
    print(f"\n{device_emoji} === Environment ===")
    print(f"📍 Region: {region_name.upper()}")
    print(f"🖥️  Device: {DEVICE_TYPE.upper()}")
    print(f"🌐 Locale: {get_locale_for_region(region_name)}")
    print(f"🌐 Accept-Language: {get_accept_language_for_region(region_name)}")
    print(f"🕐 Timezone: {get_timezone_for_region(region_name)}")
    lang_selector.print_current_language()
    proxy_manager.print_proxy_info()
    print("=" * 50)


def resolve_browser_proxy(
    *,
    use_configured_proxy: bool = True,
    probe_proxy: bool = False,
    max_proxy_attempts: int = 3,
) -> str | None:
    """Resolve and optionally probe the configured browser proxy."""

    from helpers.utils import probe_proxy_connection
    from managers.proxy_manager import proxy_manager

    if not use_configured_proxy or not proxy_manager.use_proxy:
        return None

    for proxy_attempt in range(max_proxy_attempts):
        proxy_url = proxy_manager.get_proxy()
        if not proxy_url:
            print("⚠️  Failed to obtain proxy")
            continue

        if not probe_proxy:
            return proxy_url

        print("🔍 Probing proxy...")
        try:
            ok, egress = probe_proxy_connection(proxy_url, timeout=8)
            if ok:
                print(f"✅ Proxy OK; egress IP: {egress}")
                return proxy_url
            print(f"⚠️  Proxy probe failed (attempt {proxy_attempt + 1}/{max_proxy_attempts}); retrying...")
        except Exception as e:
            print(f"⚠️  Proxy probe error: {e}")

    raise RuntimeError("All proxy attempts failed. Set region.use_proxy: false in config.yaml to skip proxy.")


def inject_hardware_noise(driver: Any) -> None:
    """Inject basic hardware-ish browser signal variation."""

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
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
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


def apply_timezone_override(driver: Any, region_name: str) -> None:
    """Apply CDP timezone override for the selected region."""

    from helpers.utils import get_timezone_for_region

    try:
        timezone = get_timezone_for_region(region_name)
        driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": timezone})
        print(f"Timezone: {timezone}")
    except Exception as e:
        print(f"Timezone override failed (non-fatal): {e}")


def apply_geolocation_override(driver: Any, region_name: str) -> None:
    """Apply approximate CDP geolocation override for the selected region."""

    geo_locations = {
        "germany": {"latitude": 52.52, "longitude": 13.405, "accuracy": 100},
        "japan": {"latitude": 35.6762, "longitude": 139.6503, "accuracy": 100},
        "usa": {"latitude": 40.7128, "longitude": -74.0060, "accuracy": 100},
    }

    try:
        location = geo_locations.get(region_name, geo_locations["usa"])
        driver.execute_cdp_cmd("Emulation.setGeolocationOverride", location)
        print("Geolocation override applied")
    except Exception as e:
        print(f"Geolocation override failed (non-fatal): {e}")
