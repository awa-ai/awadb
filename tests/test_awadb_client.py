# -*- coding:utf-8 -*-
#!/usr/bin/python3

# Copyright 2023 AwaDB authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Python implementation of the gRPC AwaDB client."""

from __future__ import print_function

import numpy as np
import struct
import sys
sys.path.append('../service/idl/')

import logging
import random

from typing import List, Optional

import grpc
import awadb_pb2
import awadb_pb2_grpc

def create(
    stub: awadb_pb2_grpc.AwaDBServerStub, 
    db_name: str,
    table_name: str
) -> None:
    db_meta = awadb_pb2.DBMeta()
    db_meta.db_name = db_name
    table_meta = db_meta.tables_meta.add()
    table_meta.name = table_name

    fields: List[awadb_pb2.FieldMeta] = [] 
    f1 = awadb_pb2.FieldMeta()
    f1.name = "name"
    f1.type = awadb_pb2.STRING
    f1.is_index = True

    f2 = awadb_pb2.FieldMeta()
    f2.name = "age"
    f2.type = awadb_pb2.INT
    f2.is_index = True

    f3 = awadb_pb2.FieldMeta()
    f3.name = "title"
    f3.type = awadb_pb2.VECTOR
    f3.is_index = True
    f3.vec_meta.data_type = awadb_pb2.FLOAT
    f3.vec_meta.dimension = 3
    f3.vec_meta.store_type = "MMAP"


    fields.append(f1)
    fields.append(f2)
    fields.append(f3)

    table_meta.fields_meta.extend(fields)

    response = stub.Create(db_meta)
    if response.code == awadb_pb2.ResponseCode.OK:
        print('table %s create success!' % table_name)
    else:
        print('table %s create failed!' % table_name)

def add_fields(
    stub: awadb_pb2_grpc.AwaDBServerStub,
    db_name: str,
    table_name: str,
    fields: List[awadb_pb2.FieldMeta] 
) -> bool:
    db_meta = awadb_pb2.DBMeta()
    db_meta.db_name = db_name
    table_meta = db_meta.tables_meta.add()
    table_meta.name = table_name
    table_meta.fields_meta.extend(fields) 
    
    response = stub.AddFields(db_meta)
    ret: bool = True 
    if response.code == awadb_pb2.ResponseCode.OK:
        print('table %s add fields success!' % table_name)
    else:
        print('table %s add fields failed!' % table_name)
        ret = False
    return ret

def add_or_update(
    stub: awadb_pb2_grpc.AwaDBServerStub,
    db_name: str,
    table_name: str,
    documents: List[awadb_pb2.Document]  
) -> bool:
    docs_data = awadb_pb2.Documents()

    docs_data.db_name = db_name
    docs_data.table_name = table_name

    docs_data.docs.extend(documents) 
    #for doc in documents:
    #    docs_data.docs.append(doc)

    response = stub.AddOrUpdate(docs_data)
    
    ret: bool = True 
    if response.code == awadb_pb2.ResponseCode.OK:
        print('table %s add_or_update success!' % table_name)
    else:
        print('table %s add_or_update failed!' % table_name)
        ret = False
    return ret

def get(
    stub: awadb_pb2_grpc.AwaDBServerStub,
    db_name: str,
    table_name: str,
    ids: List[str]
) -> awadb_pb2.Documents:
    doc_condition = awadb_pb2.DocCondition()
    doc_condition.db_name = db_name
    doc_condition.table_name = table_name
    
    doc_condition.ids.extend(ids)

    docs = stub.Get(doc_condition)

    return docs


def search(
    stub: awadb_pb2_grpc.AwaDBServerStub,
    db_name: str,
    table_name: str,
    vec_queries: List[awadb_pb2.VectorQuery],
    k: int,
    retrieval_params: str,
    pack_fields: List[str],
    filter: Optional[List[awadb_pb2.RangeFilter]] = None,
) -> awadb_pb2.SearchResponse:
    request = awadb_pb2.SearchRequest()
    request.db_name = db_name
    request.table_name = table_name
    request.vec_queries.extend(vec_queries)
    if filter is not None: 
        request.range_filters.extend(filter)

    request.topn = k
    request.retrieval_params = retrieval_params
    request.brute_force_search = True
    for field in pack_fields:
        request.pack_fields.append(field)

    results = stub.Search(request)
    return results

def delete(
    stub: awadb_pb2_grpc.AwaDBServerStub,
    db_name: str,
    table_name: str,
    ids: List[str]
) -> bool:

    doc_condition = awadb_pb2.DocCondition()
    doc_condition.db_name = db_name
    doc_condition.table_name = table_name
    
    for id in ids:
        doc_condition.ids.append(id)

    response = stub.Delete(doc_condition)

    ret: bool = True 
    if response.code == awadb_pb2.ResponseCode.OK:
        print('table %s delete doc success!' % table_name)
    else:
        print('table %s delete doc failed!' % table_name)
        ret = False
    return ret

