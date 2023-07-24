from sentence_transformers import SentenceTransformer
from transformers import AutoModel
from transformers import AutoTokenizer
from typing import Iterable, Any, List

class Embeddings:
    """Embedding models."""
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.tokenizer = None
        
        if self.model_name == "HuggingFace":
            self.llm = llm_embedding.HuggingFaceEmbeddings()
        elif self.model_name == "OpenAI":
            self.llm = llm_embedding.OpenAIEmbeddings()

    #set your own llm
    def SetModel(self, model_name):
        self.model = AutoModel.from_pretrained(model_name)

    #set your own tokenizer
    def SetTokenizer(self, tokenizer_name):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)