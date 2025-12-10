import google.generativeai as genai
import os

# Hardcoded for immediate use as requested. 
# Ideal: os.getenv("GEMINI_API_KEY")
API_KEY = "AIzaSyAsM8f9G6KOrz7F2RwrxaSTchgCPn1eMjI"

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
