from transformers import pipeline

class Summarizer:
    # Using a multilingual model optimized for news/articles
    def __init__(self, model_name="csebuetnlp/mT5_multilingual_XLSum"):
        print(f"Loading summarization model: {model_name}...")
        self.summarizer = pipeline("summarization", model=model_name)

    def summarize(self, text: str, max_length=130, min_length=30) -> str:
        """
        Generates a summary of the provided text.
        Handling long text by truncating or chunking might be needed for production,
        but for this MVP we'll rely on the model's truncation or simple limiting.
        """
        # Simple truncation to fit model limits (usually 1024 tokens)
        # In a real app, we would chunk the text and summarize chunks.
        # For now, we utilize the truncation argument.
        try:
            summary = self.summarizer(text, max_length=max_length, min_length=min_length, do_sample=False, truncation=True)
            return summary[0]['summary_text']
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary generation failed."

if __name__ == "__main__":
    s = Summarizer()
    text = "The quick brown fox jumps over the lazy dog. " * 20
    print(s.summarize(text))
