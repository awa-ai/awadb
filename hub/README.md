# Hub - A proxy service for supporting RESTful and gRPC API

## RESTful API
Now support "create", "add", "get", "delete" and "search" API, the detailed information about each API please see [here](https://github.com/awa-ai/awadb/tree/main/docs/restful_tutorial.md)

## Python API
```bash
# Install awadb python client
pip3 install grpcio
pip3 install awadb-client

# Import the package and module
from awadb_client import Awa

# Initialize awadb client
client = Awa()

# Add dict with vector to table 'example1'
client.add("example1", {'name':'david', 'feature':[1.3, 2.5, 1.9]})
client.add("example1", {'name':'jim', 'feature':[1.1, 1.4, 2.3]})

# Search
results = client.search("example1", [1.0, 2.0, 3.0])

# Output results
print(results)

# '_id' is the primary key of each document
# It can be specified clearly when adding documents
# Here no field '_id' is specified, it is generated by the awadb server 
db_name: "default"
table_name: "example1"
results {
  total: 2
  msg: "Success"
  result_items {
    score: 0.860000074
    fields {
      name: "_id" 
      value: "64ddb69d-6038-4311-9118-605686d758d9"
    }
    fields {
      name: "name"
      value: "jim"
    }
  }
  result_items {
    score: 1.55
    fields {
      name: "_id"
      value: "f9f3035b-faaf-48d4-a947-801416c005b3"
    }
    fields {
      name: "name"
      value: "david"
    }
  }
}
result_code: SUCCESS

```
More usage of Python API please see [here](https://ljeagle.github.io/awadb/)
