import google.generativeai as genai
import os

from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener API Key de forma segura
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("No se encontró GEMINI_API_KEY en las variables de entorno. Por favor verifica tu archivo .env.")

class GeminiService:
    def __init__(self):

        print("Inicializando Servicio Gemini...")
        genai.configure(api_key=API_KEY)
        # Usando gemini-2.5-flash como solicitó el usuario
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def summarize(self, text: str) -> str:
        """
        Genera un resumen conciso usando Gemini.
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
        Clasifica el documento en una categoría de negocio dinámica.
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
        Sube el archivo (PDF o Imagen) a Gemini y realiza un análisis completo.
        """
        import time
        
        try:

            print(f"Subiendo {file_path} ({mime_type}) a Gemini...")
            # 1. Subir Archivo
            uploaded_file = genai.upload_file(file_path, mime_type=mime_type)
            
            # Esperar procesamiento
            while uploaded_file.state.name == "PROCESSING":
                print("Procesando archivo en Gemini...")
                time.sleep(1)
                uploaded_file = genai.get_file(uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                raise ValueError("Gemini falló al procesar el archivo.")

            print("Archivo listo. Generando contenido...")

            # 2. Generar Contenido (Multimodal)
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
            
            # Configuración de Seguridad (Desactivar bloqueo estricto para evitar falsos positivos)
            # Configuración de Seguridad
            safety = {
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }

            # Ayuda para reintentos en error 429
            for attempt in range(3):
                try:
                    # Argumentos dinámicos para la generación
                    response = self.model.generate_content(
                        [uploaded_file, prompt], 
                        generation_config={"response_mime_type": "application/json"},
                        safety_settings=safety
                    )
                    
                    import json
                    text_resp = response.text.strip()
                    # Limpiar markdown si está presente
                    if text_resp.startswith("```json"):
                        text_resp = text_resp[7:]
                    if text_resp.startswith("```"):
                        text_resp = text_resp[3:]
                    if text_resp.endswith("```"):
                        text_resp = text_resp[:-3]
                        
                    result = json.loads(text_resp)
                    
                    # Limpieza (Opcional pero bueno para privacidad/almacenamiento)
                    # uploaded_file.delete() 
                    return result
                    
                except Exception as e:
                    if "429" in str(e):
                        wait_time = 10 * (attempt + 1)
                        print(f"Límite de Tasa (429). Esperando {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    # Manejar ValueError crudo si el JSON está mal
                    if "JSON" in str(e):
                         print(f"Fallo al parsear JSON: {response.text[:100]}...")
                         
                    if attempt == 2: # Último intento
                        raise e
            
            return {"error": "Límite de Tasa Excedido después de reintentos"}

        except Exception as e:
            print(f"Gemini Multimodal Error: {e}")
            return {
                "full_text_extracted": "", 
                "classification": {"category": "Error", "confidence": 0.0}, 
                "summary": f"Error: {str(e)}"
            }

    def semantic_search_rerank(self, query: str, candidates: list) -> list:
        """
        Usa Gemini para re-ordenar y filtrar inteligentemente los resultados de búsqueda.
        Contextualiza los candidatos de la búsqueda vectorial contra la consulta del usuario.
        """
        if not candidates:
            return []
            
        try:
            # Preparar el contexto para Gemini
            candidates_text = ""
            import os
            
            for i, cand in enumerate(candidates):
                meta = cand.get('metadata', {})
                file_id = meta.get('id')
                
                # Intentar cargar contexto de TEXTO COMPLETO
                content_context = f"Resumen: {meta.get('summary')}" # Fallback por defecto
                
                if file_id:
                    txt_path = f"data/uploads/{file_id}.txt"
                    if os.path.exists(txt_path):
                        try:
                            with open(txt_path, "r", encoding="utf-8") as f:
                                # Leer hasta 20,000 chars por doc para dar contexto profundo pero ahorrar tokens
                                # Gemini 2.5 Flash tiene contexto ENORME, así que podemos ser generosos.
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
            
            # Reconstruir la lista de resultados basada en el ranking de Gemini
            reranked_results = []
            for item in evaluation.get("results", []):
                idx = item.get("original_index")
                if idx is not None and 0 <= idx < len(candidates):
                    # Combinar datos originales con razonamiento IA
                    enhanced_cand = candidates[idx]
                    enhanced_cand["ai_reasoning"] = item.get("reasoning")
                    enhanced_cand["ai_score"] = item.get("relevance_score")
                    reranked_results.append(enhanced_cand)
            
            return reranked_results
            
        except Exception as e:
            print(f"Error de Rerank: {e}")
            # Fallback: Retornar candidatos originales
            return candidates

    def chat_with_document(self, context_text: str, query: str) -> str:
        """
        Permite chatear con un documento específico.
        """
        try:
            prompt = f"""
            Actúa como un asistente experto analizando el siguiente documento.
            
            Documento:
            {context_text[:50000]} 
            
            Consulta del Usuario: "{query}"
            
            Instrucciones:
            1. Responde basándote EXCLUSIVAMENTE en el documento proporcionado.
            2. Si la respuesta no está en el documento, dilo claramente.
            3. Sé conciso pero útil. Usa formato Markdown (negritas, listas) si ayuda a la claridad.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error al procesar la pregunta: {e}"

    def compare_documents(self, docs_list: list) -> str:
        """
        Compara múltiples documentos y genera una tabla o análisis comparativo.
        docs_list: Lista de diccionarios [{'name': '...', 'text': '...'}]
        """
        try:
            # Construir el prompt con todos los documentos
            docs_context = ""
            for i, doc in enumerate(docs_list):
                 docs_context += f"""
                 --- DOCUMENTO {i+1}: {doc.get('name')} ---
                 {doc.get('text')[:20000]}
                 
                 """
            
            prompt = f"""
            Actúa como un Consultor Analista Senior.
            Tu tarea es COMPARAR minuciosamente los siguientes documentos.
            
            {docs_context}
            
            INSTRUCCIONES:
            1. Identifica las similitudes y diferencias clave entre ellos.
            2. Extrae puntos de datos comparables (fechas, montos, cláusulas, nombres, temas).
            3. Genera una TABLA COMPARATIVA en Markdown donde las columnas sean los documentos y las filas los criterios de comparación.
            4. Después de la tabla, añade un breve párrafo de "Conclusión/Veredicto" sobre cuál es mejor o más completo (si aplica).
            5. IDIOMA: Español.
            
            Formato de salida esperado:
            ## ⚖️ Tabla Comparativa
            (Tabla Markdown)
            
            ## 💡 Análisis de Diferencias
            (Breve explicación de las diferencias más críticas)
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Error comparando documentos: {e}"
