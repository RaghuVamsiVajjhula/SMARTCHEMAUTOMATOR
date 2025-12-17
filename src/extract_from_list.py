import time
import csv
from pathlib import Path
import re
from smartchem import start_browser, login, search_chemical, click_first_result

CHEMICALS = [                  #Enter list of chemicals for which you want manudacturer list in india.
"Trazodone hydrochloride",
]


def append_results_to_csv(path, results):

    if not results:
        print("[info] No matching suppliers for this chemical — nothing to append.")
        return

    output_file = Path(path)
    file_exists = output_file.exists()

    with output_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["chemical", "supplier_name", "company_type", "country"])

        if file_exists:
            writer.writerow([])

        for r in results:
            writer.writerow([
                r["chemical"],
                r["supplier_name"],
                r["company_type"],
                r["country"]
            ])

    print(f"[success] Appended {len(results)} rows to {path}")

def has_m_or_cm(type_str):

    if not type_str:
        return False

    tokens = re.split(r'[^A-Za-z0-9]+', type_str.strip().upper())
    tokens = [t for t in tokens if t]

    return ("M" in tokens) or ("CM" in tokens)

def find_suppliers_table(page):
    tables = page.query_selector_all("table")
    for t in tables:
        try:
            txt = (t.inner_text() or "").lower()
            if ("company details" in txt) or ("type of company" in txt) or ("country" in txt):
                return t
        except:
            continue
    return None

def detect_column_indices(table):
    hdr_cells = []
    thead = table.query_selector("thead")
    if thead:
        row = thead.query_selector("tr")
        if row:
            hdr_cells = row.query_selector_all("th")

    if not hdr_cells:
        row = table.query_selector("tr")
        if row:
            hdr_cells = row.query_selector_all("th,td")

    headers = [(c.inner_text() or "").strip().lower() for c in hdr_cells]

    name_idx = next((i for i, h in enumerate(headers)
                     if "company" in h or "supplier" in h or "name" in h), None)
    country_idx = next((i for i, h in enumerate(headers) if "country" in h), None)
    type_idx = next((i for i, h in enumerate(headers) if "type" in h), None)

    if None in (name_idx, country_idx, type_idx):
        first_row = table.query_selector("tbody tr") or table.query_selector("tr:nth-of-type(2)")
        if first_row:
            tds = first_row.query_selector_all("td")
            if len(tds) >= 3:
                name_idx = name_idx if name_idx is not None else 0
                country_idx = country_idx if country_idx is not None else 1
                type_idx = type_idx if type_idx is not None else 2

    if None in (name_idx, country_idx, type_idx):
        return None

    return name_idx, country_idx, type_idx


def extract_suppliers_from_table(table, name_idx, country_idx, type_idx):
    rows = table.query_selector_all("tbody tr") or table.query_selector_all("tr")[1:]
    out = []

    for r in rows:
        try:
            cols = r.query_selector_all("td")
            if len(cols) > max(name_idx, country_idx, type_idx):
                out.append({
                    "supplier_name": (cols[name_idx].inner_text() or "").strip(),
                    "country": (cols[country_idx].inner_text() or "").strip(),
                    "company_type": (cols[type_idx].inner_text() or "").strip()
                })
        except:
            continue

    return out



def go_to_home(page):
    try:
        page.wait_for_selector(
            'a[href*="MemberServlet"][href*="requestType=1101"]',
            timeout=5000
        )
        page.click('a[href*="MemberServlet"][href*="requestType=1101"]')
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        print("[info] Navigated back to Home page.")
        return True
    except:
        try:
            page.click("text=Home")
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            print("[info] Navigated back to Home page (fallback).")
            return True
        except:
            print("[error] Failed to navigate to Home.")
            return False

def main():
    out_file = "manufacturers_output.csv"
    p, browser, context, page = start_browser(headless=False)

    try:
        ok = login(page)
        if not ok:
            print("[error] Login failed.")
            return

        time.sleep(1)

        for chem in CHEMICALS:
            print(f"\n🔍 Searching chemical: {chem}")

            if not search_chemical(page, chem):
                print(f"[warn] Could not search for {chem}")
                continue

            if not click_first_result(page):
                print(f"[warn] No results found for {chem}")
                continue

            page.wait_for_load_state("networkidle")
            time.sleep(1)

            try:
                if page.query_selector("text=Suppliers"):
                    page.click("text=Suppliers")
                    time.sleep(1)
            except:
                pass

            table = find_suppliers_table(page)
            if not table:
                print(f"[warn] No suppliers table for {chem}")
                go_to_home(page)
                continue

            idxs = detect_column_indices(table)
            if not idxs:
                print(f"[warn] Column detection failed for {chem}")
                go_to_home(page)
                continue

            name_idx, country_idx, type_idx = idxs
            rows = extract_suppliers_from_table(table, name_idx, country_idx, type_idx)

            final_rows = []
            for rec in rows:
                if rec["country"].lower() == "india" and has_m_or_cm(rec["company_type"]):
                    final_rows.append({
                        "chemical": chem,
                        "supplier_name": rec["supplier_name"],
                        "company_type": rec["company_type"],
                        "country": rec["country"]
                    })

            append_results_to_csv(out_file, final_rows)

            if not go_to_home(page):
                print("[fatal] Script stopped due to navigation failure.")
                break

            time.sleep(0.5)

    finally:
        try:
            browser.close()
            p.stop()
        except:
            pass


if __name__ == "__main__":
    main()
