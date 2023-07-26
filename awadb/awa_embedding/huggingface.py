from awadb import AwaEmbedding
from typing import Iterable, Any, List

# Use all-mpnet-base-v2 as the default model
DEFAULT_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

class HuggingFaceEmbeddings(AwaEmbedding):
    def __init__(self):
        self.tokenizer = None
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "Could not import sentence_transformers python package. "
                "Please install it with `pip install sentence_transformers`."
            ) from exc
        self.model = SentenceTransformer(DEFAULT_MODEL_NAME)

    def Embedding(self, sentence):
        tokens = []
        if self.tokenizer != None:
            tokens = self.tokenizer.tokenize(sentence)
        else:
            tokens.append(sentence)
        return self.model.encode(tokens[0])

    def EmbeddingBatch(
        self,
        texts: Iterable[str],
        **kwargs: Any,
    ) -> List[List[float]]:
        results: List[List[float]] = []
        for text in texts:
            results.append(self.model.encode(text))
        return results
