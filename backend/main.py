import datetime
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, List
try:
    from processor import DocumentProcessor
    from bq_handler import BigQueryHandler
except ImportError:
    from .processor import DocumentProcessor
    from .bq_handler import BigQueryHandler

app = FastAPI(title="Document Processor API")
processor = DocumentProcessor()
bq_handler = BigQueryHandler()

class ProcessRequest(BaseModel):
    gcs_uri: str
    name: str
    size: int
    content_type: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/process")
async def process_document(request: ProcessRequest):
    """
    Endpoint called from Cloud Function when a document is uploaded.
    """
    print(f"Processing document: {request.name} at {request.gcs_uri}")
    
    # 1. Process with Gemini
    result, error = processor.process_document(request.gcs_uri)
    
    # 2. Prepare BigQuery record
    record = {
        "document_name": request.name,
        "document_size": request.size,
        "document_type": result.get("document_type") if result else "Unknown",
        "processed_at": datetime.datetime.utcnow().isoformat(),
        "extracted_data": result.get("extracted_data") if result else None,
        "error_message": error,
        "gcs_uri": request.gcs_uri
    }
    
    # 3. Insert into BigQuery
    success, bq_error = bq_handler.insert_record(record)
    
    if not success:
        # We still return 200 to the CF if Gemini succeeded but BQ failed 
        # (to avoid retries if the document was actually processed)
        # But we log it.
        print(f"Failed to save to BigQuery: {bq_error}")
        return {"status": "partial_success", "error": bq_error, "document_type": record["document_type"]}

    if error:
        return {"status": "failed", "error": error}

    return {"status": "success", "document_type": record["document_type"]}

async def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    # In a real app, we would verify the token against Google OAuth2
    # For this exercise, we assume the token is valid if present.
    return authorization.split(" ")[1]

@app.get("/documents")
async def get_documents(
    date: Optional[str] = None, 
    limit: int = 100,
    token: str = Depends(verify_token)
):
    """
    Endpoint to list processed documents.
    """
    records, error = bq_handler.list_records(limit=limit, date_filter=date)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return records
