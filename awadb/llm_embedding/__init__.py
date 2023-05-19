# -*- coding:utf-8 -*-
#!/usr/bin/python3

from sentence_transformers import SentenceTransformer
from transformers import AutoModel
from transformers import AutoTokenizer


class LLMEmbedding:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.tokenizer = None 


    def Embedding(self, sentence):
        tokens = []
        if self.tokenizer != None:
            tokens = self.tokenizer.tokenize(sentence)
        else:
            tokens.append(sentence)
        return self.model.encode(tokens[0])

    #set your own llm
    def SetModel(self, model_name):
        self.model = AutoModel.from_pretrained(model_name)

    #set your own tokenizer
    def SetTokenizer(self, tokenizer_name):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)




