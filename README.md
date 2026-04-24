# Glycine-AI

**Agentic RAG for Legal Research & Market Monitoring in the Japanese Financial Market**

> Built during the **LLM x Law Hackathon #5** at [CodeX, Stanford Center for Legal Informatics](https://law.stanford.edu/codex-the-stanford-center-for-legal-informatics/) — Stanford Law School (April 6, 2025)

---

## Overview

**Glycine-AI** is a fully open-source, bilingual (English/Japanese) legal AI chatbot designed for foreign investors, lawyers, and researchers navigating Japan's rapidly evolving financial regulatory landscape.

Japan's financial market has undergone significant transformation over the past five years, driven by government efforts to position the country as a global asset management hub. In 2024-25, M&A deals hit record highs for PE funds, foreign investments play a pivotal role in the equity market, and shareholder activism is putting pressure on traditional corporate governance. Japan's information asymmetry presents a unique opportunity within the legal and financial sectors — Glycine-AI aims to bridge that gap.

## Features

- **Bilingual Chatbot** — Ask questions in English or Japanese about Japanese financial laws, regulations, and guidelines
- **Source Citation with PDF Preview** — Every response includes a clear audit trail with the source document and page number, displayed alongside an inline PDF preview
- **Hybrid Search RAG** — Combines dense vector search with sparse keyword search for higher retrieval accuracy
- **Low-Resource Setup** — Runs on CPU-only infrastructure (tested on DigitalOcean: 8 GB RAM / 4 vCPUs / 240 GB Disk)
- **Fully Dockerized** — One-command deployment with Docker Compose
- **SSL-Ready** — Includes Nginx reverse proxy with Let's Encrypt certbot integration
- **Password Protected** — HTTP basic auth via Nginx `.htpasswd`

## Data Sources

The knowledge base is built from official English and Japanese documents published by:

- **Financial Services Agency, Japan (JFSA, 金融庁)** — Guidelines, laws, regulations, analytical notes, supervisory discussion papers, cybersecurity reports, and more
- **Securities and Exchange Surveillance Commission (SESC, 証券取引等監視委員会)** — Annual reports, monitoring priorities, market misconduct investigation guidelines, and basic principles of securities business monitoring

## Tech Stack

| Layer | Technology |
|-------|------------|
| **LLM** | Qwen 2.5 (7B / 3B) served via Ollama (CPU); upgradeable to Qwen 3 30B on GPU with vLLM |
| **Embeddings** | HuggingFace Embeddings (locally hosted) |
| **RAG Framework** | LlamaIndex |
| **Vector Database** | PostgreSQL + PGvector (hybrid search with HNSW) |
| **Backend API** | FastAPI + Uvicorn |
| **Frontend** | Gradio (with gradio-pdf for inline PDF preview) |
| **Reverse Proxy** | Nginx with HTTP basic auth |
| **SSL** | Certbot / Let's Encrypt |
| **Containerization** | Docker + Docker Compose |

### Why Qwen 2.5?

Qwen 2.5 was selected for its superior reasoning capabilities, strong context handling for RAG workflows, and excellent language generation quality in both English and Japanese. For production deployments requiring higher throughput, Qwen 3 30B served on GPU with vLLM is recommended.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│   Nginx     │────▶│   Gradio    │────▶│   FastAPI API    │
│  (SSL+Auth) │     │   (UI)      │     │   (/ask/)        │
└─────────────┘     └─────────────┘     └────────┬─────────┘
                                                  │
                                    ┌─────────────▼─────────────┐
                                    │       RAG Engine          │
                                    │  (LlamaIndex + Qwen 2.5)  │
                                    └─────────────┬─────────────┘
                                                  │
                           ┌──────────────────────┼──────────────────────┐
                           │                      │                      │
                   ┌───────▼───────┐    ┌─────────▼─────────┐   ┌───────▼───────┐
                   │   PGvector    │    │     Ollama        │   │  Embeddings   │
                   │  (Hybrid DB)  │    │  (LLM Serving)    │   │ (HuggingFace) │
                   └───────────────┘    └───────────────────┘   └───────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- 8 GB RAM minimum (for CPU inference)

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/glycine.git
cd glycine
```

### 2. Configure Environment

Create a `.env` file based on the project's expected variables:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=glycine
OLLAMA_URL=http://ollama:11434
EMBED_MODEL=/app/embed_model
DATA_ENG=./static/data/legal_english
DATA_JAP=./static/data/legal_japanese
STATIC_PATH=/app/static/
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
GRADIO_HOST=0.0.0.0
GRADIO_PORT=7860
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
NGINX_CONFIG_FILE=nginx.conf
```

