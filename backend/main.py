from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import uvicorn

# Core Modules
from extractor import extract_text_from_pdf
# REPLACED LOCAL MODELS WITH GEMINI
from gemini_service import GeminiService
from embeddings import EmbeddingGenerator
from vector_store import VectorStore

app = FastAPI(title="Document AI API - Gemini Powered")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
print("Initializing AI Services...")
# 1. Gemini (Reasoning Engine)
gemini_service = GeminiService()

# 2. Embeddings (Search Engine - Local is faster/cheaper for vectors)
embedder = EmbeddingGenerator()

# 3. Vector Store
vector_store = VectorStore()
print("AI Services Initialized (Gemini + Local Vectors).")

# Ensure directories
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    try:
        # 1. Save File
        file_id = str(uuid.uuid4())
        file_ext = file.filename.split(".")[-1]
        filename = f"{file_id}.{file_ext}"
        file_path = f"data/uploads/{filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 1. ANALYSIS PIPELINE (Gemini Multimodal: OCR + Classify + Summarize)
        # We skip local extraction and let Gemini see the file directly.
        print("Sending PDF to Gemini for Full Analysis...")
        
        analysis_result = gemini_service.analyze_pdf(file_path)
        
        # Check if it failed
        if "error" in analysis_result:
             # Fallback? OR just return error
             pass 

        text = analysis_result.get("full_text_extracted", "")
        if not text:
             text = "Texto no encontrado por Gemini."
             
        classification = analysis_result.get("classification", {})
        category = classification.get("category", "Uncategorized")
        score = classification.get("confidence", 0.0)
        
        summary = analysis_result.get("summary", "No summary available.")
        
        # 2. Store Result (Embeddings are still local)
        print("Generating embeddings (Local)...")
        # Embedding generator needs text. Gemini provides high quality text now.
        vector = embedder.generate(text)
        
        # 3. Store in FAISS
        metadata = {
            "id": file_id,
            "filename": file.filename,
            "path": file_path,
            "category": category,
            "summary": summary,
            "deleted": False
        }
        vector_store.add_document(vector, metadata)
        
        return {
            "filename": file.filename,
            "category": category,
            "category_score": score,
            "summary": summary,
            "text_preview": text[:500] + "...",
            "full_text": text
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

@app.get("/search")
async def search_documents(query: str):
    try:
        # Search is Hybrid:
        # 1. Embed query (Local Model)
        query_embedding = embedder.generate(query)
        # 2. Search FAISS + Keyword Match
        results = vector_store.search(query_embedding, query_text=query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def get_documents():
    try:
        return vector_store.list_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    try:
        success = vector_store.delete_document(doc_id)
        if not success:
             raise HTTPException(status_code=404, detail="File not found")
        return {"status": "deleted", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents")
async def delete_all_documents():
    try:
        vector_store.clear_all()
        return {"status": "all_deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
