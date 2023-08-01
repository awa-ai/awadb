from awadb import AwaEmbedding
from typing import Iterable, Any, List
import torch
from PIL import Image
import os
import clip
import numpy as np

# Use ViT-B/32 as the default model
DEFAULT_MODEL_NAME = "ViT-B/32"

class ClipEmbeddings(AwaEmbedding):
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load(DEFAULT_MODEL_NAME, device=self.device)

    def Embedding(self, sentence):
        tokens = clip.tokenize([sentence]).to(self.device)
        with torch.no_grad():
            text_features = self.model.encode_text(tokens).float()
        return text_features

    def EmbeddingBatch(
        self,
        texts: Iterable[str],
        **kwargs: Any,
    ) -> List[List[float]]:
        tokens = clip.tokenize(texts).to(self.device)
        with torch.no_grad():
            text_features = self.model.encode_text(tokens).float()
        return text_features
    
    def EmbeddingImage(self, image_addr):
        image = self.preprocess(Image.open(image_addr)).unsqueeze(0).to(self.device)
        with torch.no_grad():
            image_features = self.model.encode_image(image).float()
        return image_features

    def EmbeddingImageBatch(self, image_folder):
        all_features = []

        # Obtain all image file in this list 
        image_list = [filename for filename in os.listdir(image_folder) if (filename.endswith(".png") or filename.endswith(".jpg")) 
                      and os.path.isfile(os.path.join(image_folder, filename))]
        with torch.no_grad():
            for filename in image_list:
                image = Image.open(os.path.join(image_folder, filename))
                features =self.model.encode_image(self.preprocess(image).unsqueeze(0).to(self.device)).float()
                all_features.append(features)
        return all_features