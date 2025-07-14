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
import os
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document as LangchainDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF
import re
from langchain.vectorstores import FAISS
from langchain.embeddings import AzureOpenAIEmbeddings
from openai import AzureOpenAI
import os,time
from langchain_community.chat_models import AzureChatOpenAI
from bs4 import BeautifulSoup
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pdf2docx import Converter
import os



# ENV setup
os.environ["OPENAI_API_VERSION"] = "2023-05-15"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://oai-gen.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "b3ada68f77114d6e856dfa777ea42ef0"
llm = AzureChatOpenAI(deployment_name="gpt_4o", temperature=0)
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

vectorstores=None
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Referer": "https://www.bseindia.com/"
}

import os

def clear_pdf_folder(folder="pdf"):
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"[INFO] Removed: {file_path}")
            except Exception as e:
                print(f"[ERROR] Failed to remove {file_path}: {e}")
    else:
        print(f"[WARNING] Folder '{folder}' does not exist.")

# Call the function

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
        time.sleep(20)
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

'''def download_pdfs(reports):
    for year, url in reports:
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            filename = f"{year}_report.pdf"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"[INFO] Downloaded: {filename}")
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")'''

def download_pdfs(reports):
    # Ensure 'pdf' folder exists
    pdf_folder = "pdf"
    os.makedirs(pdf_folder, exist_ok=True)

    for year, url in reports:
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            filename = os.path.join(pdf_folder, f"{year}_report.pdf")
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
    clear_pdf_folder()

    if not company_name:
        return jsonify({"status": "error", "message": "Missing 'company_name' in request."}), 400

    result = extract_annual_report_links(company_name)
    return ("file successfully downloaded")

#------------------------------------Embedding--------------------------------------
# Folders
input_folder = r"/Users/sushiltiwari/Documents/Agentic AI_ICICI/pdf"
faiss_folder = "vector_stores_new"
os.makedirs(faiss_folder, exist_ok=True)

# --- Heading + Table Detection Logic ---

def is_likely_table_heading(text):
    return bool(re.match(r"^\d+(\.\d+)*\s+", text)) or text.strip().isupper()

def is_likely_table_block(text):
    lines = text.split("\n")
    if len(lines) < 2:
        return False
    structured_lines = 0
    for line in lines:
        if len(re.split(r'\s{2,}|\t', line.strip())) >= 2:
            structured_lines += 1
    return structured_lines >= 2

def read_pdf_with_heading_and_table_blocks(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        blocks = []
        last_heading = None
        table_index = 0

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_blocks = page.get_text("blocks")

            sorted_blocks = sorted(page_blocks, key=lambda b: b[1])  # Sort by vertical position

            for block in sorted_blocks:
                text = block[4].strip()
                if not text or len(text) < 2:
                    continue

                if is_likely_table_heading(text):
                    last_heading = text
                elif is_likely_table_block(text):
                    table_index += 1
                    if last_heading:
                        combined = f"{last_heading}\nTable {table_index}:\n{text}"
                        blocks.append(combined.strip())
                        last_heading = None
                    else:
                        blocks.append(f"Table {table_index}:\n{text}")
                else:
                    blocks.append(text.strip())

        return blocks
    except Exception as e:
        raise RuntimeError(f"Error reading PDF '{pdf_path}': {e}")

# --- Split into Langchain Documents ---

def prepare_langchain_docs(text_blocks):
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=500)
        docs = []
        for block in text_blocks:
            for chunk in splitter.split_text(block):
                docs.append(LangchainDocument(page_content=chunk))
        return docs
    except Exception as e:
        raise RuntimeError(f"Error during text splitting: {e}")

# --- Embed and Save Vectorstore ---

def embed_and_save_vectorstore(docs, base_name):
    try:
        embeddings = AzureOpenAIEmbeddings(
            deployment="text-embedding-ada-002",
            model="text-embedding-ada-002",
            chunk_size=1000
        )
        vectorstore = FAISS.from_documents(docs, embedding=embeddings)
        vectorstore.save_local(os.path.join(faiss_folder, base_name))
        print(f"✅ Saved vectorstore for '{base_name}' at: {faiss_folder}/{base_name}")
    except Exception as e:
        raise RuntimeError(f"Error embedding or saving vectorstore for '{base_name}': {e}")

