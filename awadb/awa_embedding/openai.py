from awadb import AwaEmbedding
from typing import Iterable, Any, List
import os
import numpy as np

DEFAULT_MODEL_NAME = "text-embedding-ada-002"

class OpenAIEmbeddings(AwaEmbedding):
    def __init__(self):
        self.tokenizer = None        
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "Could not import openai python package. "
                "Please install it with `pip install openai`."
            ) from exc
        self.model = openai.Embedding
        self.tokenizer = None
        openai.api_key = os.environ["OPENAI_API_KEY"]

    def Embedding(self, sentence):
        tokens = []
        if self.tokenizer != None:
            tokens = self.tokenizer.tokenize(sentence)
        else:
            tokens.append(sentence)
        ans = self.model.create(input = tokens[0], model = DEFAULT_MODEL_NAME)["data"][0]["embedding"]
        return np.array(ans)

    def EmbeddingBatch(
        self,
        texts: Iterable[str],
        **kwargs: Any,
    ) -> List[List[float]]:
        results: List[List[float]] = []
        for text in texts:
            results.append(self.model.create(input = text, model = DEFAULT_MODEL_NAME)["data"][0]["embedding"])
        return results