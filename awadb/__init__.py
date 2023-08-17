# -*- coding:utf-8 -*-
#!/usr/bin/python3

import hashlib
import io
import json
import os
import struct
import time
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set

import awa
import numpy as np

from awadb.punctuation_marks_en import punctuation_marks
from awadb.stop_words_en import stop_words
from awadb.words_stem_en import PorterStemmer

__version__ = "0.3.10"


class FieldDataType(Enum):
    INT = 1
    FLOAT = 2
    STRING = 3
    VECTOR = 4
    ERROR = 5
    MULTI_STRING = 6


__all__ = [
    "OpenAI",
    "HuggingFace",
]


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


def md5str(str):
    m = hashlib.md5(str.encode(encoding="utf-8"))
    return m.hexdigest()


class AwaEmbedding:
    """Embedding models."""

    def __init__(self, model_name: Optional[str] = None):
        if model_name is None:
            self.model_name = "HuggingFace"
        else:
            self.model_name = model_name

        if self.model_name == "OpenAI":
            from awadb.awa_embedding.openai import OpenAIEmbeddings

            self.llm = OpenAIEmbeddings()
        else:
            from awadb.awa_embedding.huggingface import HuggingFaceEmbeddings

            self.llm = HuggingFaceEmbeddings()

    # set your own llm
    def SetModel(self, model_name):
        self.model = AutoModel.from_pretrained(model_name)

    # set your own tokenizer
    def SetTokenizer(self, tokenizer_name):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    def Embedding(self, sentence):
        return self.llm.Embedding(sentence)

    def EmbeddingBatch(
        self,
        texts: Iterable[str],
        **kwargs: Any,
    ) -> List[List[float]]:
        return self.llm.EmbeddingBatch(texts, **kwargs)


