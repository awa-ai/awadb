# RESTful API

## create table
```bash
# here the awadb proxy and server are deployed on the localhost port 8080 
http://localhost:8080/create  
{
"db": ""
"table": ""
"desc": ""
"fields" : [{"name": "", "type":"", "index":true, "store":true}, {“name”:"", "type":"", "index":true, "store":true, "dimension":768}]
}

db: creating db name
table: creating table name
desc: optional, description about the db/table
fields: the definition of each field in the table, can be a map or list of maps
        each map denotes the definition of a field in the table
name: field name
type: field type, valid type include 'string', 'int', 'long', 'float', "double", "vector" or "multi_string", otherwise invalid
index: whether the field is to index, bool type, true or false
store: whether the field is to store, bool type, true or false
dimension: the vector field's dimension
```

## add documents to table
```bash
http://localhost:8080/add  
{
"db":"default",
"table":"test",
"docs":[{"nickname":"lj" ,"feature":[1,2,3]}, {"nickname":"tk", "feature":[1,1,1]}]
}

db: creating db name
table: creating table name
docs: documents to add in the table, can be a map or list of maps
      each map denotes a document adding into table. In the map, key denotes a field name, value denotes the field value
in the example above, two documents are adding into table. 'nickname' denotes a field name, 'feature' denotes a vector field name
please note that each document has a primary key named '_id', if not specified, it will be automatically generated a string by awadb
primary key '_id' can be 'string' or 'long' type
```

## get document based on ids or filter condition
```bash
http://localhost:8080/get  
{
"db":"default",
"table":"test",
#ids value type can be long or string
"ids":[1,2,3]
}

db: creating db name
table: creating table name
ids: the primary keys of getting documents
     here 1, 2, 3 are the requested documents' primary keys 
```

## delete documents by ids or condition
```bash
http://localhost:8080/delete  
{
"db":"default",
"table":"test",
#ids value type can be long or string
"ids":[1,2,3]
}

db: creating db name
table: creating table name
ids: the primary keys of deleting documents
     here 1, 2, 3 are the requested documents' primary keys
```

## search documents by vector query and filter condition
```bash
http://localhost:8080/search
{
"db":"default", #  creating db name
"table":"test", #  creating table name
# all the vector fields
“vector_query”: [
{
"feature":[0.1, 1.2, 3.4], # vector field name and value, here the vector field name is 'feature', querying vector value is [0.1, 1.2, 3.4]
"min_score":0,             # the minimum score for querying vectors' distance score
"max_score":99999,         # the maximum score for querying vectors' distance score
"weight":1,                # the weight for querying vector field
},
{
"feature1":[0.2,1.5,3.5], # vector field name and value, here the vector field name is 'feature1', querying vector value is [0.2, 1.5, 3.5]
"min_score":0,            # the minimum score for querying vectors' distance score
"max_score":9999,         # the maximum score for querying vectors' distance score
“weight”:2,               # the weight for querying vector field
}
],
# filter condition, default all intersection 
"filters": { # keyword for field filters
            "range_filters": { # keyword for range filters of fields
                "price": { # filtering field 'price'
                    "gte": 160,  # field value greater than or equal to 160
                    "lte": 180   # field value less then or equal to 180
                },
                "sales": { # filtering field 'sales'
                    "gt":100, # field value greater than 100 
                    "lt":200  # field value less than 200 
                }
            },
             "term_filters": {    # keyword for term filters of fields
                 "labels": {      # 'labels' is the term field name
                     "value": ["100", "200", "300"], # '100', '200', '300' are the term field values
                     "operator": "or"  # or logic operation
                 }
             },
}, 

"force_brute_search": false,  # whether to force to use brute search
"topn": 30,                   # the most top n similar results
# if pack_fields not specfied，display all fields except vector fields
"pack_fields":["nickname", "price"],
# default L2
"metric_type": L2
}

```

## list the table fields information
```bash
http://localhost:8080/list
{
# if neither db nor table is specified, list all db names
# if db is specified, table not specified, list all tables in specified db
# if both db and table are specified, list the fields information in specified table
"db":"default", 
"table":"test",
}
```

