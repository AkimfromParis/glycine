from dotenv import load_dotenv
load_dotenv()
import os
from huggingface_hub import snapshot_download

# Retrieve Hugging Face token and embedding model path from environment
token = os.getenv("HUGGINGFACE_TOKEN")
embed_model = os.getenv("EMBED_MODEL", "/app/embed_model")

# Create directory for embeddings if it doesn't exist
os.makedirs(embed_model, exist_ok=True)

# Define the model to download
embedding_model_repo = "intfloat/multilingual-e5-large"  # You can update this to use other models later

# Start downloading the embedding model
print(f"\nStarting download of the embedding model: {embedding_model_repo}...")
snapshot_download(
    repo_id=embedding_model_repo,
    local_dir=embed_model,
    token=token,
)

print(f"Model downloaded to {embed_model}")