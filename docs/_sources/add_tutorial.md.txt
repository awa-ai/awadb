# Add documents to table

## Native python usage

```bash
# awadb_client is the initialized awadb client
# Here should create a table before adding documents first
awadb_client.Create("test_llm1") 

# A dictionary in python denotes a document, each key-value pair denotes each field of the document.
# If a field name is defined as 'embedding_text', the field value would be embedded with SentenceTransformer by default.
awadb_client.Add([{'embedding_text':'The man is happy'}, {'source' : 'pic1'}])
```

## Docker usage

```bash
# Add dict with vector to table 'example1'
# A dictionary in python denotes a document, each key-value pair denotes each field of the document.
# If table 'example1' not exist, it would be created automaticly
# awadb_client is the initialized awadb client
awadb_client.add("example1", {'name':'david', 'feature':[1.3, 2.5, 1.9]})
```



