from transformers import pipeline

class DocumentClassifier:
    def __init__(self, model_name="joeddav/xlm-roberta-large-xnli"):
        print(f"Loading classification model: {model_name}...")
        self.classifier = pipeline("zero-shot-classification", model=model_name)
        
        # Optimized labels for multilingual business context (EN/ES)
        # Using descriptive phrases helps zero-shot models accuracy.
        self.candidate_labels = [
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
