# RESTful API tutorial

Now support "create", "add", "get", "delete", "search" and "list".

## create table
```bash
# here the awadb proxy and server are deployed on the localhost port 8080 

curl -H "Content-Type: application/json" -X POST -d \
'{
"db": "default"
"table": "test"
"desc": "This is a schema description about the table default/test"
"fields" : [{"name": "nickname", "type":"string",  "desc":"description about the field nickname", "index":true,  "store":true}, {“name”:"feature", "type":"vector", "desc":"vector field feature", "index":true, "store":true, "dimension":768}]
}' http://localhost:8080/create
```

## add documents to table
```bash
curl -H "Content-Type: application/json" -X POST -d \
'{
"db":"default",
"table":"test",
"docs":[{"nickname":"lj" ,"feature":[1,2,3]}, {"nickname":"tk", "feature":[1,1,1]}]
}' http://localhost:8080/add  
```

## get document based on ids or filter condition
```bash
curl -H "Content-Type: application/json" -X POST -d \
'{
"db":"default",
"table":"test",
#ids value type can be long or string
"ids":[1,2,3]
# filter condition, if ids is not empty, filter is not valid.
"filters": {
            "range_filters": {
                "price": {
                    "gte": 160,
                    "lte": 180
                }
            },
            "term_filters": {
                "labels": {
                    "value": ["100", "200", "300"],
                    "operator": "or"
                }
            }
} 
}' http://localhost:8080/get  
```

## delete documents by ids or condition
```bash
curl -H "Content-Type: application/json" -X POST -d \
'{
"db":"default",
"table":"test",
#ids value type can be long or string
"ids":[1,2,3],
# filter condition, if ids is not empty, filter is not valid.
"filters": {
            "range_filters": {
                "price": {
                    "gte": 160,
                    "lte": 180
                }
            },
            "term_filters": {
                "labels": {
                    "value": ["100", "200", "300"],
                    "operator": "or"
                }
            }
} 
}' http://localhost:8080/delete  
```

## search documents by vector query and filter condition
```bash
curl -H "Content-Type: application/json" -X POST -d \
'{
"db":"default",
"table":"test",
# default or for all the vector fields
“vector_query”: [
{
"feature":[0.1, 1.2, 3.4],
"min_score":0,
"max_score":99999,
"weight":1,
},
{
"feature1":[0.1,1.2,3.4],
"min_score":0,
"max_score":9999,
“weight”:2,
}
],
# filter condition, default all and
"filters": {
            "range_filters": {
                "price": {
                    "gte": 160,
                    "lte": 180
                },
                "sales": {
                    "gte":100,
                    "lte":10
                }
            },
            "term_filters": {
                "labels": {
                    "value": ["100", "200", "300"],
                    "operator": "or"
                }
            },
}, 

"force_brute_search": false,
"topn": 30,
# if pack_fields not specfied，display all fields except vector fields
"pack_fields":["nickname", "price"],
# default L2
"metric_type": L2
}' http://localhost:8080/search
```

## list the table fields information
```bash
curl -H "Content-Type: application/json" -X POST -d \
'{
"db":"default",
"table":"test",
}' http://localhost:8080/list
```

More description about RESTful API please see [here](https://github.com/awa-ai/awadb/tree/main/docs/source/restful_api.md)
