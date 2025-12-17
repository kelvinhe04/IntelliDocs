from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
import uuid
import uvicorn
from gtts import gTTS

# Módulos Principales
# from extractor import extract_text_from_pdf
# MODELOS LOCALES REEMPLAZADOS POR GEMINI
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

# Inicializar Servicios (Lazy Loading)
# Inicializar Servicios (Lazy Loading)
gemini_service = None
embedder = None
vector_store = None

def get_services():
    global gemini_service, embedder, vector_store
    if gemini_service is None:
        print("⚡ Cargando Servicios de IA (Primera Ejecución)...")
        try:
            gemini_service = GeminiService()
            embedder = EmbeddingGenerator()
            vector_store = VectorStore()
            print("✅ Servicios de IA listos.")
        except Exception as e:
            print(f"❌ Error cargando servicios: {e}")
            raise e
    return gemini_service, embedder, vector_store

# Asegurar directorios
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    msg_services = get_services()
    gemini_service, embedder, vector_store = msg_services
    try:
        # 0. Verificar Duplicados
        if vector_store.check_file_exists(file.filename):
             raise HTTPException(status_code=400, detail=f"El archivo '{file.filename}' ya existe en el sistema.")
             
        # 1. Guardar Archivo
        file_id = str(uuid.uuid4())
        file_ext = file.filename.split(".")[-1]
        filename = f"{file_id}.{file_ext}"
        file_path = f"data/uploads/{filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 1. PIPELINE DE ANÁLISIS (Gemini Multimodal: OCR + Clasificación + Resumen)
        
        # Detectar Tipo MIME
        mime_type = file.content_type
        if not mime_type or mime_type == "application/octet-stream":
             if file_ext in ["jpg", "jpeg"]: mime_type = "image/jpeg"
             elif file_ext == "png": mime_type = "image/png"
             elif file_ext == "webp": mime_type = "image/webp"
             else: mime_type = "application/pdf"
             
        print(f"Enviando {filename} ({mime_type}) a Gemini para Análisis Completo...")
        
        analysis_result = gemini_service.analyze_file(file_path, mime_type=mime_type)
        
        # Verificar si falló
        if "error" in analysis_result:
             # ¿Fallback? O solo retornar error
             pass 

        text = analysis_result.get("full_text_extracted", "")
        if not text:
             text = "Texto no encontrado por Gemini."
             
        classification = analysis_result.get("classification", {})
        category = classification.get("category", "Uncategorized")
        score = classification.get("confidence", 0.0)
        
        summary = analysis_result.get("summary", "Resumen no disponible.")
        
        # 2. Almacenar Resultado (Embeddings siguen siendo locales)
        print("Generando embeddings (Local)...")
        
        # GUARDAR TEXTO COMPLETO EN DISCO para Contexto de Búsqueda Semántica
        txt_path = f"data/uploads/{file_id}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        # El generador de embeddings necesita texto. Gemini provee texto de alta calidad ahora.
        vector = embedder.generate(text)
        
        # 3. Almacenar en FAISS
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
    gemini_service, embedder, vector_store = get_services()
    try:
        # La búsqueda es Híbrida + Rerank con Gemini:
        # 1. Embed query (Modelo Local)
        query_embedding = embedder.generate(query)
        
        # 2. Búsqueda en FAISS + Coincidencia de Palabras Clave
        # Obtener más candidatos (k=15) para dar a Gemini un buen grupo para filtrar
        raw_candidates = vector_store.search(query_embedding, query_text=query, k=15)
        
        # 3. Reranking Semántico con Gemini
        # Pedir a Gemini que filtre el ruido y encuentre las coincidencias verdaderas
        refined_results = gemini_service.semantic_search_rerank(query, raw_candidates)
        
        return refined_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def get_documents():
    _, _, vector_store = get_services()
    try:
        return vector_store.list_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    _, _, vector_store = get_services()
    try:
        success = vector_store.delete_document(doc_id)
        if not success:
             raise HTTPException(status_code=404, detail="Archivo no encontrado")
        return {"status": "eliminado", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents")
async def delete_all_documents():
    _, _, vector_store = get_services()
    try:
        vector_store.clear_all()
        return {"status": "todos_eliminados"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat_document")
async def chat_document(payload: dict = Body(...)):
    gemini_service, _, _ = get_services()
    try:
        doc_id = payload.get("doc_id")
        query = payload.get("query")
        
        if not doc_id or not query:
             raise HTTPException(status_code=400, detail="Faltan parámetros doc_id o query")
             
        # Leer texto del documento
        txt_path = f"data/uploads/{doc_id}.txt"
        if not os.path.exists(txt_path):
             raise HTTPException(status_code=404, detail="Documento no encontrado")
             
        with open(txt_path, "r", encoding="utf-8") as f:
            context_text = f.read()
            
        # Llamar a Gemini
        answer = gemini_service.chat_with_document(context_text, query)
        return {"answer": answer}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_audio")
async def generate_audio(payload: dict = Body(...)):
    try:
        text = payload.get("text")
        if not text:
             raise HTTPException(status_code=400, detail="Falta texto")
        
        # Generar Audio
        # Truncar si es muy largo para TTS rápido (max 500 chars para demo rápida)
        # O dejarlo todo si se quiere leer el resumen completo.
        # Usaremos el resumen completo.
        
        tts = gTTS(text=text, lang='es')
        audio_filename = f"audio_{uuid.uuid4()}.mp3"
        audio_path = f"data/uploads/{audio_filename}"
        tts.save(audio_path)
        
        # Deberíamos servir el archivo estático o devolverlo como FileResponse
        # Para simplificar, devolveremos la URL local relativa si Streamlit pudiera leerla
        # Pero como backend y frontend están separados en ejecución, mejor devolver el path 
        # y que streamlit lo lea si comparte FS, o devolver el archivo binario.
        
        # Vamos a devolver la ruta, asumiendo que Streamlit corre localmente y tiene acceso a "data/uploads"
        return {"audio_path": audio_path} 

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/compare")
async def compare_documents(payload: dict = Body(...)):
    gemini_service, _, vector_store = get_services()
    try:
        doc_ids = payload.get("doc_ids") # Lista de IDs o Filenames
        if not doc_ids or len(doc_ids) < 2:
             raise HTTPException(status_code=400, detail="Se requieren al menos 2 documentos para comparar.")
             
        docs_data = []
        for doc_identifier in doc_ids:
            # Intentar encontrar archivo .txt
            # Asumimos que doc_identifier puede ser ID o Filename. 
            # Si es filename, necesitamos buscar su ID o asumir que filename == ID si usamos backend simple.
            # En v1, usabamos ID. Pero frontend a veces tiene solo filename.
            # Vamos a buscar el .txt directamente si existe
            
            # Caso ideal: Es el ID directo
            txt_path = f"data/uploads/{doc_identifier}.txt"
            
            # Caso 2: Es filename, buscar en metadatos (lento pero seguro)
            if not os.path.exists(txt_path):
                 # Lookup simple
                 found = False
                 all_docs = vector_store.list_documents()
                 for d in all_docs:
                     if d['filename'] == doc_identifier:
                         txt_path = f"data/uploads/{d['id']}.txt"
                         doc_identifier = d['filename'] # Usar nombre real para display
                         found = True
                         break
                 if not found:
                     continue # Skip si no se encuentra
            
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()
                    docs_data.append({"name": doc_identifier, "text": text})

        if len(docs_data) < 2:
             raise HTTPException(status_code=400, detail="No se encontraron suficientes textos válidos para comparar.")

        # Llamar a Gemini
        comparison_data = gemini_service.compare_documents(docs_data)
        return {"comparison": comparison_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export_comparison_excel")
async def export_comparison_excel(payload: dict = Body(...)):
    try:
        data = payload.get("comparison_table")
        if not data:
            raise HTTPException(status_code=400, detail="No hay datos para exportar")
            
        import pandas as pd
        
        # Crear DataFrame
        df = pd.DataFrame(data)
        
        # Guardar Excel
        filename = f"comparacion_{uuid.uuid4()}.xlsx"
        file_path = f"data/uploads/{filename}"
        
        # Guardar usando openpyxl engine
        df.to_excel(file_path, index=False, engine='openpyxl')
        
        return {"excel_path": file_path}
        
    except Exception as e:
        print(f"Error Exporting Excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
