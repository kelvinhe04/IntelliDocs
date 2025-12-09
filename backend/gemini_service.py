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
        Classifies the document into a business category and provides a confidence score.
        """
        categories = [
            "Contrato o Acuerdo Legal / Legal Contract", 
            "Factura o Reporte Financiero / Financial Invoice", 
            "Recibo o Comprobante de Pago / Receipt",
            "Hoja de Vida o CV / Resume", 
            "Manual Técnico o Guía de Usuario / Technical Manual", 
            "Documento de Recursos Humanos / HR Document", 
            "Identificación o Pasaporte / ID or Passport",
            "Formulario o Solicitud / Application Form",
            "Marketing y Publicidad / Marketing", 
            "Operaciones y Logística / Operations", 
            "Propuesta de Ventas o Cotización / Sales Proposal", 
            "Documento Administrativo / Administrative",
            "Acta de Reunión / Meeting Minutes",
            "Plan de Proyecto o Cronograma / Project Plan",
            "Presentación o Diapositivas / Presentation Slides",
            "Correo Electrónico o Memo / Email or Memo",
            "Documento Médico o Receta / Medical Record",
            "Certificado o Diploma / Certificate",
            "Investigación o Artículo / Research Paper",
            "Otro Documento / Other"
        ]
        
        try:
            prompt = f"""
            Analiza el siguiente documento y clasifícalo en EXACTAMENTE UNA de las siguientes categorías:
            {categories}
            
            Responde SOLO con un formato JSON así:
            {{
                "category": "Nombre de la categoría elegida",
                "confidence": 0.95,
                "reasoning": "Breve razón de por qué"
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
