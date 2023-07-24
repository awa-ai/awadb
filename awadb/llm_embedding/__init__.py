# -*- coding:utf-8 -*-
#!/usr/bin/python3

from sentence_transformers import SentenceTransformer
from transformers import AutoModel
from transformers import AutoTokenizer
from typing import Iterable, Any, List
from awadb import llm_embedding

class LLMEmbedding:
    """Embedding models."""
    def __init__(self, model_name):
        self.model_name = model_name
        if self.model_name == "HuggingFace":
            from awadb.llm_embedding.huggingface import HuggingFaceEmbeddings
            self.llm = HuggingFaceEmbeddings()
        elif self.model_name == "OpenAI":
            from awadb.llm_embedding.openai import OpenAIEmbeddings
            self.llm = OpenAIEmbeddings()

    #set your own llm
    def SetModel(self, model_name):
        self.model = AutoModel.from_pretrained(model_name)

    #set your own tokenizer
    def SetTokenizer(self, tokenizer_name):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    def Embedding(self, sentence):
        return self.llm.Embedding(sentence)
    
    def EmbeddingBatch(
        self,
        texts: Iterable[str],
        **kwargs: Any,
    ) -> List[List[float]]:
        return self.llm.EmbeddingBatch(texts, **kwargs)