# -*- coding:utf-8 -*-
#!/usr/bin/python3

import os
import json
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set
import uuid
import numpy as np
import struct

import grpc
from awadb.py_idl.awadb_pb2 import * 
from awadb.py_idl.awadb_pb2_grpc import AwaDBServerStub 



DEFAULT_SERVER_ADDR = "0.0.0.0:50005"

DEFAULT_DB_NAME = "default"

DOC_PRIMARY_KEY_NAME = "_id"

DEFAULT_TOPN = 10

class MetricType(Enum):
    L2 = 1
    INNER_PRODUCT = 2

class FieldDataType(Enum):
    INT = 1
    LONG = 2
    FLOAT = 3 
    STRING = 4 
    VECTOR = 5 
    ERROR =6 
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


class Awa:
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

        self.root_dir = "."
        data_dir = self.root_dir + "/data"
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)


        self.tables_fields_check = {}
        self.tables_fields_type = {}
        self.tables_vector_field_name = {}
        self.tables_attr = {}
        self.tables_extra_new_fields = {}

        existed_meta_file = data_dir + "/tables.meta"
        if os.path.isfile(existed_meta_file):
            self.__read()


    def close(self):
        if self.channel is not None:
            slef.channel.close()


    def add(
        self,
        table_name: str,
        docs,
        db_name: str = DEFAULT_DB_NAME,
    ) -> bool:
        """Add documents into the specified table.
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
        if not db_table_name in self.tables_fields_check:
            self.tables_fields_check[db_table_name] = False
            self.tables_fields_type[db_table_name] = {}
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
        vec_query,
        db_name: str = DEFAULT_DB_NAME,
        topn: int = DEFAULT_TOPN,
        meta_filter: Optional[dict] = None,
        include_fields: Optional[Set[str]] = None,
        brute_force_search: bool = False,
        metric_type: MetricType = MetricType.L2,
        **kwargs: Any,
    ):
        """Vector search in the specified table.
        Args:
            table_name: The specified table for search.
            vec_query: Querying vector.
            db_name: Database name, default to DEFAULT_DB_NAME.
            topn: The topn nearest neighborhood documents to return.
            meta_filter (Optional[dict]): Filter by metadata. Defaults to None.
            E.g. `{"color" : "red", "price": 4.20}`. Optional.
            E.g. `{"max_price" : 15.66, "min_price": 4.20}`
            `price` is the metadata field, means range filter(4.20<'price'<15.66).
            E.g. `{"maxe_price" : 15.66, "mine_price": 4.20}`
            `price` is the metadata field, means range filter(4.20<='price'<=15.66).
            include_fields: The fields whether included in the search results.
            brute_force_search: Brute force search or not. Default to not.
                                If vectors not indexed, automatically to use brute force search.
            metric_type: The distance type of computing vectors. Default to L2.
            kwargs: Any possible extended parameters.

        Returns:
            Results of searching.
        """
        if self.__network_error():
            return ""
        if len(table_name) == 0:
            print("Please specify the table name!")
            return ""

        query_type = typeof(vec_query)

        show_results = []
        if (
            query_type == FieldDataType.ERROR
            or query_type == FieldDataType.INT
            or query_type == FieldDataType.FLOAT
        ):
            return "" 

        db_table_name = db_name + "/" + table_name
        request = SearchRequest()
        request.db_name = db_name
        request.table_name = table_name
        vec_request = request.vec_queries.add()
        vec_request.field_name = self.tables_vector_field_name[db_table_name]
        vec_request.min_score = -1 
        vec_request.max_score = 999999 
        request.topn = topn
        if metric_type == MetricType.L2:
            request.retrieval_params = "{\"metric_type\":\"L2\"}"
        else:
            request.retrieval_params = "{\"metric_type\":\"InnerProduct\"}"
        request.brute_force_search = brute_force_search
        if meta_filter is not None:
            __add_filter(db_table_name, request, meta_filter)


        if include_fields is None:
            request.is_pack_all_fields = True
        else:
            for pack_field in include_fields:
                request.pack_fields.append(pack_field)

        if query_type == FieldDataType.STRING:  # semantic text search
            embedding = self.llm.Embedding(query)
            vec_query.value = embedding.tobytes()
        elif query_type == FieldDataType.VECTOR:  # vector search
            vec_value = None
            #notice: the added vectors should also be normalized
            if metric_type == MetricType.INNER_PRODUCT:
                vec_value = self.__normalize(vec_query)
            elif metric_type == MetricType.L2:
                vec_value = np.array(vec_query, dtype=np.dtype("float32"))
            vec_request.value = vec_value.tobytes()

            response = self.stub.Search(request)
            return response

        return "" 

    def get(
        self,
        table_name: str,
        db_name: str = DEFAULT_DB_NAME,
        ids: Optional[List[str]] = None,
        **kwargs: Any,
    ):
        """Get documents of the primary keys in the the specified table.
        Args:
            table_name: The specified table for search and storage.
            db_name: Database name, default to DEFAULT_DB_NAME.
            ids: The primary keys of the queried documents.

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
      
        doc_condition.ids.extend(ids)

        response = self.stub.Get(doc_condition)
        return response

    def delete(
        self,
        table_name: str,
        db_name: str = DEFAULT_DB_NAME,
        ids: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> bool:
        """Delete docs in the specified table.
        Args:
            table_name: The specified table for deleting.
            db_name: Database name, default to DEFAULT_DB_NAME.
            ids: The primary keys of the deleted documents.

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
      
        doc_condition.ids.extend(ids)

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
                return -3
            fields_type[field_name] = f_type
        else:
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
            if field_name == "_id":
                awadb_field.value = field_value.to_bytes(8, "little")
                awadb_field.type = LONG 
            else:
                awadb_field.value = field_value.to_bytes(4, "little")
                awadb_field.type = INT
            self.__add_field(db_table_name, field_name, awadb_field.type, is_index, add_new_field)
        elif field_type == FieldDataType.FLOAT:
            awadb_field.value = struct.pack("<f", field_value)
            awadb_field.type = FLOAT
            self.__add_field(db_table_name, field_name, awadb_field.type, is_index, add_new_field)
        elif field_type == FieldDataType.STRING:
            awadb_field.value = str.encode(field_value)
            awadb_field.type = STRING
            if field_name == "embedding_text":
                is_index = False
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
            self.tables_vector_field_name[db_table_name] = field_name

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
            self.__write()

    def __read(self):
        created_table_path = self.root_dir + "/data/tables.meta"
        with open(created_table_path, "r", encoding="unicode_escape") as f:
            tables_meta = json.load(fp=f)

            self.tables_fields_check = tables_meta["fields_check"]

            for table_name in tables_meta["fields_type"]:
                table_field_dict = {}
                for each_field_type in tables_meta["fields_type"][table_name]:
                    for f_id in each_field_type:
                        if each_field_type[f_id] == "INT":
                            table_field_dict[f_id] = FieldDataType.INT
                        elif each_field_type[f_id] == "LONG":
                            table_field_dict[f_id] = FieldDataType.LONG
                        elif each_field_type[f_id] == "FLOAT":
                            table_field_dict[f_id] = FieldDataType.FLOAT
                        elif each_field_type[f_id] == "STRING":
                            table_field_dict[f_id] = FieldDataType.STRING
                        elif each_field_type[f_id] == "MULTI_STRING":
                            table_field_dict[f_id] = FieldDataType.MULTI_STRING
                        elif each_field_type[f_id] == "VECTOR":
                            table_field_dict[f_id] = FieldDataType.VECTOR
                self.tables_fields_type[table_name] = table_field_dict

            self.tables_vector_field_name = tables_meta["vector_field_name"]

            for table_name in tables_meta["tables_info"]:
                table_info = DBMeta()
                db_name = table_name.split("/")[0]
                table_info.db_name = db_name
                table_meta = table_info.tables_meta.add()
                table_meta.name = table_name.split("/")[1]

                vec_fields_map = {}
                for each_field_info in tables_meta["tables_info"][table_name][
                    "fields_info"
                ]:
                    field_info = table_meta.fields_meta.add()
                    field_info.name = each_field_info["name"]
                    if each_field_info["data_type"] == "INT":
                        field_info.type = INT
                    elif each_field_info["data_type"] == "LONG":
                        field_info.type = LONG
                    elif each_field_info["data_type"] == "FLOAT":
                        field_info.type = FLOAT
                    elif each_field_info["data_type"] == "STRING":
                        field_info.type = STRING
                    elif each_field_info["data_type"] == "MULTI_STRING":
                        field_info.type = MULTI_STRING
                    elif each_field_info["data_type"] == "VECTOR":
                        field_info.type = VECTOR
                        vec_fields_map[field_info.name] = field_info    


                    field_info.is_index = each_field_info["is_index"]

                for each_vec_info in tables_meta["tables_info"][table_name][
                    "vec_fields"
                ]:
                    vec_field = table_meta.fields_meta.add()
                    vec_field.name = each_vec_info["name"]
                    if each_vec_info["data_type"] == "INT":
                        vec_field.vec_meta.data_type = INT 
                    elif each_vec_info["data_type"] == "FLOAT":
                        vec_field.vec_meta.data_type = FLOAT
                    elif each_vec_info["data_type"] == "STRING":
                        vec_field.vec_meta.data_type = STRING
                    elif each_vec_info["data_type"] == "MULTI_STRING":
                        vec_field.vec_meta.data_type = MULTI_STRING
                    vec_field.is_index = each_vec_info["is_index"]
                    vec_field.vec_meta.dimension = each_vec_info["dimension"]
                    vec_field.vec_meta.store_type = each_vec_info["store_type"]
                    vec_field.vec_meta.store_param = each_vec_info["store_param"]
                    vec_field.vec_meta.has_source = each_vec_info["has_source"]

                self.tables_attr[table_name] = table_info

    def __write(self):
        tables_meta = {}
        tables_meta["fields_check"] = self.tables_fields_check
        tables_types = {}
        for table_name in self.tables_fields_type:
            fields_type_list = []
            for f_id in self.tables_fields_type[table_name]:
                field_dict = {}
                if self.tables_fields_type[table_name][f_id] == FieldDataType.INT:
                    field_dict[f_id] = "INT"
                elif self.tables_fields_type[table_name][f_id] == FieldDataType.FLOAT:
                    field_dict[f_id] = "FLOAT"
                elif self.tables_fields_type[table_name][f_id] == FieldDataType.STRING:
                    field_dict[f_id] = "STRING"
                elif (
                    self.tables_fields_type[table_name][f_id]
                    == FieldDataType.MULTI_STRING
                ):
                    field_dict[f_id] = "MULTI_STRING"
                elif self.tables_fields_type[table_name][f_id] == FieldDataType.VECTOR:
                    field_dict[f_id] = "VECTOR"
                fields_type_list.append(field_dict)

            tables_types[table_name] = fields_type_list

        tables_meta["fields_type"] = tables_types
        tables_meta["vector_field_name"] = self.tables_vector_field_name

        tables_dict = {}
        for key in self.tables_attr:
            table_attr_info = {}
            table_meta = self.tables_attr[key].tables_meta[0]
            fields_list = []
            for field_meta in table_meta.fields_meta:
                fields_dict = {}
                if field_meta.type == INT:
                    fields_dict["data_type"] = "INT"
                elif field_meta.type == LONG:
                    fields_dict["data_type"] = "LONG"
                elif field_meta.type == FLOAT:
                    fields_dict["data_type"] = "FLOAT"
                elif field_meta.type == STRING:
                    fields_dict["data_type"] = "STRING"
                elif field_meta.type == MULTI_STRING:
                    fields_dict["data_type"] = "MULTI_STRING"
                elif field_meta.type == VECTOR:
                    fields_dict["data_type"] = "VECTOR"
                    continue

                fields_dict["name"] = field_meta.name
                
                fields_dict["is_index"] = field_meta.is_index
                fields_list.append(fields_dict)
            table_attr_info["fields_info"] = fields_list

            vec_fields_list = []
            table_meta = self.tables_attr[key].tables_meta[0]
            for field_meta in table_meta.fields_meta:
                if field_meta.type != VECTOR:
                    continue
                vec_fields_dict = {}
                vec_fields_dict["name"] = field_meta.name
                if field_meta.vec_meta.data_type == INT:
                    vec_fields_dict["data_type"] = "INT"
                elif field_meta.vec_meta.data_type == LONG:
                    vec_fields_dict["data_type"] = "LONG"
                elif field_meta.vec_meta.data_type == FLOAT:
                    vec_fields_dict["data_type"] = "FLOAT"
                elif field_meta.vec_meta.data_type == STRING:
                    vec_fields_dict["data_type"] = "STRING"
                elif field_meta.vec_meta.data_type == VECTOR:
                    vec_fields_dict["data_type"] = "VECTOR"

                vec_fields_dict["is_index"] = field_meta.is_index
                vec_fields_dict["dimension"] = field_meta.vec_meta.dimension
                vec_fields_dict["store_type"] = field_meta.vec_meta.store_type
                vec_fields_dict["store_param"] = field_meta.vec_meta.store_param
                vec_fields_dict["has_source"] = field_meta.vec_meta.has_source
                vec_fields_list.append(vec_fields_dict)
            table_attr_info["vec_fields"] = vec_fields_list
            tables_dict[key] = table_attr_info

        tables_meta["tables_info"] = tables_dict

        created_table_path = self.root_dir + "/data/tables.meta"
        with open(created_table_path, "w", encoding="unicode_escape") as f:
            json.dump(tables_meta, f)

