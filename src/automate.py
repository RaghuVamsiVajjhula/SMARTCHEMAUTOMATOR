from smartchem import (
    start_browser,
    login,
    search_chemical,
    click_first_result,
    click_applications_tab,
    download_applications_excel,
)
import traceback
from pathlib import Path

def main():
    p, browser, context, page = start_browser(headless=False)

    try:
        ok = login(page)
        if not ok:
            print("[error] Login failed. Exiting.")
            return
        print("[info] Logged in successfully.")

        
        chemical = "19794-93-5"                #Enter chemical name here and it will download
                                                    # an excel sheet with list of appliactions.


        print(f"[info] Searching for: {chemical}")
        ok2 = search_chemical(page, chemical)
        if not ok2:
            print("[error] Search failed. Exiting.")
            return
        print("[info] Search submitted.")

        print("[info] Clicking the first search result...")
        ok3 = click_first_result(page)
        if not ok3:
            print("[error] Could not open the first result. Exiting.")
            return
        print("[info] First result opened.")

        page.wait_for_timeout(1200)

        print("[info] Opening Applications tab...")
        ok_app = click_applications_tab(page)
        if not ok_app:
            print("[error] Could not open Applications tab. Exiting.")
            return
        print("[info] Applications tab clicked.")


        page.wait_for_timeout(1200)

        print("[info] Attempting to download Applications Excel...")
        download_path = download_applications_excel(page, save_folder="downloads")
        if download_path:
            saved = Path(download_path).resolve()
            print(f"[success] Applications Excel downloaded to: {saved}")
        else:
            print("[error] Failed to download the Applications Excel.")

        page.wait_for_timeout(1000)

    except Exception:
        print("[exception] Unexpected error during automation:")
        traceback.print_exc()
    finally:
        try:
            browser.close()
            p.stop()
        except Exception:
            pass

    print("[info] Script finished.")

if __name__ == "__main__":
    main()
