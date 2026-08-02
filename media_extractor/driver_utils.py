"""
Browser driver lifecycle helpers.

seleniumbase is imported lazily (inside the function, not at module load
time) so the rest of this package stays importable — and unit-testable —
in environments without a full undetected-Chrome/CDP stack installed.
"""

from typing import Any


def create_driver() -> Any:
    """Initialize and return an undetected Chrome driver."""
    from seleniumbase import Driver

    driver = Driver(uc_cdp=True, uc=True)
    driver.implicitly_wait(5)
    return driver


def quit_driver(driver: Any) -> None:
    """Safely tear down a driver instance, if one is active."""
    if driver:
        driver.quit()
