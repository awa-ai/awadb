# -*- coding:utf-8 -*-
#!/usr/bin/python3

import os
import numpy as np
import struct
import json
import io

from enum import Enum

import awa


class FieldDataType(Enum):
    INT = 1
    FLOAT = 2 
    STRING = 3 
    VECTOR = 4
    ERROR = 5

def typeof(variate):
    v_type = FieldDataType.ERROR
    if isinstance(variate,int):
        v_type = FieldDataType.INT 
    elif isinstance(variate,str):
        v_type = FieldDataType.STRING 
    elif isinstance(variate,float):
        v_type = FieldDataType.FLOAT 
    elif isinstance(variate,list):
        is_vector = True 
        for element in variate:
            if not (isinstance(element, int) or isinstance(element, float) or isinstance(element, np.float32)):
                is_vector = False 
                break
        if is_vector:
            v_type = FieldDataType.VECTOR
    elif type(variate).__name__ == 'ndarray':
        v_type = FieldDataType.VECTOR

    return v_type


class Client:
    def __init__(self, root_dir="."):
        self.root_dir = root_dir 
        log_dir = root_dir + '/log'
        data_dir = root_dir + '/data'
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)

        self.using_table_engine = None 
        self.using_table_name = ''
        self.key_confirmed_name = '_id'
        self.key_nick_name = '' 
        
        self.tables_fields_check = {}
        self.tables_fields_type = {}
        self.tables_fields_names = {} 
        self.tables_vector_field_name = {} 
        self.tables_doc_count = {} 
        self.tables_attr = {} 
        self.tables_have_obvious_primary_key = {} 
        self.tables_primary_key_fid_no = {} 
        self.tables = {}
        self.tables_embedding_text_fid_no = {}


        existed_meta_file = data_dir + '/tables.meta'
        if os.path.isfile(existed_meta_file):
            self.Read()

        self.llm = None
        

    def Write(self):
        tables_meta = {}
        tables_meta['fields_check'] = self.tables_fields_check
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
                elif self.tables_fields_type[table_name][f_id] == FieldDataType.VECTOR:
                    field_dict[f_id] = "VECTOR"
                fields_type_list.append(field_dict)

            tables_types[table_name] = fields_type_list

        tables_meta['fields_type'] = tables_types
        tables_meta['fields_name'] = self.tables_fields_names
        tables_meta['vector_field_name'] = self.tables_vector_field_name 
        tables_meta['embedding_field_no'] =  self.tables_embedding_text_fid_no

        tables_meta['doc_count'] = self.tables_doc_count
        tables_meta['has_obvious_primary_key'] = self.tables_have_obvious_primary_key
        tables_meta['primary_key_fid_no'] = self.tables_primary_key_fid_no
      
        tables_dict = {} 
        for key in self.tables_attr:
            table_attr_info = {}
            fields_info = self.tables_attr[key].Fields()
            fields_list = [] 
            for field_info in fields_info:
                fields_dict = {}
                fields_dict['name'] = field_info.name
                if field_info.data_type == awa.DataType.INT:
                    fields_dict['data_type'] = 'INT'
                elif field_info.data_type == awa.DataType.FLOAT:
                    fields_dict['data_type'] = 'FLOAT'
                elif field_info.data_type == awa.DataType.STRING:
                    fields_dict['data_type'] = 'STRING'
                elif field_info.data_type == awa.DataType.VECTOR:
                    fields_dict['data_type'] = 'VECTOR'

                fields_dict['is_index'] = field_info.is_index
                fields_list.append(fields_dict)
            table_attr_info['fields_info'] = fields_list

            vec_fields_list = [] 
            vec_fields_info = self.tables_attr[key].VectorInfos()
            for vec_field_info in vec_fields_info:
                vec_fields_dict = {}
                vec_fields_dict['name'] = vec_field_info.name
                if vec_field_info.data_type == awa.DataType.INT:
                    vec_fields_dict['data_type'] = 'INT'
                elif vec_field_info.data_type == awa.DataType.FLOAT:
                    vec_fields_dict['data_type'] = 'FLOAT'
                elif vec_field_info.data_type == awa.DataType.STRING:
                    vec_fields_dict['data_type'] = 'STRING'
                elif vec_field_info.data_type == awa.DataType.VECTOR:
                    vec_fields_dict['data_type'] = 'VECTOR'

                vec_fields_dict['is_index'] = vec_field_info.is_index
                vec_fields_dict['dimension'] = vec_field_info.dimension
                vec_fields_dict['model_id'] = vec_field_info.model_id
                vec_fields_dict['store_type'] = vec_field_info.store_type
                vec_fields_dict['store_param'] = vec_field_info.store_param
                vec_fields_list.append(vec_fields_dict)
            table_attr_info['vec_fields'] = vec_fields_list
            tables_dict[key] = table_attr_info
        
        tables_meta['tables_info'] = tables_dict 

        created_table_path = self.root_dir + '/data/tables.meta'
        with open(created_table_path, 'w', encoding='unicode_escape') as f:
            json.dump(tables_meta, f)

    def Read(self):
        created_table_path = self.root_dir + '/data/tables.meta'
        with open(created_table_path, 'r', encoding='unicode_escape') as f:
            tables_meta = json.load(fp = f)

            self.tables_fields_check = tables_meta['fields_check'] 
            self.tables_doc_count = tables_meta['doc_count']
            self.tables_have_obvious_primary_key = tables_meta['has_obvious_primary_key'] 
            self.tables_primary_key_fid_no = tables_meta['primary_key_fid_no'] 

            for table_name in tables_meta['fields_type']:
                table_field_dict = {}
                for each_field_type in tables_meta['fields_type'][table_name]:
                    for f_id in each_field_type:
                        if each_field_type[f_id] == "INT":
                            table_field_dict[int(f_id)] = FieldDataType.INT
                        elif each_field_type[f_id] == "FLOAT":
                            table_field_dict[int(f_id)] = FieldDataType.FLOAT
                        elif each_field_type[f_id] == "STRING":
                            table_field_dict[int(f_id)] = FieldDataType.STRING
                        elif each_field_type[f_id] == "VECTOR":
                            table_field_dict[int(f_id)] = FieldDataType.VECTOR
                self.tables_fields_type[table_name] = table_field_dict

            self.tables_fields_names = tables_meta['fields_name'] 
            self.tables_vector_field_name = tables_meta['vector_field_name']
            self.tables_embedding_text_fid_no = tables_meta['embedding_field_no'] 

            for table_name in tables_meta['tables_info']:
           
                table_info = awa.TableInfo()
                for each_field_info in tables_meta['tables_info'][table_name]['fields_info']:
                    field_info = awa.FieldInfo()
                    field_info.name = each_field_info['name'] 
                    if each_field_info['data_type'] == "INT":
                        field_info.data_type = awa.DataType.INT
                    elif each_field_info['data_type'] == "FLOAT":
                        field_info.data_type = awa.DataType.FLOAT
                    elif each_field_info['data_type'] == "STRING":
                        field_info.data_type = awa.DataType.STRING
                    elif each_field_info['data_type'] == "VECTOR":
                        field_info.data_type = awa.DataType.VECTOR
                    field_info.is_index = each_field_info['is_index'] 
                    table_info.AddField(field_info)

                for each_vec_info in tables_meta['tables_info'][table_name]['vec_fields']:
                    vec_info = awa.VectorInfo()
                    vec_info.name = each_vec_info['name']
                    if each_vec_info['data_type'] == "INT":
                        vec_info.data_type = awa.DataType.INT
                    elif each_vec_info['data_type'] == "FLOAT":
                        vec_info.data_type = awa.DataType.FLOAT
                    elif each_vec_info['data_type'] == "STRING":
                        vec_info.data_type = awa.DataType.STRING
                    elif each_vec_info['data_type'] == "VECTOR":
                        vec_info.data_type = awa.DataType.VECTOR
                    vec_info.is_index = each_vec_info['is_index']
                    vec_info.dimension = each_vec_info['dimension']
                    vec_info.model_id = each_vec_info['model_id']
                    vec_info.store_type = each_vec_info['store_type']
                    vec_info.store_param = each_vec_info['store_param']
                    table_info.AddVectorInfo(vec_info)

                table_info.SetIndexingSize(10000)
                table_info.SetRetrievalType("IVFPQ")
                table_info.SetRetrievalParam('{"ncentroids" : 256, "nsubvector" : 16}')
                self.tables_attr[table_name] = table_info

    def Create(self, name):
        if name in self.tables:
            print('Table %s exist! Please directly Use(%s)' % (name, name))
            return False
        log_dir = self.root_dir + '/log/'
        log_dir = log_dir + name 
        data_dir = self.root_dir + '/data/'
        data_dir = data_dir + name
        new_table = awa.Init(log_dir, data_dir)
        self.tables[name] = new_table
        self.using_table_name = name
        self.using_table_engine = new_table
        self.tables_fields_check[name] = False
        self.tables_have_obvious_primary_key[name] = False
        self.tables_primary_key_fid_no[name] = None
        self.tables_doc_count[name] = 0
 

    def Use(self, table_name):
        if not table_name in self.tables:
            print('Table %s not exist! Please create first!')
            return False
        self.using_table_name = table_name 
        self.using_table_engine = self.tables[table_name]


    def __FieldCheck(self, field_idx, field_name, field_data, fields_type):
        if not self.tables_fields_check[self.using_table_name]:
            f_type = typeof(field_data)
            if f_type == FieldDataType.ERROR:
                error_msg = Exception("Field data type error! Please input right data type : int|float|string|vector!")
                raise error_msg
            fields_type[field_idx] = f_type
        else:
            f_type = typeof(field_data)
             
            if self.tables_fields_type[self.using_table_name][field_idx] != f_type: 
                error_msg = Exception("No. %d field data type not %d, should %d!" % (field_idx, f_type, self.tables_fields_type[self.using_table_name][field_idx]))
                raise error_msg
            elif field_name != self.key_confirmed_name and (not (field_name in self.tables_fields_names[self.using_table_name])):
                error_msg = Exception("Field name \'%s\' not exist!" % field_name)
                raise error_msg


        return f_type 

    def AddField(self, name, datatype, is_index): 
        if not self.tables_fields_check[self.using_table_name]:
            f_info = awa.FieldInfo()
            f_info.name = name 
            f_info.data_type = datatype
            f_info.is_index = is_index 
            self.tables_attr[self.using_table_name].AddField(f_info)
            return True
        return False
   

    def AddVectorField(self, name, datatype, is_index, dimension, store_type, store_param, has_source):
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


    def CheckAddField(self, awadb_field, fields_type, field_no, field_name, field_value, has_field_name):
        field_type = self.__FieldCheck(field_no, field_name, field_value, fields_type)

        is_index = False
        if not self.tables_fields_check[self.using_table_name] and has_field_name:
            if not self.tables_have_obvious_primary_key[self.using_table_name] and field_name.startswith('@'):
                self.tables_have_obvious_primary_key[self.using_table_name] = True
                self.tables_primary_key_fid_no[self.using_table_name] = field_no
            if field_name.startswith('!'):
                is_index = True

        awadb_field.name = field_name 
        if field_type == FieldDataType.INT:
            awadb_field.value = field_value.to_bytes(4, 'little') 
            awadb_field.datatype = awa.DataType.INT
            self.AddField(field_name, awadb_field.datatype, is_index)
        elif field_type == FieldDataType.FLOAT: 
            awadb_field.value = struct.pack('<f', field_value)
            awadb_field.datatype = awa.DataType.FLOAT
            self.AddField(field_name, awadb_field.datatype, is_index)
        elif field_type == FieldDataType.STRING:
            awadb_field.value = field_value
            awadb_field.datatype = awa.DataType.STRING
            self.AddField(field_name, awadb_field.datatype, is_index)
 
        
        elif field_type == FieldDataType.VECTOR:
            if (type(field_value).__name__ == 'ndarray'):
                awadb_field.value = field_value.tobytes()
            else:
                vec_value = np.array(field_value, dtype = np.dtype('float32'))
                awadb_field.value = vec_value.tobytes()

            awadb_field.datatype = awa.DataType.VECTOR 
            self.AddVectorField(field_name, awadb_field.datatype, True,
                len(field_value), 'Mmap', '{"cache_size" : 1000}',   False)
            self.tables_vector_field_name[self.using_table_name] = field_name


    def Delete(self, key_id_of_doc):
        if self.using_table_name == '' or key_id_of_doc == '':
            print('Please specify table name and primary key of the table!')
            return False

        return awa.Delete(self.using_table_engine, key_id_of_doc)


    def Get(self, key_id_of_doc):
        if self.using_table_name == '' or key_id_of_doc == '':
            print('Please specify the primary key of the current table!')
            return False
        doc = awa.Doc() 

        awa.GetDoc(self.using_table_engine, key_id_of_doc, doc)

        doc_detail = {}
        doc_detail['key'] = doc.Key()
        for field in doc.TableFields():
            if field.datatype == awa.DataType.INT:
                int_value = struct.unpack("<i", bytearray(field.value, encoding="utf-8"))[0] 
                doc_detail[field.name] = int_value
            elif field.datatype == awa.DataType.FLOAT:
                float_value = struct.unpack("<f4", field.value)[0]
                doc_detail[field.name] = float_value
            elif field.datatype == awa.DataType.STRING:
                doc_detail[field.name] = field.value 
            elif field.datatype == awa.DataType.VECTOR:
                vec_data = awa.FloatVec()
                ret = field.GetVecData(vec_data)
                if vec_data.__len__() == 0:
                    print('Get vector data error!')
                    break
                vec_result = [] 
                for each_vec_data in vec_data:
                    vec_result.append(each_vec_data)

                doc_detail[field.name] = vec_result 

        for field in doc.VectorFields():
            if field.datatype == awa.DataType.VECTOR:
                vec_data = awa.FloatVec()
                ret = field.GetVecData(vec_data)
                if vec_data.__len__() == 0:
                    print('Get vector data error!')
                    break
                vec_result = [] 
                for each_vec_data in vec_data:
                    vec_result.append(each_vec_data)

                doc_detail[field.name] = vec_result 

        return doc_detail


    def __ProcessTextEmbedding(self, doc):
        field_no = 0 
        for field in doc:
            if (not self.tables_fields_check[self.using_table_name]) and type(field).__name__=='dict':
                for key in field:
                    if key == 'embedding_text':
                        from awadb import llm_embedding
                        self.llm = llm_embedding.LLMEmbedding()

                        doc.append(self.llm.Embedding(field[key]))
                        self.tables_embedding_text_fid_no[self.using_table_name] = field_no
            else:
                if self.using_table_name in self.tables_embedding_text_fid_no and field_no == self.tables_embedding_text_fid_no[self.using_table_name]:
                    field_value = field 
                    if type(field).__name__ == 'dict':
                        if 'embedding_text' in field:
                            field_value = field['embedding_text']
                        else:
                            continue
                    doc.append(self.llm.Embedding(field_value))
                    
            field_no = field_no + 1



    '''
    primary_key : format @name
    is_index :  format !province
    '''
    def Add(self, doc):
        if not isinstance(doc, list):
            error_msg = Exception("Incorrect argument, list type is needed for Add!!!")
            raise error_msg

        if not self.tables_fields_check[self.using_table_name]:
            if (self.using_table_name == ''):
                print("Please specify your table name!")
                return False 

            self.tables_attr[self.using_table_name] = awa.TableInfo()
            self.tables_attr[self.using_table_name].SetName(self.using_table_name)
   
        self.__ProcessTextEmbedding(doc)

        ret = True 
        field_no = 0
        fields_type = {}
        fields_names = {}
        
        awadb_doc = awa.Doc()
       
        for field in doc:
            if (type(field).__name__=='dict'):
                for key in field:
                    awadb_field = awa.Field()
                    self.CheckAddField(awadb_field, fields_type, field_no, key, field[key], True)        
                    fields_names[key] = field_no 
                    awadb_doc.AddField(awadb_field)

            else:
                # solve all kinds of situations
                awadb_field = awa.Field()

                field_name = ''
                if not self.tables_fields_check[self.using_table_name]:
                    field_name = "Field@" + str(field_no)
                else:
                    #todo : not need to traverse
                    for f_name in self.tables_fields_names[self.using_table_name]:
                        if self.tables_fields_names[self.using_table_name][f_name] == field_no:
                            field_name = f_name

                self.CheckAddField(awadb_field, fields_type, field_no, field_name, field, False) 
                fields_names[field_name] = field_no
               
                awadb_doc.AddField(awadb_field)

            field_no = field_no + 1


        if not self.tables_have_obvious_primary_key[self.using_table_name]:
            fid = awa.Field()
            fid.name = self.key_confirmed_name
            fid.value = str(self.tables_doc_count[self.using_table_name])
            fid.datatype = awa.DataType.STRING
            awadb_doc.SetKey(fid.value)
            awadb_doc.AddField(fid)
            self.__FieldCheck(field_no, fid.name, fid.value, fields_type)
            self.tables_primary_key_fid_no[self.using_table_name] = field_no
           

        if (not self.tables_fields_check[self.using_table_name]):
            self.tables_attr[self.using_table_name].SetIndexingSize(10000)
            self.tables_attr[self.using_table_name].SetRetrievalType('IVFPQ')
            self.tables_attr[self.using_table_name].SetRetrievalParam('{"ncentroids" : 256, "nsubvector" : 16}')
            
            self.tables_fields_type[self.using_table_name] = fields_type
            
            if not self.tables_have_obvious_primary_key[self.using_table_name]:
                self.AddField(self.key_confirmed_name, awa.DataType.STRING, True)
                fields_names[self.key_confirmed_name] = field_no 
            self.tables_fields_names[self.using_table_name] = fields_names

            if not awa.Create(self.using_table_engine, self.tables_attr[self.using_table_name]):
                return False

        if not awa.AddDoc(self.using_table_engine, self.using_table_name, awadb_doc):
            return False

        self.tables_doc_count[self.using_table_name] += 1
        
        if (not self.tables_fields_check[self.using_table_name]):   
            self.tables_fields_check[self.using_table_name] = True 
            self.Write()
        doc[:]=[]
        return True 

    def Search(self, query, topn, *filters):
        query_type = typeof(query) 
        
        show_results = []
        if query_type == FieldDataType.ERROR or query_type == FieldDataType.INT or query_type == FieldDataType.FLOAT:
            return show_results

        vec_query = awa.VectorQuery()
        vec_query.name = self.tables_vector_field_name[self.using_table_name]
        
        if query_type == FieldDataType.STRING:  # semantic text search
            embedding = self.llm.Embedding(query)
            vec_query.value = embedding.tobytes()

        elif query_type == FieldDataType.VECTOR:  #vector search 
            vec_value = np.array(query, dtype = np.dtype('float32'))
            vec_query.value = vec_value.tobytes()
        
        vec_query.min_score = -1 
        vec_query.max_score = 999999
            
        req = awa.Request()
        req.SetReqNum(1)
        req.AddVectorQuery(vec_query)
        req.SetTopN(topn)
        req.SetBruteForceSearch(1)
        req.SetL2Sqrt(True)

        response = awa.Response()
        fvec_names = awa.StrVec()
        for field_name in self.tables_fields_names[self.using_table_name]:
            if field_name == '_id':
                continue
            fvec_names.append(field_name)

        ret = awa.DoSearch(self.using_table_engine, req, response)
        response.PackResults(fvec_names)

        search_result_vec = response.Results()
        for search_result in search_result_vec:
            result_per_request = {}
            result_per_request['ResultSize'] = search_result.result_items.__len__()
              
            result_items_list = []
            items = search_result.result_items
            for item in items:
                i = 0
                l = item.names.__len__()
                item_detail = {}
                while i < l :
                    name = item.names[i]
             
                    f_type = self.tables_fields_type[self.using_table_name][self.tables_fields_names[self.using_table_name][name]]
                    if f_type == FieldDataType.INT:
                        int_value = struct.unpack("<i", bytearray(item.values[i], encoding="utf-8"))[0] 
                        item_detail[name] = int_value
                    elif f_type == FieldDataType.FLOAT:
                        float_value = struct.unpack("<f", item.values[i])[0] 
                        item_detail[name] = float_value
                    elif f_type == FieldDataType.STRING:
                        item_detail[name] = item.values[i] 
                    elif f_type == FieldDataType.VECTOR:
                        vec_data = awa.FloatVec()
                        item.GetVecData(name, vec_data)
                        vec_result = [] 
                        for each_vec_data in vec_data:
                            vec_result.append(each_vec_data)
                        #item_detail[name] = vec_result
                    i = i + 1
                item_detail['score'] = item.score
                result_items_list.append(item_detail)

            result_per_request['ResultItems'] = result_items_list
            show_results.append(result_per_request)
        return show_results



