/**
 * Copyright 2023 The AwaDB Authors.
 *
 * This source code is licensed under the Apache License, Version 2.0 license
 * found in the LICENSE file in the root directory of this source tree.
 */

#include <stdio.h>
#include "util/log.h" 
#include "docid_fields_mgr.h"


namespace tig_gamma  {

DocidFieldsMgr::DocidFieldsMgr()  {
  docid_fields_map_ = nullptr;
  capacity_ = 0;
  size_ = 0;
  last_flushed_size_ = 0;
  field_id_bytes_ = sizeof(uint8_t);
  field_pos_bytes_ = sizeof(uint32_t);
  fields_size_ = 0;

  block_docs_num_ = 0;
}

DocidFieldsMgr::~DocidFieldsMgr()  {
  Destroy(docid_fields_map_, size_, true);
  flush_thread_.join();
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
  //const uint32_t &slot_str_size,
  //const uint32_t &str_max_size)  {
  const std::string &root_path)  {
  block_docs_num_ = block_docs_num;
  //slot_str_size_ = slot_str_size;
  //str_max_size_ = str_max_size;
  root_path_ = root_path;
 
  persist_file_ = root_path_ + "/docid_fields.mgr";

  bool ret = false;
  if (utils::file_exist(persist_file_))  {
    ret = Load(persist_file_); 
  }  else  {
    docid_fields_map_ = new char *[block_docs_num_];
  
    for (uint32_t i = 0; i < block_docs_num_; i++)  {
      docid_fields_map_[i] = nullptr;
    }  
    capacity_ = block_docs_num_;
  }

  auto flush_op = std::bind(&DocidFieldsMgr::Flush, this);
  flush_thread_ = std::thread(flush_op);
  return  ret ? true : (docid_fields_map_ != nullptr ? true : false);
}


void DocidFieldsMgr::Flush()  {
  while (true)  {
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    if (last_flushed_size_ < size_)  {
      Dump(persist_file_, last_flushed_size_);
    } 
  }  
}

int DocidFieldsMgr::AddField(
  const FieldInfo &field_info,
  const uint8_t &fid)  {
  if (fid_name2id_.find(field_info.name) == fid_name2id_.end())  {
    fid_name2id_[field_info.name] = fid;
    fid_id2name_[fid] = field_info.name;
    fid_name2type_[field_info.name] = field_info.data_type;
    fid2index_[field_info.name] = field_info.is_index;
    
    std::string path = root_path_ + "/" + field_info.name;
    if (field_info.data_type == DataType::INT ||
      field_info.data_type == DataType::LONG ||
      field_info.data_type == DataType::FLOAT ||
      field_info.data_type == DataType::DOUBLE)  {
      if (!utils::isFolderExist(path.c_str())) {
	mkdir(path.c_str(), S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);
      }

      FixedFieldColumnData *fixed_field = new FixedFieldColumnData(field_info.name);
      if (!fixed_field->Init(path, field_info.data_type))  return -1;
      fixed_field_map_[field_info.name] = fixed_field;
    }  else if (field_info.data_type == DataType::STRING) {
      
      if (!utils::isFolderExist(path.c_str())) {
	mkdir(path.c_str(), S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);
      }

      StrFieldColumnData *str_field = new StrFieldColumnData(field_info.name);
      if (!str_field->Init(path))  return -2; 
      str_field_map_[field_info.name] = str_field; 
    }  else if (field_info.data_type == DataType::MULTI_STRING) {
      if (!utils::isFolderExist(path.c_str())) {
	mkdir(path.c_str(), S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH);
      }    

      MultiStrFieldColumnData *mul_str_field = new MultiStrFieldColumnData(field_info.name);
      if (!mul_str_field->Init(path))  return -3; 
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
  //const std::vector<Field> &fields)  {
  std::vector<Field> &fields)  {
 
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
  if (!docid_fields_map_ || !docid_fields_map_[docid])  { return -2; } 
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
    LOG(ERROR)<<"id_pos is "<<id_pos;
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

int DocidFieldsMgr::GetAllFields(std::vector<FieldInfo> &fields)  {
  for (auto &iter: fid_name2type_)  {
    FieldInfo field;
    field.name = iter.first;
    field.data_type = iter.second;
    if (fid2index_.find(field.name) == fid2index_.end())  {
      field.is_index = false;
    }  else  {
      field.is_index = fid2index_[field.name];
    }
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

bool DocidFieldsMgr::Load(const std::string &file_path) {
  FILE *fp = fopen(file_path.c_str(), "rb");
  fread((void *)&capacity_, sizeof(uint32_t), 1, fp);
  fread((void *)&size_, sizeof(uint32_t), 1, fp);
  fread((void *)&fields_size_, sizeof(uint8_t), 1, fp);

  for (size_t i = 0; i < fields_size_; i++)  {
    uint8_t field_name_len = 0;

    fread((void *)&field_name_len, sizeof(uint8_t), 1, fp);
    char buf[field_name_len]; 
    fread((void *)buf, sizeof(char), field_name_len, fp);
    std::string field_name(buf, field_name_len);
    uint8_t field_id, data_type, is_index = 0;
    fread((void *)&field_id, sizeof(uint8_t), 1, fp);
    fread((void *)&data_type, sizeof(uint8_t), 1, fp);
    fread((void *)&is_index, sizeof(uint8_t), 1, fp);
    
    DataType field_type = DataType::INT;
    if (data_type == 0) {
      field_type = DataType::INT;
    } else if (data_type == 1)  {
      field_type = DataType::LONG;
    } else if (data_type == 2)  {
      field_type = DataType::FLOAT;
    } else if (data_type == 3)  {
      field_type = DataType::DOUBLE;
    } else if (data_type == 4)  {
      field_type = DataType::STRING;
    } else if (data_type == 5)  {
      field_type = DataType::VECTOR;
    } else if (data_type == 6)  {
      field_type = DataType::MULTI_STRING;
    }

    std::string path = root_path_ + "/" + field_name;
    if (field_type == DataType::INT ||
      field_type == DataType::LONG ||
      field_type == DataType::FLOAT ||
      field_type == DataType::DOUBLE)  {
      if (!utils::isFolderExist(path.c_str())) {
	continue; 
      }

      FixedFieldColumnData *fixed_field = new FixedFieldColumnData(field_name);
      if (!fixed_field->Init(path, field_type))  return -1;
      fixed_field_map_[field_name] = fixed_field;
    }  else if (field_type == DataType::STRING) {
      if (!utils::isFolderExist(path.c_str())) {
        continue; 
      }

      StrFieldColumnData *str_field = new StrFieldColumnData(field_name);
      if (!str_field->Init(path))  return -2; 
      str_field_map_[field_name] = str_field; 
    }  else if (field_type == DataType::MULTI_STRING) {
      if (!utils::isFolderExist(path.c_str())) {
        continue;
      }    

      MultiStrFieldColumnData *mul_str_field = new MultiStrFieldColumnData(field_name);
      if (!mul_str_field->Init(path))  return -3; 
      mul_str_field_map_[field_name] = mul_str_field; 
    } 

    fid_id2name_[field_id] = field_name;
    fid_name2id_[field_name] = field_id;
    fid_name2type_[field_name] = field_type;
    fid2index_[field_name] = is_index == 1 ? true : false;
  }
  
  uint32_t fields_info[size_];
  fread((void *)fields_info, sizeof(uint32_t), size_, fp);

  docid_fields_map_ = new char *[capacity_];
  for (size_t i = 0; i < capacity_; i++)  {
    docid_fields_map_[i] = nullptr; 
    if (i < size_)  {
      docid_fields_map_[i] = new char[fields_info[i] + 1];
      uint8_t fields_num = fields_info[i] / (sizeof(uint8_t) + sizeof(uint32_t));

      memcpy((void *)docid_fields_map_[i], (void *)&fields_num, sizeof(uint8_t));
      fread((void *)(docid_fields_map_[i] + 1), sizeof(char), fields_info[i], fp); 
    }  
  } 
  
  fclose(fp);
  return true;
}

bool DocidFieldsMgr::Dump(const std::string &file_path, uint32_t &flushed_size) {
  if (capacity_ < size_)  {
    LOG(ERROR)<<"Capacity should be greater than size!!!";
    return false;
  }

  if (fields_size_ != fid_id2name_.size())  {
    LOG(ERROR)<<"fields num is conflict!!!"; 
    return false;
  }
  
  FILE *fp = fopen(file_path.c_str(), "wb");
 
  fwrite((void *)&capacity_, sizeof(uint32_t), 1, fp);
  flushed_size = size_;
  fwrite((void *)&flushed_size, sizeof(uint32_t), 1, fp);
  fwrite((void *)&fields_size_, sizeof(uint8_t), 1, fp);
  for (auto iter: fid_id2name_)  {
    if (fid_name2type_.find(iter.second) == fid_name2type_.end()
	|| fid2index_.find(iter.second) == fid2index_.end())  {
      LOG(ERROR)<<"Field "<<iter.second<<" information not complete!"; 
      return false; 
    }
    uint8_t field_name_len = (uint8_t)(iter.second.length());

    fwrite((void *)&field_name_len, sizeof(uint8_t), 1, fp);
    fwrite((void *)(iter.second).c_str(), sizeof(char), field_name_len, fp);
    fwrite((void *)&(iter.first), sizeof(uint8_t), 1, fp);
    uint8_t data_type = 100;
    if (fid_name2type_[iter.second] == DataType::INT) {
      data_type = 0;
    } else if (fid_name2type_[iter.second] == DataType::LONG)  {
      data_type = 1;
    } else if (fid_name2type_[iter.second] == DataType::FLOAT)  {
      data_type = 2;
    } else if (fid_name2type_[iter.second] == DataType::DOUBLE)  {
      data_type = 3;
    } else if (fid_name2type_[iter.second] == DataType::STRING)  {
      data_type = 4;
    } else if (fid_name2type_[iter.second] == DataType::VECTOR)  {
      data_type = 5;
    } else if (fid_name2type_[iter.second] == DataType::MULTI_STRING)  {
      data_type = 6;
    }
    fwrite((void *)&data_type, sizeof(uint8_t), 1, fp);
    uint8_t is_index = 0;
    if (fid2index_[iter.second])  {
      is_index = 1;
    }
    fwrite((void *)&is_index, sizeof(uint8_t), 1, fp);
  }
   
  uint32_t fields_info[flushed_size]; 
  for (uint32_t i = 0; i < flushed_size; i++)  {
    if (!docid_fields_map_[i]) {
      LOG(ERROR)<<"Data format error!";
      return false;
    }
    uint8_t fids_size = 0;
    memcpy((void *)&fids_size, (void *)docid_fields_map_[i], sizeof(char));  
    fields_info[i] = fids_size * (sizeof(uint8_t) + sizeof(uint32_t)); 
  }
  fwrite((void *)fields_info, sizeof(uint32_t), flushed_size, fp);

  for (uint32_t i = 0; i < flushed_size; i++)  {
    fwrite((void *)(docid_fields_map_[i] + 1), sizeof(char), fields_info[i], fp); 
  }  
  fclose(fp);
  return true;
}

}

