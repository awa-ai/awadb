# -*- coding:utf-8 -*-
#!/usr/bin/python3

from sentence_transformers import SentenceTransformer
from transformers import AutoModel
from transformers import AutoTokenizer
from typing import Iterable, Any, List

class LLMEmbedding:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.tokenizer = None

        if self.model_name == "HuggingFace":
            self.llm = llm_embedding.HuggingFaceEmbeddings()
        elif self.model_name == "OpenAI":
            self.llm = llm_embedding.OpenAiEmbeddings()