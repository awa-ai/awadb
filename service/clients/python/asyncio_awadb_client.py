# Copyright 2020 The gRPC Authors
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
"""The Python AsyncIO implementation of the gRPC route guide client."""

import asyncio
import logging
import random
from typing import Iterable, List

import grpc
import awadb_pb2
import awadb_pb2_grpc
import awadb_resources


# Performs an unary call
async def create(
    stub: awadb_pb2_grpc.AwaDBServerStub, 
    db_name: str,
    table_name: str
) -> None:
    db_meta = awadb_pb2.DBMeta()
    db_meta.db_name = db_name
    table_meta = db_meta.tables_meta.add()
    table_meta.name = table_name

    response = await stub.Create(db_meta)
    if response.code == awadb_grpc.ResponseCode.OK:
        print('table %s create success!' % table_name)
    else:
        print('table %s create failed!' % table_name)

async def add_fields(
    stub: awadb_pb2_grpc.AwaDBServerStub,
    db_name: str,
    table_name: str,
    fields: List[awadb_pb2.awadb_grpc.FieldMeta] 
) -> bool:
    db_meta = awadb_pb2.DBMeta()
    db_meta.db_name = db_name
    table_meta = db_meta.tables_meta.add()
    table_meta.name = table_name
    table_meta.fields_meta.extend(fields) 
    
    response = await stub.AddFields(db_meta)
    ret: bool = True 
    if response.code == awadb_grpc.ResponseCode.OK:
        print('table %s add fields success!' % table_name)
    else:
        print('table %s add fields failed!' % table_name)
        ret = False
    return ret

async def add_or_update(
    stub: awadb_pb2_grpc.AwaDBServerStub,
    db_name: str,
    table_name: str,
    documents: List[awadb_pb2.awadb_grpc.Document]  
) -> bool:
    

async def get(
    stub: awadb_pb2_grpc.AwaDBServerStub,
    db_name: str,
    table_name: str,
    ids: List[str]
) -> List[awadb_pb2.awadb_grpc.Document]:



async def search(
    stub: awadb_pb2_grpc.AwaDBServerStub,
    db_name: str,
    table_name: str,
    vec_queries: list,
    filter: dict,
    k: int,
    retrieval_params: str,
    pack_fields: List[str]
) -> awadb_pb2.awadb_grpc.SearchResponse:



async def delete(
    stub: awadb_pb2_grpc.AwaDBServerStub,
    db_name: str,
    table_name: str,
    ids: List[str]
) -> bool:


async def main() -> None:
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = awadb_pb2_grpc.AwaDBServerStub(channel)
    
        print("-------------- Create --------------")
        await create(stub)
        
        print("-------------- AddFields --------------")
        await add_fields(stub)
        
        print("-------------- AddOrUpdate --------------")
        await add_or_update(stub)
        
        print("-------------- Get --------------")
        await get(stub)
        
        print("-------------- Search --------------")
        await search(stub)
        
        print("-------------- Delete --------------")
        await delete(stub)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.get_event_loop().run_until_complete(main())
