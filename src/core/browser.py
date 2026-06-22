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

    def close(self) -> None:
        """Close the browser and remove the temporary profile."""

        try:
            if self.driver:
                try:
                    self.driver.quit()
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
        get_timezone_for_region,
        get_user_agent_for_region,
        is_mobile,
    )
    from managers.proxy_manager import proxy_manager

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
    options.add_argument(f"--user-agent={get_user_agent_for_region(detected_region)}")

    resolved_proxy = proxy_url
    if not resolved_proxy and use_configured_proxy and proxy_manager.use_proxy:
        resolved_proxy = proxy_manager.get_proxy()
    if resolved_proxy:
        options.add_argument(f"--proxy-server={resolved_proxy}")

    user_data_dir = tempfile.mkdtemp(prefix=f"{profile_prefix}{random.randint(1000, 9999)}_")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    try:
        driver = uc.Chrome(options=options, user_data_dir=user_data_dir)
        wait = WebDriverWait(driver, timeout)
        try:
            driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {
                "timezoneId": get_timezone_for_region(detected_region),
            })
        except Exception:
            pass
        return BrowserSession(driver=driver, wait=wait, user_data_dir=user_data_dir)
    except Exception:
        shutil.rmtree(user_data_dir, ignore_errors=True)
        raise
