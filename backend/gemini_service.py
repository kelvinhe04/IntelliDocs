import google.generativeai as genai
import os

# Hardcoded for immediate use as requested. 
# Ideal: os.getenv("GEMINI_API_KEY")
API_KEY = "AIzaSyB_GzkU8lg_xxW9vnZaMPbJwsQ40ZtyrZg"

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