### 3. Launch

```bash
docker compose up --build
```

This will start all services in order:
1. **PostgreSQL + PGvector** — vector database
2. **Ollama** — LLM serving (pulls `qwen2.5:3b-instruct`)
3. **Embedding service** — downloads the HuggingFace embedding model
4. **Ingestion (English)** — indexes English PDFs into the vector store
5. **Ingestion (Japanese)** — indexes Japanese PDFs into the vector store
6. **RAG API + Gradio UI** — serves the chatbot application
7. **Nginx** — reverse proxy with SSL and authentication

### 4. Access the Application

- **Gradio UI**: `http://localhost:7860`
- **FastAPI API**: `http://localhost:8000/docs`
- **Nginx (with SSL)**: `https://your-domain.com`

## API Usage

```bash
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"query_str": "What are the strategic initiatives to promote Japan as a leading asset management center?"}'
```

Response:

```json
{
  "response": "...",
  "page_label": "3",
  "file_name": "FSA-Supervisory-Discussion-Paper-...pdf",
  "file_path": "/app/static/data/legal_english/..."
}
```

## Project Structure

```
glycine/
├── api.py                  # Gradio UI (chatbot + PDF preview)
├── main.py                 # FastAPI backend (/ask/ endpoint)
├── rag.py                  # RAG query processing (language detection, routing)
├── config.py               # LLM & embedding configuration, prompt templates (EN/JP)
├── query_engine.py         # PGvector hybrid search query engine
├── ingestion_eng.py        # English PDF ingestion pipeline
├── ingestion_jap.py        # Japanese PDF ingestion pipeline
├── dl.py                   # Embedding model downloader
├── config.py               # Model settings and prompt formatting
├── docker-compose.yaml     # Multi-service orchestration
├── Dockerfile              # Application container
├── Dockerfile.ollama       # Ollama CPU-optimized container
├── init.sql                # PostgreSQL initialization
├── requirements.txt        # Python dependencies
├── nginx/
│   ├── nginx.conf          # Nginx configuration
│   ├── nginx-ssl.conf      # SSL-enabled Nginx configuration
│   └── .htpasswd           # HTTP basic auth credentials
├── static/
│   ├── data/
│   │   ├── legal_english/  # English PDF documents (FSA, SESC)
│   │   └── legal_japanese/ # Japanese PDF documents
│   └── qwen-wisteria.png   # Favicon
└── setup-ssl.sh            # Let's Encrypt SSL setup script
```

## Adding Your Own Documents

Place PDF files in `static/data/legal_english/` or `static/data/legal_japanese/` and re-run the ingestion:

```bash
docker compose run ingestion_eng
docker compose run ingestion_jap
```

The ingestion pipeline includes deduplication via SHA-256 checksums, so only new or modified files will be processed.

## Scaling Up

For production workloads requiring faster inference:

1. **GPU + vLLM**: Keep Ollama or replace with vLLM serving XXB on a GPU instance
2. **Larger Embedding Model**: Swap the embedding model in `dl.py` for a higher-dimensional model
3. **Horizontal Scaling**: The FastAPI and Gradio services can be scaled independently behind the Nginx proxy

## Disclaimer

This tool is intended for **informational and research purposes only**. It utilizes publicly available content from Japan's [FSA](https://www.fsa.go.jp/en/index.html) and the [SESC](https://www.fsa.go.jp/sesc/english/index.html), including official English translations where available. Users are strongly advised to consult the original Japanese documents for accuracy and completeness. **This tool does not provide legal, financial, or professional advice.**

## Author

**Akim Mousterou** — [LinkedIn](https://www.linkedin.com/in/akim-mousterou/)

Built at the LLM x Law Hackathon #5, CodeX — Stanford Law School

## License

This project is open source. See the [LICENSE](LICENSE) file for details.