# --- Process All PDFs in Folder ---
def process_all_pdfs():
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"Input folder does not exist: {input_folder}")
   
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]
    if not pdf_files:
        raise FileNotFoundError("No PDF files found in the input folder.")

    results = {
        "success": [],
        "failed": []
    }

    for file in pdf_files:
        base = os.path.splitext(file)[0]
        pdf_path = os.path.join(input_folder, file)

        print(f"📄 Processing PDF: {file}")
        try:
            blocks = read_pdf_with_heading_and_table_blocks(pdf_path)
            docs = prepare_langchain_docs(blocks)
            embed_and_save_vectorstore(docs, base)
            results["success"].append(file)
        except Exception as e:
            print(f"❌ Failed to process {file}: {e}")
            results["failed"].append({"file": file, "error": str(e)})
   
    return results


# --- Flask Endpoint ---

@app.route('/run-process', methods=['POST'])
def run_process():
    try:
        results = process_all_pdfs()

        if results["failed"]:
            return jsonify({
                "status": "partial_success",
                "message": "Some files failed during processing.",
                "results": results
            }), 207  # 207 Multi-Status for partial success
        else:
            return jsonify({
                "status": "success",
                "message": "All PDF files processed successfully.",
                "results": results
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to process files due to: {str(e)}"
        }), 500

embedding_model = AzureOpenAIEmbeddings(
    deployment="text-embedding-ada-002",
    model="text-embedding-ada-002",
    chunk_size=1000
)
# ----------------------
# Load Vectorstores
# ----------------------

# FAISS_FOLDER_ROOT = r"C:\Users\SJ00969837\Downloads\Pdf_information\moneycontrol_data\faiss_outputs"

# vectorstores_money_control = []
# for folder in os.listdir(FAISS_FOLDER_ROOT):
#     path = os.path.join(FAISS_FOLDER_ROOT, folder)
#     if os.path.isdir(path):
#         try:
#             store = FAISS.load_local(
#                 folder_path=path,
#                 embeddings=embedding_model,
#                 allow_dangerous_deserialization=True
#             )
#             vectorstores_money_control.append((folder, store))
#         except Exception as e:
#             print(f"⚠️ Skipping {folder}: {e}")
import os
from langchain.vectorstores import FAISS

def load_all_vectorstores(parent_dir: str) -> list:
    """
    Load all FAISS vector stores from subdirectories under the given parent directory.

    Args:
        parent_dir (str): Path to the main directory containing FAISS vector stores.
        embedding_model: Embedding model used to load the vector stores.

    Returns:
        List[Tuple[str, FAISS]]: A list of tuples (subdir_name, vectorstore)
    """
    vectorstores = []

    if not os.path.exists(parent_dir):
        raise FileNotFoundError(f"❌ Directory not found: {parent_dir}")

    for subdir in os.listdir(parent_dir):
        full_path = os.path.join(parent_dir, subdir)
        if os.path.isdir(full_path):
            try:
                store = FAISS.load_local(
                    folder_path=full_path,
                    embeddings=embedding_model,
                    allow_dangerous_deserialization=True  # ⚠️ Use with trusted data only
                )
                vectorstores.append((subdir, store))
            except Exception as e:
                print(f"⚠️ Failed to load FAISS store from {full_path}: {e}")

    return vectorstores

'''VECTOR_DIRS = [
    # "vector_stores_new/integrated-annual-report-fy-2022-23",
    "vector_stores_new/2024_report",
    "vector_stores_new/2025_report"
]

vectorstores = []
for path in VECTOR_DIRS:
    name = os.path.basename(path)
    store = FAISS.load_local(
    folder_path=path,
    embeddings=embedding_model,
    allow_dangerous_deserialization=True  # ✅ TRUSTED source only
)
    vectorstores.append((name, store))'''

# ----------------------
# User Query
# ----------------------

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key="b3ada68f77114d6e856dfa777ea42ef0",
    api_version="2023-05-15",
    azure_endpoint="https://oai-gen.openai.azure.com/"
)

