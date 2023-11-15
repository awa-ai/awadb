# Initialize an awadb client

## Native python usage

Just `pip3 install awadb`, available for Linux and MacOSX.
The initialization code is as below: 

```bash
import awadb
# Initialize awadb client!
awadb_client = awadb.Client()
```

## Docker usage

Preliminary preparations: pull docker image and then install the awadb-client as below: 

```bash
# 1. Pull AwaDB docker image
docker pull ljeagle/awadb:v0.08

# 2. Run AwaDB Server
docker run -itd -p 50005:50005 ljeagle/awadb:v0.08

# 3. Install AwaDB Client
pip3 install awadb-client
```

The initialization code of docker usage is simple as below:

```bash
# Import the package and module
from awadb.client import Awa

# Initialize awadb client
awadb_client = Awa()
```

