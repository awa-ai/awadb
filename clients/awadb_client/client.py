# -*- coding:utf-8 -*-
#!/usr/bin/python3

from __future__ import annotations

import logging

import json
import os
import struct
import uuid
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set

import grpc
import numpy as np
from awadb_client.py_idl.awadb_pb2 import *
from awadb_client.py_idl.awadb_pb2_grpc import AwaDBServerStub
from awadb_client.awadb_api import AwaAPI
from awadb_client.awadb_api import DEFAULT_DB_NAME
from awadb_client.awadb_api import DEFAULT_TOPN
from awadb_client.awadb_api import DOC_PRIMARY_KEY_NAME
from awadb_client.awadb_api import MetricType

__version__ = "0.0.9"

DEFAULT_SERVER_ADDR = "0.0.0.0:50005"

class FieldDataType(Enum):
    INT = 1
    LONG = 2
    FLOAT = 3
    STRING = 4 
    VECTOR = 5 
    ERROR = 6 
    MULTI_STRING = 7

def typeof(variate):
    v_type = FieldDataType.ERROR
    if isinstance(variate, int):
        v_type = FieldDataType.INT
    elif isinstance(variate, str):
        v_type = FieldDataType.STRING
    elif isinstance(variate, float):
        v_type = FieldDataType.FLOAT
    elif isinstance(variate, list):
        element_size = variate.__len__()
        number_count = 0
        str_count = 0
        for element in variate:
            if isinstance(element, str):
                str_count = str_count + 1
            elif (
                isinstance(element, int)
                or isinstance(element, float)
                or isinstance(element, np.float32)
            ):
                number_count = number_count + 1
        if number_count == element_size:
            v_type = FieldDataType.VECTOR
        elif str_count == element_size:
            v_type = FieldDataType.MULTI_STRING
    elif type(variate).__name__ == "ndarray":
        v_type = FieldDataType.VECTOR

    return v_type


