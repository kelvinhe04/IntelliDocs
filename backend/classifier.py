from transformers import pipeline

class DocumentClassifier:
    def __init__(self, model_name="facebook/bart-large-mnli"):
        print(f"Loading classification model: {model_name}...")
        self.classifier = pipeline("zero-shot-classification", model=model_name)
        # Expanded categories common in business
        self.candidate_labels = [
            "legal", 
            "financiero", 
            "técnico", 
            "recursos humanos", 
            "marketing", 
            "operaciones", 
            "ventas", 
            "administrativo",
            "otros"
        ]

    def classify(self, text: str) -> dict:
        """
        Classifies the text into one of the candidate categories.
        Returns a dict with labels and scores.
        """
        # Truncate text for classification if too long (models usually handle 512/1024 tokens)
        truncated_text = text[:1024] 
        result = self.classifier(truncated_text, self.candidate_labels)
        return result

if __name__ == "__main__":
    c = DocumentClassifier()
    text = "Este contrato establece los términos legales entre ambas partes."
    print(c.classify(text))
