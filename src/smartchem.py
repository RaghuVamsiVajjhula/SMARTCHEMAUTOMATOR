from playwright.sync_api import sync_playwright
from config import SMARTCHEM_URL, SMARTCHEM_USERNAME, SMARTCHEM_PASSWORD
from config import SELECTOR_USERNAME, SELECTOR_PASSWORD, SELECTOR_LOGIN_BUTTON
import time, re
from pathlib import Path
from urllib.parse import urljoin

def wait_for_selector_safe(page, selector, timeout_ms=5000, poll_interval=0.25):

    elapsed = 0.0
    while elapsed < (timeout_ms / 1000.0):
        try:
            el = page.query_selector(selector)
            if el:
                return True
        except Exception:
            pass
        time.sleep(poll_interval)
        elapsed += poll_interval
    return False

def start_browser(headless=False):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    return p, browser, context, page


def login(page, pause_after=False):
    try:
        page.goto(SMARTCHEM_URL, wait_until="domcontentloaded")
    except Exception as e:
        print("[error] could not navigate to SMARTCHEM_URL:", e)
        return False

    if not wait_for_selector_safe(page, SELECTOR_USERNAME, timeout_ms=40000):
        print("[error] username selector not found on login page.")
        return False

    try:
        page.fill(SELECTOR_USERNAME, SMARTCHEM_USERNAME or "")
        page.fill(SELECTOR_PASSWORD, SMARTCHEM_PASSWORD or "")
        page.click(SELECTOR_LOGIN_BUTTON)
    except Exception as e:
        print("[error] failed to fill or click login controls:", e)
        return False

    time.sleep(1.5)

    if pause_after:
        print("[debug] paused after login; press ENTER in terminal to continue")
        input("Press ENTER to continue...")

    return True

def search_chemical(page, chemical):
    selector_input_candidates = [
        'input#textInputChem',
        'input[name="T"]',
        'div#keyword input',
        'input.searchField',
    ]
    submit_anchor_selector = 'a[onclick*="submitChemicalSearchForm"]'
    form_id = "theChemForm"

    input_selector = None
    for sel in selector_input_candidates:
        if wait_for_selector_safe(page, sel, timeout_ms=1200):
            input_selector = sel
            break

    if not input_selector:
        print("[error] chemical search input not found (tried multiple selectors).")
        return False

    filled = False
    try:
        page.fill(input_selector, chemical)
        time.sleep(0.2)
        val = page.eval_on_selector(input_selector, "el => el.value")
        if val and chemical.lower() in val.lower():
            filled = True
    except Exception:
        filled = False

    if not filled:
        try:
            page.click(input_selector)
            page.type(input_selector, chemical, delay=40)
            time.sleep(0.2)
            val = page.eval_on_selector(input_selector, "el => el.value")
            if val and chemical.lower() in val.lower():
                filled = True
        except Exception:
            filled = False

    if not filled:
        try:
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

    try:
        if wait_for_selector_safe(page, submit_anchor_selector, timeout_ms=2000):
            page.click(submit_anchor_selector)
            time.sleep(1.0)
            return True
    except Exception as e:
        print("[warn] clicking submit anchor failed:", e)

    try:
        page.evaluate(f"submitChemicalSearchForm(document.getElementById('{form_id}'))")
        time.sleep(1.0)
        return True
    except Exception as e:
        print("[error] both click and JS submit failed:", e)
        return False

def click_first_result(page):
    selector = 'a[href^="javascript:getDetailsForChemical"]'
    if not wait_for_selector_safe(page, selector, timeout_ms=8000):
        print("[error] first result link not found")
        return False

    try:
        page.click(selector)
        time.sleep(1.5)
        return True
    except Exception as e:
        print("[error] could not click first result link:", e)
        return False

def click_applications_tab(page):
    candidates = [
        'text=Applications',
        'a[href^="javascript:getDetailsForChemical"] >> text=Applications',
        'a[onclick*="getDetailsForChemical"] >> text=Applications',
        'li:has-text("Applications")',
    ]
    for sel in candidates:
        if wait_for_selector_safe(page, sel, timeout_ms=2000):
            try:
                page.click(sel)
                time.sleep(1.0)
                print("[debug] clicked Applications using selector:", sel)
                return True
            except Exception as e:
                print("[warn] clicking Applications via selector failed:", sel, e)
                continue
    print("[error] could not find or click Applications tab")
    return False

def _extract_url_from_onclick(onclick_value: str):
    if not onclick_value:
        return None
    m = re.search(r"['\"](\/[^'\"]+)['\"]", onclick_value)
    if m:
        return m.group(1)
    m2 = re.search(r"(https?:\/\/[^\s'\"()]+)", onclick_value)
    if m2:
        return m2.group(1)
    return None


def download_applications_excel(page, save_folder="downloads"):
    downloads_dir = Path(save_folder)
    downloads_dir.mkdir(parents=True, exist_ok=True)

    download_anchor_selector = 'a[onclick*="downloadType=3"], a[onclick*="downloadType"]'
    download_img_selector = 'img[src*="dw.png"], img[title^="Download Chemical"]'

    found_sel = None
    if wait_for_selector_safe(page, download_anchor_selector, timeout_ms=6000):
        found_sel = download_anchor_selector
    elif wait_for_selector_safe(page, download_img_selector, timeout_ms=6000):
        found_sel = download_img_selector
    else:
        print("[error] download control not found in Applications area (tried anchor & image).")
        return None

    try:
        print("[debug] trying click+expect_download on:", found_sel)
        with page.expect_download() as download_info:
            page.click(found_sel)
        download = download_info.value
        suggested = download.suggested_filename or "applications.xlsx"
        save_path = downloads_dir / suggested
        download.save_as(str(save_path))
        print("[debug] download saved to:", save_path)
        return str(save_path)
    except Exception as e_click:
        print("[warn] click+expect_download failed or no download event:", e_click)

    try:
        onclick_val = None
        el = page.query_selector(download_anchor_selector)
        if el:
            onclick_val = page.get_attribute(download_anchor_selector, "onclick")
        else:
            img_parent = page.query_selector(f"{download_img_selector} >> xpath=..")
            if img_parent:
                onclick_val = img_parent.get_attribute("onclick")
            else:
                any_anchor = page.query_selector('a[onclick*="downloadType"]')
                if any_anchor:
                    onclick_val = any_anchor.get_attribute("onclick")

        if not onclick_val:
            print("[error] no onclick attribute found for download control (fallback).")
            return None

        print("[debug] onclick (excerpt):", (onclick_val or "")[:200])

        url_path = _extract_url_from_onclick(onclick_val)
        if not url_path:
            print("[error] could not extract URL from onclick.")
            return None

        download_url = urljoin(SMARTCHEM_URL, url_path)
        print("[debug] fallback download URL:", download_url)

        ctx = page.context
        new_page = ctx.new_page()
        try:
            with new_page.expect_download() as dl_info:
                new_page.goto(download_url)
            download = dl_info.value
            suggested = download.suggested_filename or "applications.xlsx"
            save_path = downloads_dir / suggested
            download.save_as(str(save_path))
            print("[debug] fallback download saved to:", save_path)
            try:
                new_page.close()
            except:
                pass
            return str(save_path)
        except Exception as e_nav:
            print("[error] navigation download fallback failed:", e_nav)
            try:
                new_page.close()
            except:
                pass
            return None

    except Exception as e_final:
        print("[error] download fallback logic error:", e_final)
        return None
