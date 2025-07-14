from langchain.vectorstores import FAISS
from langchain.embeddings import AzureOpenAIEmbeddings
from openai import AzureOpenAI
import os,time
from langchain_community.chat_models import AzureChatOpenAI
from bs4 import BeautifulSoup

# ----------------------
# Azure OpenAI Config
# ----------------------
import os
os.environ["OPENAI_API_VERSION"] = "2023-05-15"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://oai-gen.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "b3ada68f77114d6e856dfa777ea42ef0"
llm = AzureChatOpenAI(deployment_name="gpt_4o", temperature=0)
# groq_api_key = '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'
# llm = init_chat_model("gemini-2.5-flash", model_provider="google_vertexai")
# ----------------------
# Load Embeddings
# ----------------------
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
VECTOR_DIRS = [
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
    vectorstores.append((name, store))

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

@app.route('/update-html', methods=['POST'])
def update_html_chunks():
    try:
       
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
        return jsonify({'status': 'success', 'message': 'HTML chunks updated and saved.', 'output_path': output_path}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


"""chunks = extract_chunks(html_content)


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

# Save to new file (not overwriting original)
with open(output_path, 'w', encoding='utf-8') as file:
    file.write(html_content)

print(f"💾 All updates written to: {output_path}")"""

from bs4 import BeautifulSoup

'''# File paths
html_path = r"code_html/credict_form_updated.html"
log_path = r"comparison_log.txt"

# Read the log file
with open(log_path, 'r', encoding='utf-8') as f:
    log_content = f.read().strip()

# Read the HTML file as text
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Pattern: <h1>Validation Report</h1> followed by a <textarea> (captures only that block)
pattern = re.compile(
    r'(<h1>\s*Validation Report\s*</h1>.*?<textarea[^>]*>)(.*?)(</textarea>)',
    re.DOTALL
)

# Replace the matched textarea content
def replacer(match):
    before = match.group(1)
    existing_content = match.group(2).strip()
    after = match.group(3)

    updated_content = f"{existing_content}\n{log_content}" if existing_content else log_content
    return f"{before}{updated_content}{after}"

updated_html = pattern.sub(replacer, html)

# Write back the updated HTML with structure preserved
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(updated_html)
'''