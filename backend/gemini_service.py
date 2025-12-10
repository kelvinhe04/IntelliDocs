import google.generativeai as genai
import os

# Hardcoded for immediate use as requested. 
# Ideal: os.getenv("GEMINI_API_KEY")
API_KEY = "AIzaSyBUB6d1AeqcyJ25TbyohtaIVtpRMj27BLk"

class GeminiService:
    def __init__(self):
        print("Initializing Gemini Service...")
        genai.configure(api_key=API_KEY)
        # Using the latest available model from list_models()
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def summarize(self, text: str) -> str:
        """
        Generates a concise summary using Gemini.
        """
        try:
            prompt = f"""
            Actúa como un analista de documentos experto. 
            Resume el siguiente texto en español de manera concisa y profesional.
            Menciona los puntos clave, fechas importantes y entidades (nombres, empresas).
            Longitud máxima: 2-3 párrafos.
            
            Texto:
            {text[:30000]} 
            """
            # Truncate to avoid context limit if extremely large, though 1.5 Flash has huge context.
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini Summary Error: {e}")
            return "Error generando resumen con Gemini."

    def classify(self, text: str) -> dict:
        """
        Classifies the document into a dynamic business category.
        """
        try:
            prompt = f"""
            Analiza el siguiente documento y determina su CATEGORÍA de negocio más profesional y descriptiva.
            
            INSTRUCCIONES:
            1. NO uses una lista predefinida. Genera la categoría que mejor describa este documento específico.
            2. Usa Español, sé conciso (máximo 3-4 palabras). Ejemplos: "Contrato de Arrendamiento", "Factura de Proveedor", "Informe de Auditoría", "Cédula de Ciudadanía".
            3. Dame un nivel de confianza (0.0 a 1.0) basado en qué tan claro es el documento.
            
            Responde SOLO con un formato JSON así:
            {{
                "category": "Nombre de la Categoría",
                "confidence": 0.95,
                "reasoning": "Breve razón"
            }}
            
            Texto del documento:
            {text[:10000]}
            """
            
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            import json
            result = json.loads(response.text)
            return result
        except Exception as e:
            print(f"Gemini Classification Error: {e}")
            return {"category": "Desconocido", "confidence": 0.0, "reasoning": "Error en API"}

    def analyze_file(self, file_path: str, mime_type: str = "application/pdf") -> dict:
        """
        Uploads File (PDF or Image) to Gemini and performs Full Analysis.
        """
        import time
        
        try:
            print(f"Uploading {file_path} ({mime_type}) to Gemini...")
            # 1. Upload File
            uploaded_file = genai.upload_file(file_path, mime_type=mime_type)
            
            # Wait for processing
            while uploaded_file.state.name == "PROCESSING":
                print("Processing file in Gemini...")
                time.sleep(1)
                uploaded_file = genai.get_file(uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                raise ValueError("Gemini failed to process the file.")

            print("File ready. Generating content...")

            # 2. Generate Content (Multimodal)
            prompt = """
            Actúa como un sistema experto de procesamiento de documentos e imágenes (OCR + IA).
            Tu tarea es analizar este archivo (PDF o Imagen) y extraer toda la información en un formato estructurado.
            
            REALIZA ESTAS 3 TAREAS:
            1. **EXTRACCIÓN INTELIGENTE**: 
               - Si es PDF: Convierte el contenido visual a **Markdown**.
               - Si es IMAGEN: Describe detalladamente el contenido visual (texto, tablas, diagramas, escenas) en **Markdown**.
               - LEE EN ORDEN LÓGICO.
               - IDIOMA: Todo el contenido generado debe estar en ESPAÑOL.
            2. **CLASIFICACIÓN**: Determina la categoría del documento/imagen. **IMPORTANTE: Debes dar el nombre de la categoría EXCLUSIVAMENTE EN ESPAÑOL**.
            3. **RESUMEN**: Genera un resumen ejecutivo en español.
            
            Responde ÚNICAMENTE con este JSON:
            {
                "full_text_extracted": "El texto/descripción completa aquí...",
                "classification": {
                    "category": "Nombre Categoría",
                    "confidence": 0.95
                },
                "summary": "Resumen aquí..."
            }
            """
            
            # Safety Settings (Disable strict blocking to avoid false positives on documents)
            safety = {
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }

            # Helper for retries on 429
            for attempt in range(3):
                try:
                    response = self.model.generate_content(
                        [uploaded_file, prompt], 
                        generation_config={"response_mime_type": "application/json"},
                        safety_settings=safety
                    )
                    
                    import json
                    text_resp = response.text.strip()
                    # Clean markdown if present
                    if text_resp.startswith("```json"):
                        text_resp = text_resp[7:]
                    if text_resp.startswith("```"):
                        text_resp = text_resp[3:]
                    if text_resp.endswith("```"):
                        text_resp = text_resp[:-3]
                        
                    result = json.loads(text_resp)
                    
                    # Cleanup (Optional but good for privacy/storage)
                    # uploaded_file.delete() 
                    return result
                    
                except Exception as e:
                    if "429" in str(e):
                        wait_time = 10 * (attempt + 1)
                        print(f"Rate Limit (429). Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    # Handle raw ValueError if JSON is bad
                    if "JSON" in str(e):
                         print(f"JSON Parsing failed: {response.text[:100]}...")
                         
                    if attempt == 2: # Last attempt
                        raise e
            
            return {"error": "Rate Limit Exceeded after retries"}

        except Exception as e:
            print(f"Gemini Multimodal Error: {e}")
            return {
                "full_text_extracted": "", 
                "classification": {"category": "Error", "confidence": 0.0}, 
                "summary": f"Error: {str(e)}"
            }

    def semantic_search_rerank(self, query: str, candidates: list) -> list:
        """
        Uses Gemini to intelligently re-rank and filter search results.
        Contextualizes the vector search candidates against the user query.
        """
        if not candidates:
            return []
            
        try:
            # Prepare the context for Gemini
            candidates_text = ""
            import os
            
            for i, cand in enumerate(candidates):
                meta = cand.get('metadata', {})
                file_id = meta.get('id')
                
                # Try to load FULL TEXT context
                content_context = f"Resumen: {meta.get('summary')}" # Default fallback
                
                if file_id:
                    txt_path = f"data/uploads/{file_id}.txt"
                    if os.path.exists(txt_path):
                        try:
                            with open(txt_path, "r", encoding="utf-8") as f:
                                # Read up to 20,000 chars per doc to give deep context but save tokens
                                # Gemini 2.5 Flash has HUGE context, so we can be generous.
                                full_text = f.read(50000) 
                                content_context = f"CONTENIDO COMPLETO (Extracto):\n{full_text}..."
                        except Exception:
                            pass

                candidates_text += f"""
                [ID: {i}]
                Archivo: {meta.get('filename')}
                Categoría: {meta.get('category')}
                {content_context}
                -----------------------------------
                """

            prompt = f"""
            Actúa como un Motor de Búsqueda Semántica Avanzado.
            Tu tarea es filtrar y re-ordenar una lista de documentos candidatos basándote en la consulta del usuario.
            
            Consulta del Usuario: "{query}"
            
            Candidatos encontrados (Búsqueda Vectorial Cruda):
            {candidates_text}
            
            INSTRUCCIONES:
            1. Analiza la RELEVANCIA REAL de cada documento con respecto a la consulta.
            2. FILTRA fuera los resultados irrelevantes (ruido).
            3. ORDENA los restantes por relevancia (de mayor a menor).
            4. Explica brevemente por qué es relevante.
            
            Responde ÚNICAMENTE con este JSON:
            {{
                "results": [
                    {{
                        "original_index": 0,  // El ID [ID: X] del candidato original
                        "relevance_score": 0.95, // 0.0 a 1.0
                        "reasoning": "Explica por qué coincide con la búsqueda"
                    }}
                ]
            }}
            """
            
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            import json
            evaluation = json.loads(response.text)
            
            # Reconstruct the results list based on Gemini's ranking
            reranked_results = []
            for item in evaluation.get("results", []):
                idx = item.get("original_index")
                if idx is not None and 0 <= idx < len(candidates):
                    # Combine original data with AI reasoning
                    enhanced_cand = candidates[idx]
                    enhanced_cand["ai_reasoning"] = item.get("reasoning")
                    enhanced_cand["ai_score"] = item.get("relevance_score")
                    reranked_results.append(enhanced_cand)
            
            return reranked_results
            
        except Exception as e:
            print(f"Rerank Error: {e}")
            # Fallback: Return original candidates
            return candidates
