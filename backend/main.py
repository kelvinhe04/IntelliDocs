from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from typing import List

# Import our modules
from extractor import extract_text_from_pdf
from summarizer import Summarizer
from classifier import DocumentClassifier
from embeddings import EmbeddingGenerator
from vector_store import VectorStore

app = FastAPI(title="Document Analysis API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules (load models onc at startup)
print("Initializing models...")
summarizer = Summarizer()
classifier = DocumentClassifier()
embedder = EmbeddingGenerator()
vector_store = VectorStore()
print("Models initialized.")

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    try:
        # Save file
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 1. Extract Text
        text = extract_text_from_pdf(file_path)
        if not text:
            return {"error": "Could not extract text from file"}
            
        if text.startswith("Error:"):
            return {"error": text}
            
        # 2. Classify
        classification = classifier.classify(text)
        category = classification['labels'][0]
        score = classification['scores'][0]
        
        # 3. Summarize
        summary = summarizer.summarize(text)
        
        # 4. Embed and Store
        embedding = embedder.generate(text)
        metadata = {
            "id": file_id,
            "filename": file.filename,
            "category": category,
            "summary": summary,
            "path": file_path
        }
        vector_store.add_document(embedding, metadata)
        
        return {
            "filename": file.filename,
            "category": category,
            "category_score": score,
            "summary": summary,
            "category_score": score,
            "summary": summary,
            "text_preview": text[:500] + "...",
            "full_text": text
        }

    except Exception as e:
        print(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_documents(query: str):
    try:
        query_embedding = embedder.generate(query)
        # Pass query text for hybrid search
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
