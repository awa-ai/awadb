<p align="center">
    <b>AwaDB - the AI Native database for embedding vectors</b>. <br />
    Lightweight, Easily use, Real time index and search!!!
</p>

No OS environment limitation, Linux, MacOSX and Windows are all supported!

# Installation 
```bash
# 1. Pull AwaDB docker image
docker pull ljeagle/awadb:v0.09

# 2. Run AwaDB Server
docker run -itd -p 50005:50005 ljeagle/awadb:v0.09

# 3. Install AwaDB Client
pip3 install awadb-client
```

# Quick start as below:

## Example 1 : A simple example for quick start
```bash
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

More detailed sdk usage you can read [here](https://github.com/awa-ai/awadb/blob/main/clients/awadb/client.py)

## Example 2 : Use the 960 dimension dataset [GIST](http://corpus-texmex.irisa.fr/) in the example2 for adding and searching vectors
```bash
from awadb_client import Awa
import h5py

# Add the first 100000 vectors of the GIST‘s train group data into table example2  
def insert_data_test(client, gist):
    total = 100000
    docs = []
    i = 0
    while i <= total:
        if i != 0 and i % 50 == 0:
            client.add("example2", docs)
            del docs[:]
                
        doc = {}
        doc['_id'] = i
        doc['feature'] = gist["train"][i]
        docs.append(doc)
        i = i + 1

# Search the first 1000 vectors of the GIST's test group data in table example2 
def search_data_test(client, gist):
    i = 0
    while i < 1000:
        res = client.search("example2", gist["test"][i])
        i = i + 1

if __name__ == "__main__":
    # Initialize awadb client
    client = Awa()
    # default gist vector data file path, please replace your own downloaded gist data path
    gist_file_path = './gist-960-euclidean.hdf5'
    f = h5py.File(gist_file_path, 'r')
    
    # insert batch docs example
    insert_data_test(client, f)

    # search test example
    search_data_test(client, f)
```

More detailed quick start examples you can find [hear](https://github.com/awa-ai/awadb/blob/main/tests/test_awadb_client.py)
