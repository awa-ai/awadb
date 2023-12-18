/*
 *
 * Copyright 2023 AwaDB authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

#include "util/log.h"

#include "c_api/gamma_api.h"
#include "cpp_api/awadb_cpp_interface.h"
#include "awadb_async_call.h"

bool CreateCall::ProcessCreateRequest()  {
  if (!request_.has_db_name() || request_.db_name().empty())  return false; 
  bool status = true;
  std::string db_table_name = request_.db_name() + "/";
  if (request_.tables_meta_size() == 0)  return false;
  for (int i = 0; i < request_.tables_meta_size(); i++)  {
    awadb_grpc::TableMeta *table_meta_ptr = request_.mutable_tables_meta((int)i);
    // create table 
    if (!table_meta_ptr->name().empty())  {
      db_table_name += table_meta_ptr->name();

      bool is_init_engine = false;
      void *engine = nullptr;
      if (data_->engines_.find(db_table_name, engine))  {
	if (!engine)  {
	  LOG(ERROR)<<"table "<<table_meta_ptr->name()<<" engine in db "<<request_.db_name()<<" is empty!";
	  status = false;
	  continue;
	}
      }	else  {
        std::string data_dir = data_->data_dir_ + "/";
        if (!utils::isFolderExist(data_dir.c_str())) {
          mkdir(data_dir.c_str(), S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);
        }
        std::string data_db_dir = data_dir + request_.db_name();
        if (!utils::isFolderExist(data_db_dir.c_str())) {
          mkdir(data_db_dir.c_str(), S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);
        }

        data_dir += db_table_name;
        
        std::string log_dir = data_->log_dir_ + "/";
	log_dir += db_table_name;

        engine = Init(log_dir.c_str(), data_dir.c_str());
        if (!engine)  {
	  LOG(ERROR)<<"table "<<table_meta_ptr->name()<<" engine in db "
		  <<request_.db_name()<<" init error!";
          status = false;
	  continue;
	}
	is_init_engine = true;
      }	

      awadb::TableInfo table_info;
      table_info.SetName(table_meta_ptr->name());
      
      for (int j = 0; j < table_meta_ptr->fields_meta_size(); j++)  {
        awadb_grpc::FieldMeta *field_meta_ptr = table_meta_ptr->mutable_fields_meta((int)j);
        awadb::FieldInfo field_info;
        field_info.name = field_meta_ptr->name();
	bool is_vector_data = false;
	switch (field_meta_ptr->type())  {
	  case awadb_grpc::FieldType::INT:  {
	    field_info.data_type = awadb::DataType::INT;
	    break;
	  }
	  
	  case awadb_grpc::FieldType::LONG:  {
	    field_info.data_type = awadb::DataType::LONG;
	    break;
	  }
	  
	  case awadb_grpc::FieldType::FLOAT:  {
	    field_info.data_type = awadb::DataType::FLOAT;
	    break;
	  }
	    
	  case awadb_grpc::FieldType::DOUBLE:  {
	    field_info.data_type = awadb::DataType::DOUBLE;
	    break;
	  }
	     
	  case awadb_grpc::FieldType::STRING:  {
            field_info.data_type = awadb::DataType::STRING;
	    break;
	  }
	     
	  case awadb_grpc::FieldType::VECTOR:  {
            is_vector_data = true;
	    awadb::VectorInfo vec_info;
	    vec_info.name = field_meta_ptr->name();
	    if (field_meta_ptr->vec_meta().data_type() == awadb_grpc::FieldType::INT)  {
	      vec_info.data_type = awadb::DataType::INT;  
	    }  else if (field_meta_ptr->vec_meta().data_type() == awadb_grpc::FieldType::LONG)  {
	      vec_info.data_type = awadb::DataType::LONG; 

            }  else if (field_meta_ptr->vec_meta().data_type() == awadb_grpc::FieldType::FLOAT)  {
	      vec_info.data_type = awadb::DataType::FLOAT; 
	    }  else if (field_meta_ptr->vec_meta().data_type() == awadb_grpc::FieldType::DOUBLE)  {
	      vec_info.data_type = awadb::DataType::DOUBLE; 
	    }
	    vec_info.is_index = field_meta_ptr->is_index(); 
	    vec_info.dimension = field_meta_ptr->vec_meta().dimension(); 
	    vec_info.store_type = field_meta_ptr->vec_meta().store_type();
	    vec_info.store_param = field_meta_ptr->vec_meta().store_param();
	    vec_info.has_source = field_meta_ptr->vec_meta().has_source(); 
	    table_info.AddVectorInfo(vec_info);
	    break;
	  }
	     
	  case awadb_grpc::FieldType::MULTI_STRING:  {
	    field_info.data_type = awadb::DataType::MULTI_STRING;
	    break;
	  }
	  default: { break; }
	} 
      
        if (is_vector_data) continue;	

	field_info.is_index = field_meta_ptr->is_index();
        table_info.AddField(field_info);
      }

      table_info.SetIndexingSize(10000);
      table_info.SetRetrievalType("IVFPQ");
      table_info.SetRetrievalParam("{\"ncentroids\" : 256, \"nsubvector\" : 16}");

      status = Create(engine, table_info);

      if (is_init_engine)  data_->engines_.insert(db_table_name, engine);
    }
  }
  return status; 
}

void CreateCall::Proceed() {
  if (status_ == CREATE) {
    // Make this instance progress to the PROCESS state.
    status_ = PROCESS;

    // As part of the initial CREATE state, we *request* that the system
    // start processing SayHello requests. In this request, "this" acts are
    // the tag uniquely identifying the request (so that different CallData
    // instances can serve different requests concurrently), in this case
    // the memory address of this CallData instance.
    data_->service_->RequestCreate(&ctx_, &request_, &responder_, data_->cq_, data_->cq_,
                   this);
  } else if (status_ == PROCESS) {
    // Spawn a new CallData instance to serve new clients while we process
    // the one for this CallData. The instance will deallocate itself as
    // part of its FINISH state.
    new CreateCall(data_);

    bool ret = ProcessCreateRequest();

    if (ret)  {
      reply_.set_code(awadb_grpc::OK);
    }  else  {
      reply_.set_code(awadb_grpc::INTERNAL_ERROR);
    }

    // And we are done! Let the gRPC runtime know we've finished, using the
    // memory address of this instance as the uniquely identifying tag for
    // the event.
    status_ = FINISH;
    responder_.Finish(reply_, Status::OK, this);
  } else {
    GPR_ASSERT(status_ == FINISH);
    // Once in the FINISH state, deallocate ourselves (CallData).
    delete this;
  }
}

bool CheckTableCall::ProcessCheckTableRequest()  {
  if (!request_.has_db_name() || request_.db_name().empty() ||
      !request_.has_table_name() || request_.table_name().empty())  return false; 
  bool status = false;
  std::string db_table_name = request_.db_name() + "/";
  db_table_name += request_.table_name();

  void *engine = nullptr;
  if (data_->engines_.find(db_table_name, engine)) {
    if (!engine)  {
      LOG(ERROR)<<"table "<<request_.table_name()<<" engine in db "<<request_.db_name()<<" is empty!";
    }
    status = true;
  }
  if (!status)  {
    return status;
  }

  std::vector<awadb::FieldInfo> scalar_fields;
  std::vector<awadb::VectorInfo> vector_fields;
  GetFieldsInfo(engine, scalar_fields, vector_fields);

  awadb_grpc::DBMeta *exist_table_ptr = reply_.mutable_exist_table(); 
  //awadb_grpc::DBMeta db_meta;
  exist_table_ptr->set_db_name(request_.db_name());

  awadb_grpc::TableMeta *table_meta = exist_table_ptr->add_tables_meta();

  table_meta->set_name(request_.table_name());

  for (auto &iter: scalar_fields)  {
    awadb_grpc::FieldMeta *field_meta = table_meta->add_fields_meta();
    field_meta->set_name(iter.name);
    switch (iter.data_type)  {
      case awadb::DataType::INT: {
        field_meta->set_type(awadb_grpc::INT);		
        break;	
      }
      case awadb::DataType::LONG: {
	field_meta->set_type(awadb_grpc::LONG); 
        break; 
      }
      case awadb::DataType::FLOAT: {
	field_meta->set_type(awadb_grpc::FLOAT); 
        break; 
      }
      case awadb::DataType::DOUBLE: {
	field_meta->set_type(awadb_grpc::DOUBLE); 
        break; 
      }
      case awadb::DataType::STRING: {
	field_meta->set_type(awadb_grpc::STRING); 
        break; 
      }
      case awadb::DataType::MULTI_STRING: {
	field_meta->set_type(awadb_grpc::MULTI_STRING); 
        break; 
      }
      default: {
	break;
      }
    }
    field_meta->set_is_index(iter.is_index); 
  }

  for (auto &iter: vector_fields)  {
    awadb_grpc::FieldMeta *field_meta = table_meta->add_fields_meta();
    field_meta->set_name(iter.name);
    field_meta->set_is_index(iter.is_index);
    field_meta->set_type(awadb_grpc::VECTOR);

    awadb_grpc::VectorMeta *vector_meta = field_meta->mutable_vec_meta();
    vector_meta->set_dimension(iter.dimension); 

    switch (iter.data_type)  {
      case awadb::DataType::INT: {
        vector_meta->set_data_type(awadb_grpc::INT);		
        break;
      }
      case awadb::DataType::LONG: {
	vector_meta->set_data_type(awadb_grpc::LONG); 
        break;
      }
      case awadb::DataType::FLOAT: {
	vector_meta->set_data_type(awadb_grpc::FLOAT); 
        break;
      }
      case awadb::DataType::DOUBLE: {
	vector_meta->set_data_type(awadb_grpc::DOUBLE); 
        break;
      }
      default: {
	break;
      }
    }
  }

  return true; 
}


void CheckTableCall::Proceed() {
  if (status_ == CREATE) {
    // Make this instance progress to the PROCESS state.
    status_ = PROCESS;

    // As part of the initial CREATE state, we *request* that the system
    // start processing SayHello requests. In this request, "this" acts are
    // the tag uniquely identifying the request (so that different CallData
    // instances can serve different requests concurrently), in this case
    // the memory address of this CallData instance.
    data_->service_->RequestCheckTable(&ctx_, &request_, &responder_, data_->cq_, data_->cq_,
          this);
  } else if (status_ == PROCESS) {
    // Spawn a new CallData instance to serve new clients while we process
    // the one for this CallData. The instance will deallocate itself as
    // part of its FINISH state.
    new CheckTableCall(data_);

    // The actual processing.
    bool ret = ProcessCheckTableRequest();

    if (ret)  {
      reply_.set_is_existed(true);
    }  else  {
      reply_.set_is_existed(false);
    }

    // And we are done! Let the gRPC runtime know we've finished, using the
    // memory address of this instance as the uniquely identifying tag for
    // the event.
    status_ = FINISH;
    responder_.Finish(reply_, Status::OK, this);
  } else {
    GPR_ASSERT(status_ == FINISH);
    // Once in the FINISH state, deallocate ourselves (CallData).
    delete this;
  }
}


bool AddFieldsCall::ProcessAddFieldsRequest() {
  if (!request_.has_db_name() || request_.db_name().empty())  return false; 
  bool status = true; 
  std::string db_table_name = request_.db_name() + "/";
  for (int i = 0; i < request_.tables_meta_size(); i++)  {
    awadb_grpc::TableMeta *table_meta_ptr = request_.mutable_tables_meta((int)i);
    if (table_meta_ptr->has_name() && !table_meta_ptr->name().empty())  {
      db_table_name += table_meta_ptr->name();

      void *engine = nullptr;
      if (data_->engines_.find(db_table_name, engine))  {
	if (!engine)  {
	  LOG(ERROR)<<"table "<<table_meta_ptr->name()
		  <<" engine in db "<<request_.db_name()<<" is empty!";
	  status = false;
	  continue; 
	}  
      }  else  {
        return false;
      }

      for (int j = 0; j < table_meta_ptr->fields_meta_size(); j++)  {
        awadb_grpc::FieldMeta *field_meta_ptr = table_meta_ptr->mutable_fields_meta((int)j);
        awadb::FieldInfo field_info;
        field_info.name = field_meta_ptr->name();
	bool is_vector_data = false;
	switch (field_meta_ptr->type())  {
	  case awadb_grpc::FieldType::INT:  {
	    field_info.data_type = awadb::DataType::INT;
	    break;
	  }
	  
	  case awadb_grpc::FieldType::LONG:  {
	    field_info.data_type = awadb::DataType::LONG;
	    break;
	  }
	  
	  case awadb_grpc::FieldType::FLOAT:  {
	    field_info.data_type = awadb::DataType::FLOAT;
	    break;
	  }
	    
	  case awadb_grpc::FieldType::DOUBLE:  {
	    field_info.data_type = awadb::DataType::DOUBLE;
	    break;
	  }
	     
	  case awadb_grpc::FieldType::STRING:  {
            field_info.data_type = awadb::DataType::STRING;
	    break;
	  }
	     
	  case awadb_grpc::FieldType::VECTOR:  {
            is_vector_data = true;
	    break;
	  }
	     
	  case awadb_grpc::FieldType::MULTI_STRING:  {
	    field_info.data_type = awadb::DataType::MULTI_STRING;
	    break;
	  }
	  default: { break; }
	}
       
        if (is_vector_data)  continue;

	field_info.is_index = field_meta_ptr->is_index();
	status = AddNewField(engine, field_info);
      }
    }
  }
  return status;
}


void AddFieldsCall::Proceed() {
  if (status_ == CREATE) {
    // Make this instance progress to the PROCESS state.
    status_ = PROCESS;

    // As part of the initial CREATE state, we *request* that the system
    // start processing SayHello requests. In this request, "this" acts are
    // the tag uniquely identifying the request (so that different CallData
    // instances can serve different requests concurrently), in this case
    // the memory address of this CallData instance.
    data_->service_->RequestAddFields(&ctx_, &request_, &responder_, data_->cq_, data_->cq_,
          this);
  } else if (status_ == PROCESS) {
    // Spawn a new CallData instance to serve new clients while we process
    // the one for this CallData. The instance will deallocate itself as
    // part of its FINISH state.
    new AddFieldsCall(data_);

    // The actual processing.
    bool ret = ProcessAddFieldsRequest();

    if (ret)  {
      reply_.set_code(awadb_grpc::OK);
    }  else  {
      reply_.set_code(awadb_grpc::INTERNAL_ERROR);
    }

    // And we are done! Let the gRPC runtime know we've finished, using the
    // memory address of this instance as the uniquely identifying tag for
    // the event.
    status_ = FINISH;
    responder_.Finish(reply_, Status::OK, this);
  } else {
    GPR_ASSERT(status_ == FINISH);
    // Once in the FINISH state, deallocate ourselves (CallData).
    delete this;
  }
}

bool AddOrUpdateCall::ProcessAddOrUpdateRequest()  {
  if (!request_.has_db_name() || request_.db_name().empty() ||
      !request_.has_table_name() || request_.table_name().empty())  return false; 
  bool status = false; 
  std::string db_table_name = request_.db_name() + "/";
  db_table_name += request_.table_name();

  void *engine = nullptr;
  if (data_->engines_.find(db_table_name, engine))  {
    if (!engine)  {
      LOG(ERROR)<<"table "<<request_.table_name()<<" engine in db "<<request_.db_name()<<" is empty!";
      return false; 
    }
    status = true;
    awadb::Docs batch_docs;
    for (int i = 0; i < request_.docs_size(); i++)  {
      awadb::Doc doc;
      awadb_grpc::Document *doc_ptr = request_.mutable_docs((int)i);
      if (!doc_ptr->has_id())  {
        continue;
      }
      doc.SetKey(doc_ptr->id());
      for (int j = 0; j < doc_ptr->fields_size(); j++)  {
	awadb_grpc::Field *field_ptr = doc_ptr->mutable_fields(j);
	if (!field_ptr->has_name() || field_ptr->name().empty())  continue;
        awadb::Field field;
	field.name = field_ptr->name();	
	field.value = field_ptr->value();
	switch (field_ptr->type())  {
	  case awadb_grpc::FieldType::INT: {
	    field.datatype = awadb::DataType::INT; 
	    int int_value = 0;
	    memcpy((void *)&int_value, (void *)field.value.c_str(), sizeof(int));
	    break; 
	  }
	  case awadb_grpc::FieldType::LONG:  {
	    field.datatype = awadb::DataType::LONG;
	    break; 
	  }
	  case awadb_grpc::FieldType::FLOAT:  {
	    field.datatype = awadb::DataType::FLOAT;
	    break;
	  }
	  case awadb_grpc::FieldType::DOUBLE:  {
	    field.datatype = awadb::DataType::DOUBLE; 
	    break; 
	  }
	  case awadb_grpc::FieldType::STRING:  {
            field.datatype = awadb::DataType::STRING;
	    break;
	  }
	  case awadb_grpc::FieldType::MULTI_STRING:  {
	    field.datatype = awadb::DataType::MULTI_STRING;
	    break; 
	  }
	  case awadb_grpc::FieldType::VECTOR:  {
	    field.datatype = awadb::DataType::VECTOR;
	    break; 
	  }
	  default:  {
	    break;
          }
	}
	if (field_ptr->has_source())  field.source = field_ptr->source();
        if (field.datatype == awadb::DataType::MULTI_STRING)  {
          for (int k = 0; k < field_ptr->mul_str_value_size(); k++)  {
	    field.mul_str_value.push_back(field_ptr->mul_str_value(k));
	  }
	}	
	doc.AddField(field);
      }  
      
      batch_docs.AddDoc(doc); 
    }
    status = AddDocs(engine, batch_docs); 
  }  else  {
    LOG(ERROR)<<"table "<<request_.table_name()<<" engine in db "<<request_.db_name()<<" not exist!";
  }
  return status;
}

void AddOrUpdateCall::Proceed() {
  if (status_ == CREATE) {
    // Make this instance progress to the PROCESS state.
    status_ = PROCESS;

    // As part of the initial CREATE state, we *request* that the system
    // start processing SayHello requests. In this request, "this" acts are
    // the tag uniquely identifying the request (so that different CallData
    // instances can serve different requests concurrently), in this case
    // the memory address of this CallData instance.
    data_->service_->RequestAddOrUpdate(&ctx_, &request_, &responder_, data_->cq_, data_->cq_,
                                  this);
  } else if (status_ == PROCESS) {
    // Spawn a new CallData instance to serve new clients while we process
    // the one for this CallData. The instance will deallocate itself as
    // part of its FINISH state.
    new AddOrUpdateCall(data_);

    // The actual processing.
    bool ret = ProcessAddOrUpdateRequest();

    if (ret)  {
      reply_.set_code(awadb_grpc::OK);
    }  else  {
      reply_.set_code(awadb_grpc::INTERNAL_ERROR);
    }

    // And we are done! Let the gRPC runtime know we've finished, using the
    // memory address of this instance as the uniquely identifying tag for
    // the event.
    status_ = FINISH;
    responder_.Finish(reply_, Status::OK, this);
  } else {
    GPR_ASSERT(status_ == FINISH);
    // Once in the FINISH state, deallocate ourselves (CallData).
    delete this;
  } 
}

void GetCall::AddFields(
  awadb_grpc::Document *doc,
  std::vector<awadb::Field> &fields)  {
  for (size_t i = 0; i < fields.size(); i++)  {
    awadb_grpc::Field *field = doc->add_fields();
    field->set_name(fields[i].name);
    field->set_value(fields[i].value);
    field->set_source(fields[i].source);
    bool is_mul_str = false; 
    switch (fields[i].datatype)  {
      case awadb::DataType::INT: {
        field->set_type(awadb_grpc::FieldType::INT); 
        break;
      }
      case awadb::DataType::LONG: {
        field->set_type(awadb_grpc::FieldType::LONG); 
        break;
      }
      case awadb::DataType::FLOAT: {
        field->set_type(awadb_grpc::FieldType::FLOAT); 
        break;
      }
      case awadb::DataType::DOUBLE: {
	field->set_type(awadb_grpc::FieldType::DOUBLE); 
	break; 
      }
      case awadb::DataType::STRING: {
        field->set_type(awadb_grpc::FieldType::STRING); 
        break; 
      }
      case awadb::DataType::MULTI_STRING: {
        field->set_type(awadb_grpc::FieldType::MULTI_STRING);
        is_mul_str = true;
        break;
      }
      case awadb::DataType::VECTOR: {
        field->set_type(awadb_grpc::FieldType::VECTOR);
        break; 
      }

      default: {
        break; 
      }
    }

    if (is_mul_str)  {
      for (size_t j = 0; j < fields[i].mul_str_value.size() ; j++)  {
        field->add_mul_str_value(fields[i].mul_str_value[j]);
      }	  
    }
  }
}

// now just support get ids
void GetCall::ProcessGetRequest()  {
  if (request_.db_name().empty() || request_.table_name().empty())  return; 
  std::string db_table_name = request_.db_name() + "/";
  db_table_name += request_.table_name();

  void *engine = nullptr;
  if (data_->engines_.find(db_table_name, engine))  {
    if (!engine)  {
      LOG(ERROR)<<"table "<<request_.table_name()<<" engine in db "<<request_.db_name()<<" is empty!";
      return;
    }
   
    awadb::Request request;
    for (size_t i = 0; i < request_.range_filters_size(); i++)  {
      awadb::RangeFilter range_filter;
      range_filter.field = (request_.mutable_range_filters(i))->field_name();
      range_filter.lower_value = (request_.mutable_range_filters(i))->lower_value();
      range_filter.upper_value = (request_.mutable_range_filters(i))->upper_value();
      range_filter.include_lower = (request_.mutable_range_filters(i))->include_lower();
      range_filter.include_upper = (request_.mutable_range_filters(i))->include_upper();

      request.AddRangeFilter(range_filter); 
    }

    for (size_t i = 0; i < request_.term_filters_size(); i++)  {
      awadb::TermFilter term_filter;
      term_filter.field = (request_.mutable_term_filters(i))->field_name();
      term_filter.value = (request_.mutable_term_filters(i))->value();
      term_filter.is_union = (request_.mutable_term_filters(i))->is_union();
      request.AddTermFilter(term_filter); 
    }  

    size_t request_ids_size = request_.ids_size();
    if (request_ids_size == 0)  {
      LOG(INFO)<<"Get ids set is empty!";
    }
    std::vector<std::string> ids;
    std::map<std::string, awadb::Doc> docs; 
    for (size_t i = 0; i < request_ids_size; i++)  {
      ids.push_back(request_.ids(i)); 
    }
    GetDocs(engine, ids, request, docs);

    reply_.set_db_name(request_.db_name());
    reply_.set_table_name(request_.table_name());
    for (auto &iter: docs)  {
      awadb_grpc::Document *doc = reply_.add_docs();
      std::vector<awadb::Field> &table_fields = iter.second.TableFields();
      AddFields(doc, table_fields);
      std::vector<awadb::Field> &vec_fields = iter.second.VectorFields();
      AddFields(doc, vec_fields);
      doc->set_id((iter.second).Key());
    }
  } else  {
    LOG(ERROR)<<"table "<<request_.table_name()<<" engine in db "<<request_.db_name()<<" not exist!";
  }
  return;
}

void GetCall::Proceed() {
  if (status_ == CREATE) {
    // Make this instance progress to the PROCESS state.
    status_ = PROCESS;

    // As part of the initial CREATE state, we *request* that the system
    // start processing SayHello requests. In this request, "this" acts are
    // the tag uniquely identifying the request (so that different CallData
    // instances can serve different requests concurrently), in this case
    // the memory address of this CallData instance.
    data_->service_->RequestGet(&ctx_, &request_, &responder_, data_->cq_, data_->cq_,
                                  this);
  } else if (status_ == PROCESS) {
    // Spawn a new CallData instance to serve new clients while we process
    // the one for this CallData. The instance will deallocate itself as
    // part of its FINISH state.
    new GetCall(data_);

    // The actual processing.
    ProcessGetRequest();
    
    // And we are done! Let the gRPC runtime know we've finished, using the
    // memory address of this instance as the uniquely identifying tag for
    // the event.
    status_ = FINISH;
    responder_.Finish(reply_, Status::OK, this);
  } else {
    GPR_ASSERT(status_ == FINISH);
    // Once in the FINISH state, deallocate ourselves (CallData).
    delete this;
  }
}

void SearchCall::ProcessSearchRequest()  {
  if (!request_.has_db_name() || request_.db_name().empty() ||
    !request_.has_table_name() || request_.table_name().empty())  return; 
  std::string db_table_name = request_.db_name() + "/";
  db_table_name += request_.table_name();

  void *engine = nullptr;
  if (data_->engines_.find(db_table_name, engine))  {
    if (!engine)  {
      LOG(ERROR)<<"table "<<request_.table_name()
	<<" engine in db "<<request_.db_name()<<" is empty!";
      return;
    }
   
    awadb::Request search_req;
    awadb::Response search_res;
    int vec_num = request_.vec_queries_size(); 
    if (vec_num > 0)  search_req.SetReqNum(vec_num); 
    for (int i = 0; i < vec_num; i++)  {
      awadb_grpc::VectorQuery *vec_query = request_.mutable_vec_queries(i);
      awadb::VectorQuery v_query;
      v_query.name = vec_query->field_name();
      v_query.value = vec_query->value();
      v_query.min_score = (double)vec_query->min_score();
      v_query.max_score = (double)vec_query->max_score();
      v_query.boost = vec_query->boost();
      v_query.has_boost = vec_query->is_boost() ? 1 : 0;
      v_query.retrieval_type = vec_query->retrieval_type(); 
      search_req.AddVectorQuery(v_query); 
    }

    if (vec_num > 1 && request_.has_mul_vec_logic_op())  {
      bool mul_vec_logic_op = true;
      if (request_.mul_vec_logic_op() == awadb_grpc::MultiVectorLogicOp::OR)  {
        mul_vec_logic_op = false;
      }
      search_req.SetMulVecLogicOp(mul_vec_logic_op); 
    }

    
    for (int i = 0; i < request_.page_text_queries_size(); i++)  {
      search_req.AddPageText(request_.page_text_queries(i));  
    }

    for (int i = 0; i < request_.term_filters_size(); i++)  {
      awadb::TermFilter t_filter;
      awadb_grpc::TermFilter * term_filter = request_.mutable_term_filters(i);
      t_filter.field = term_filter->field_name();
      t_filter.value = term_filter->value();
      t_filter.is_union = term_filter->is_union(); 
      search_req.AddTermFilter(t_filter);
    }

    for (int i = 0; i < request_.range_filters_size(); i++)  {
      awadb::RangeFilter r_filter;
      awadb_grpc::RangeFilter * range_filter = request_.mutable_range_filters(i);
      r_filter.field = range_filter->field_name();
      r_filter.lower_value = range_filter->lower_value();
      r_filter.upper_value = range_filter->upper_value();
      r_filter.include_lower = range_filter->include_lower();
      r_filter.include_upper = range_filter->include_upper();
      search_req.AddRangeFilter(r_filter);
    }
 
    search_req.SetMultiVectorRank(1);
    search_req.SetTopN(request_.topn());
    search_req.SetBruteForceSearch(request_.brute_force_search() ? 1 : 0);
    search_req.SetRetrievalParams(request_.retrieval_params());
    search_req.SetOnlineLogLevel(request_.online_log_level());
    
    if (request_.has_is_l2())  {
      search_req.SetMetricType(request_.is_l2());
    }

    int ret = DoSearch(engine, search_req, search_res);

    if (ret != 0)  {
      LOG(WARNING)<<"Search has problem! return value "<<ret;
    }

    std::vector<std::string> pack_fields;
    for (int i = 0; i < request_.pack_fields_size(); i++)  {
      pack_fields.push_back(request_.pack_fields(i));
    } 

    std::map<std::string, awadb::DataType> fields_type;
    GetFieldsType(engine, pack_fields, fields_type);   
    
    ret = search_res.PackResults(pack_fields);
    reply_.set_db_name(request_.db_name());
    reply_.set_table_name(request_.table_name());
    if (ret == 0)  {
      reply_.set_result_code(awadb_grpc::SearchResultCode::SUCCESS);
    }  else  {
      reply_.set_result_code(awadb_grpc::SearchResultCode::SEARCH_ERROR);
    }
    std::vector<awadb::SearchResult> &results = search_res.Results();
    for (size_t i = 0; i < results.size(); i++)  {
      awadb_grpc::SearchResult *result_ptr = reply_.add_results();
      result_ptr->set_total(results[i].total);
      if (!results[i].msg.empty())  {
	result_ptr->set_msg(results[i].msg);
      }
      int return_topn = request_.topn();
      LOG(ERROR)<<"result items size is "<<results[i].result_items.size();
      if ((size_t)return_topn > results[i].result_items.size())  return_topn = results[i].result_items.size();
      for (int j = 0; j < return_topn; j++)  {
        awadb_grpc::ResultItem *item_ptr = result_ptr->add_result_items();
	item_ptr->set_score((float)results[i].result_items[j].score);

        LOG(ERROR)<<"result score is "<<(float)results[i].result_items[j].score;
	awadb::ResultItem &item_tmp = results[i].result_items[j];
        for (size_t k = 0; k < item_tmp.names.size(); k++)  {
	  awadb_grpc::Field *new_field = item_ptr->add_fields();
          new_field->set_name(item_tmp.names[k]);
          new_field->set_value(item_tmp.values[k]);
	  if (fields_type.find(item_tmp.names[k]) != fields_type.end())  {
	    switch(fields_type[item_tmp.names[k]])  {
	      case awadb::DataType::INT:  {
	        new_field->set_type(awadb_grpc::FieldType::INT);
	        break; 
	      }
	      case awadb::DataType::LONG:  {
	        new_field->set_type(awadb_grpc::FieldType::LONG);	
	        break;	
	      }
	      case awadb::DataType::FLOAT:  {
	        new_field->set_type(awadb_grpc::FieldType::FLOAT);	
	        break;	
	      }
	      case awadb::DataType::DOUBLE:  {
	        new_field->set_type(awadb_grpc::FieldType::DOUBLE);	
		break;		 
              }
	      case awadb::DataType::STRING:  {
	        new_field->set_type(awadb_grpc::FieldType::STRING);
		break;		 
              }
	      case awadb::DataType::MULTI_STRING:  {
	        new_field->set_type(awadb_grpc::FieldType::MULTI_STRING);
		break;
              }
	      case awadb::DataType::VECTOR:  {
	        new_field->set_type(awadb_grpc::FieldType::VECTOR);
		break;		 
	      }
              default:  {
	        break; 
	      }
	    } 
	  }
	}	
      }
    }
  } else  {
    LOG(ERROR)<<"table "<<request_.table_name()<<" engine in db "<<request_.db_name()<<" not exist!";
  } 
  return;
}

void SearchCall::Proceed() {
  if (status_ == CREATE) {
    // Make this instance progress to the PROCESS state.
    status_ = PROCESS;

    // As part of the initial CREATE state, we *request* that the system
    // start processing SayHello requests. In this request, "this" acts are
    // the tag uniquely identifying the request (so that different CallData
    // instances can serve different requests concurrently), in this case
    // the memory address of this CallData instance.
    data_->service_->RequestSearch(&ctx_, &request_, &responder_, data_->cq_, data_->cq_,
                           this);
  } else if (status_ == PROCESS) {
    // Spawn a new CallData instance to serve new clients while we process
    // the one for this CallData. The instance will deallocate itself as
    // part of its FINISH state.
    new SearchCall(data_);

    // The actual processing.
    ProcessSearchRequest();
    // And we are done! Let the gRPC runtime know we've finished, using the
    // memory address of this instance as the uniquely identifying tag for
    // the event.
    status_ = FINISH;
    responder_.Finish(reply_, Status::OK, this);
  } else {
    GPR_ASSERT(status_ == FINISH);
    // Once in the FINISH state, deallocate ourselves (CallData).
    delete this;
  }
}

bool DeleteCall::ProcessDeleteRequest()  {
  bool status = false; 
  if (request_.db_name().empty() || request_.table_name().empty())  return status; 
  std::string db_table_name = request_.db_name() + "/";
  db_table_name += request_.table_name();

  void *engine = nullptr;
  if (data_->engines_.find(db_table_name, engine))  {
    if (!engine)  {
      LOG(ERROR)<<"table "<<request_.table_name()<<" engine in db "<<request_.db_name()<<" is empty!";
      return status;
    }
   
    awadb::Request request;
    for (size_t i = 0; i < request_.range_filters_size(); i++)  {
      awadb::RangeFilter range_filter;
      range_filter.field = (request_.mutable_range_filters(i))->field_name();
      range_filter.lower_value = (request_.mutable_range_filters(i))->lower_value();
      range_filter.upper_value = (request_.mutable_range_filters(i))->upper_value();
      range_filter.include_lower = (request_.mutable_range_filters(i))->include_lower();
      range_filter.include_upper = (request_.mutable_range_filters(i))->include_upper();

      request.AddRangeFilter(range_filter); 
    }

    for (size_t i = 0; i < request_.term_filters_size(); i++)  {
      awadb::TermFilter term_filter;
      term_filter.field = (request_.mutable_term_filters(i))->field_name();
      term_filter.value = (request_.mutable_term_filters(i))->value();
      term_filter.is_union = (request_.mutable_term_filters(i))->is_union();
      request.AddTermFilter(term_filter); 
    }  

    size_t request_ids_size = request_.ids_size();
    if (request_ids_size == 0)  {
      LOG(INFO)<<"Delete ids is empty!";
    }
    std::vector<std::string> ids;
    for (size_t i = 0; i < request_ids_size; i++)  {
      ids.push_back(request_.ids(i)); 
    }
    status = Delete(engine, ids, request);
     
  }  else  {
    LOG(ERROR)<<"table "<<request_.table_name()<<" engine in db "<<request_.db_name()<<" not exist!";
  }
  return status;
}

void DeleteCall::Proceed() {
  if (status_ == CREATE) {
    // Make this instance progress to the PROCESS state.
    status_ = PROCESS;

    // As part of the initial CREATE state, we *request* that the system
    // start processing SayHello requests. In this request, "this" acts are
    // the tag uniquely identifying the request (so that different CallData
    // instances can serve different requests concurrently), in this case
    // the memory address of this CallData instance.
    data_->service_->RequestDelete(&ctx_, &request_, &responder_, 
      data_->cq_, data_->cq_, this);
  } else if (status_ == PROCESS)  {
    new DeleteCall(data_);
    bool ret = ProcessDeleteRequest();  
    if (ret)  {
      reply_.set_code(awadb_grpc::OK);
    }  else  {
      reply_.set_code(awadb_grpc::INTERNAL_ERROR);
    }

    // And we are done! Let the gRPC runtime know we've finished, using the
    // memory address of this instance as the uniquely identifying tag for
    // the event.
    status_ = FINISH;
    responder_.Finish(reply_, Status::OK, this);
  } else {
     GPR_ASSERT(status_ == FINISH);
     // Once in the FINISH state, deallocate ourselves (CallData).
     delete this;
  }
}

