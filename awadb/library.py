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

import awa
from awadb.punctuation_marks_en import punctuation_marks
from awadb.stop_words_en import stop_words
from awadb.words_stem_en import PorterStemmer

import numpy as np
from awadb.awadb_api import AwaAPI
from awadb.awadb_api import DEFAULT_DB_NAME
from awadb.awadb_api import DEFAULT_TOPN
from awadb.awadb_api import DOC_PRIMARY_KEY_NAME
from awadb.awadb_api import MetricType

__version__ = "0.3.13"

__all__ = [
    "OpenAI",
    "HuggingFace",
]

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

class AwaLocal(AwaAPI):
    """Interface implemented by AwaDB local library client"""
    def __init__(
        self,
        root_dir = ".",
        model_name = "HuggingFace",
    ):
        """Initialize the AwaDB library client.
        
        Args:
            root_dir: Logging and data directory. Default to current directory ".". 
            model_name: Embedding model name.

        Returns:
            None.
        """

        self.root_dir = root_dir
        log_dir = root_dir + "/log"
        data_dir = root_dir + "/data"
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)

        self.log_dir = log_dir
        self.data_dir = data_dir
        self.key_confirmed_name = DOC_PRIMARY_KEY_NAME 
        self.key_nick_name = ""

        self.tables_fields_check = {}
        self.tables_fields_type = {}
        self.tables_vector_fields_type = {}
        self.tables_doc_count = {}
        self.tables_attr = {}
        self.tables = {}
        self.db_tables = {}
        self.english_word_stemmer = PorterStemmer()
        self.tables_extra_new_fields = {} 
        self.row_fields = {}

        existed_meta_file = data_dir + "/tables.meta"
        if os.path.isfile(existed_meta_file):
            self.__read()

        self.is_duplicate_texts = True
       
        if model_name not in __all__:
            print("Could not find this model: ", model_name)
            print("Still use default model 'HuggingFace' instead.\n")
            model_name = "HuggingFace"

        self.model_name = model_name 
        self.llm = None 
        #AwaEmbedding(self.model_name)
       
    def __write(self):
        """Persist the schema information of created tables.
        
        Returns:
            None.
        """

        tables_meta = {}
        tables_meta["fields_check"] = self.tables_fields_check
        tables_types = {}
        for table_name in self.tables_fields_type:
            fields_type_list = []
            for f_id in self.tables_fields_type[table_name]:
                field_dict = {}
                if self.tables_fields_type[table_name][f_id] == FieldDataType.INT:
                    field_dict[f_id] = "INT"
                if self.tables_fields_type[table_name][f_id] == FieldDataType.LONG:
                    field_dict[f_id] = "LONG"
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
        tables_meta["vector_field_name"] = self.tables_vector_fields_type

        tables_meta["doc_count"] = self.tables_doc_count

        tables_dict = {}
        for key in self.tables_attr:
            table_attr_info = {}
            fields_info = self.tables_attr[key].Fields()
            fields_list = []
            for field_info in fields_info:
                fields_dict = {}
                fields_dict["name"] = field_info.name
                if field_info.data_type == awa.DataType.INT:
                    fields_dict["data_type"] = "INT"
                elif field_info.data_type == awa.DataType.LONG:
                    fields_dict["data_type"] = "LONG"
                elif field_info.data_type == awa.DataType.FLOAT:
                    fields_dict["data_type"] = "FLOAT"
                elif field_info.data_type == awa.DataType.STRING:
                    fields_dict["data_type"] = "STRING"
                elif field_info.data_type == awa.DataType.MULTI_STRING:
                    fields_dict["data_type"] = "MULTI_STRING"
                elif field_info.data_type == awa.DataType.VECTOR:
                    fields_dict["data_type"] = "VECTOR"

                fields_dict["is_index"] = field_info.is_index
                fields_list.append(fields_dict)
            table_attr_info["fields_info"] = fields_list

            vec_fields_list = []
            vec_fields_info = self.tables_attr[key].VectorInfos()
            for vec_field_info in vec_fields_info:
                vec_fields_dict = {}
                vec_fields_dict["name"] = vec_field_info.name
                if vec_field_info.data_type == awa.DataType.INT:
                    vec_fields_dict["data_type"] = "INT"
                elif vec_field_info.data_type == awa.DataType.FLOAT:
                    vec_fields_dict["data_type"] = "FLOAT"
                elif vec_field_info.data_type == awa.DataType.STRING:
                    vec_fields_dict["data_type"] = "STRING"
                elif vec_field_info.data_type == awa.DataType.MULTI_STRING:
                    vec_fields_dict["data_type"] = "MULTI_STRING"
                elif vec_field_info.data_type == awa.DataType.VECTOR:
                    vec_fields_dict["data_type"] = "VECTOR"

                vec_fields_dict["is_index"] = vec_field_info.is_index
                vec_fields_dict["dimension"] = vec_field_info.dimension
                vec_fields_dict["model_id"] = vec_field_info.model_id
                vec_fields_dict["store_type"] = vec_field_info.store_type
                vec_fields_dict["store_param"] = vec_field_info.store_param
                vec_fields_list.append(vec_fields_dict)
            table_attr_info["vec_fields"] = vec_fields_list
            tables_dict[key] = table_attr_info

        tables_meta["tables_info"] = tables_dict

        created_table_path = self.root_dir + "/data/tables.meta"
        with open(created_table_path, "w", encoding="unicode_escape") as f:
            json.dump(tables_meta, f)

    def __read(self):
        """Read the schema information of created tables.
        
        Returns:
            None.
        """
        created_table_path = self.root_dir + "/data/tables.meta"
        with open(created_table_path, "r", encoding="unicode_escape") as f:
            tables_meta = json.load(fp=f)

            self.tables_fields_check = tables_meta["fields_check"]
            self.tables_doc_count = tables_meta["doc_count"]

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
                self.__load(table_name) 
                self.tables_fields_type[table_name] = table_field_dict

            self.tables_vector_fields_type = tables_meta["vector_field_name"]

            for table_name in tables_meta["tables_info"]:
                table_info = awa.TableInfo()
                for each_field_info in tables_meta["tables_info"][table_name][
                    "fields_info"
                ]:
                    field_info = awa.FieldInfo()
                    field_info.name = each_field_info["name"]
                    if each_field_info["data_type"] == "INT":
                        field_info.data_type = awa.DataType.INT
                    elif each_field_info["data_type"] == "FLOAT":
                        field_info.data_type = awa.DataType.FLOAT
                    elif each_field_info["data_type"] == "STRING":
                        field_info.data_type = awa.DataType.STRING
                    elif each_field_info["data_type"] == "MULTI_STRING":
                        field_info.data_type = awa.DataType.MULTI_STRING
                    elif each_field_info["data_type"] == "VECTOR":
                        field_info.data_type = awa.DataType.VECTOR
                    field_info.is_index = each_field_info["is_index"]
                    table_info.AddField(field_info)

                for each_vec_info in tables_meta["tables_info"][table_name][
                    "vec_fields"
                ]:
                    vec_info = awa.VectorInfo()
                    vec_info.name = each_vec_info["name"]
                    if each_vec_info["data_type"] == "INT":
                        vec_info.data_type = awa.DataType.INT
                    elif each_vec_info["data_type"] == "FLOAT":
                        vec_info.data_type = awa.DataType.FLOAT
                    elif each_vec_info["data_type"] == "STRING":
                        vec_info.data_type = awa.DataType.STRING
                    elif each_vec_info["data_type"] == "MULTI_STRING":
                        vec_info.data_type = awa.DataType.MULTI_STRING
                    elif each_vec_info["data_type"] == "VECTOR":
                        vec_info.data_type = awa.DataType.VECTOR
                    vec_info.is_index = each_vec_info["is_index"]
                    vec_info.dimension = each_vec_info["dimension"]
                    vec_info.model_id = each_vec_info["model_id"]
                    vec_info.store_type = each_vec_info["store_type"]
                    vec_info.store_param = each_vec_info["store_param"]
                    table_info.AddVectorInfo(vec_info)

                table_info.SetIndexingSize(10000)
                table_info.SetRetrievalType("IVFPQ")
                table_info.SetRetrievalParam('{"ncentroids" : 256, "nsubvector" : 16}')
                self.tables_attr[table_name] = table_info

        
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
            If db_name is None and table_name is None, return all the databases.
            if db_name is None and table_name is not None, return empty list.
            If table_name is None, db_name is not None, return all tables in db_name.
            If neither db_name nor table_name is None, return the schema of the table. 
        """
        # return all databases
        if db_name is None and table_name is None:
            all_dbs = []
            for db in self.db_tables:
                all_dbs.append(db)
            return all_dbs

        elif db_name is None and table_name is not None:
            return []
        elif db_name is not None and table_name is None:
            if db_name not in self.db_tables:
                return []
            return self.db_tables[db_name]
        else:
            db_table_name = db_name + "/" + table_name
            if db_table_name not in self.tables_fields_type:
                return []
            return self.tables_fields_type[db_table_name]

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

        if db_name == "" or table_name == "":
            print("Please specify your database and table name!")
            return False
        
        db_table_name = db_name + "/" + table_name

        if not isinstance(docs, list) and (not isinstance(docs, dict)):
            print("Incorrect argument, list or dict type is needed for Add!!!")
            return False

        if not db_table_name in self.tables_fields_check:
            self.tables_fields_check[db_table_name] = False

            self.tables_attr[db_table_name] = awa.TableInfo()
            self.tables_attr[db_table_name].SetName(db_table_name)
            self.tables_fields_type[db_table_name] = {}
            self.tables_vector_fields_type[db_table_name] = {}
            self.tables_extra_new_fields[db_table_name] = []
            self.tables_doc_count[db_table_name] = 0
        self.__process_docs_embedding(docs)

        fields_type = {}
        awadb_docs = awa.DocsVec()
        has_primary_key = False
        if isinstance(docs, dict):
            doc = awa.Doc()
            for field_name in docs:
                awadb_field = awa.Field()
                ret = self.__check_add_field(db_table_name, awadb_field, fields_type, field_name, docs[field_name])
                if ret < 0:
                    continue
                doc.AddField(awadb_field)
                if field_name == self.key_confirmed_name:
                    has_primary_key = True
                    doc.SetKey(awadb_field.value)

            if not has_primary_key:
                key_fid = awa.Field()
                ret = self.__check_add_field(
                    db_table_name,
                    key_fid,
                    fields_type,
                    self.key_confirmed_name,
                    str(uuid.uuid4()).split("-")[-1])
                if ret == 0:
                    doc.AddField(key_fid)
                    doc.SetKey(key_fid.value)
            awadb_docs.append(doc)
        else: # list of doc
            for doc_item in docs:
                if type(doc_item).__name__ == "dict":
                    doc = awa.Doc()
                    for field_name in doc_item:
                        awadb_field = awa.Field()
                        ret = self.__check_add_field(db_table_name, awadb_field, fields_type, field_name, doc_item[field_name])
                        if ret < 0:
                            continue
                        doc.AddField(awadb_field)
                        if field_name == self.key_confirmed_name:
                            has_primary_key = True
                            doc.SetKey(awadb_field.value)

                    if not has_primary_key:
                        key_fid = awa.Field()
                        ret = self.__check_add_field(
                            db_table_name,
                            key_fid,
                            fields_type,
                            self.key_confirmed_name,
                            str(uuid.uuid4()).split("-")[-1])
                        if ret == 0:
                            doc.AddField(key_fid)
                            doc.SetKey(key_fid.value)
                    awadb_docs.append(doc)

        if not self.tables_fields_check[db_table_name]:
            self.tables_attr[db_table_name].SetIndexingSize(10000)
            self.tables_attr[db_table_name].SetRetrievalType("IVFPQ")
            self.tables_attr[db_table_name].SetRetrievalParam(
                '{"ncentroids" : 256, "nsubvector" : 16}'
            )

            table_engine = None
            if db_table_name in self.tables:
                table_engine = self.tables[db_table_name]
            else:
                table_engine = self.__create(db_table_name)
                if table_engine is not None:
                    self.tables_doc_count[db_table_name] = 0

            if table_engine is None:
                print('table engine is none')
                return False

            if not awa.Create(table_engine, self.tables_attr[db_table_name]):
                print('create error')
                return False
       
            if db_name not in self.db_tables:
                self.db_tables[db_name] = []
                self.db_tables[db_name].append(table_name)
            else:
                self.db_tables[db_name].append(table_name)

            for extra_field in self.tables_extra_new_fields[db_table_name]:
                if not awa.AddNewField(table_engine, extra_field):
                    print("Add new field %s failed!" % extra_field.name)

        if not awa.AddDocs(self.tables[db_table_name], awadb_docs):
            print('add docs error')
            return False

        self.tables_doc_count[db_table_name] += awadb_docs.__len__() 

        if not self.tables_fields_check[db_table_name]:
            self.tables_fields_check[db_table_name] = True
            self.__write()
        if isinstance(docs, list):
            docs[:] = []
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

            vec_query: Querying vector.

            db_name: Database name, default to DEFAULT_DB_NAME.

            topn: The topn nearest neighborhood documents to return.

            filters (Optional[dict]): Filter by fields. Defaults to None.

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

            Notice that field f1 and f2 should have the same dimension compared to vec_query.

            kwargs: Any possible extended parameters.

        Returns:
            Results of searching.
        """
        show_results = {} 
        db_table_name = db_name + "/" + table_name
        if db_table_name not in self.tables:
            return show_results 

        query_type = typeof(query)

        if (
            query_type == FieldDataType.ERROR
            or query_type == FieldDataType.INT
            or query_type == FieldDataType.FLOAT
        ):
            return show_results

        req = awa.Request()
        vec_value = None
        query_dimension = 0
        if query_type == FieldDataType.STRING:  # semantic text search
            embedding = self.llm.Embedding(query)
            if metric_type == MetricType.INNER_PRODUCT:
                vec_value = self.__normalize(embedding)
                req.SetRetrievalParams('{"metric_type":"InnerProduct"}')
                req.SetMetricType(False) 
            elif metric_type == MetricType.L2:
                vec_value = embedding
                req.SetRetrievalParams('{"metric_type":"L2"}')
                req.SetMetricType(True)
        elif query_type == FieldDataType.VECTOR:  # vector search
            if metric_type == MetricType.INNER_PRODUCT:
                vec_value = self.__normalize(query)
                req.SetRetrievalParams('{"metric_type":"InnerProduct"}')
                req.SetMetricType(False)
            elif metric_type == MetricType.L2:
                vec_value = np.array(query, dtype=np.dtype("float32"))
                req.SetRetrievalParams('{"metric_type":"L2"}')
                req.SetMetricType(True)
        if vec_value is not None:
            query_dimension = vec_value.__len__()
        
        vectors_num = 0 
        for vec_field_name in self.tables_vector_fields_type[db_table_name]:
            if query_dimension == self.tables_vector_fields_type[db_table_name][vec_field_name]:
                vec_request = awa.VectorQuery() 
                vec_request.name = vec_field_name 
                vec_request.min_score = -1 
                vec_request.max_score = 999999
                vec_request.value = vec_value.tobytes()
                vec_request.has_boost = True
                vec_request.boost = 1.0
                if mul_vec_weight is not None and vec_field_name in mul_vec_weight:
                    vec_request.boost = mul_vec_weight[vec_field_name]
                    req.SetMultiVectorRank(1)

                req.AddVectorQuery(vec_request) 
                vectors_num = vectors_num + 1
        if vectors_num == 0:
            print("Query vector dimension is not valid!")
            return ""
        elif vectors_num > 1:
            # todo: request.mul_vec_logic_op = OR
            print("vector query > 1")

        req.SetReqNum(1)
        req.SetTopN(topn)
        req.SetBruteForceSearch(1)
        self.__add_filter(db_table_name, req, filters)

        response = awa.Response()
        fvec_names = awa.StrVec()
        for field_name in self.tables_fields_type[db_table_name]:
            if include_fields is not None and field_name in include_fields:
                fvec_names.append(field_name)
        
        ret = awa.DoSearch(self.tables[db_table_name], req, response)
        response.PackResults(fvec_names)

        show_results["Db"] = db_name
        show_results["Table"] = table_name

        search_result_vec = response.Results()
        search_result_index = 0
        search_results = []
        while search_result_index < search_result_vec.__len__():
            search_result = search_result_vec[search_result_index]
            result_per_request = {}
            result_per_request["ResultSize"] = search_result.total

            result_items_list = []
            items = search_result.result_items
            item_index = 0
            # for item in items:
            while item_index < items.__len__():
                item = items[item_index]
                i = 0
                l = item.names.__len__()
                item_detail = {}
                while i < l:
                    name = item.names[i]
                    if include_fields is not None and name not in include_fields:
                        i = i + 1
                        continue

                    f_type = self.tables_fields_type[db_table_name][name]
                    if f_type == FieldDataType.INT:
                        int_value = int(item.values[i])
                        item_detail[name] = int_value
                    if f_type == FieldDataType.LONG:
                        long_value = int(item.values[i])
                        item_detail[name] = long_value
                    elif f_type == FieldDataType.FLOAT:
                        float_value = float(item.values[i])
                        item_detail[name] = float_value
                    elif f_type == FieldDataType.STRING:
                        item_detail[name] = item.values[i]
                    elif f_type == FieldDataType.MULTI_STRING:
                        mul_str_vec = awa.StrVec()
                        item.GetMulStr(item.values[i], mul_str_vec)
                        str_size = mul_str_vec.__len__()
                        if str_size == 0:
                           i = i + 1
                           continue
                        elif str_size == 1:
                            item_detail[name] = mul_str_vec[0]
                        else:
                            final_mul_str = []
                            str_no = 0
                            while str_no < str_size:
                                final_mul_str.append(mul_str_vec[str_no])
                                str_no = str_no + 1
                            item_detail[name] = final_mul_str
                    elif f_type == FieldDataType.VECTOR:
                        vec_data = awa.FloatVec()
                        item.GetVecData(name, vec_data)
                        vec_result = []
                        j = 0
                        while j < vec_data.__len__():
                            each_vec_data = vec_data[j]
                            vec_result.append(each_vec_data)
                            j = j + 1
                        item_detail[name] = vec_result
                    i = i + 1
                if include_fields is None:
                    item_detail["score"] = item.score
                result_items_list.append(item_detail)
                item_index = item_index + 1

            result_per_request["ResultItems"] = result_items_list
            search_results.append(result_per_request)
            search_result_index = search_result_index + 1
        
        if response.Results().__len__() == 1:
            show_results["SearchResults"] = search_results[0]
        else:
            show_results["SearchResults"] = search_results
        return show_results

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
     
        docs_detail = []
        if table_name == "":
            print("Please specify the table name!")
            return docs_detail
        if ids is None and filters is None:
            print(
                "ids or filters should be specified at least one!"
            )
            return docs_detail

        db_table_name = db_name + "/" + table_name
        
        if ids is None and filters is not None:
            req = awa.Request()
            req.SetReqNum(1)
            if limit is not None:
                req.SetTopN(limit)
            req.SetBruteForceSearch(1)
            default_retrieval_type = '{"metric_type":"L2"}'
            req.SetRetrievalParams(default_retrieval_type)

            self.__add_filter(db_table_name, req, filters)

            response = awa.Response()
            fvec_names = awa.StrVec()
            for field_name in self.tables_fields_type[db_table_name]:
                if include_fields is not None and field_name in include_fields:
                    fvec_names.append(field_name)

            ret = awa.DoSearch(db_table_name, req, response)
            response.PackResults(fvec_names)

            search_result_vec = response.Results()
            search_result_index = 0
            # the usage of iterator pybind11 struct may cause crash in MacOSX x86 environment
            while search_result_index < search_result_vec.__len__():
                search_result = search_result_vec[search_result_index]
                # for search_result in search_result_vec:
                items = search_result.result_items
                item_index = 0
                # for item in items:
                while item_index < items.__len__():
                    i = 0
                    item = items[item_index]
                    l = item.names.__len__()
                    item_detail = {}
                    while i < l:
                        name = item.names[i]
                        if (
                            include_fields is not None
                            and name not in include_fields
                        ):
                            i = i + 1
                            continue
                        f_type = self.tables_fields_type[db_table_name][name]
                        if f_type == FieldDataType.INT:
                            int_value = int(item.values[i])
                            item_detail[name] = int_value
                        elif f_type == FieldDataType.FLOAT:
                            float_value = float(item.values[i])
                            item_detail[name] = float_value
                        elif f_type == FieldDataType.STRING:
                            item_detail[name] = item.values[i]
                        elif f_type == FieldDataType.MULTI_STRING:
                            mul_str_vec = awa.StrVec()
                            item.GetMulStr(item.values[i], mul_str_vec)
                            str_size = mul_str_vec.__len__()
                            if str_size == 0:
                                i = i + 1
                                continue
                            elif str_size == 1:
                                item_detail[name] = mul_str_vec[0]
                            else:
                                final_mul_str = []
                                str_no = 0
                                while str_no < str_size:
                                    final_mul_str.append(mul_str_vec[str_no])
                                    str_no = str_no + 1
                                item_detail[name] = final_mul_str
                        elif f_type == FieldDataType.VECTOR:
                            vec_data = awa.FloatVec()
                            item.GetVecData(name, vec_data)
                            vec_result = []
                            vec_index = 0
                            while vec_index < vec_data.__len__():
                                each_vec_data = vec_data[vec_index]
                                # for each_vec_data in vec_data:
                                vec_result.append(each_vec_data)
                                vec_index = vec_index + 1
                            item_detail[name] = vec_result
                        i = i + 1
                    docs_detail.append(item_detail)
                    item_index = item_index + 1
                search_result_index = search_result_index + 1
            return docs_detail

        if not self.__check_ids_type(db_table_name, ids):
            print("Input ids should be list of str or long")
            return ""

        doc_results = awa.DocsMap()
        ids_list = awa.StrVec()
        for key_id in ids:
            doc_results[key_id] = awa.Doc()
            ids_list.append(key_id)

        awa.GetDocs(self.tables[db_table_name], ids_list, doc_results)

        for key_id in ids:
            if doc_results[key_id].Key() == "-1":
                continue

            doc_detail = {}
            field_index = 0
            while field_index < doc_results[key_id].TableFields().__len__():
                field = doc_results[key_id].TableFields()[field_index]
                # for field in doc_results[key_id].TableFields():
                if include_fields is not None and field.name not in include_fields:
                    field_index = field_index + 1
                    continue
                if field.datatype == awa.DataType.INT:
                    int_value = int(field.value)
                    doc_detail[field.name] = int_value
                elif field.datatype == awa.DataType.FLOAT:
                    float_value = float(field.value)
                    doc_detail[field.name] = float_value
                elif field.datatype == awa.DataType.STRING:
                    doc_detail[field.name] = field.value
                elif field.datatype == awa.DataType.MULTI_STRING:
                    mul_str_vec = []
                    for each_str in field.mul_str_value:
                        mul_str_vec.append(each_str)
                    doc_detail[field.name] = mul_str_vec

                field_index = field_index + 1

            field_index = 0
            while field_index < doc_results[key_id].VectorFields().__len__():
                field = doc_results[key_id].VectorFields()[field_index]
                # for field in doc_results[key_id].VectorFields():
                if include_fields is not None and field.name not in include_fields:
                    field_index = field_index + 1
                    continue
                if field.datatype == awa.DataType.VECTOR:
                    vec_data = awa.FloatVec()
                    ret = field.GetVecData(vec_data)
                    if vec_data.__len__() == 0:
                        print("Get vector data error!")
                        break

                    vec_result = []
                    vec_index = 0
                    while vec_index < vec_data.__len__():
                        each_vec_data = vec_data[vec_index]
                        # for each_vec_data in vec_data:
                        vec_result.append(each_vec_data)
                        vec_index = vec_index + 1
                    doc_detail[field.name] = vec_result
                field_index = field_index + 1

            docs_detail.append(doc_detail)
        return docs_detail

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
        if table_name == "" or db_name == "":
            print("Please specify the table name!")
            return False 
        if ids is None and filters is None:
            print(
                "ids or filters should be specified at least one!"
            )
            return False 

        db_table_name = db_name + "/" + table_name
        if ids is not None:
            if not self.__check_ids_type(db_table_name, ids):
                print("Input ids should be list of str or long")
                return False 

            ids_list = awa.StrVec()
            for each_id in ids:
                if isinstance(each_id, int):
                    ids_list.append(str(each_id))
                else:
                    ids_list.append(each_id)
            return awa.Delete(db_table_name, ids_list)

        if filters is not None:
            # todo : delete ids which satisfy the filter conditions
            return False

    def close(
        self,
        table_name: str,
        db_name: str = DEFAULT_DB_NAME,
    ) -> bool:
        """Close the specified table engine.
        
        Args:
            table_name: The table name of closing.
            db_name: The database name. 

        Returns:
            True or False, whether close table engine success.
        """
        if len(table_name) == 0 or len(db_name) == 0:
            print("Table and database should both be specified!")
            return False

        db_table_name = db_name + "/" + table_name
        if db_table_name not in self.tables:
            print("Database %s and table %s not exist!" % (db_name, table_name))
            return False

        if awa.Close(self.tables[db_table_name]) == 0:
            return True
        return False

    def load(
        self,
        table_name: str,
        db_name: str = DEFAULT_DB_NAME,
    ) -> bool:
        """Load the specified table.
        
        Args:
            table_name: The loading table name.
            db_name: The database name. 

        Returns:
            True or False, whether loading the specified table success.
        """

        if len(table_name) == 0 or len(db_name) == 0:
            return False

        db_table_name = db_name + "/" + table_name

        if not db_table_name in self.tables:
            self.__create(db_table_name)
        
        if self.tables[db_table_name] is None:
            print("Db table %s created failed!", db_table_name)
            return False

        if not awa.LoadFromLocal(self.tables[db_table_name]):
            print("Table %s can not be loaded!" % db_table_name)
            return False
        
        return True
    
    def __text_preprocess(
        self,
        text: str,
        **kwargs: Any,
    ) -> Dict[str, int]:
        """Preprocess text, now just for English.

        Args:
            text: the text to be preprocessed.
        Returns:
            Each word and its frequency in text.
        """

        words = text.split()  # now just support english
        words_count_dict: Dict[str, int] = {}
        for word in words:
            if len(word) > 30:
                continue
            if word in punctuation_marks:
                continue
            for each_mark in punctuation_marks:
                if each_mark in word:
                    word = word.replace(each_mark, "")

            word = word.lower()
            if word in stop_words:
                continue
            # stem the word
            word = self.english_word_stemmer.stem(word, 0, len(word) - 1)

            if word in words_count_dict:
                words_count_dict[word] = words_count_dict[word] + 1
            else:
                words_count_dict[word] = 1
        return words_count_dict

    def __process_doc_embedding(
        self,
        doc: dict,
    ):
        """Preprocess text embedding.

        Args:
            doc: the document to be processed for its texts.
        Returns:
            None.
        """
        for field_name in doc:
            if field_name == "embedding_text":
                from awadb import AwaEmbedding 
                self.llm = AwaEmbedding(self.model_name)
                doc["text_embedding"] = self.llm.Embedding(doc[field_name])

    def __process_docs_embedding(
        self, 
        docs,
    ) -> bool:
        """Preprocess text and embedding.

        Args:
            docs: the documents to be processed for its texts.
        Returns:
            None.
        """

        if isinstance(docs, dict):
            self.__process_doc_embedding(docs)
            return
        for doc in docs:
            if type(doc).__name__ == "dict":
                self.__process_doc_embedding(doc)
            else:
                print("field should be the format of dict")
        return

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

    def __create(self, db_table_name):
        """Create a new table.
        
        Args:
            db_table_name: the creating db_table name.

        Returns:
            The table engine created.
        """

        if db_table_name in self.tables:
            print("Table %s exist! Please directly Use(%s)" % (table_name, table_name))
            return None

        table_log_dir = self.log_dir + "/" + db_table_name
        table_data_dir = self.data_dir + "/" + db_table_name
        if not os.path.isdir(table_log_dir):
            os.makedirs(table_log_dir)
        if not os.path.isdir(table_data_dir):
            os.makedirs(table_data_dir)

        new_table = awa.Init(table_log_dir, table_data_dir)
        self.tables[db_table_name] = new_table
        return new_table

    def __load(self, db_table_name) -> bool:
        """Load the specified table.
        
        Args:
            table_name: the loading table name.

        Returns:
            True or False, whether loading the specified table success.
        """

        if not db_table_name in self.tables:
            self.__create(db_table_name)
        
        if self.tables[db_table_name] is None:
            print("Db table %s created failed!", db_table_name)
            return False

        if not awa.LoadFromLocal(self.tables[db_table_name]):
            print("Table %s can not be loaded!" % db_table_name)
            return False
        return True

    def __normalize(vec_array):
        x = None
        if isinstance(vec_array, list):
            x = np.array(vec_array, dtype=np.dtype("float32"))
        elif type(vec_array).__name__ == "ndarray":
            x = vec_array
        if x is None:
            return
        x_l2_norm = np.linalg.norm(x,ord=2)
        x_l2_normalized = x / x_l2_norm
        return x_l2_normalized

    def __check_ids_type(
        self,
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

    def __add_filter(
        self,
        db_table_name,
        request,
        filters: Optional[dict] = None,
        **kwargs: Any,
    ):
        """Add filters for search request.

        Args:
            request: Search request.
            filters: Field filter, each key-value pair denotes field_name-field_value pair.

        Returns:
            None.
        """
        if filters is not None:
            range_filters: dict = {}
            term_filters: dict = {}
            for field_name in filters:
                field_value = filters[field_name]
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
                        range_filters[field_name] = awa.RangeFilter()
                        range_filters[field_name].field = field_name
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
                        term_filters[field_name] = awa.TermFilter()
                        term_filters[field_name].field = field_name
                    term_filters[field_name].value = field_value
                    #term_filters[field_name].is_union = True
                    term_filters[field_name].is_union = 1

            for field_name in range_filters:
                request.AddRangeFilter(range_filters[field_name])

            for field_name in term_filters:
                request.AddTermFilter(term_filters[field_name])

        return None

    def __field_check(
        self, 
        db_table_name,
        field_name, 
        field_data, 
        fields_type):
        """Check the field whether existed.
           If existed, check whether the field data type is right.
        
        Args:
            db_table_name: database/table_name
            field_name: the checking field name.
            field_data: field value. 
            fields_type: the existed fields and their data type.

        Returns:
            Field checked code, 0 denotes ok, negative value means errors.
        """

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
        """Add a field to the current table schema.
        
        Args:
            db_table_name: db_name/table_name.
            name: field name.
            datatype: field data type.
            is_index: whether the field is to be indexed.
            add_new_field: whether adding a new field to the created table.

        Returns:
            True or False, whether adding the field to the table schema success.
        """

        if not self.tables_fields_check[db_table_name]:
            f_info = awa.FieldInfo()
            f_info.name = name
            f_info.data_type = datatype
            f_info.is_index = is_index
            if datatype != awa.DataType.MULTI_STRING:
                self.tables_attr[db_table_name].AddField(f_info)
            else:
                self.tables_extra_new_fields[db_table_name].append(f_info)
            return True

        if add_new_field:
            f_info = awa.FieldInfo()
            f_info.name = name
            f_info.data_type = datatype
            f_info.is_index = is_index
            if not awa.AddNewField(db_table_name, f_info):
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
        """Add a vector field to the current table schema.
        
        Args:
            db_table_name: db_name/table_name.
            name: vector field name.
            datatype: vector field data type, such as int or float for each dimension's value.
            is_index: whether the vector field is to be indexed.
            dimension: whether adding a new field to the created table.
            store_type: the vectors' store type, such as MemoryOnly, Mmap.
            store_param: the parameters about vector store.
            has_source: whether has the source referenced to the vector field

        Returns:
            True or False, whether adding the vector field to the table schema success.
        """

        if not self.tables_fields_check[db_table_name]:
            v_info = awa.VectorInfo()
            v_info.name = name
            v_info.data_type = datatype
            v_info.is_index = is_index
            v_info.dimension = dimension
            v_info.store_type = store_type
            v_info.store_param = store_param
            v_info.has_source = has_source
            self.tables_attr[db_table_name].AddVectorInfo(v_info)
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
        """check and Add a field to the current table schema.
        
        Args:
            db_table_name: db_name/table_name.
            awadb_field: field struct for the db engine.
            fields_type: dict for the field and field data type.
            field_name: the field name to be checked
            field_value: the field value to be checked.

        Returns:
            True or False, whether checking and adding the field success.
        """

        ret = self.__field_check(db_table_name, field_name, field_value, fields_type)

        if ret < 0:
            return -1 

        add_new_field = False
        if ret == 1:
            add_new_field = True

        is_index = True

        awadb_field.name = field_name
        field_type = fields_type[field_name]
        if field_type == FieldDataType.INT:
            awadb_field.value = field_value.to_bytes(4, "little")
            awadb_field.datatype = awa.DataType.INT
            if ret != 2:
                self.__add_field(db_table_name, field_name, awadb_field.datatype, is_index, add_new_field)
        elif field_type == FieldDataType.LONG:
            awadb_field.value = field_value.to_bytes(8, "little")
            awadb_field.datatype = awa.DataType.LONG
            if ret != 2:
                self.__add_field(db_table_name, field_name, awadb_field.datatype, is_index, add_new_field)
        elif field_type == FieldDataType.FLOAT:
            awadb_field.value = struct.pack("<f", field_value)
            awadb_field.datatype = awa.DataType.FLOAT
            if ret != 2:
                self.__add_field(db_table_name, field_name, awadb_field.datatype, is_index, add_new_field)
        elif field_type == FieldDataType.STRING:
            awadb_field.value = str.encode(field_value)
            awadb_field.datatype = awa.DataType.STRING
            is_index = False
            #if field_name == "embedding_text":
            #    is_index = False
            if ret != 2:
                self.__add_field(db_table_name, field_name, awadb_field.datatype, is_index, add_new_field)
        elif field_type == FieldDataType.MULTI_STRING:
            if isinstance(field_value, str):
                awadb_field.mul_str_value.append(field_value)
            else:
                for each_str in field_value:
                    awadb_field.mul_str_value.append(each_str)

            awadb_field.datatype = awa.DataType.MULTI_STRING
            if ret != 2:
                self.__add_field(db_table_name, field_name, awadb_field.datatype, is_index, add_new_field)

        elif field_type == FieldDataType.VECTOR:
            dimension = field_value.__len__()
            if type(field_value).__name__ == "ndarray":
                awadb_field.value = field_value.tobytes()
            else:
                vec_value = np.array(field_value, dtype=np.dtype("float32"))
                awadb_field.value = vec_value.tobytes()

            awadb_field.datatype = awa.DataType.VECTOR
            if ret != 2:
                self.__add_vector_field(
                    db_table_name,
                    field_name,
                    awadb_field.datatype,
                    True,
                    len(field_value),
                    "Mmap",
                    '{"cache_size" : 2000}',
                    False,
                )
                self.tables_vector_fields_type[db_table_name][field_name] = dimension 

        return 0