class Client:
    def __init__(self, root_dir="."):
        self.root_dir = root_dir
        log_dir = root_dir + "/log"
        data_dir = root_dir + "/data"
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)

        self.using_table_engine = None
        self.using_table_name = ""
        self.key_confirmed_name = "_id"
        self.key_nick_name = ""

        self.tables_fields_check = {}
        self.tables_fields_type = {}
        self.tables_vector_field_name = {}
        self.tables_doc_count = {}
        self.tables_attr = {}
        self.tables = {}
        self.english_word_stemmer = PorterStemmer()
        self.extra_new_fields = []
        self.row_fields = {}

        existed_meta_file = data_dir + "/tables.meta"
        if os.path.isfile(existed_meta_file):
            self.Read()

        self.llm = None
        self.is_duplicate_texts = True
        self.model_name = "HuggingFace"

    def Write(self):
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

    def Read(self):
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

    def Create(self, table_name, model_name="HuggingFace"):
        if model_name not in __all__:
            raise NameError("Could not find this model: ", model_name)

        if table_name in self.tables:
            print("Table %s exist! Please directly Use(%s)" % (table_name, table_name))
            return False
        log_dir = self.root_dir + "/log/"
        log_dir = log_dir + table_name
        data_dir = self.root_dir + "/data/"
        data_dir = data_dir + table_name
        new_table = awa.Init(log_dir, data_dir)
        self.tables[table_name] = new_table
        self.using_table_name = table_name
        self.using_table_engine = new_table
        self.tables_fields_check[table_name] = False
        self.tables_doc_count[table_name] = 0
        self.model_name = model_name
        self.llm = AwaEmbedding(self.model_name)
        return True

    def Close(self, table_name: Optional[str] = None):
        if table_name is None:
            if self.using_table_engine is None:
                return False
            if awa.Close(self.using_table_engine) == 0:
                self.using_table_engine = None
                return True
            return False

        if table_name is not None and (not table_name in self.tables):
            print("Table %s not exist!" % table_name)
            return False
        self.using_table_engine = self.tables[table_name]
        if self.using_table_engine is None:
            return False
        if awa.Close(self.using_table_engine) == 0:
            self.using_table_engine = None
            return True
        return False

    def ListAllTables(self) -> List[str]:
        results: List[str] = []
        for table in self.tables_fields_check:
            results.append(table)
        return results

    def GetCurrentTable(self) -> str:
        return self.using_table_name

    def Load(self, table_name) -> bool:
        if not table_name in self.tables:
            self.Create(table_name)

        self.using_table_name = table_name
        self.using_table_engine = self.tables[table_name]
        if not awa.LoadFromLocal(self.using_table_engine):
            print("Table %s can not be loaded!" % self.using_table_name)
            return False
        return True

    def Use(self, table_name) -> bool:
        return self.Load(table_name)

    def __FieldCheck(self, field_name, field_data, fields_type):
        f_type = typeof(field_data)
        if f_type == FieldDataType.ERROR:
            print(
                "Field data type error! Please input right data type : int|float|string|vector|multi_string!"
            )
            return -1

        if field_name in fields_type:
            return -2

        if field_name in self.tables_fields_type[self.using_table_name]:
            if (
                f_type == FieldDataType.STRING
                and self.tables_fields_type[self.using_table_name][field_name]
                == FieldDataType.MULTI_STRING
            ):
                fields_type[field_name] = FieldDataType.MULTI_STRING
                return 0

            if f_type != self.tables_fields_type[self.using_table_name][field_name]:
                return -3
            fields_type[field_name] = f_type
        else:
            self.tables_fields_type[self.using_table_name][field_name] = f_type
            fields_type[field_name] = f_type
            return 1
        return 0

    def AddField(self, name, datatype, is_index, add_new_field):
        if not self.tables_fields_check[self.using_table_name]:
            f_info = awa.FieldInfo()
            f_info.name = name
            f_info.data_type = datatype
            f_info.is_index = is_index
            if datatype != awa.DataType.MULTI_STRING:
                self.tables_attr[self.using_table_name].AddField(f_info)
            else:
                self.extra_new_fields.append(f_info)
            return True

        if add_new_field:
            f_info = awa.FieldInfo()
            f_info.name = name
            f_info.data_type = datatype
            f_info.is_index = is_index
            if not awa.AddNewField(self.using_table_engine, f_info):
                print("Add new field %s failed!" % name)
                return False

        return True

    def AddVectorField(
        self, name, datatype, is_index, dimension, store_type, store_param, has_source
    ):
        if not self.tables_fields_check[self.using_table_name]:
            v_info = awa.VectorInfo()
            v_info.name = name
            v_info.data_type = datatype
            v_info.is_index = is_index
            v_info.dimension = dimension
            v_info.store_type = store_type
            v_info.store_param = store_param
            v_info.has_source = has_source
            self.tables_attr[self.using_table_name].AddVectorInfo(v_info)
            return True
        return False

    def CheckAddField(
        self,
        awadb_field,
        fields_type,
        field_name,
        field_value,
    ):
        ret = self.__FieldCheck(field_name, field_value, fields_type)

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
            awadb_field.datatype = awa.DataType.INT

            self.AddField(field_name, awadb_field.datatype, is_index, add_new_field)
        elif field_type == FieldDataType.FLOAT:
            awadb_field.value = struct.pack("<f", field_value)
            awadb_field.datatype = awa.DataType.FLOAT
            self.AddField(field_name, awadb_field.datatype, is_index, add_new_field)
        elif field_type == FieldDataType.STRING:
            awadb_field.value = field_value
            awadb_field.datatype = awa.DataType.STRING
            if field_name == "embedding_text":
                is_index = False
            self.AddField(field_name, awadb_field.datatype, is_index, add_new_field)
        elif field_type == FieldDataType.MULTI_STRING:
            if isinstance(field_value, str):
                awadb_field.AddMulStr(field_value)
            else:
                for each_str in field_value:
                    awadb_field.AddMulStr(each_str)

            awadb_field.datatype = awa.DataType.MULTI_STRING
            self.AddField(field_name, awadb_field.datatype, is_index, add_new_field)

        elif field_type == FieldDataType.VECTOR:
            if type(field_value).__name__ == "ndarray":
                awadb_field.value = field_value.tobytes()
            else:
                vec_value = np.array(field_value, dtype=np.dtype("float32"))
                awadb_field.value = vec_value.tobytes()

            awadb_field.datatype = awa.DataType.VECTOR
            self.AddVectorField(
                field_name,
                awadb_field.datatype,
                True,
                len(field_value),
                "Mmap",
                '{"cache_size" : 2000}',
                False,
            )
            self.tables_vector_field_name[self.using_table_name] = field_name
        return 0

    def Delete(
        self,
        ids: List[str],
    ) -> bool:
        """Delete the documents which have the specified ids.

        Args:
            ids: The id list of the updating embedding vector.
        Returns:
            True or False.
        """

        if self.using_table_name == "" or len(ids) == 0:
            print("Please specify table name and primary keys of the table!")
            return False

        ids_list = awa.StrVec()
        for each_id in ids:
            ids_list.append(each_id)
        return awa.Delete(self.using_table_engine, ids_list)

    def UpdateTexts(
        self,
        ids: List[str],
        text_field_name: str,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        **args: Any,
    ) -> List[str]:
        """Update the documents which have the specified ids.

        Args:
            ids: The id list of the updating embedding vector.
            text_field_name: The text field name.
            texts: The texts of the updating documents.
            metadatas: The metadatas of the updating documents.
        Returns:
            the ids of the updated documents.
        """

        return self.AddTexts(
            text_field_name=text_field_name,
            embedding_field_name="text_embedding",
            texts=texts,
            metadatas=metadatas,
            ids=ids,
        )

    def Get(
        self,
        ids: Optional[List[str]] = None,
        text_in_page_content: Optional[str] = None,
        meta_filter: Optional[dict] = None,
        not_include_fields: Optional[Set[str]] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> list:
        """Get the documents which have the specified ids.
           If ids is specified, text_in_page_content, meta_filter, and limit will be invalid.

        Args:
            ids: The ids of the embedding vectors.
            text_in_page_content: Filter by the text in page_content of Document in LangChain.
            meta_filter: Filter by any metadata of the document.
            not_include_fields: Not pack the specified fields of each document.
            limit: The number of documents to return. Optional. Defaults to 5.

        Returns:
            Documents which satisfy the input conditions.
        """

        DEFAULT_LIMIT = 5
        docs_detail = []
        if self.using_table_name == "":
            print("Please specify the table name!")
            return docs_detail
        if ids is None and text_in_page_content is None and meta_filter is None:
            print(
                "ids, text_in_page_content or meta_filter should be specified at least one!"
            )
            return docs_detail

        if not_include_fields is None:
            not_include_fields = {"text_embedding"}
        elif "text_embedding" not in not_include_fields:
            not_include_fields.add("text_embedding")

        if ids is None and (
            (text_in_page_content is not None) or (meta_filter is not None)
        ):
            req = awa.Request()
            req.SetReqNum(1)
            if limit is not None:
                req.SetTopN(limit)
            else:
                req.SetTopN(DEFAULT_LIMIT)
            req.SetBruteForceSearch(1)
            default_retrieval_type = '{"metric_type":"InnerProduct"}'
            req.SetRetrievalParams(default_retrieval_type)

            self.AddFilter(req, text_in_page_content, meta_filter)

            response = awa.Response()
            fvec_names = awa.StrVec()
            for field_name in self.tables_fields_type[self.using_table_name]:
                if not_include_fields is not None and field_name in not_include_fields:
                    continue
                fvec_names.append(field_name)

            ret = awa.DoSearch(self.using_table_engine, req, response)
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
                            not_include_fields is not None
                            and name in not_include_fields
                        ):
                            i = i + 1
                            continue
                        f_type = self.tables_fields_type[self.using_table_name][name]
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

        doc_results = awa.DocsMap()
        ids_list = awa.StrVec()
        for key_id in ids:
            doc_results[key_id] = awa.Doc()
            ids_list.append(key_id)

        awa.GetDocs(self.using_table_engine, ids_list, doc_results)

        for key_id in ids:
            if doc_results[key_id].Key() == "-1":
                continue

            doc_detail = {}
            field_index = 0
            while field_index < doc_results[key_id].TableFields().__len__():
                field = doc_results[key_id].TableFields()[field_index]
                # for field in doc_results[key_id].TableFields():
                if not_include_fields is not None and field.name in not_include_fields:
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
                if not_include_fields is not None and field.name in not_include_fields:
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

    def __TextPreprocess(
        self,
        text: str,
        **kwargs: Any,
    ) -> Dict[str, int]:
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

    def __ProcessTextEmbedding(self, doc):
        for field in doc:
            if type(field).__name__ == "dict":
                for key in field:
                    if key == "embedding_text":
                        self.llm = AwaEmbedding(self.model_name)
                        embedding_field = {}
                        embedding_field["text_embedding"] = self.llm.Embedding(
                            field[key]
                        )
                        doc.append(embedding_field)
            else:
                print("field should be the format of dict")

    def AddTexts(
        self,
        text_field_name: str,
        embedding_field_name: str,
        texts: Iterable[str],
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[dict]] = None,
        is_duplicate_texts: Optional[bool] = None,
        ids: Optional[List[str]] = None,
        **args: Any,
    ) -> List[str]:
        added_ids: List[str] = []
        if not self.tables_fields_check[self.using_table_name]:
            if self.using_table_name == "":
                print("Please specify your table name!")
                return added_ids

            self.tables_attr[self.using_table_name] = awa.TableInfo()
            self.tables_attr[self.using_table_name].SetName(self.using_table_name)
            self.tables_fields_type[self.using_table_name] = {}

        if is_duplicate_texts is not None:
            self.is_duplicate_texts = is_duplicate_texts

        if embeddings is None:
            if self.llm is None:
                # Set llm
                self.llm = AwaEmbedding(self.model_name)
            embeddings = self.llm.EmbeddingBatch(texts)

        awa_docs = awa.DocsVec()
        words_in_docs = awa.WordsCount()

        adding_docs_no = 0
        for text in texts:
            fields_type = {}
            doc = awa.Doc()
            key_field = awa.Field()
            key_field_value = ""
            # add unique primary id for each unique document
            if self.is_duplicate_texts:
                if ids is None:
                    key_field_value = md5str(text)
                else:
                    key_field_value = ids[adding_docs_no]
            # auto increasing id
            else:
                if ids is None:
                    key_field_value = str(self.tables_doc_count[self.using_table_name])
                else:
                    key_field_value = ids[adding_docs_no]
            self.CheckAddField(
                key_field, fields_type, self.key_confirmed_name, key_field_value
            )
            doc.AddField(key_field)
            added_ids.append(key_field.value)
            doc.SetKey(key_field.value)
            text_field = awa.Field()
            self.CheckAddField(text_field, fields_type, text_field_name, text)
            words_in_text = self.__TextPreprocess(text)
            words_in_doc = awa.WordsInDoc()
            for word in words_in_text:
                word_count = awa.WordCount()
                word_count.word = word
                word_count.count = words_in_text[word]
                words_in_doc.AddWordCount(word_count)
            words_in_docs.append(words_in_doc)
            embedding_field = awa.Field()
            self.CheckAddField(
                embedding_field,
                fields_type,
                embedding_field_name,
                embeddings[adding_docs_no],
			)
            doc.AddField(text_field)
            doc.AddField(embedding_field)
            if metadatas is not None:
                for field in metadatas[adding_docs_no]:
                    meta_field = awa.Field()
                    self.CheckAddField(
                        meta_field,
                        fields_type,
                        field,
                        metadatas[adding_docs_no][field],
                    )
                    if not self.tables_fields_check[self.using_table_name]:
                        self.row_fields[field] = meta_field.datatype
                    doc.AddField(meta_field)

                if self.tables_fields_check[self.using_table_name]:
                    for field in self.row_fields:
                        if not field in fields_type:
                            meta_field = awa.Field()
                            field_value = None
                            if self.row_fields[field] == awa.DataType.INT:
                                field_value = 0
                            elif self.row_fields[field] == awa.DataType.FLOAT:
                                field_value = 0.0 
                            elif self.row_fields[field] == awa.DataType.STRING:
                                field_value = "" 
                            elif self.row_fields[field] == awa.DataType.MULTI_STRING:
                                field_value = [""]
							
                            self.CheckAddField(
								meta_field,
                                fields_type,
                                field,
                                field_value,
                            )
                            doc.AddField(meta_field)

            awa_docs.append(doc)
            self.tables_doc_count[self.using_table_name] += 1
            adding_docs_no = adding_docs_no + 1
            if not self.tables_fields_check[self.using_table_name]:
                self.tables_attr[self.using_table_name].SetIndexingSize(10000)
                self.tables_attr[self.using_table_name].SetRetrievalType("IVFPQ")
                self.tables_attr[self.using_table_name].SetRetrievalParam(
                    '{"ncentroids" : 256, "nsubvector" : 16}'
                )

                if not awa.Create(
                    self.using_table_engine, self.tables_attr[self.using_table_name]
                ):
                    error_msg = Exception("Create table error!!!")
                    raise error_msg

                self.tables_fields_check[self.using_table_name] = True
                for extra_field in self.extra_new_fields:
                    if not awa.AddNewField(self.using_table_engine, extra_field):
                        print("Add new field %s failed!" % extra_field.name)

                self.Write()

        awa.AddTexts(self.using_table_engine, awa_docs, words_in_docs)

        return added_ids

    def Add(self, doc):
        if not isinstance(doc, list):
            print("Incorrect argument, list type is needed for Add!!!")
            return False

        if not self.tables_fields_check[self.using_table_name]:
            if self.using_table_name == "":
                print("Please specify your table name!")
                return False

            self.tables_attr[self.using_table_name] = awa.TableInfo()
            self.tables_attr[self.using_table_name].SetName(self.using_table_name)
            self.tables_fields_type[self.using_table_name] = {}

        self.__ProcessTextEmbedding(doc)

        fields_type = {}
        awadb_doc = awa.Doc()

        has_primary_key = False
        for field in doc:
            if type(field).__name__ == "dict":
                for key in field:
                    if key == self.key_confirmed_name:
                        has_primary_key = True
                    awadb_field = awa.Field()
                    self.CheckAddField(awadb_field, fields_type, key, field[key])
                    awadb_doc.AddField(awadb_field)

        if not has_primary_key:
            key_fid = awa.Field()
            self.CheckAddField(
                key_fid,
                fields_type,
                self.key_confirmed_name,
                str(self.tables_doc_count[self.using_table_name]),
            )
            awadb_doc.AddField(key_fid)
            awadb_doc.SetKey(key_fid.value)

        if not self.tables_fields_check[self.using_table_name]:
            self.tables_attr[self.using_table_name].SetIndexingSize(10000)
            self.tables_attr[self.using_table_name].SetRetrievalType("IVFPQ")
            self.tables_attr[self.using_table_name].SetRetrievalParam(
                '{"ncentroids" : 256, "nsubvector" : 16}'
            )

            if not awa.Create(
                self.using_table_engine, self.tables_attr[self.using_table_name]
            ):
                return False

            for extra_field in self.extra_new_fields:
                if not awa.AddNewField(self.using_table_engine, extra_field):
                    print("Add new field %s failed!" % extra_field.name)

        if not awa.AddDoc(self.using_table_engine, self.using_table_name, awadb_doc):
            return False

        self.tables_doc_count[self.using_table_name] += 1

        if not self.tables_fields_check[self.using_table_name]:
            self.tables_fields_check[self.using_table_name] = True
            self.Write()
        doc[:] = []
        return True

    def AddFilter(
        self,
        request,
        text_in_page_content: Optional[str] = None,
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
                if field_name not in self.tables_fields_type[self.using_table_name]:
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
                    term_filters[field_name].is_union = True

            for field_name in range_filters:
                request.AddRangeFilter(range_filters[field_name])

            for field_name in term_filters:
                request.AddTermFilter(term_filters[field_name])

        if text_in_page_content is not None:
            words_count = self.__TextPreprocess(text_in_page_content)
            for word in words_count:
                request.AddPageText(word)

        return None

    def Search(
        self,
        query,
        topn,
        text_in_page_content: Optional[str] = None,
        meta_filter: Optional[dict] = None,
        not_include_fields: Optional[Set[str]] = None,
        **kwargs: Any,
    ):
        query_type = typeof(query)

        show_results = []
        if (
            query_type == FieldDataType.ERROR
            or query_type == FieldDataType.INT
            or query_type == FieldDataType.FLOAT
        ):
            return show_results

        vec_query = awa.VectorQuery()
        vec_query.name = self.tables_vector_field_name[self.using_table_name]

        if query_type == FieldDataType.STRING:  # semantic text search
            embedding = self.llm.Embedding(query)
            vec_query.value = embedding.tobytes()

        elif query_type == FieldDataType.VECTOR:  # vector search
            vec_value = np.array(query, dtype=np.dtype("float32"))
            vec_query.value = vec_value.tobytes()

        vec_query.min_score = -1
        vec_query.max_score = 999999

        req = awa.Request()
        req.SetReqNum(1)
        req.AddVectorQuery(vec_query)
        req.SetTopN(topn)
        req.SetBruteForceSearch(1)
        default_retrieval_type = '{"metric_type":"InnerProduct"}'
        req.SetRetrievalParams(default_retrieval_type)
        self.AddFilter(req, text_in_page_content, meta_filter)

        response = awa.Response()
        fvec_names = awa.StrVec()
        for field_name in self.tables_fields_type[self.using_table_name]:
            if field_name == "_id" or (
                not_include_fields is not None and field_name in not_include_fields
            ):
                continue

            fvec_names.append(field_name)

        ret = awa.DoSearch(self.using_table_engine, req, response)
        response.PackResults(fvec_names)

        search_result_vec = response.Results()
        search_result_index = 0
        while search_result_index < search_result_vec.__len__():
            search_result = search_result_vec[search_result_index]
            result_per_request = {}
            result_per_request["ResultSize"] = search_result.result_items.__len__()

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
                    if not_include_fields is not None and name in not_include_fields:
                        i = i + 1
                        continue

                    f_type = self.tables_fields_type[self.using_table_name][name]
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
                        j = 0
                        while j < vec_data.__len__():
                            each_vec_data = vec_data[j]
                            vec_result.append(each_vec_data)
                            j = j + 1
                        item_detail[name] = vec_result
                    i = i + 1
                if not_include_fields is not None and "score" not in not_include_fields:
                    item_detail["score"] = item.score
                result_items_list.append(item_detail)
                item_index = item_index + 1

            result_per_request["ResultItems"] = result_items_list
            show_results.append(result_per_request)
            search_result_index = search_result_index + 1
        return show_results
