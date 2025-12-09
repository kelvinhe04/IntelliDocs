import google.generativeai as genai
import os

# Hardcoded for immediate use as requested. 
# Ideal: os.getenv("GEMINI_API_KEY")
API_KEY = "AIzaSyCnvMdPIHj00EDAnEb9cJKj9toabvmExFo"

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

    def analyze_pdf(self, file_path: str) -> dict:
        """
        Uploads PDF to Gemini and performs Full Analysis (Extraction + Classification + Summary).
        Single API call for maximum efficiency and completeness.
        """
        import time
        
        try:
            print(f"Uploading {file_path} to Gemini...")
            # 1. Upload File
            pdf_file = genai.upload_file(file_path, mime_type="application/pdf")
            
            # Wait for processing (usually instant for small files)
            while pdf_file.state.name == "PROCESSING":
                print("Processing file in Gemini...")
                time.sleep(2)
                pdf_file = genai.get_file(pdf_file.name)

            if pdf_file.state.name == "FAILED":
                raise ValueError("Gemini failed to process the PDF file.")

            print("File ready. Generating content...")

            # 2. Generate Content (Multimodal)
            prompt = """
            Actúa como un sistema experto de procesamiento de documentos (OCR + IA).
            Tu tarea es analizar este archivo PDF y extraer toda la información en un formato estructurado.
            
            REALIZA ESTAS 3 TAREAS:
            1. **EXTRACCIÓN INTELIGENTE**: Convierte el contenido visual del documento a **Markdown bien estructurado**.
               - LEE EN ORDEN LÓGICO: Si hay columnas, lee columna por columna. No mezcles texto.
               - DIAGRAMAS: Si hay diagramas o diapositivas, agrupa el texto de forma coherente. Si describes una imagen, HAZLO EN ESPAÑOL.
               - FORMATO: Usa Títulos (#), Listas (-) y Tablas de MD para mantener la estructura visual.
               - IDIOMA: Todo el contenido generado (descripciones, etiquetas inferidas) debe estar en ESPAÑOL.
            2. **CLASIFICACIÓN**: Determina la categoría del documento. **IMPORTANTE: Debes dar el nombre de la categoría EXCLUSIVAMENTE EN ESPAÑOL**. (Ej: "Acuerdo de Empleabilidad", "Contrato Legal").
            3. **RESUMEN**: Genera un resumen ejecutivo en español.
            
            Responde ÚNICAMENTE con este JSON:
            {
                "full_text_extracted": "El texto completo del PDF aquí...",
                "classification": {
                    "category": "Nombre Categoría",
                    "confidence": 0.95
                },
                "summary": "Resumen aquí..."
            }
            """
            
            # Helper for retries on 429
            for attempt in range(3):
                try:
                    response = self.model.generate_content(
                        [pdf_file, prompt], 
                        generation_config={"response_mime_type": "application/json"}
                    )
                    
                    import json
                    result = json.loads(response.text)
                    
                    # Cleanup (Optional but good for privacy/storage)
                    # pdf_file.delete() 
                    return result
                    
                except Exception as e:
                    if "429" in str(e):
                        wait_time = 10 * (attempt + 1)
                        print(f"Rate Limit (429). Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise e
            
            return {"error": "Rate Limit Exceeded after retries"}

        except Exception as e:
            print(f"Gemini Multimodal Error: {e}")
            return {
                "full_text_extracted": "", 
                "classification": {"category": "Error", "confidence": 0.0}, 
                "summary": f"Error: {str(e)}"
            }
