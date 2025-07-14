import os
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document as LangchainDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF
import re
# ENV setup
os.environ["OPENAI_API_VERSION"] = "2023-05-15"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://oai-gen.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "b3ada68f77114d6e856dfa777ea42ef0"

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

# --- Split into Langchain Documents ---

def prepare_langchain_docs(text_blocks):
    splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=500)
    docs = []
    for block in text_blocks:
        for chunk in splitter.split_text(block):
            docs.append(LangchainDocument(page_content=chunk))
    return docs

# --- Embed and Save Vectorstore ---

def embed_and_save_vectorstore(docs, base_name):
    embeddings = AzureOpenAIEmbeddings(
        deployment="text-embedding-ada-002",
        model="text-embedding-ada-002",
        chunk_size=1000
    )
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    vectorstore.save_local(os.path.join(faiss_folder, base_name))
    print(f"✅ Saved vectorstore for '{base_name}' at: {faiss_folder}/{base_name}")

# --- Process All PDFs in Folder ---

def process_all_pdfs():
    for file in os.listdir(input_folder):
        if file.lower().endswith(".pdf"):
            base = os.path.splitext(file)[0]
            pdf_path = os.path.join(input_folder, file)

            print(f"📄 Processing PDF: {file}")
            blocks = read_pdf_with_heading_and_table_blocks(pdf_path)
            docs = prepare_langchain_docs(blocks)
            embed_and_save_vectorstore(docs, base)


# --- Run the Pipeline ---

if __name__ == "__main__":
    process_all_pdfs()