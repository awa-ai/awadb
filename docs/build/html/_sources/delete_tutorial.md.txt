# Delete documents from table

## Native python usage
```bash
# Delete the documents whose the primary keys are the list of ids.
# awadb_client is initialize and created as [before](./init_client_tutorial.html).
# ret denotes True or False for deleting specified documents.
ret = awadb_client.Delete(ids=["key"])
```

## Docker usage
```bash
# Delete the documents whose the primary keys are the list of ids in table "example1".
# awadb_client is initialize and created as [before](./init_client_tutorial.html).
# ret denotes True or False for deleting specified documents.
re = awadb_client.delete("example1", ids=["key"])
```
