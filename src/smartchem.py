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
        page.goto(SMARTCHEM_URL, wait_until="domcontentloaded")
        page.wait_for_selector(SELECTOR_USERNAME)
    except Exception as e:
        print("[error] login page did not load or username selector missing:", e)
        return False

    try:
        page.fill(SELECTOR_USERNAME, SMARTCHEM_USERNAME or "")
        page.fill(SELECTOR_PASSWORD, SMARTCHEM_PASSWORD or "")
        page.click(SELECTOR_LOGIN_BUTTON)
    except Exception as e:
        print("[error] failed to fill or click login:", e)
        return False

    # small wait to allow login navigation
    page.wait_for_timeout(2000)

    # don't pause here (caller decides)
    return True


def search_chemical(page, chemical):
    """
    Robustly fill the chemical input and submit the search.
    Returns True on success, False on failure.
    """
    # selectors from your inspector
    selector_input_candidates = [
        'input#textInputChem',    # primary
        'input[name="T"]',        # alternate shown in inspector
        'div#keyword input',      # defensive
        'input.searchField',      # class alternative
    ]
    submit_anchor_selector = 'a[onclick*="submitChemicalSearchForm"]'
    form_id = "theChemForm"

    input_selector = None
    # 1) find an existing selector
    for sel in selector_input_candidates:
        try:
            page.wait_for_selector(sel, timeout=1000)
            input_selector = sel
            # found it
            break
        except Exception:
            continue

    if not input_selector:
        print("[error] chemical input not found (tried multiple selectors).")
        return False

    # 2) Try to fill in multiple ways
    filled = False
    try:
        # direct fill (fast)
        page.fill(input_selector, chemical)
        # short pause to let any JS auto-complete react
        page.wait_for_timeout(300)
        # verify by reading value
        val = page.eval_on_selector(input_selector, "el => el.value")
        if val and chemical.lower() in val.lower():
            filled = True
    except Exception:
        filled = False

    if not filled:
        try:
            # click then type (more human-like)
            page.click(input_selector)
            page.type(input_selector, chemical, delay=50)  # small delay per char
            page.wait_for_timeout(300)
            val = page.eval_on_selector(input_selector, "el => el.value")
            if val and chemical.lower() in val.lower():
                filled = True
        except Exception:
            filled = False

    if not filled:
        try:
            # JS fallback: set value and dispatch events
            js = (
                "el = document.querySelector(%r);"
                "if(el){ el.value = %r; el.dispatchEvent(new Event('input',{bubbles:true}));"
                "el.dispatchEvent(new Event('change',{bubbles:true})); return el.value;} else return null;"
            ) % (input_selector, chemical)
            val = page.evaluate(js)
            if val and chemical.lower() in val.lower():
                filled = True
        except Exception as e:
            print("[warn] JS fallback to set value failed:", e)
            filled = False

    if not filled:
        print("[error] unable to fill chemical input with any method.")
        return False

    # 3) Submit: try clicking anchor, otherwise call JS submit function
    try:
        page.click(submit_anchor_selector)
        # small wait for results to start loading
        page.wait_for_timeout(1500)
        return True
    except Exception as e_click:
        # fallback to calling the site's JS submit function directly
        try:
            page.evaluate(f"submitChemicalSearchForm(document.getElementById('{form_id}'))")
            page.wait_for_timeout(1500)
            return True
        except Exception as e_eval:
            print("[error] both click and JS submit failed:", e_click, e_eval)
            return False

def click_first_result(page):
    """
    Clicks the first chemical name link in the results table.
    This link always has href starting with 'javascript:getDetailsForChemical'
    """
    selector = 'a[href^="javascript:getDetailsForChemical"]'

    try:
        print("[debug] waiting for first result link...")
        page.wait_for_selector(selector, timeout=6000)
    except Exception as e:
        print("[error] result link not found:", e)
        return False

    try:
        print("[debug] clicking first result link")
        page.click(selector)
        page.wait_for_timeout(2000)
        return True
    except Exception as e:
        print("[error] could not click result link:", e)
        return False
