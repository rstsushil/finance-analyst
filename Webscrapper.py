from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import requests
import time
import os
from flask import Flask, request, jsonify
app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Referer": "https://www.bseindia.com/"
}

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    return webdriver.Chrome(options=options)

def close_popup_if_present(driver, wait):
    try:
        close_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.btn-close[data-bs-dismiss='modal']")))
        close_button.click()
        print("[INFO] Popup closed.")
    except:
        print("[INFO] No popup shown.")

def search_company(driver, wait, company_name):
    search_box = wait.until(EC.presence_of_element_located((By.ID, "getquotesearch")))
    search_box.send_keys(company_name)
    time.sleep(1)
    search_box.send_keys(Keys.ENTER)
    time.sleep(5)
    print(f"[INFO] Redirected to: {driver.current_url}")

def click_financials_tab(driver, wait):
    try:
        financials_heading = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[@id='l6']//div[@id='heading2']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", financials_heading)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", financials_heading)
        print("[INFO] Expanded Financials section.")
    except Exception as e:
        raise Exception(f"Financials expandable section not found: {e}")

def click_annual_reports(driver, wait):
    try:
        annual_link = wait.until(EC.element_to_be_clickable((By.ID, "l62")))
        href = annual_link.get_attribute("href")
        full_url = urljoin("https://www.bseindia.com", href)
        print(f"[INFO] Navigating to Annual Reports: {full_url}")
        annual_link.click()
        time.sleep(12)
    except Exception as e:
        raise Exception(f"Annual Reports link not found: {e}")

def extract_top2_annual_report_pdfs(driver):
    try:
        print("[INFO] Waiting for the annual report table to load...")
        WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located(
            (By.XPATH, "//table[contains(@ng-if, 'loader.ARState') and contains(@class, 'ng-scope')]//tbody/tr")
        ))

        rows = driver.find_elements(By.XPATH, "//table[contains(@ng-if, 'loader.ARState') and contains(@class, 'ng-scope')]//tbody/tr")
        reports = []

        for row in rows:
            try:
                year = row.find_element(By.XPATH, "./td[1]").text.strip()
                link = row.find_element(By.XPATH, ".//a[contains(@href, '.pdf')]").get_attribute("href")

                # Fix malformed URL
                link = link.replace("AttachHis//", "AttachHis/")

                if year.isdigit():
                    reports.append((int(year), link))
            except:
                continue

        top2 = sorted(reports, key=lambda x: x[0], reverse=True)[:2]

        print("\n[RESULT] Top 2 Annual Report PDF URLs:")
        for year, link in top2:
            print(f"{year}: {link}")

        download_pdfs(top2)
        return top2

    except Exception as e:
        print(f"[ERROR] Could not extract report URLs: {e}")
        return []

def download_pdfs(reports):
    for year, url in reports:
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            filename = f"{year}_report.pdf"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"[INFO] Downloaded: {filename}")
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")

def extract_annual_report_links(company_name):
    driver = setup_driver()
    wait = WebDriverWait(driver, 15)
    try:
        driver.get("https://www.bseindia.com/")
        time.sleep(3)
        close_popup_if_present(driver, wait)
        search_company(driver, wait, company_name)
        click_financials_tab(driver, wait)
        click_annual_reports(driver, wait)
        extract_top2_annual_report_pdfs(driver)
    except Exception as e:
        print("[ERROR]", e)
    finally:
        driver.quit()

@app.route('/fetch_annual_reports', methods=['POST'])
def fetch_annual_reports():
    data = request.json
    company_name = data.get("input")

    if not company_name:
        return jsonify({"status": "error", "message": "Missing 'company_name' in request."}), 400

    result = extract_annual_report_links(company_name)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
# # âœ… Run the script
# extract_annual_report_links("Tech Mahindra")
