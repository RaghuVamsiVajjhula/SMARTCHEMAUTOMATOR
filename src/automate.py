# src/automate.py
from smartchem import start_browser, login, search_chemical
import traceback

def main():
    p, browser, context, page = start_browser(headless=False)

    try:
        ok = login(page, pause_after=False)
        if not ok:
            print("Login failed. Exiting.")
            return

        # HARD-CODED chemical name (change as needed)
        chemical_to_search = "Tributylamine"

        print(f"[info] searching for: {chemical_to_search}")
        ok2 = search_chemical(page, chemical_to_search)
        if ok2:
            print("[info] search submitted (no pause).")
        else:
            print("[error] search failed.")

        # allow a moment for results to render before we close
        page.wait_for_timeout(2500)

    except Exception:
        print("Exception during automation:")
        traceback.print_exc()

    finally:
        try:
            browser.close()
            p.stop()
        except:
            pass
    print("Script finished.")

if __name__ == "__main__":
    main()
