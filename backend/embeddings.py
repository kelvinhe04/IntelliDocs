import google.generativeai as genai
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

class EmbeddingGenerator:
    def __init__(self, model_name="models/text-embedding-004"):
        print(f"Initializing Gemini Embedding Model via API: {model_name}...")
        self.model_name = model_name
        if API_KEY:
            genai.configure(api_key=API_KEY)
        else:
             print("⚠️ Warning: GEMINI_API_KEY not found. Embeddings will fail.")

    def generate(self, text: str) -> np.ndarray:
        """
        Genera un vector de embedding usando Gemini API.
        Retorna un numpy array de float32.
        """
        try:
            # Clean text to avoid API issues with empty/whitespace
            if not text or not text.strip():
                print("Warning: Empty text for embedding.")
                return np.zeros(768, dtype=np.float32)

            text = text.replace("\n", " ")
            
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document" 
            )
            
            embedding = result['embedding']
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            print(f"❌ Error generating embedding with Gemini: {e}")
            # Retornar vector zero para no romper el flujo, aunque la búsqueda no servirá para este doc
            return np.zeros(768, dtype=np.float32)

if __name__ == "__main__":
    e = EmbeddingGenerator()
    vec = e.generate("This is a test document.")
    print(f"Vector shape: {vec.shape}")
