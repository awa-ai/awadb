/**
 * Copyright 2023 The AwaDB Authors.
 *
 * This source code is licensed under the Apache License, Version 2.0 license
 * found in the LICENSE file in the root directory of this source tree.
 */

#include "util/log.h" 
#include "docid_fields_mgr.h"


namespace tig_gamma  {

DocidFieldsMgr::DocidFieldsMgr()  {
  docid_fields_map_ = nullptr;
  capacity_ = 0;
  size_ = 0;
  field_id_bytes_ = sizeof(uint8_t);
  field_pos_bytes_ = sizeof(uint32_t);
  fields_size_ = 0;

  block_docs_num_ = 0;
  slot_str_size_ = 0;
  str_max_size_ = 0;
}

DocidFieldsMgr::~DocidFieldsMgr()  {
  Destroy(docid_fields_map_, size_, true);
  if (docid_fields_map_)  {
    for (size_t i = 0; i < size_; i++)  {
      if (docid_fields_map_[i])  {
        delete[] docid_fields_map_[i];
	docid_fields_map_[i] = nullptr;
      }
    }
    delete[] docid_fields_map_;
    docid_fields_map_ = nullptr; 
  }
}

void DocidFieldsMgr::Destroy(char ** &ptr, const uint32_t &size, bool destroy_all)  {
   if (ptr)  {
    if (destroy_all)  {
      for (uint32_t i = 0; i < size; i++)  {
        if (ptr[i])  {
          delete[] ptr[i];
	  ptr[i] = nullptr;
        }
      }
    }
    delete[] ptr;
    ptr = nullptr; 
  }
}


bool DocidFieldsMgr::Init(const uint32_t &block_docs_num,
  const uint32_t &slot_str_size,
  const uint32_t &str_max_size)  {
  block_docs_num_ = block_docs_num;
  slot_str_size_ = slot_str_size;
  str_max_size_ = str_max_size;
  docid_fields_map_ = new char *[block_docs_num_];
  
  for (uint32_t i = 0; i < block_docs_num_; i++)  {
    docid_fields_map_[i] = nullptr;
  }  
  capacity_ = block_docs_num_;
  return  docid_fields_map_ != nullptr ? true : false;
}


int DocidFieldsMgr::AddField(
  const FieldInfo &field_info,
  const uint8_t &fid)  {
  if (fid_name2id_.find(field_info.name) == fid_name2id_.end())  {
    fid_name2id_[field_info.name] = fid;
    fid_id2name_[fid] = field_info.name;
    fid_name2type_[field_info.name] = field_info.data_type;
    fid2index_[field_info.name] = field_info.is_index;
    if (field_info.data_type == DataType::INT ||
      field_info.data_type == DataType::LONG ||
      field_info.data_type == DataType::FLOAT ||
      field_info.data_type == DataType::DOUBLE)  {
      FixedFieldColumnData *fixed_field = new FixedFieldColumnData();
      if (!fixed_field->Init(block_docs_num_, field_info.data_type))  return -1;
      fixed_field_map_[field_info.name] = fixed_field;  
    }  else if (field_info.data_type == DataType::STRING) {
      StrFieldColumnData *str_field = new StrFieldColumnData();
      if (!str_field->Init(slot_str_size_, str_max_size_))  return -2; 
      str_field_map_[field_info.name] = str_field; 
    }  else if (field_info.data_type == DataType::MULTI_STRING) {
      MultiStrFieldColumnData *mul_str_field = new MultiStrFieldColumnData();
      if (!mul_str_field->Init(slot_str_size_, str_max_size_))  return -3; 
      mul_str_field_map_[field_info.name] = mul_str_field; 
    } 
    fields_size_++; 
  }  else  {
    LOG(INFO)<<"FIELD "<<field_info.name<<" already exists!";
  }

  return (int)fid;
}


int DocidFieldsMgr::Put(
  const uint32_t &docid,
  const std::vector<Field> &fields)  {
  
  std::vector<uint8_t> field_ids;
  std::vector<uint32_t> field_posids;
  
  for (uint32_t i = 0; i < fields.size(); i++)  { 
    if (fid_name2id_.find(fields[i].name) == fid_name2id_.end())  {
      LOG(ERROR)<<"field name "<<fields[i].name<<" should AddField first!";
      continue; 
    }


    uint32_t field_value_id = 0;
    if (fields[i].datatype == DataType::INT ||
      fields[i].datatype == DataType::LONG ||
      fields[i].datatype == DataType::FLOAT ||
      fields[i].datatype == DataType::DOUBLE)  {
      field_value_id = fixed_field_map_[fields[i].name]->GetCurMaxId();
      fixed_field_map_[fields[i].name]->Put(fields[i]);
    }  else if (fields[i].datatype == DataType::STRING)  {
      field_value_id = str_field_map_[fields[i].name]->GetCurMaxId();
      str_field_map_[fields[i].name]->Put(fields[i]);
    }  else if (fields[i].datatype == DataType::MULTI_STRING)  {
      field_value_id = mul_str_field_map_[fields[i].name]->GetCurMaxId(); 
      mul_str_field_map_[fields[i].name]->Put(fields[i]);
    }
    field_ids.push_back(fid_name2id_[fields[i].name]);
    field_posids.push_back(field_value_id);
  }

  return Put(docid, field_ids, field_posids);  
}

int DocidFieldsMgr::Find(
  const uint8_t &fid,
  const char *fid_values_ptr,
  const uint32_t &fids_size)  {
  if (fids_size == 0)  return -1;  
  uint32_t start = 0, end = fids_size - 1;
  do {
    uint8_t start_value = *((uint8_t *)fid_values_ptr + start);
    if  (start_value == fid)  {
      return start; 
    }  else if (start_value > fid)  {
      return -2;
    }  else {
      uint8_t end_value = *((uint8_t *)fid_values_ptr + end);
      if (end_value == fid)  return end;
      else if (fid > end_value)  return -3;
      else  {
        uint32_t mid = (start + end) >> 1;
	uint8_t mid_value = *((uint8_t *)fid_values_ptr + mid);
	if (fid == mid_value)  return mid;
	else if (fid > mid_value)  start = mid + 1;
	else  end = mid - 1;
      } 
    }
  }  while(start < end);

  return -4;
}

int DocidFieldsMgr::Get(
  const uint32_t &docid,
  Field &field)  {
  if (docid >= size_)  return -1;
  uint8_t fields_num = 0;
  if (!docid_fields_map_ || !docid_fields_map_[docid])  return -2; 
  memcpy((void *)&fields_num, (void *)docid_fields_map_[docid], field_id_bytes_);
  char *offset = docid_fields_map_[docid] + field_id_bytes_;

  if (fid_name2id_.find(field.name) == fid_name2id_.end())  {
    return -3;
  }
  uint8_t field_id = fid_name2id_[field.name];
  field.datatype = fid_name2type_[field.name];
  if (!offset)  {
     LOG(ERROR)<<"offset is nullptr";
  }
  int id_pos = Find(field_id, offset, (uint32_t)fields_num);
  if (id_pos < 0)  {
    return -4;
  }
  uint32_t id = *((uint32_t *)(docid_fields_map_[docid] + field_id_bytes_ + (uint32_t)fields_num * field_id_bytes_) + id_pos); 

  if (field.datatype == DataType::INT ||
    field.datatype == DataType::LONG ||
    field.datatype == DataType::FLOAT ||
    field.datatype == DataType::DOUBLE)  {
    fixed_field_map_[field.name]->Get(id, field); 
  }  else if (field.datatype == DataType::STRING)  {
    str_field_map_[field.name]->Get(id, field);   
  }  else if (field.datatype == DataType::MULTI_STRING)  {
    mul_str_field_map_[field.name]->Get(id, field); 
  }
  return 0;
}

int DocidFieldsMgr::Get(
  const uint32_t &docid,
  std::vector<Field> &fields)  {

  if (docid >= size_)  return -1;
  uint8_t fields_num = 0;
  memcpy((void *)&fields_num, (void *)docid_fields_map_[docid], field_id_bytes_);
  char *offset = docid_fields_map_[docid] + field_id_bytes_;

  std::vector<std::vector<Field>::iterator> erasing_iterators;
  std::vector<Field>::iterator iter = fields.begin();
  for (; iter != fields.end(); iter++)  {
    if (fid_name2id_.find(iter->name) == fid_name2id_.end())  {
      erasing_iterators.push_back(iter);
    }
    uint8_t field_id = fid_name2id_[iter->name];
    int id_pos = Find(field_id, offset, (uint32_t)fields_num);
    if (id_pos < 0)  {
      erasing_iterators.push_back(iter);
    }
    uint32_t id = *((uint32_t *)(docid_fields_map_[docid] + field_id_bytes_ + fields_num * field_id_bytes_) + id_pos); 

    iter->datatype = fid_name2type_[iter->name]; 
    if (iter->datatype == DataType::INT ||
      iter->datatype == DataType::LONG ||
      iter->datatype == DataType::FLOAT ||
      iter->datatype == DataType::DOUBLE)  {
      fixed_field_map_[iter->name]->Get(id, *iter); 
    }  else if (iter->datatype == DataType::STRING)  {
      str_field_map_[iter->name]->Get(id, *iter);   
    }  else if (iter->datatype == DataType::MULTI_STRING)  {
      mul_str_field_map_[iter->name]->Get(id, *iter); 
    }
  }

  for (uint32_t i = erasing_iterators.size() - 1; i >= 0; i--)  {
    fields.erase(erasing_iterators[i]); 
  }

  return 0;
}

int DocidFieldsMgr::GetAllFields(
  const uint32_t&docid,
  std::vector<Field> &fields)  {

  for (auto &iter: fid_name2id_)  {
    Field field; 
    field.name = iter.first; 
    field.datatype = fid_name2type_[iter.first];  
    if (Get(docid, field) < 0)  continue;
    fields.push_back(field);
  }
  return 0;
}



int DocidFieldsMgr::Put(
  const uint32_t &docid,
  const std::vector<uint8_t> &field_ids,
  const std::vector<uint32_t> &field_posids)  {
  if (field_ids.size() != field_posids.size())  return -1; 
  if (docid >= capacity_)  {
    uint32_t original_capacity = capacity_;
    capacity_ *= 2;
    char **extend = new char *[capacity_];
    if (!extend)  return -2;
    for (uint32_t i = 0; i < capacity_; i++)  {
      if (i < size_)  extend[i] = docid_fields_map_[i];
      else  extend[i] = nullptr;
    }
    
    Destroy(docid_fields_map_, original_capacity, false);
    docid_fields_map_ = extend; 
  } 
 
  uint8_t fields_num = (uint8_t)field_ids.size();
  uint32_t bytes_length = fields_num *(field_id_bytes_ + field_pos_bytes_) + field_id_bytes_;
  if (docid_fields_map_[docid] != nullptr)  {
    delete docid_fields_map_[docid];
    docid_fields_map_[docid] = nullptr;
  } 
  docid_fields_map_[docid] = new char[bytes_length];
  memcpy((void *)docid_fields_map_[docid], (void *)&fields_num, field_id_bytes_);
  char *offset = docid_fields_map_[docid] + field_id_bytes_;
  memcpy((void *)offset, (void *)(field_ids.data()), fields_num * field_id_bytes_);
  offset += field_id_bytes_ * fields_num;
  memcpy((void *)offset, (void *)field_posids.data(), fields_num * field_pos_bytes_);
  size_++; 

  return 0;
}

}

