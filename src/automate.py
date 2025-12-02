from smartchem import start_browser, login, search_chemical, click_first_result
import traceback

def main():
    p, browser, context, page = start_browser(headless=False)

    try:
        ok = login(page)
        if not ok:
            print("Login failed")
            return

        chemical = "Tributylamine"   # hard-coded

        print(f"[info] Searching: {chemical}")
        ok2 = search_chemical(page, chemical)
        if not ok2:
            print("Search failed")
            return

        print("[info] Clicking the first result link...")
        ok3 = click_first_result(page)
        if ok3:
            print("[info] Result opened successfully!")
        else:
            print("[error] Could not open the result!")

        page.wait_for_timeout(3000)

    except Exception:
        traceback.print_exc()
    finally:
        try:
            browser.close()
            p.stop()
        except:
            pass

if __name__ == "__main__":
    main()
