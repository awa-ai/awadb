from clipembedding import ClipEmbeddings

if __name__ == "__main__":
    embedding = ClipEmbeddings()
    print(embedding.EmbeddingBatch(["111", "12121", "test string"]))
    print(embedding.Embedding("121212"))
    print(embedding.EmbeddingImage("test.png"))
    print(embedding.EmbeddingImageBatch("testfolder"))