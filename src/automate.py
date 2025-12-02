# src/automate.py
from smartchem import start_browser, login
import traceback

def main():
    p, browser, context, page = start_browser(headless=False)
    try:
        ok = login(page, pause_after=True)
        if ok:
            print("Login flow executed (see browser).")
        else:
            print("Login flow did NOT complete successfully.")
    except Exception:
        print("Exception during automation:")
        traceback.print_exc()
    finally:
        try:
            browser.close()
            p.stop()
        except Exception:
            pass
    print("Script finished.")

if __name__ == "__main__":
    main()




    
