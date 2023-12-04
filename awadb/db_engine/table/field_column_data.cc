/**
 * Copyright 2023 The AwaDB Authors.
 *
 * This source code is licensed under the Apache License, Version 2.0 license
 * found in the LICENSE file in the root directory of this source tree.
 */

#include "util/log.h"
#include "c_api/api_data/gamma_doc.h"
#include "field_column_data.h"

namespace tig_gamma  {

FixedFieldColumnData::FixedFieldColumnData(const std::string &name) : name_(name)  {
  //slot_element_count_ = 0;
  element_size_ = 0;
  root_path_ = "";
  max_id_ = 0;
  storage_mgr_ = nullptr;
}

FixedFieldColumnData::~FixedFieldColumnData() {
  /* 
  for (uint32_t i = 0; i < data_.size(); i++)  {
    if (data_[i])  {
      delete data_[i];
      data_[i] = nullptr;
    }
  }*/
  if (storage_mgr_)  {
    delete storage_mgr_;
    storage_mgr_ = nullptr;
  } 
}

bool FixedFieldColumnData::Init(
  const std::string &root_path,
  const DataType &element_type)  {
  switch (element_type)  {
    case DataType::INT:  {
      element_size_ = sizeof(int); 
      break;
    }
    case DataType::LONG:  {
      element_size_ = sizeof(long);
      break;
    }
    case DataType::FLOAT:  {
      element_size_ = sizeof(float);
      break; 
    }
    case DataType::DOUBLE: {
      element_size_ = sizeof(double);
      break; 
    }
    default : {
      element_size_ = 65535;
      break; 
    } 
  }
  /*
  slot_element_count_ = slot_element_count;
  char *init_data = new char[slot_element_count_ * element_size_];
  if (!init_data) return false; 
  data_.push_back(init_data);
  */ 
  
  root_path_ = root_path;
  if (!storage_mgr_)  {
    StorageManagerOptions options;
    options.segment_size = 500000;
    options.fixed_value_bytes = element_size_;
    options.seg_block_capacity = 400000;
    storage_mgr_ = 
	new StorageManager(root_path_, BlockType::TableBlockType, options);
    if (!storage_mgr_)  return false; 
    int cache_size = 512;
    int str_cache_size = 512;
    int ret = storage_mgr_->Init(name_ + "col_table", cache_size, str_cache_size);
    if (ret)  {
      LOG(ERROR)<<"Init column table of field "<<name_<<" error, ret="<<ret;
      return false; 
    }
    LOG(INFO)<<"Init field "<<name_<<" column table success! fixed_value_bytes is "
	    <<options.fixed_value_bytes<<", path is "<<root_path_;
    max_id_ = storage_mgr_->Size();   
  }
  return true;
}

//int FixedFieldColumnData::Put(const Field &field)  {
/*
int FixedFieldColumnData::Put(Field &field)  {
  uint32_t slot_id = max_id_ / slot_element_count_;
  if (slot_id > data_.size())  {
    LOG(ERROR)<<"Docid "<<max_id_<<" is too large!";
    return -1;
  }  else if (slot_id == data_.size())  {
    char *slot_data = new char[slot_element_count_ * element_size_];
    if (!slot_data)  return -2;
    data_.push_back(slot_data);
  }

  uint32_t pos_id = max_id_ % slot_element_count_;
  if (field.datatype == DataType::INT)  {
    int v = 0;
    memcpy((void *)&v, (void *)field.value.c_str(), element_size_);
  } 
  memcpy((void *)(data_[slot_id] + pos_id * element_size_), (void *)field.value.c_str(), element_size_);
  max_id_++;
  return 0;
}


//todo: multi-threads to speedup
//int FixedFieldColumnData::Put(const std::vector<Field> &fields_array)  {
int FixedFieldColumnData::Put(std::vector<Field> &fields_array)  {
 
  int ret = 0;	
  for (uint32_t i = 0; i < fields_array.size(); i++)  {
    int each_ret = Put(fields_array[i]); 
    if (each_ret != 0) ret = each_ret; 
  } 
  return ret;
}
*/

int FixedFieldColumnData::Put(Field &field)  {
  storage_mgr_->Add((const uint8_t *)field.value.c_str(), element_size_);
  max_id_++;
  return 0;
}


int FixedFieldColumnData::Put(std::vector<Field> &fields_array)  {
 
  int ret = 0;	
  for (uint32_t i = 0; i < fields_array.size(); i++)  {
    int each_ret = Put(fields_array[i]); 
    if (each_ret != 0) ret = each_ret; 
  } 
  return ret;
}

/*
//todo: multi-threads to speedup
int FixedFieldColumnData::Get(
  const std::vector<uint32_t> &ids,
  std::vector<Field> &field_value_array)  {

  int ret = 0;	
  for (uint32_t i = 0; i < ids.size(); i++)  {
    int each_ret = Get(ids[i], field_value_array[i]);
    if (each_ret != 0)  ret = each_ret; 
  }

  return ret;
}


int FixedFieldColumnData::Get(const uint32_t &id, Field &field_value)  {
  uint32_t slot_id = id / slot_element_count_;
  if (slot_id >= data_.size()) {
    LOG(ERROR)<<"Docid "<<id<<" not exist!";
    return -1;
  }

  uint32_t pos_id = id % slot_element_count_;

  char *data_ptr = data_[slot_id] + pos_id * element_size_;
  switch (field_value.datatype)  {
    case DataType::INT:  {
      int value = 0;
      memcpy((void *)&value, (void *)data_ptr, element_size_);
      field_value.value = std::to_string(value);
      break;
    }
    case DataType::FLOAT:  {
      float value = 0;
      memcpy((void *)&value, (void *)data_ptr, element_size_);
      field_value.value = std::to_string(value);
      break;
    }
    case DataType::LONG:  {
      long value = 0;
      memcpy((void *)&value, (void *)data_ptr, element_size_);
      field_value.value = std::to_string(value);
      break;
    }
    case DataType::DOUBLE:  {
      double value = 0;
      memcpy((void *)&value, (void *)data_ptr, element_size_);
      field_value.value = std::to_string(value);
      break;
    }
    default:  break;
  }

  //memcpy((void *)&field_value.value, (void *)(data_[slot_id] + pos_id * element_size_), element_size_);
  return 0;
}
*/

int FixedFieldColumnData::Get(const uint32_t &id, Field &field_value)  {
  if (!storage_mgr_)  return -1;
  const uint8_t *doc_value = nullptr;
  storage_mgr_->Get((int)id, doc_value);
  field_value.value = std::string((const char *)doc_value, element_size_);
  return 0;
}

int FixedFieldColumnData::Get(
  const std::vector<uint32_t> &ids,
  std::vector<Field> &field_value_array)  {

  int ret = 0;	
  for (uint32_t i = 0; i < ids.size(); i++)  {
    int each_ret = Get(ids[i], field_value_array[i]);
    if (each_ret != 0)  ret = each_ret; 
  }

  return ret;
}


StrFieldColumnData::StrFieldColumnData(const std::string &name) : name_(name)  {
  /*
  latest_slot_id_ = 0;
  latest_offset_ = 0;
  slot_str_size_ = 0;
  str_max_size_ = 0;
  total_str_count_ = 0;*/
  element_size_ = 0; 
  total_str_count_ = 0;
  storage_mgr_ = nullptr;
}

StrFieldColumnData::~StrFieldColumnData()  {
  /* 
  for (uint32_t i = 0; i < str_data_.size(); i++)  {
    delete[] str_data_[i];
    str_data_[i] = nullptr;
    str_offset_[i].clear();
  }
  str_data_.clear();
  str_offset_.clear();
  cur_slot_str_size_.clear();
  max_id_in_slot_.clear();
  */
  if (storage_mgr_)  {
    delete storage_mgr_;
    storage_mgr_ = nullptr;
  } 

}


bool StrFieldColumnData::Init(const std::string &root_path)  {
  root_path_ = root_path;
  if (!storage_mgr_)  {
    element_size_ = sizeof(uint32_t) + sizeof(in_block_pos_t) + sizeof(str_len_t);
    StorageManagerOptions options;
    options.segment_size = 500000;
    options.fixed_value_bytes = element_size_;
    options.seg_block_capacity = 400000;
    storage_mgr_ = 
	new StorageManager(root_path_, BlockType::TableBlockType, options);
    if (!storage_mgr_)  return false; 
    int cache_size = 512;
    int str_cache_size = 512;
    int ret = storage_mgr_->Init(name_ + "_col_table", cache_size, str_cache_size);
    if (ret)  {
      LOG(ERROR)<<"Init column table of field "<<name_<<" error, ret="<<ret;
      return false; 
    }
    LOG(INFO)<<"Init field "<<name_<<" column table success! fixed_value_bytes is "
	    <<options.fixed_value_bytes<<", path is "<<root_path_; 
    total_str_count_ = storage_mgr_->Size(); 
  }

  return true;
}

/*
bool StrFieldColumnData::Init(
  const uint32_t &slot_str_size,
  const uint32_t &str_max_size)  {
  slot_str_size_ = slot_str_size;
  str_max_size_ = str_max_size;
  return ExtendSlotData();
}
*/

/*
bool StrFieldColumnData::ExtendSlotData()  {
  char *slot_data = new char[slot_str_size_];
  if (!slot_data)  return false;
  str_data_.push_back(slot_data);

  std::vector<uint32_t> slot_str_list;
  str_offset_.push_back(slot_str_list);
  cur_slot_str_size_.push_back(0); 
  max_id_in_slot_.push_back(0); 

  return true;
}*/

int StrFieldColumnData::Put(const Field &field)  {
  str_len_t len = field.value.size();
  uint32_t block_id;
  in_block_pos_t in_block_pos;
  storage_mgr_->AddString(field.value.c_str(), len, block_id, in_block_pos);
  uint8_t buf[element_size_];
  memcpy(buf, &block_id, sizeof(uint32_t));
  memcpy(buf + sizeof(uint32_t), &in_block_pos, sizeof(in_block_pos_t));
  memcpy(buf + sizeof(uint32_t) + sizeof(in_block_pos_t), &len, sizeof(str_len_t));
  storage_mgr_->Add((const uint8_t *)buf, element_size_);
  total_str_count_++; 
  return 0;
}

int StrFieldColumnData::Put(const std::vector<Field> &fields_array)  {
  int ret = 0; 
  for (uint32_t i = 0; i < fields_array.size(); i++)  {
    int each_ret = Put(fields_array[i]);
    if (each_ret != 0)  ret = each_ret;
  }
  return ret; 
}


/*
int StrFieldColumnData::Put(const std::string &str)  {
  uint32_t cur_max_slot = str_data_.size() - 1;
  if (latest_slot_id_ < cur_max_slot)  {
    LOG(ERROR)<<"latest_slot_id_ should not less than the size of str_data_";
    return -1; 
  }  else if (latest_slot_id_ > cur_max_slot + 1)  {
    LOG(ERROR)<<"latest_slot_id_ is too large!";
    return -2;
  }  else  {
    if (latest_slot_id_ == cur_max_slot + 1)  {
      if (latest_offset_ > 0)  {
		LOG(ERROR)<<"latest_offset_ shold be zero!";
		return -3; 
      }
      if (!ExtendSlotData())  {
        LOG(ERROR)<<"can not allocate new slot data!";
        return -4;	
      }
    }

    uint32_t cur_str_size = str.size();
    if (cur_str_size > str_max_size_)  {
      LOG(ERROR)<<"Putting string is too large! Max support string size is "<<str_max_size_;
      return -5; 
    }
   
    uint32_t total_slot_size = latest_offset_ + cur_str_size;
    if (total_slot_size > slot_str_size_)  {

      if (!ExtendSlotData())  {
        LOG(ERROR)<<"can not allocate new slot data!";
        return -4;	
      }
      
      latest_slot_id_++;
      latest_offset_ = 0;
    }  
    
    char *str_pos = str_data_[latest_slot_id_] + latest_offset_; 
    memcpy((void *)str_pos, (void *)str.c_str(), cur_str_size); 
    str_offset_[latest_slot_id_].push_back(latest_offset_);
    max_id_in_slot_[latest_slot_id_] = total_str_count_;
    cur_slot_str_size_[latest_slot_id_] = latest_offset_ + cur_str_size; 

    if (cur_slot_str_size_[latest_slot_id_] == slot_str_size_)  {
      latest_slot_id_++;
      latest_offset_ = 0;
    }  else  {
      latest_offset_ += cur_str_size;
    }
  }
  total_str_count_++;
  return 0; 
}
*/

/*
 -1 : id in the slot of less than slot_id
  0 : id in the slot of slot_id
  1 : id in the slot of larger than slot_id
 * */
/*
int StrFieldColumnData::IdInSlot(
  const uint32_t &id,
  const uint32_t &slot_id)  {
  if (id > max_id_in_slot_[slot_id])  return 1;
  uint32_t start_id = (slot_id == 0) ? 0 : max_id_in_slot_[slot_id - 1] + 1;
  return id < start_id ? -1 : 0;
}


int StrFieldColumnData::Seek(
  const uint32_t &id,
  uint32_t &slot_id,
  uint32_t &pos_in_slot)  {
  if (id >= total_str_count_)  {
    LOG(ERROR)<<"id "<<id<<" not exists in string field";
    return -1;
  }
  
  uint32_t start = 0, end = max_id_in_slot_.size() - 1;
  do {
    if (start == end)  {
      if (IdInSlot(id, start) != 0)  return -2;
      slot_id = start;
      pos_in_slot = id - (start == 0 ? 0 : max_id_in_slot_[start - 1] + 1);
      return 0;
    }
    int ret = IdInSlot(id, start);
    if (ret < 0) return -3;
    else if (ret == 0)  {
      slot_id = start;
      pos_in_slot = id - (start == 0 ? 0 : max_id_in_slot_[start - 1] + 1);
      return 0;  
    }  else  {
      ret = IdInSlot(id, end);
      if (ret == 0)  {
        slot_id = end;
	pos_in_slot = id - (end == 0 ? 0 : max_id_in_slot_[end - 1] + 1);
	return 0;
      }  else if (ret > 0) {
	return -4;
      }  else  {
	uint32_t mid = (start + end) >> 1;
	ret = IdInSlot(id, mid);
	if (ret < 0)  {
          end = mid - 1;
	}  else if (ret > 0)  {
	  start = mid + 1;
	}  else  {
	  slot_id = mid;
	  pos_in_slot = id - (mid == 0 ? 0 : max_id_in_slot_[mid - 1] + 1);
	  return 0;
	}
      } 
    }
  }  while (start < end);
  return -5;
}
*/

int StrFieldColumnData::Get(
  const uint32_t &id, 
  Field &field_value)  {
  const uint8_t *ori_doc_value = nullptr;
  storage_mgr_->Get((int)id, ori_doc_value);
  if (!ori_doc_value)  return -1;
  uint32_t block_id;
  in_block_pos_t pos;
  str_len_t len;
  memcpy(&block_id, (void *)ori_doc_value, sizeof(uint32_t)); 
  memcpy(&pos, (void *)(ori_doc_value + sizeof(uint32_t)), sizeof(in_block_pos_t));
  memcpy(&len, (void *)(ori_doc_value + sizeof(uint32_t) + sizeof(in_block_pos_t)), sizeof(str_len_t));
  storage_mgr_->GetString((int)id, field_value.value, block_id, pos, len);

  return 0;
}

int StrFieldColumnData::Get(
  const std::vector<uint32_t> &ids,
  std::vector<Field> &field_value_array)  {
  int ret = 0;
  for (uint32_t i = 0; i < ids.size(); i++)  {
    int each_ret = Get(ids[i], field_value_array[i]);
    if (each_ret != 0)  ret = each_ret;
  }

  return ret;
}	

/*
int StrFieldColumnData::Get(
  const uint32_t &id,
  char *&str,
  uint32_t &str_size)  {
  uint32_t slot_id = 0, pos_in_slot = 0;
  if (Seek(id, slot_id, pos_in_slot) != 0)  return -1;

  if (pos_in_slot >= str_offset_[slot_id].size())  return -2;
  str = str_data_[slot_id] + str_offset_[slot_id][pos_in_slot];
  uint32_t pos_end = 0; 
  if (pos_in_slot == str_offset_[slot_id].size() - 1)  {
    pos_end = cur_slot_str_size_[slot_id];
  }  else  {
    pos_end = str_offset_[slot_id][pos_in_slot + 1];
  }
  str_size = pos_end - str_offset_[slot_id][pos_in_slot];
  return 0;
}
*/


MultiStrFieldColumnData::MultiStrFieldColumnData(const std::string &name) : name_(name) {
  /* 
  latest_slot_id_ = 0;
  latest_offset_ = 0;
  slot_str_size_ = 0;
  str_max_size_ = 0;
  */
  element_size_ = 0; 
  total_str_count_ = 0;
  storage_mgr_ = nullptr;
}

MultiStrFieldColumnData::~MultiStrFieldColumnData()  {
  /* 
  for (uint32_t i = 0; i < str_data_.size(); i++)  {
    delete[] str_data_[i];
    str_data_[i] = nullptr;

    for (uint32_t j = 0; j < str_offset_[i].size(); j++)  {
      delete str_offset_[i][j];
      str_offset_[i][j] = nullptr;
    }
    str_offset_[i].clear();
  }
  str_data_.clear();
  str_offset_.clear();
  cur_slot_str_size_.clear();
  max_id_in_slot_.clear();
  */
  if (!storage_mgr_)  {
    delete storage_mgr_;
    storage_mgr_ = nullptr; 
  }
}

bool MultiStrFieldColumnData::Init(const std::string &root_path) {
  //const uint32_t &slot_str_size,
  //const uint32_t &str_max_size)  {
  /*
   * slot_str_size_ = slot_str_size;
  str_max_size_ = str_max_size;
  return ExtendSlotData();
  */
  root_path_ = root_path;
  if (!storage_mgr_)  {
    element_size_ = sizeof(uint32_t) + sizeof(in_block_pos_t) + sizeof(str_len_t);
    StorageManagerOptions options;
    options.segment_size = 500000;
    options.fixed_value_bytes = element_size_;
    options.seg_block_capacity = 400000;
    storage_mgr_ = 
	new StorageManager(root_path_, BlockType::TableBlockType, options);
    if (!storage_mgr_)  return false; 
    int cache_size = 512;
    int str_cache_size = 512;
    int ret = storage_mgr_->Init(name_ + "_col_table", cache_size, str_cache_size);
    if (ret)  {
      LOG(ERROR)<<"Init column table of field "<<name_<<" error, ret="<<ret;
      return false; 
    }
    total_str_count_ = storage_mgr_->Size();
    LOG(INFO)<<"Init field "<<name_<<" column table success! fixed_value_bytes is "
	    <<options.fixed_value_bytes<<", path is "<<root_path_; 
  }

  return true;

}

/*
bool MultiStrFieldColumnData::ExtendSlotData()  {
  char *slot_data = new char[slot_str_size_];
  if (!slot_data)  return false;
  str_data_.push_back(slot_data);

  std::vector<MultiStrUnit *> slot_str_list;
  str_offset_.push_back(slot_str_list);
  cur_slot_str_size_.push_back(0); 
  max_id_in_slot_.push_back(0); 

  return true;
}
*/


int MultiStrFieldColumnData::Put(const Field &field)  {

  size_t mul_str_count = field.mul_str_value.size(), total_str_size = 0;
  if (mul_str_count == 0)  return 0;
  std::vector<uint8_t> mul_strs;
  if (mul_str_count > 255)  { LOG(ERROR)<<"Multiple strings can not exceed 255";  return -1;}
  mul_strs.push_back((uint8_t)mul_str_count);
  for (size_t i = 0; i < mul_str_count; i++)  {
    size_t each_str_size = field.mul_str_value[i].size();
    if (each_str_size > 255)  {
      LOG(ERROR)<<"The length of each string in multiple strings can not exceed 255";
      return -2;
    }
    mul_strs.push_back((uint8_t)each_str_size);
    total_str_size += each_str_size;
  }

  size_t mul_buf_size = (mul_str_count + 1) * sizeof(uint8_t) + total_str_size;
  char mul_buf[mul_buf_size];
  for (size_t i = 0; i < mul_strs.size(); i++) {
    memcpy((void *)(mul_buf + i), (void *)&mul_strs[i], sizeof(uint8_t)); 
  }
 
  size_t acc_str_bytes = 0; 
  for (size_t i = 0; i < mul_str_count; i++)  {
    size_t each_str_size = field.mul_str_value[i].size();
    memcpy((void *)(mul_buf + mul_str_count + 1 + acc_str_bytes), 
      (void *)field.mul_str_value[i].c_str(),
      each_str_size);
    acc_str_bytes += each_str_size; 
  } 

  str_len_t len = (str_len_t)mul_buf_size;
  uint32_t block_id;
  in_block_pos_t in_block_pos;
  storage_mgr_->AddString(mul_buf, len, block_id, in_block_pos);

  uint8_t buf[element_size_];
  memcpy(buf, &block_id, sizeof(uint32_t));
  memcpy(buf + sizeof(uint32_t), &in_block_pos, sizeof(in_block_pos_t));
  memcpy(buf + sizeof(uint32_t) + sizeof(in_block_pos_t), &len, sizeof(str_len_t));
  storage_mgr_->Add((const uint8_t *)buf, element_size_);
  total_str_count_++;
  return 0;
}


int MultiStrFieldColumnData::Get(
  const uint32_t &id, 
  Field &field_value)  {
  const uint8_t *ori_doc_value = nullptr;
  storage_mgr_->Get((int)id, ori_doc_value);
  if (!ori_doc_value)  return -1;
  uint32_t block_id;
  in_block_pos_t pos;
  str_len_t len;
  memcpy(&block_id, (void *)ori_doc_value, sizeof(uint32_t)); 
  memcpy(&pos, (void *)(ori_doc_value + sizeof(uint32_t)), sizeof(in_block_pos_t));
  memcpy(&len, (void *)(ori_doc_value + sizeof(uint32_t) + sizeof(in_block_pos_t)), sizeof(str_len_t));
  std::string mul_strs = ""; 
  storage_mgr_->GetString((int)id, mul_strs, block_id, pos, len);

  if (mul_strs.length() <= 2)  return -2;
  uint8_t strs_count = 0;
  memcpy((void *)&strs_count, (void *)mul_strs.c_str(), sizeof(uint8_t));
  if (mul_strs.size() <= strs_count + 1)  return -3;
 
  size_t acc_bytes = 0; 
  for (size_t i = 0; i < strs_count; i++)  {
    uint8_t str_len = 0;
    memcpy((void *)&str_len, (void *)(mul_strs.c_str() + 1 + i), sizeof(uint8_t));

    field_value.mul_str_value.push_back(std::string(mul_strs.c_str() + 1 + strs_count + acc_bytes, str_len));
    acc_bytes += str_len;
  }

  return 0;
}

}