import re
#"Please provide defaulter and credit history details including RBI defaulters' list status (for borrower, directors, partners, proprietors, guarantors), any connection to past NPA/OTS/Write-off cases (with shareholding details and justification, if applicable), CIBIL report references (consumer and commercial), reference to ECGC Specific Approval List (in case of export finance), and any pending litigation against promoters, partners, or directors.",
# Assume you already have this list prepared
user_questions = [
    " what is the name of company for which you have financial data about and what is its branch zone, business activity,type of industry, activity code,and category(company type- large/medium/small)",
    "Please provide the credit rating details as per the latest assessment from external rating agencies, including the name of the rating agency and the rating assigned to the borrower/account.",
    "Please provide the complete borrower profile that includes date of incorporation/inception, banking relationship start date with us, registered office and factory addresses where factory has its plant, constitution type(type of company private limited or public limited), borrowing powers (if any), and size/segment classification options(MSME / Medium / Large) what it is among these 3. Please provide all the asked information",
    "Please provide ownership and governance-related details, including names, designations, and shareholding of all Directors/Partners,others(include Nationalised Banks,Alternative Investment Fund  ,Bodies Corporate - Non Banking Financial Companies  ,IEPF) and public (Resident Individuals); whether the proposal attracts Connected Lending or Section 20 conditions (Yes/No); Also give all shareholding pattern as on the last quarter  (type of holders, % holding, % holding net of pledged shares, and paid-up capital); and, for listed companies, the face value, current market price, 52-week high/low, and market capitalization.Provide and fetch all the information",
    "there are several question in this answer all Please confirm whether the borrower and all associated individuals/entities (including promotors,directors, partners, proprietors, and guarantors) appear in any of the following: the RBI Defaulters’ List, any past NPA/OTS/Write-off cases (including details of shareholding, amount, and % held), the CIBIL consumer or commercial lists, the ECGC Specific Approval List (if applicable), or have any pending litigation. Also, if there are any name matches in the RBI list, indicate whether suitable affidavits have been obtained. Additionally, provide reasons for recommending the case if any such negative records exist for all the questions mentioned. Attach the relevant CIBIL reports.",  
   
    # "Please provide the audited consolidated financial figures for FY2023, FY2024, and FY2025, including the following details for each year: Net Sales (with units in ₹ lakhs or crores), percentage increase or decrease in Net Sales compared to the previous year, EBITDA and its percentage to Net Sales, Net Profit After Tax (PAT) and its percentage to Net Sales, Cash Accruals, Tangible Net Worth (excluding revaluation reserves and quasi equity), TOL/TNW ratio, Net Working Capital, Current Ratio, and DSCR. Additionally, indicate the units used (₹ in lakhs or crores), specify if any item is not applicable, ",
   
    "Please provide the audited consolidated financial figures for FY2023, FY2024, and FY2025, including the following details for each year: Net Sales (with units in billion), EBITDA and its percentage to Net Sales(example Give Ebita value along with its percentage to Net Sales ), Give Net Profit After Tax (PAT) value and its percentage to Net Sales Value, Cash Accruals( calculate by cash accural=Net Profit + Depreciation + Non-cash Expenses), Tangible Net Worth (excluding revaluation reserves and quasi equity)(Use formula Tangible Net Worth = Total Assets - Total Liabilities - Intangible Assets), Total Debt,TOL/TNW ratio, TD/EBIDTA, Current Ratio, and DSCR. Additionally, indicate the units used (₹ in billion), specify if any item is not applicable, ",
   
    "Please provide a comprehensive note covering the following aspects: they are ,Background in brief (of promoters, their experience, past dealings): Include details of the activities carried out by the promoters, the business model pursued, and any special or noteworthy aspects that should be highlighted.,Conduct of Accounts: Comment on the compliance with terms and conditions, operation of accounts, repayment history (including term loans and LC/BG commitments), routing of funds, bill operations, drawing power availability, upkeep of key accounting records, average utilization of credit limits, and whether the account has ever been restructured. Mention any adverse features observed. Additionally, provide the name of the company’s auditors and any qualifying remarks they may have made. and last one is Industry Scenario: Comment on any significant developments within the company’s industry that may impact its performance or outlook like((a)Stable demand growth and increase in utilisation rates envisaged:(b).• Consolidated domestic industry: ,About are of operation",
    #"Please mention any qualifying comments made by the company’s auditors, and provide a brief but descriptive note on the overall industry scenario and any significant developments or changes that have affected or are expected to affect the applicant company’s financial position or operations.",
    "Please provide the standalone Profitability Analysis for the company on a % to Sales basis for the following financial years — FY2023 (Audited), FY2024 (Audited), FY2025 (Audited),For each year, specify the values for: Total Sales, RM and Spares, RM and Spares, Freight and Transport, Employee Cost, and Depreciation, ",
    "Please provide the cost-related profitability metrics for the company as a percentage of Sales for each of the following financial years — FY2023 (Audited), FY2024 (Audited), FY2025 (Audited), Specifically, provide values for: Other Expenses, Total Exp Before Interest%, Profit Before interest %,",
   
    "Please provide the profitability and income metrics as a percentage of Sales for the company for each of the following financial years — FY2023 (Audited), FY2024 (Audited), FY2025 (Audited),  For each year, specify: Interest %, Profit After Interest %, Profit Before Tax (PBT) %, and Profit After Tax (PAT) %.",
   
    "Please provide key financial indicators for FY2023 to FY2025, including  EBITDA and its percentage to Net Sales(example Give Ebita value along with its percentage to Net Sales ), Give Net Profit After Tax (PAT) value and its percentage to Net Sales Value, Cash Accruals(use formula cash accural = Net Profit + Depreciation + Non-cash Expenses), ",
    "Please provide key financial indicators for FY2023 to FY2025 Tangible Net Worth (excluding revaluation reserves and quasi-equity)(refer to Tangible Net Worth = Total Assets - Total Liabilities - Intangible Assets), TOL/TNW Ratio(refer to Total Liabilities / Total Net Worth), Net Working Capital, Current Ratio, ",
    "Please provide key financial indicators for FY2023 to FY2025 for DSCR. Additionally, provide brief comments on each of following (a)Comments in brief on each key financial Indicator(Comments should include position of the various financial ratios vis-à-vis the benchmarks and proper explanations/clarifications wherever the ratios and performance in absolute terms vary with the benchmarks. Comparison between estimates and actual for the last year and reasons for variances)Impact of contingent liabilities on financial position (as % to TNW) (as per comments in last audited B/S including AUDIT qualifications if any) be given.",
   
    "Please provide the standalone Net Working Capital (NWC) details for FY2023 to FY2026, including all  standalone components like share capital,  general reserves, other reserves,P/L Account,Equity Instruments,Term Loans, Term Deposits,Other Term Liabilities",
    "Please provide the standalone Net Working Capital (NWC) details for FY2023 to FY2026, including all  standalone components of Long Term Sources(A) like Net Fixed Assets,Investments,Other Non-Current Assets*,Advances to Suppliers of Capital Goods,Intangible Assets,Long Term Uses (B)Net Working Capital(A-B) ",
    "provide your  descriptive comments on the following (a) adequacy of NWC also give its value in explanantion, explaining any significant variations in sources and uses along with their reasons. (b)Treatment proposed to meet shortfall if any (c) Comments on Cash Flow pleaseGive as long and descriptive content and answer as possible for all(include point wrt,Increase in capital ,increase/decrease in Non current assets,net cash used,increase/decrease in net addition in term loan, usage of funds that  is investments in group companies)" ,
   
    "provide a peer group or industry comparison including company names, years, and corresponding financial  metrics such as Sales,Inventory Days, EBIT, EBIT as % of Sales, NPAT, NPAT as % of Sales, TOL/TNW, and Current Ratio.",
   # 18
    " Please give me standalone  value for  FY2023,FY2024,FY2025 FOR Inventory Days(Inventory Days = (Average Inventory / Cost of Goods Sold) × 365),Debtors Days(Debtors Days = (Average Accounts Receivable / Revenue) × 365) ,Creditors Days(Creditors Days = (Average Accounts Payable / Cost of Goods Sold) × 365) ,Gross Operating Cycle(Gross Operating Cycle = Inventory Days + Debtors Days),Net Operating Cycle(Net Operating Cycle = Gross Operating Cycle − Creditors Days)",
    "Please give me standalone  value for  FY2023,FY2024,FY2025 FOR Stock of RM,Raw Material consumed,(Stock of RM / Raw Material consumed) X 12,Stock of WIP,Cost of Production",
    "Please give me standalone  value for  FY2023,FY2024,FY2025 Please give me standalone  value for  FY2023,FY2024,FY2025 (Stock of WIP/ Cost of Production) X 12,Stock of Finished goods,Cost of Sales,(Stock of Finished goods/ Cost of Sales) X 12,Debtors",
    "Please give me standalone  value for  FY2023,FY2024,FY2025 Please give me standalone  value for  FY2023,FY2024,FY2025 Gross sales,(Debtors / Gross sales) X 12,Creditors,Raw Material Purchased,(Creditors/RawMaterial Purchased) X 12,Gross operating Cycle (RM + WIP + FG + Debtors),Net Operating Cycle (RM + WIP   +FG+Debtors–Creditors)",
   
    "Please provide the summarized working for fund-based working capital assessment for FY2024 (Audited), FY2025 (Audited), including: Total Current Assets, Other Current Liabilities (excluding bank borrowing), Working Capital Gap (WC Gap), Minimum NWC (25% of Current Accets)(excluding export receivables & domestic receivables arising out of bills under letters of credit), ",
    "Please provide the summarized working for fund-based working capital assessment for FY2024 (Audited), FY2025 (Audited), including:  Actual NWC Level, difference between WC Gap and Minimum NWC (3–4), difference between WC Gap and Actual NWC (3–5), Maximum Permissible Bank Finance (MPBF – lower of 3–4 or 3–5), and any excess borrowing, if applicable. also give Limit proposed in consortium and our share value ",
    "Please provide the assessment details for the proposed Letter of Credit (LC) limit for FY2025, including total raw material purchased for the year, percentage of RM purchaes under LC , Raw material purchased under LC, RW monthly purchases under LC(RM PURCHAES UNDER lC/12),RW  LC period(MONTHS=LEAD PERIOD+transit period+usance period that is 180 days) (covering lead, transit, and usance), and the calculated total LC limit(Monthly purchases under LC X total period).",
    "Please provide the regulatory declarations and confirmations on the following points: in yes or no for questions (a). Relationship if any, of the Directors/Partners/Proprietor of the borrowing entity to any of the directors/Senior officials of the Bank; if no relationship exists, specific declaration to be made. (b). Whether exposure in the account existing as well as proposed to the borrowing entity and the group is within prudential exposure ceilings as per lending policy. (c). Confirmation that an undertaking is obtained from guarantors stating no consideration is received/proposed from the borrower for offering personal guarantees. (d). Confirmation that the borrower has provided an undertaking for disclosure of names of directors/partners/proprietor to RBI/CIBIL. (e). Study of balance sheets of sister concerns to analyze interlocking/diversion of funds (preferably on common date or not older than 9 months); specific conclusions to be drawn. (f). Reference to RBI defaulter's list and CIBIL database, with full details and financial implications if defaulters are personal guarantors. (g.) Declaration from borrowers/guarantors/partners/directors that no third-party litigation is pending; if any, include details below names. (h). Undertaking from company confirming payments to small investors (if public deposits are accepted) and timely payments to SSI suppliers. (i). Submission of quarterly certificate by firm/company regarding accounts opened with other banks; Nil certificate to be obtained if none. (j.) Undertaking confirming borrower is not a director of other banks or associated with such directors through interest or substantial holdings. (k). Compliance with instructions on obtaining/sharing information relating to credit, derivatives, and un-hedged forex exposure for consortium/multiple/joint lending. (l.) Confirmation that an undertaking is obtained stating that the company’s directors are not directors/relatives of directors of banks.",
   
    "Please provide a descriptive SWOT analysis for the borrower, detailing key Strengths(tell about (a)Diversified business profile(b) Financial stability,(c)Operation effeciency, Market share and position), Weaknesses((a) competitos,process effeciency, Opportunities((a) strategic partnership), and Threats((a) NPA,(b) market and ecocomic condition(c)geopolitical issues). Additionally, outline the strategic mitigations proposed to address the identified weaknesses and threats. Pleae be as descriptive and breif in this answer as possible remember that"
]