class Awa(AwaAPI):
    """Interface implemented by AwaDB service client"""
    def __init__(
        self,
        server_addr: Optional[str] = None,
    ):
        """Initialize the AwaDB client.
        
        Args:
            server_addr: AwaDB sever ip:port. Default to 0.0.0.0:50005.

        Returns:
            None.
        """

        if server_addr is None:
            self.channel = grpc.insecure_channel(DEFAULT_SERVER_ADDR)
        else:
            self.channel = grpc.insecure_channel(server_addr)
        self.stub = AwaDBServerStub(self.channel)

        self.tables_fields_check = {}
        self.tables_fields_type = {}
        self.tables_vector_fields_type = {}
        self.tables_attr = {}
        self.tables_extra_new_fields = {}
        
    def close(self):
        """Close the connection of AwaDB client and server.

        Args: None.

        Returns: None.
        """
        if self.channel is not None:
            self.channel.close()

    def create(
        self,
        db_meta: DBMeta,
    ) -> bool: 
        """Create db or specified table.
        
        Args:
            db_meta: DB schema information.

        Returns: True or False for creating db or tables 
        """

    def list(
        self,
        db_name: Optional[str] = None,
        table_name: Optional[str] = None,
    ):
        """List the db or tables in db.

        Args:
            db_name: Database name, default to None.
            table_name: Table name, default to None.

        Returns: 
            If db_name and table_name both are None, return all the databases.
            If table_name is None, return all tables in db_name.
            If neither db_name nor table_name is None, return the schema of the table. 
        """


    def drop(
        self,
        db_name: str,
        table_name: Optional[str] = None,
    ) -> bool:
        """Drop the db or the table in db.

        Args:
            db_name: Database name, default to None.
            table_name: Table name, default to None.

        Returns: 
            If table_name is None, and there are no tables in database "db_name",
            the database can be dropped successfully, otherwise failed.
        """

    def add(
        self,
        table_name: str,
        docs,
        db_name: str = DEFAULT_DB_NAME,
    ) -> bool:
        """Add documents into the specified table.
           If table not existed, it will be created automatically.

        Args:
            table_name: The specified table for search and storage.
            
            docs: The adding documents which can be described as dict or list of dicts.
                    Each key-value pair in dict is a field of document.
            
            db_name: Database name, default to DEFAULT_DB_NAME.

        Returns:
            Success or failure of adding the documents into the specified table.
        """

        if self.__network_error():
            return ""
        if len(table_name) == 0:
            return False
        is_dict = isinstance(docs, dict)
        documents = Documents()
        documents.db_name = db_name
        documents.table_name = table_name
        db_table_name = db_name + "/" + table_name
        self.__check_table_from_server(table_name, db_table_name, db_name)
        if not db_table_name in self.tables_fields_check:
            self.tables_fields_check[db_table_name] = False
            self.tables_fields_type[db_table_name] = {}
            self.tables_vector_fields_type[db_table_name] = {} 
            self.tables_extra_new_fields[db_table_name] = [] 
            db_meta = DBMeta()
            db_meta.db_name = db_name
            table_meta = db_meta.tables_meta.add()
            table_meta.name = table_name
            self.tables_attr[db_table_name] = db_meta

        if not is_dict:
            is_list = isinstance(docs, list)
            if not is_list:
                print('The adding docs format error!')
                return False
            for doc in docs:
                if not isinstance(doc, dict):
                    continue
                pb_doc = documents.docs.add()
                self.__assemble_doc(db_table_name, pb_doc, doc)

        else:
            pb_doc = documents.docs.add()
            self.__assemble_doc(db_table_name, pb_doc, docs)
        
        status = self.stub.AddOrUpdate(documents)
        if status.code != OK:
            print("Add docs error code %d!" % int(status.code))
            return False
        return True
    
    def search(
        self,
        table_name: str,
        query,
        db_name: str = DEFAULT_DB_NAME,
        topn: int = DEFAULT_TOPN,
        filters: Optional[dict] = None,
        include_fields: Optional[Set[str]] = None,
        brute_force_search: bool = False,
        metric_type: MetricType = MetricType.L2,
        mul_vec_weight: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ):
        """Vector search in the specified table.

        Args: 
            table_name: The specified table for search.

            query: Input query, including vector or text. now just support vector query.

            db_name: Database name, default to DEFAULT_DB_NAME.

            topn: The topn nearest neighborhood documents to return.

            filters (Optional[dict]): Filter by filters. Defaults to None.

            E.g. `{"color" : "red", "price": 4.20}`. Optional.

            E.g. `{"max_price" : 15.66, "min_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<'price'<15.66).

            E.g. `{"maxe_price" : 15.66, "mine_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<='price'<=15.66).

            include_fields: The fields whether included in the search results.

            brute_force_search: Brute force search or not. Default to not.
                                        If vectors not indexed, automatically to use brute force search.

            metric_type: The distance type of computing vectors. Default to L2.

            mul_vec_weight: Multiple vector field search weights. Default to None.

            E.g. `{'f1': 2.0, 'f2': 1.0}`  vector field f1 weight is 2.0, vector field f2 weight is 1.0.

            Notice that field f1 and f2 should have the same dimension compared to query.

            kwargs: Any possible extended parameters.

        Returns:
            Results of searching.
        """
        if self.__network_error():
            return ""
        if len(table_name) == 0:
            print("Please specify the table name!")
            return ""

        query_type = typeof(query)

        if query_type != FieldDataType.VECTOR:
            return ""

        db_table_name = db_name + "/" + table_name
        request = SearchRequest()
        request.db_name = db_name
        request.table_name = table_name
        
        vec_value = ""
        #notice: the added vectors should also be normalized
        if metric_type == MetricType.INNER_PRODUCT:
            vec_value = self.__normalize(query)
            request.retrieval_params = "{\"metric_type\":\"InnerProduct\"}"
            request.is_l2 = False
        elif metric_type == MetricType.L2:
            vec_value = np.array(query, dtype=np.dtype("float32"))
            request.retrieval_params = "{\"metric_type\":\"L2\"}"
            request.is_l2 = True 

        query_dimension = vec_value.__len__()
      
        self.__check_table_from_server(table_name, db_table_name, db_name)
        vectors_num = 0 
        for vec_field_name in self.tables_vector_fields_type[db_table_name]:
            if query_dimension == self.tables_vector_fields_type[db_table_name][vec_field_name]:
                vec_request = request.vec_queries.add()
                vec_request.field_name = vec_field_name 
                vec_request.min_score = -1 
                vec_request.max_score = 999999
                vec_request.value = vec_value.tobytes()
                vec_request.is_boost = True
                vec_request.boost = 1.0
                if mul_vec_weight is not None and vec_field_name in mul_vec_weight:
                    vec_request.boost = mul_vec_weight[vec_field_name]

                vectors_num = vectors_num + 1
        if vectors_num == 0:
            print("Query vector dimension is not valid!")
            return ""
        elif vectors_num > 1:
            #request.mul_vec_logic_op = OR
            print("vector query > 1")

        request.topn = topn
        request.brute_force_search = brute_force_search
        if filters is not None:
            __add_filter(db_table_name, request, filters)

        if include_fields is None:
            for field_name in self.tables_fields_type[db_table_name]:
                if self.tables_fields_type[db_table_name][field_name] != FieldDataType.VECTOR:
                    request.pack_fields.append(field_name)
            #request.is_pack_all_fields = True
        else:
            for pack_field in include_fields:
                request.pack_fields.append(pack_field)
       
        response = self.stub.Search(request)
        show_results = self.__transfer2results(response)

        return show_results 

    def __transfer2results(
        self,
        response,
    ):
        results = {}
        results["Db"] = response.db_name
        results["Table"] = response.table_name
        search_results = []
        for result in response.results:
            search_result = {}
            search_result["ResultSize"] = result.total
            search_result["Msg"] = result.msg

            each_query_result_items = []
            for item in result.result_items:
                result_item = {}
                result_item["score"] = item.score
                for field in item.fields:
                    if field.type == FieldType.INT:
                        result_item[field.name] = int(field.value)
                    elif field.type == FieldType.LONG:
                        result_item[field.name] = int(field.value)
                    elif field.type == FieldType.FLOAT:
                        result_item[field.name] = float(field.value)
                    elif field.type == FieldType.DOUBLE:
                        result_item[field.name] = float(field.value)
                    elif field.type == FieldType.STRING:
                        result_item[field.name] = field.value.decode('utf-8')
                    elif field.type == FieldType.MULTI_STRING:
                        mul_array = [] 
                        for mul_str in field.mul_str_value:
                            mul_array.append(mul_str)
                        result_item[field.name] = mul_array
                    elif field.type == FieldType.VECTOR:
                        print("vector")
                each_query_result_items.append(result_item)
            search_result["ResultItems"] = each_query_result_items
            search_results.append(search_result)

        if response.results.__len__() == 1:
            results["SearchResults"] = search_results[0]
        else:
            results["SearchResults"] = search_results

        return results


    def get(
        self,
        table_name: str,
        db_name: str = DEFAULT_DB_NAME,
        ids: Optional[list] = None,
        filters: Optional[dict] = None,
        include_fields: Optional[Set[str]] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ):
        """Get documents of the primary keys in the the specified table.

        Args:
            table_name: The specified table for search and storage.

            db_name: Database name, default to DEFAULT_DB_NAME.

            ids: The primary keys of the queried documents.

            filters: Filter by fields. Defaults to None.

            E.g. `{"color" : "red", "price": 4.20}`. Optional.

            E.g. `{"max_price" : 15.66, "min_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<'price'<15.66).

            E.g. `{"maxe_price" : 15.66, "mine_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<='price'<=15.66).

            include_fields: The fields whether included in the get results.

            limit: The limited return results.

        Returns:
            The detailed information of the queried documents.
        """

        if self.__network_error():
            return "" 
        if table_name is None or len(table_name) == 0 or ids is None:
            return "" 

        doc_condition = DocCondition()
        doc_condition.db_name = db_name
        doc_condition.table_name = table_name
      
        db_table_name = db_name + "/" + table_name
        
        self.__check_table_from_server(table_name, db_table_name, db_name)
        if not self.__check_ids_type(db_table_name, ids):
            print("Input ids should be list of str or long")
            return ""
        
        if self.tables_fields_type[db_table_name][DOC_PRIMARY_KEY_NAME] == FieldDataType.LONG:
            for each_id in ids: 
                doc_condition.ids.append(each_id.to_bytes(8, "little"))

        elif self.tables_fields_type[db_table_name][DOC_PRIMARY_KEY_NAME] == FieldDataType.STRING:
            for each_id in ids: 
                doc_condition.ids.append(str.encode(each_id))

        response = self.stub.Get(doc_condition)
        return response

    def delete(
        self,
        table_name: str,
        db_name: str = DEFAULT_DB_NAME,
        ids: Optional[list] = None,
        filters: Optional[dict] = None, 
        **kwargs: Any,
    ) -> bool:
        """Delete docs in the specified table.

        Args:
            table_name: The specified table for deleting.

            db_name: Database name, default to DEFAULT_DB_NAME.

            ids: The primary keys of the deleted documents.

            filters: Filter by fields. Defaults to None.

            E.g. `{"color" : "red", "price": 4.20}`. Optional.

            E.g. `{"max_price" : 15.66, "min_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<'price'<15.66).

            E.g. `{"maxe_price" : 15.66, "mine_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<='price'<=15.66).
        Returns:
            True of False of the deleting operation.
        """

        if self.__network_error():
            return "" 
        if table_name is None or len(table_name) == 0 or ids is None:
            return "" 

        doc_condition = DocCondition()
        doc_condition.db_name = db_name
        doc_condition.table_name = table_name
      
        db_table_name = db_name + "/" + table_name
        self.__check_table_from_server(table_name, db_table_name, db_name)
        if not self.__check_ids_type(db_table_name, ids):
            print("Input ids should be list of str or long")
            return ""

        if self.tables_fields_type[db_table_name][DOC_PRIMARY_KEY_NAME] == FieldDataType.LONG:
            for each_id in ids: 
                doc_condition.ids.append(each_id.to_bytes(8, "little"))

        elif self.tables_fields_type[db_table_name][DOC_PRIMARY_KEY_NAME] == FieldDataType.STRING:
            for each_id in ids: 
                doc_condition.ids.append(str.encode(each_id))

        response = self.stub.Delete(doc_condition)
        return response

    def __normalize(vec_array):
        x = np.array(vec_array, dtype=np.dtype("float32"))
        x_l2_norm = np.linalg.norm(x,ord=2)
        x_l2_normalized = x / x_l2_norm
        return x_l2_normalized

    def __network_error(
        self
    ):
        if self.channel is None or self.stub is None:
            print('Channel or Stub can be None!!!')
            return  True
        return False 

    def __check_ids_type(self,
        db_table_name: str,  
        ids: list,
    ) -> bool:
        if self.tables_fields_type[db_table_name][DOC_PRIMARY_KEY_NAME] == FieldDataType.LONG:
            id_count = 0 
            for each_id in ids:
                if isinstance(each_id, int):
                    id_count = id_count + 1
            if id_count != ids.__len__():
                return False
        elif self.tables_fields_type[db_table_name][DOC_PRIMARY_KEY_NAME] == FieldDataType.STRING:
            str_count = 0
            for each_id in ids:
                if isinstance(each_id, str):
                    str_count = str_count + 1
            if str_count != ids.__len__():
                return False

        return True

    def __check_table_from_server(
        self,
        table_name,
        db_table_name,
        db_name: str = DEFAULT_DB_NAME
    ):
        if not db_table_name in self.tables_fields_check:
            db_table_req = DBTableName()
            db_table_req.db_name = db_name
            db_table_req.table_name = table_name
            table_status = self.stub.CheckTable(db_table_req)
            if table_status.is_existed:
                db_meta = DBMeta()
                db_meta.db_name = db_name
                table_meta_attr = db_meta.tables_meta.add()
                table_meta_attr.name = table_name
                self.tables_attr[db_table_name] = db_meta
                for table_meta in table_status.exist_table.tables_meta:
                    fields_type = {} 
                    vector_fields_type = {} 
                    for field_meta in table_meta.fields_meta:
                        if field_meta.type == INT:
                            fields_type[field_meta.name] = FieldDataType.INT 
                        elif field_meta.type == LONG:
                            fields_type[field_meta.name] = FieldDataType.LONG
                        elif field_meta.type == FLOAT:
                            fields_type[field_meta.name] = FieldDataType.FLOAT
                        elif field_meta.type == DOUBLE:
                            fields_type[field_meta.name] = FieldDataType.FLOAT
                        elif field_meta.type == STRING:
                            fields_type[field_meta.name] = FieldDataType.STRING
                        elif field_meta.type == MULTI_STRING:
                            fields_type[field_meta.name] = FieldDataType.MULTI_STRING
                        elif field_meta.type == VECTOR:
                            fields_type[field_meta.name] = FieldDataType.VECTOR
                            vector_fields_type[field_meta.name] = field_meta.vec_meta.dimension

                    self.tables_fields_type[db_table_name] = fields_type
                    self.tables_vector_fields_type[db_table_name] = vector_fields_type

                self.tables_fields_check[db_table_name] = True

    def __add_filter(
        self,
        db_table_name,
        request,
        meta_filter: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        if meta_filter is not None:
            range_filters: dict = {}
            term_filters: dict = {}
            for field_name in meta_filter:
                field_value = meta_filter[field_name]
                has_range_value = True
                is_max_value = True
                max_value_include = False
                min_value_include = False
                if field_name.startswith("max_"):
                    field_name = field_name[4:]
                elif field_name.startswith("min_"):
                    field_name = field_name[4:]
                    is_max_value = False
                elif field_name.startswith("maxe_"):
                    field_name = field_name[5:]
                    max_value_include = True
                elif field_name.startswith("mine_"):
                    field_name = field_name[5:]
                    is_max_value = False
                    min_value_include = True
                else:
                    has_range_value = False
                if field_name not in self.tables_fields_type[db_table_name]:
                    print("field name %s not exist!" % field_name)
                    continue

                field_type = typeof(field_value)

                if field_type == FieldDataType.INT or field_type == FieldDataType.FLOAT:
                    if field_name not in range_filters:
                        range_filters[field_name] = request.range_filters().add()
                        range_filters[field_name].field_name = field_name
                    bytes_value = (
                        field_value.to_bytes(4, "little")
                        if (field_type == FieldDataType.INT)
                        else struct.pack("<f", field_value)
                    )
                    if not has_range_value:
                        range_filters[field_name].lower_value = bytes_value
                        range_filters[field_name].upper_value = bytes_value
                        range_filters[field_name].include_lower = True
                        range_filters[field_name].include_upper = True
                    else:
                        if is_max_value:
                            range_filters[field_name].upper_value = bytes_value
                            range_filters[field_name].include_upper = max_value_include
                        else:
                            range_filters[field_name].lower_value = bytes_value
                            range_filters[field_name].include_lower = min_value_include

                elif field_type == FieldDataType.STRING:
                    if field_name not in term_filters:
                        term_filters[field_name] = request.term_filters().add() 
                        term_filters[field_name].field_name = field_name
                    term_filters[field_name].value = field_value
                    term_filters[field_name].is_union = True

        return None


    def __field_check(
        self, 
        db_table_name,
        field_name, 
        field_data, 
        fields_type):
        f_type = typeof(field_data)
        if field_name == DOC_PRIMARY_KEY_NAME and f_type == FieldDataType.INT:
            f_type = FieldDataType.LONG

        if f_type == FieldDataType.ERROR:
            print(
                "Field data type error! Please input right data type : int|float|string|vector|multi_string!"
            )
            return -1

        if field_name in fields_type:
            return 2

        if field_name in self.tables_fields_type[db_table_name]:
            if (
                f_type == FieldDataType.STRING
                and self.tables_fields_type[db_table_name][field_name]
                == FieldDataType.MULTI_STRING
            ):
                fields_type[field_name] = FieldDataType.MULTI_STRING
                return 0

            if f_type != self.tables_fields_type[db_table_name][field_name]:
                print('Input data type is conflict with the original field %s in db_table %s' % (field_name, db_table_name))
                return -3
            if f_type == FieldDataType.VECTOR:
                if field_data.__len__() != self.tables_vector_fields_type[db_table_name][field_name]:
                    print('Input vector field %s dimension is not consistent, the dimension should be %d!' \
                            %(field_name, self.tables_vector_fields_type[db_table_name][field_name]))
                    return -4

            fields_type[field_name] = f_type
        else:
            if self.tables_fields_check[db_table_name] and f_type == FieldDataType.VECTOR:
                print('New vector field %s can not added after table %s created!' % (field_name, db_table_name)) 
                return -5

            self.tables_fields_type[db_table_name][field_name] = f_type
            fields_type[field_name] = f_type
            return 1
        return 0

    def __add_field(self, db_table_name, name, datatype, is_index, add_new_field):
        if not self.tables_fields_check[db_table_name]:
            if datatype != MULTI_STRING:
                table_meta = self.tables_attr[db_table_name].tables_meta[0]
                field_meta = table_meta.fields_meta.add()
                field_meta.name = name
                field_meta.type = datatype
                field_meta.is_index = is_index
            else:
                db_meta = DBMeta()
                this_db_meta = self.tables_attr[db_table_name]
                db_meta.db_name = this_db_meta.db_name
                table_meta = db_meta.tables_meta.add()
                table_meta.name = this_db_meta.tables_meta[0].name
                field_meta = table_meta.fields_meta.add()
                field_meta.name = name
                field_meta.type = datatype
                field_meta.is_index = is_index

                self.tables_extra_new_fields[db_table_name].append(db_meta)
            return True

        if add_new_field:
            db_meta = DBMeta()
            this_db_meta = self.tables_attr[db_table_name]
            db_meta.db_name = this_db_meta.db_name
            table_meta = db_meta.tables_meta.add()
            table_meta.name = this_db_meta.tables_meta[0].name
            field_meta = table_meta.fields_meta.add()
            field_meta.name = name
            field_meta.type = datatype
            field_meta.is_index = is_index

            status = self.stub.AddFields(db_meta)

            if status.code != OK:
                print("Add new field %s failed!" % name)
                return False

        return True

    def __add_vector_field(
        self, 
        db_table_name, 
        name, 
        datatype, 
        is_index, 
        dimension, 
        store_type, 
        store_param, 
        has_source
    ):
        if not self.tables_fields_check[db_table_name]:
            table_meta = self.tables_attr[db_table_name].tables_meta[0]
            field_meta = table_meta.fields_meta.add()
            field_meta.name = name
            field_meta.type = VECTOR
            field_meta.is_index = is_index
            field_meta.vec_meta.data_type = FLOAT 
            field_meta.vec_meta.dimension = dimension
            field_meta.vec_meta.store_type = store_type
            field_meta.vec_meta.store_param = store_param
            field_meta.vec_meta.has_source = has_source
            return True
        return False

    def __check_add_field(
        self,
        db_table_name,
        awadb_field,
        fields_type,
        field_name,
        field_value,
    ):
        ret = self.__field_check(db_table_name, field_name, field_value, fields_type)

        if ret < 0:
            return ret

        add_new_field = False
        if ret == 1:
            add_new_field = True

        is_index = True

        awadb_field.name = field_name
        field_type = fields_type[field_name]
        if field_type == FieldDataType.INT:
            awadb_field.value = field_value.to_bytes(4, "little")
            awadb_field.type = INT
            self.__add_field(db_table_name, field_name, awadb_field.type, is_index, add_new_field)
        elif field_type == FieldDataType.LONG:
            awadb_field.value = field_value.to_bytes(8, "little")
            awadb_field.type = LONG 
            self.__add_field(db_table_name, field_name, awadb_field.type, is_index, add_new_field)
        elif field_type == FieldDataType.FLOAT:
            awadb_field.value = struct.pack("<f", field_value)
            awadb_field.type = FLOAT
            self.__add_field(db_table_name, field_name, awadb_field.type, is_index, add_new_field)
        elif field_type == FieldDataType.STRING:
            awadb_field.value = str.encode(field_value)
            awadb_field.type = STRING
            is_index = False
            #if field_name == "embedding_text":
            #    is_index = False
            self.__add_field(db_table_name, field_name, awadb_field.type, is_index, add_new_field)
        elif field_type == FieldDataType.MULTI_STRING:
            if isinstance(field_value, str):
                awadb_field.mul_str_value.append(field_value)
            else:
                for each_str in field_value:
                    awadb_field.mul_str_value.append(each_str)

            awadb_field.type = MULTI_STRING
            self.__add_field(db_table_name, field_name, awadb_field.type, is_index, add_new_field)

        elif field_type == FieldDataType.VECTOR:
            dimension = field_value.__len__()
            if type(field_value).__name__ == "ndarray":
                awadb_field.value = field_value.tobytes()
            else:
                vec_value = np.array(field_value, dtype=np.dtype("float32"))
                awadb_field.value = vec_value.tobytes()

            awadb_field.type = VECTOR
            self.__add_vector_field(
                db_table_name,
                field_name,
                awadb_field.type,
                True,
                len(field_value),
                "Mmap",
                '{"cache_size" : 2000}',
                False,
            )
            self.tables_vector_fields_type[db_table_name][field_name] = dimension 

        return 0

    def __assemble_doc(
        self,
        db_table_name: str,
        doc: Document,
        dict_doc,
    ):
        fields_type = {}
        has_primary_key = False
        for field_name in dict_doc:
            field = doc.fields.add()
            status = self.__check_add_field(db_table_name, field, fields_type, field_name, dict_doc[field_name])
            if status < 0:
                return False 
            
            if field_name == DOC_PRIMARY_KEY_NAME:
                has_primary_key = True
                data_type = typeof(dict_doc[field_name])
                if data_type == FieldDataType.INT:
                    doc.id = dict_doc[field_name].to_bytes(8, "little")
                elif data_type == FieldDataType.STRING:
                    doc.id = str.encode(dict_doc[field_name])
        
        if not has_primary_key:
            key_field = doc.fields.add()
            default_gen_id = str(uuid.uuid4())
            doc.id = str.encode(default_gen_id)

            self.__check_add_field(db_table_name, key_field, fields_type,
                DOC_PRIMARY_KEY_NAME, default_gen_id)

        if not self.tables_fields_check[db_table_name]:
            status = self.stub.Create(self.tables_attr[db_table_name])
            if status.code != OK:
                print("Create table %s failed!" % db_table_name)
                return False
            for extra_field in self.tables_extra_new_fields[db_table_name]:
                status = self.stub.AddFields(extra_field)
                if status.code != OK:
                    print("Add new extra field failed!")
                    return False
            self.tables_fields_check[db_table_name] = True

