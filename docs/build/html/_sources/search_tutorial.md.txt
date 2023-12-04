# Search from table

## Native python usage
```bash
# Search the top 3 results similar to the sentence "The man is happy".
# awadb_client is initialize and created as [before](./init_client_tutorial.html) 
results = awadb_client.Search("The man is happy", 3)
```

## Docker usage
```bash
# Search the results most similar to the vector query "[1.0, 2.0, 3.0]" from table "example1"
# awadb_client is initialize as [before](./init_create_tutorial.html)
# topn is default to 10
results = awadb_client.search("example1", [1.0, 2.0, 3.0])
```