def normalize(vec_array):
    x = np.array(vec_array)
    x_l2_norm = np.linalg.norm(x,ord=2)
    x_l2_normalized = x / x_l2_norm
    return x_l2_normalized


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel("localhost:50005") as channel:
        stub = awadb_pb2_grpc.AwaDBServerStub(channel)
      
        db_name = "defalut"
        table_name = "test"

        print("-------------- Create --------------")
        create(stub, db_name, table_name)
    
        fields: List[awadb_pb2.FieldMeta] = [] 
        f1 = awadb_pb2.FieldMeta()
        f1.name = "height"
        f1.type = awadb_pb2.FLOAT
        f1.is_index = True

        fields.append(f1)

        print("-------------- AddFields --------------")
        add_fields(stub, db_name, table_name, fields)

        docs_list: List[awadb_pb2.Document] = []
        doc1 = awadb_pb2.Document() 
        doc1.id = "1"
        fid1 = doc1.fields.add()
        fid1.name = "name"
        name_value = "vincent"
        fid1.value = str.encode(name_value)
        fid1.type = awadb_pb2.STRING

        fid2 = doc1.fields.add()
        fid2.name = "age"
        fid2_value = 20
        fid2.value = fid2_value.to_bytes(4, "little") 
        fid2.type = awadb_pb2.INT
        
        fid3 = doc1.fields.add()
        fid3.name = "title"
        value = [31.23, 3.2, 5.1]
        normalize_value = normalize(value)
        fid3.value = np.array(normalize_value, dtype=np.dtype("float32")).tobytes()
        fid3.type = awadb_pb2.VECTOR
      
        fid4 = doc1.fields.add()
        fid4.name = "height"
        fid4_value = 1.71 
        fid4.value = struct.pack("<f", fid4_value)
        fid4.type = awadb_pb2.FLOAT



        doc2 = awadb_pb2.Document() 
        doc2.id = "2"
        fid1 = doc2.fields.add()
        fid1.name = "name"
        name_value = "david"
        fid1.value = str.encode(name_value)
        fid1.type = awadb_pb2.STRING

        fid2 = doc2.fields.add()
        fid2.name = "age"
        fid2_value = 16
        fid2.value = fid2_value.to_bytes(4, "little") 
        fid2.type = awadb_pb2.INT
        
        fid3 = doc2.fields.add()
        fid3.name = "title"
        value = [2.3, 1.8, 3.8]
        normalize_value = normalize(value)
        fid3.value = np.array(normalize_value, dtype=np.dtype("float32")).tobytes()
        fid3.type = awadb_pb2.VECTOR

        fid4 = doc2.fields.add()
        fid4.name = "height"
        fid4_value = 1.81 
        fid4.value = struct.pack("<f", fid4_value)
        fid4.type = awadb_pb2.FLOAT


        docs_list.append(doc1)
        docs_list.append(doc2)

        print("-------------- AddOrUpdate --------------")
        add_or_update(stub, db_name, table_name, docs_list)

        ids: List[str] = []
        ids.append("2")
        print("-------------- Get --------------")
        documents = get(stub, db_name, table_name, ids)

        print(documents)
        print(documents.db_name)
        print(documents.table_name)

        for document in documents.docs:
            print("doc id is %s" % document.id)
        
            for fid in document.fields:
                if fid.type == awadb_pb2.INT:
                    print(int(fid.value))
                if fid.type == awadb_pb2.FLOAT:
                    print(float(fid.value)) 
                elif fid.type == awadb_pb2.STRING:
                    print(str(fid.value, encoding = "utf-8"))


        v_queries: List[awadb_pb2.VectorQuery] = []
        v_query = awadb_pb2.VectorQuery()
        v_query.field_name = "title" 
        vec_value = [2.3, 5.6, 1.3] 
        normalize_value = normalize(vec_value)
        v_query.value = np.array(normalize_value, dtype=np.dtype("float32")).tobytes()
        v_query.min_score = -1
        v_query.max_score = 999999
        v_queries.append(v_query)
        k = 2
       
        pack_fields: List[str] = []
        pack_fields.append("name")
        pack_fields.append("age")
        pack_fields.append("height")

        default_retrieval_type = "{\"metric_type\":\"InnerProduct\"}"
        print("-------------- Search --------------")
        response = search(stub, db_name, 
            table_name, v_queries, 
            k, default_retrieval_type, pack_fields)
      
        print(response)
        '''
        print(response.db_name)
        print(response.table_name)
        for result in response.results:
            print("total result is %d"%result.total)
            for item in result.result_items:
                print("score is %f" % item.score)
                for f in item.fields:
                    if f.type == awadb_pb2.INT:
                        print(int(f.value))
                    elif f.type == awadb_pb2.FLOAT:
                        print(float(f.value))
                    elif f.type == awadb_pb2.STRING:
                        print(str(f.value, encoding = "utf-8"))
        '''
        ids: List[str] = []
        ids.append("2")
        print("-------------- Delete --------------")
        delete(stub, db_name, table_name, ids)

if __name__ == "__main__":
    logging.basicConfig()
    run()
