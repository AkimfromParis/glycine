import os
from dotenv import load_dotenv
from sqlalchemy import make_url
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex
from llama_index.core.prompts import RichPromptTemplate

load_dotenv()

def create_query_engine(language: str, prompt_tmpl: RichPromptTemplate):
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB")

    if None in [db_host, db_port, db_user, db_password, db_name]:
        raise ValueError("Missing required database configuration in .env file")

    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    url = make_url(connection_string)

    table_name = "legal_" + ("japanese" if language == "ja" else "english")

    hybrid_vector_store = PGVectorStore.from_params(
        database=db_name,
        host=url.host,
        password=url.password,
        port=url.port,
        user=url.username,
        table_name=table_name,
        embed_dim=1024,
        hybrid_search=True,
        hnsw_kwargs={
        "hnsw_m": 16,
        "hnsw_ef_construction": 64,
        "hnsw_ef_search": 40,
        "hnsw_dist_method": "vector_cosine_ops",
    },
    )

    hybrid_index = VectorStoreIndex.from_vector_store(vector_store=hybrid_vector_store)

    return hybrid_index.as_query_engine(
        vector_store_query_mode="hybrid",
        text_qa_template=prompt_tmpl,
        sparse_top_k=3
    )