html_path = r"code_html/credict_form.html"

# Derive updated output file path
output_path = html_path.replace(".html", "_updated.html")

# Load original HTML content
with open(html_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

custom_k_per_question = {
    1: 80,
    2: 80,
    3: 180,
    4: 80,
    5:200,
    6:150,
    7:200,
    8:150,
    9:80,
    10:80,
    11:80,
    12:80,
    13:180,
    14:120,
    15:120,
    16:120,
    17:80,
    18:80,
    19:80,
    20:80,
    21:80,
    22:80,                    
    23:150,
    24:80,
    25:200}
   
   
def extract_chunks(content):
    pattern = re.compile(r'<!--\s*extract_(\d+)_start\s*--*>(.*?)<!--\s*extract_\1_end\s*--*>', re.DOTALL | re.IGNORECASE)
    extracted = {match.group(1): match.group(2).strip() for match in pattern.finditer(content)}

    print("📦 Extracted Chunks:")
    for k, v in extracted.items():
        print(f" - extract_{k}: {len(v)} chars")
    return extracted

# Replace a chunk between markers
def replace_chunk(content, extract_num, new_html):
    start = f"<!-- extract_{extract_num}_start"
    end = f"<!-- extract_{extract_num}_end"

    pattern = re.compile(
        rf'({re.escape(start)}\s*--*>)(.*?)(?=({re.escape(end)}\s*--*>))',
        re.DOTALL
    )

    if pattern.search(content):
        print(f"🔁 Replacing content in extract_{extract_num} with updated HTML")
        return pattern.sub(rf'\1\n{new_html}\n', content)
    else:
        print(f"⚠️ Pattern for extract_{extract_num} not found in HTML.")
        return content
default_k=70

comparison_log_path = r"comparison_log.txt"

def get_updated_chunk(question, original_html, question_index):

    global vectorstores
    k_value = custom_k_per_question.get(question_index, default_k)
    cleaned_data_primary = ""
    cleaned_data_secondary = ""

    def generate_answer(vectorstore, name):
        retrieved_contexts = []
        for name, store in vectorstore:
            print("k_value",k_value)
            docs = store.similarity_search(question, k=k_value)
            combined_context = "\n".join(doc.page_content.strip() for doc in docs)
           
            # Add header and footer around the content for each vectorstore
            labeled_context = (
                f"\n--- Start of extract from: {name} ---\n"
                f"{combined_context}"
                f"\n--- End of extract from: {name} ---\n"
            )
            retrieved_contexts.append((name, labeled_context))

        # retrieved_contexts.append((name, labeled_context))
        # docs = vectorstore.similarity_search(question, k=k_value)
        # combined_context = "\n".join(doc.page_content.strip() for doc in docs)

        final_prompt = f"""
You are a financial analyst assistant. Answer the question using only the information provided in the following extracts from annual reports.

Instructions:
- Provide all output in **Indian Rupees (₹) billion**.
- If the question asks for a **percentage**, give the percentage value.
- If the question asks for an **amount**, provide the amount in ₹ billion.
- If the question asks for a **summary or reason**, explain it clearly and concisely.
- Carefully read the user question to understand whether it requires a **quantitative**, **descriptive**, or **mixed** response, and answer accordingly.
- Do **not hallucinate** or fabricate any data that is not present in the extract.
- Present your response asked format for clarity and ease of understanding.

Note:
- The retrieved content may include financial data for FY 2022–23, FY 2023–24, and FY 2024–25. Use only the relevant year(s) as required by the question.
- All figures in the extract are in **crore**. Convert them to **₹ billion** (1 billion = 100 crore) for your response.
- Percentage values are already calculated on crore-based data unless stated otherwise.
- Do not assume or guess values. If the answer is clearly present in the extract, provide it.
- You may not find all the answer in the context prvided in that case do not fill out wronfg answer emember jusr retunr the html structire as it is

Question: {question}

The output values should be filled in this HTML structure. Only give the html filled chunk codeas an output no extra line fo text remmeber

{original_html}

Make sure in html only value is updated no other modification in the html format do not remove existing add the value.
Do not alter the html format just fill the results
Do not give any extra line of text or explanation in outout just html updated script do cor change the format of html code just fill in relevant information in the chunkat required place

### Extract from {name}:
--- Start of extract from: {name} ---
{retrieved_contexts}
--- End of extract from: {name} ---

Answer:
"""
        for attempt in range(3):
            try:
                response = llm.invoke(final_prompt)
                print("v----------",response)
                result = response.content.strip()
                match = re.search(r"```(?:html)?\s*([\s\S]*?)\s*```", result)
                return match.group(1).strip() if match else result
            except Exception as e:
                print(f"⚠️ Retry {attempt + 1} failed for {name}: {e}")
                time.sleep(5)
        return original_html  # fallback

    # Step 1: Answer from Primary Vectorstore
    cleaned_data_primary = generate_answer(vectorstores, "Files_report")

#     # Step 2: Answer from Secondary Vectorstore
#     cleaned_data_secondary = generate_answer(vectorstores_money_control, "Moneycontrol")

#     # Step 3: Compare the outputs
#     comparison_prompt = f"""
# You are a compliance assistant. Two different document sources were used to answer the same financial question.

# Compare the following two answers and point out:
# - Differences in figures (amounts, percentages)


# --- Annual_report ---
# {cleaned_data_primary}

# --- Moneycontrol ---
# {cleaned_data_secondary}

# Provide a short comparison summary below:
# """

#     try:
#         comparison_response = llm.invoke(comparison_prompt)
#         comparison_result = comparison_response.content.strip()
#     except Exception as e:
#         comparison_result = f"Comparison failed: {e}"

#     # Step 4: Append comparison result to file
#     with open(comparison_log_path, 'a', encoding='utf-8') as f:
#         f.write(f"Comparison Result:\n{comparison_result}\n")

    # Step 5: Return only one clean HTML output (primary)
    return cleaned_data_primary

# === Step 1: Convert HTML to PDF ===
def html_to_pdf(html_file_path, output_pdf_path="output.pdf"):
    if not os.path.exists(html_file_path):
        print(f"❌ HTML file not found: {html_file_path}")
        return False

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    abs_path = os.path.abspath(html_file_path).replace("\\", "/")
    file_url = "file://" + abs_path
    driver.get(file_url)

    print("[INFO] Rendering and saving PDF...")
    pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {"printBackground": True})

    with open(output_pdf_path, "wb") as f:
        f.write(base64.b64decode(pdf_data['data']))

    print(f"✅ PDF created successfully: {output_pdf_path}")
    driver.quit()
    return True

