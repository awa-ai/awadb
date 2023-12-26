# Docker deployment

## Preparation

1. docker pull ljeagle/awadb:v0.15
2. docker pull ljeagle/awadb_proxy:v0.15

## Docker compose deployment

3. enter the project [deploy directory](https://github.com/awa-ai/awadb/tree/main/deploy), then input the command "docker-compose up -d"

Note, docker and docker compose should be installed first.

## Check and usage

If all are right, the container service of awadb and awadb_proxy will be started normally.

- Restful usage 
```bash
curl -H "Content-Type: application/json" -X POST -d '{"db":"default", "table":"test", "docs":[{"_id":1, "name":"lj", "age":23, "f":[1,0]},{"_id":2, "name":"david", "age":32, "f":[1,2]}]}' http://localhost:8080/add
```
If show add successfully. Congrats! You can start to use awadb!
Detailed usage of RESTful API please see [here](https://github.com/awa-ai/awadb/tree/main/docs/restful_tutorial.md)

- Python usage

```bash
pip3 install grpcio
pip3 install awadb-client

# Import the package and module
from awadb_client import Awa

# Initialize awadb client
client = Awa()

# Add dict with vector to table 'example1'
client.add("example1", {'name':'david', 'feature':[1.3, 2.5, 1.9]})
```
If show add successfully. Congrats! AwaDB docker installed all right, you can try what you want next!
Detailed usage of Python API please see [here](https://ljeagle.github.io/awadb/)
