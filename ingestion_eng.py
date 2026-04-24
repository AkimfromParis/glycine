# ingestion_eng.py

import os
import warnings
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, make_url, text

from llama_index.core import Settings, VectorStoreIndex, StorageContext
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.file import PyMuPDFReader
from llama_index.vector_stores.postgres import PGVectorStore

# Setup
warnings.filterwarnings('ignore')
load_dotenv()

# Constants
STATIC_DATA_DIR = Path(os.getenv("DATA_ENG", "/app/static/data/legal_english"))  # Use DATA_ENG from .env
STATIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Prompt Formatting
def completion_to_prompt(completion):
    return f"<|im_start|>system\n<|im_end|>\n<|im_start|>user\n{completion}<|im_end|>\n<|im_start|>assistant\n"

def messages_to_prompt(messages):
    prompt = ""
    for message in messages:
        prompt += f"<|im_start|>{message.role}\n{message.content}<|im_end|>\n"
    if not prompt.startswith("<|im_start|>system"):
        prompt = "<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n" + prompt
    return prompt + "<|im_start|>assistant\n"

# LLM and Embeddings 
Settings.llm = Ollama(
    model="qwen2.5:3b-instruct", # Change your LLM 
    request_timeout=500,
    base_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
    temperature=0.1,
    top_k=6,
    top_p=0.7,
    messages_to_prompt=messages_to_prompt,
    completion_to_prompt=completion_to_prompt,
    options={"num_gpu": 0}
)

Settings.embed_model = HuggingFaceEmbedding('./embed_model')
Settings.text_splitter = SentenceSplitter(chunk_size=1024)

# Environment Variables
db_host = os.getenv("POSTGRES_HOST")
db_port = os.getenv("POSTGRES_PORT")
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_name = os.getenv("POSTGRES_DB")
data_folder = os.getenv("DATA_ENG", "./data/legal_english") 

connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
url = make_url(connection_string)
engine = create_engine(connection_string)

# PGVector Store Setup
hybrid_vector_store = PGVectorStore.from_params(
    database=db_name,
    host=url.host,
    password=url.password,
    port=url.port,
    user=url.username,
    table_name="legal_english",
    embed_dim=1024,
    hybrid_search=True,
    text_search_config="english",
    hnsw_kwargs={
        "hnsw_m": 16,
        "hnsw_ef_construction": 64,
        "hnsw_ef_search": 40,
        "hnsw_dist_method": "vector_cosine_ops",
    },
)

storage_context = StorageContext.from_defaults(vector_store=hybrid_vector_store)
parser = PyMuPDFReader()

# File Management
def copy_to_static(file_path: Path) -> Path:
    target_path = STATIC_DATA_DIR / file_path.name
    if not target_path.exists():
        shutil.copy(file_path, target_path)
    return target_path

# Metadata and DB Operations
def create_metadata_table():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS processed_files (
                file_name TEXT PRIMARY KEY,
                file_checksum TEXT,
                ingested_at TIMESTAMP DEFAULT NOW()
            );
        """))

def compute_checksum(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def is_already_ingested(file_name: str, checksum: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM processed_files WHERE file_name = :file_name AND file_checksum = :checksum"),
            {"file_name": file_name, "checksum": checksum}
        ).fetchone()
        return result is not None

def mark_as_ingested(file_name: str, checksum: str):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO processed_files (file_name, file_checksum)
                VALUES (:file_name, :checksum)
                ON CONFLICT DO NOTHING
            """),
            {"file_name": file_name, "checksum": checksum}
        )

def get_metadata(file_path: Path):
    file_name = file_path.name
    absolute_path = str(file_path.resolve())
    return {
        "file_path": absolute_path,
        "file_name": file_name,
        "ingested_at": str(datetime.now())
    }

# Ingestion Logic
def ingest_single_pdf(original_file_path: Path):
    if original_file_path.suffix.lower() != ".pdf":
        return

    checksum = compute_checksum(original_file_path)
    file_name = original_file_path.name

    if is_already_ingested(file_name, checksum):
        print(f"[SKIP] Already ingested: {file_name}")
        return

    print(f"[INFO] Ingesting: {file_name}")

    static_file_path = copy_to_static(original_file_path)

    try:
        raw_pages = parser.load_data(
            static_file_path,
            extra_info=get_metadata(static_file_path),
        )
    except Exception as e:
        print(f"[ERROR] Failed to parse {file_name}: {e}")
        return

    base_metadata = get_metadata(static_file_path)

    for i, page in enumerate(raw_pages):
        page.metadata.update(base_metadata)
        page.metadata["page_label"] = str(i + 1)

    VectorStoreIndex.from_documents(
        raw_pages,
        storage_context=storage_context,
        show_progress=True
    )

    mark_as_ingested(file_name, checksum)
    print(f"[OK] Ingested: {file_name}")

# Main Entry
if __name__ == "__main__":
    create_metadata_table()
    files = list(Path(data_folder).glob("*.pdf"))
    print(f"[INFO] Found {len(files)} files in {data_folder}")
    for file in files:
        try:
            ingest_single_pdf(file)
        except Exception as e:
            print(f"[ERROR] Failed to ingest {file.name}: {e}")