import random
import time
from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


def jitter_delay(min_sec: float = 0.5, max_sec: float = 2.0) -> None:
    """Sleep for a randomized interval."""

    if random.random() < 0.15:
        time.sleep(random.uniform(2.5, 5.0))
    time.sleep(random.uniform(min_sec, max_sec))


def type_text(element: Any, text: str) -> None:
    """Type text into a Selenium element with small timing variation."""

    speed_factor = random.uniform(0.7, 1.3)
    for char in text:
        element.send_keys(char)
        delay = random.uniform(0.04, 0.15) * speed_factor
        if random.random() < 0.05:
            delay += random.uniform(0.2, 0.5)
        time.sleep(delay)


def click_element(driver: Any, element: Any) -> None:
    """Click a Selenium element with a JS fallback."""

    try:
        action = ActionChains(driver)
        action.move_to_element_with_offset(
            element,
            random.randint(-5, 5),
            random.randint(-5, 5),
        )
        action.perform()
        time.sleep(random.uniform(0.1, 0.4))
        action.click_and_hold().pause(random.uniform(0.05, 0.15)).release().perform()
    except Exception:
        try:
            element.click()
        except Exception:
            driver.execute_script("arguments[0].click();", element)


def safe_input(
    wait: Any,
    selector: tuple[str, str],
    value: str,
    *,
    max_retries: int = 3,
) -> bool:
    """Fill an input with stale-element retries."""

    for attempt in range(max_retries):
        try:
            element = wait.until(EC.presence_of_element_located(selector))
            element.click()
            jitter_delay(0.3, 0.8)
            element.clear()
            type_text(element, value)
            return True
        except Exception:
            if attempt < max_retries - 1:
                print(f"   Input retry {attempt + 1}/{max_retries}...")
                jitter_delay(1, 2)
            else:
                raise
    return False


def page_contains_any(driver: Any, needles: list[str]) -> bool:
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
