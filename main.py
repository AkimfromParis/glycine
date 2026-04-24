import os
import uvicorn
import traceback
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag import process_query

# Load environment variables
load_dotenv()

# Initialize FastAPI App
app = FastAPI()

# Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class QueryRequest(BaseModel):
    query_str: str

class QueryResponse(BaseModel):
    response: str
    page_label: str
    file_name: str
    file_path: str

# API Endpoint
@app.post("/ask/", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    try:
        result = process_query(request.query_str)
        return QueryResponse(**result)
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing the query: {str(e)}")

# Uvicorn Server Launch
def run():
    uvicorn.run(
        "main:app",
        host=os.getenv("UVICORN_HOST", "0.0.0.0"),
        port=int(os.getenv("UVICORN_PORT", 8000)),
        workers=int(os.getenv("UVICORN_WORKERS", 1)),
        timeout_keep_alive=500,
        log_level="info",
        reload=bool(os.getenv("UVICORN_RELOAD", False))  # Enables reload in dev mode
    )

if __name__ == "__main__":
    run()