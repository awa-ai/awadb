# Get documents from table

## Native python usage
```bash
# Get the documents whose the primary keys are the list of ids.
# awadb_client is initialize and created as [before](./init_client_tutorial.html) 
results = awadb_client.Get(ids=["key"])
```

## Docker usage
```bash
# Get the documents whose the primary keys are the list of ids in table "example1".
# awadb_client is initialize and created as [before](./init_client_tutorial.html) 
results = awadb_client.get("example1", ids=["key"])
```