# === Step 2: Convert PDF to DOCX ===
def convert_pdf_to_docx(pdf_path, docx_path="output.docx"):
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        print("[INFO] Converting PDF to DOCX...")
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        print(f"✅ DOCX created successfully: {docx_path}")
    except Exception as e:
        print(f"❌ Conversion failed: {e}")

# === RUN BOTH CONVERSIONS SEQUENTIALLY ===
html_file_path = r"code_html/credict_form_updated.html"  # Hardcoded path
pdf_output_path = r"output.pdf"
docx_output_path = r"output.docx"

@app.route('/update-html', methods=['POST'])
def update_html_chunks():
    global vectorstores
    try:
        vectorstores = load_all_vectorstores(r'vector_stores_new')
       
        # Step 1: Extract current chunks
        chunks = extract_chunks(html_content)

        # Step 2: Update each chunk
        for i in range(1, len(user_questions) + 1):
            extract_id = str(i)
            question = user_questions[i - 1]

            if extract_id not in chunks:
                print(f"⚠️ extract_{extract_id} not found in original HTML.")
                continue

            original_chunk_html = chunks[extract_id]
            updated_html_chunk = get_updated_chunk(question, original_chunk_html, i)

            html_content = replace_chunk(html_content, extract_id, updated_html_chunk)
            print(f"✅ Updated extract_{extract_id} in memory.\n")

        # Step 3: Save to new file
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(html_content)

        print(f"💾 All updates written to: {output_path}")
        if html_to_pdf(html_file_path, pdf_output_path):
            final_result_path=convert_pdf_to_docx(pdf_output_path, docx_output_path)
        return jsonify({'status': 'success', 'message':'HTML chunks updated and saved.', 'output_path': final_result_path}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0',port=9061)
# # âœ… Run the script
# extract_annual_report_links("Tech Mahindra")
