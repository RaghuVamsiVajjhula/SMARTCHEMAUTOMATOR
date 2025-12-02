# src/smartchem.py
from playwright.sync_api import sync_playwright, TimeoutError
from config import SMARTCHEM_URL, SMARTCHEM_USERNAME, SMARTCHEM_PASSWORD
from config import SELECTOR_USERNAME, SELECTOR_PASSWORD, SELECTOR_LOGIN_BUTTON
import time

def start_browser(headless=False):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    return p, browser, context, page

def login(page, pause_after=False):
    try:
        print(f"[debug] going to: {SMARTCHEM_URL}")
        page.goto(SMARTCHEM_URL, wait_until="domcontentloaded")
        page.wait_for_selector(SELECTOR_USERNAME, timeout=8000)
    except TimeoutError:
        print("[error] login page did not load or username selector not found.")
        return False
    except Exception as e:
        print("[error] unexpected error while loading login page:", e)
        return False

    try:
        page.fill(SELECTOR_USERNAME, SMARTCHEM_USERNAME or "")
        print("[debug] username filled")
        page.fill(SELECTOR_PASSWORD, SMARTCHEM_PASSWORD or "")
        print("[debug] password filled")
        page.click(SELECTOR_LOGIN_BUTTON)
        print("[debug] clicked login button")
    except Exception as e:
        print("[error] failed to fill/click login:", e)
        return False

    page.wait_for_timeout(3000)

    if pause_after:
        print("[debug] paused after login. Inspect the browser and press ENTER in terminal to continue.")
        input("Press ENTER to continue...")

    return True




