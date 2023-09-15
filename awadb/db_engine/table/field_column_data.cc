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

FixedFieldColumnData::FixedFieldColumnData() {
  slot_element_count_ = 0;
  element_size_ = 0;
  max_id_ = 0;
}

FixedFieldColumnData::~FixedFieldColumnData() {
  for (uint32_t i = 0; i < data_.size(); i++)  {
    if (data_[i])  {
      delete data_[i];
      data_[i] = nullptr;
    }
  } 
}

bool FixedFieldColumnData::Init(
  const uint32_t &slot_element_count,
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
  slot_element_count_ = slot_element_count;
  char *init_data = new char[slot_element_count_ * element_size_];
  if (!init_data) return false; 
  data_.push_back(init_data);
  return true;
}

//int FixedFieldColumnData::Put(const Field &field)  {
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


StrFieldColumnData::StrFieldColumnData()  {
  latest_slot_id_ = 0;
  latest_offset_ = 0;
  slot_str_size_ = 0;
  str_max_size_ = 0;
  total_str_count_ = 0;
}

StrFieldColumnData::~StrFieldColumnData()  {
  for (uint32_t i = 0; i < str_data_.size(); i++)  {
    delete[] str_data_[i];
    str_data_[i] = nullptr;
    str_offset_[i].clear();
  }
  str_data_.clear();
  str_offset_.clear();
  cur_slot_str_size_.clear();
  max_id_in_slot_.clear();
}

bool StrFieldColumnData::Init(
  const uint32_t &slot_str_size,
  const uint32_t &str_max_size)  {
  slot_str_size_ = slot_str_size;
  str_max_size_ = str_max_size;
  return ExtendSlotData();
}

bool StrFieldColumnData::ExtendSlotData()  {
  char *slot_data = new char[slot_str_size_];
  if (!slot_data)  return false;
  str_data_.push_back(slot_data);

  std::vector<uint32_t> slot_str_list;
  str_offset_.push_back(slot_str_list);
  cur_slot_str_size_.push_back(0); 
  max_id_in_slot_.push_back(0); 

  return true;
}

int StrFieldColumnData::Put(const Field &field)  {
  return Put(field.value);
}

int StrFieldColumnData::Put(const std::vector<Field> &fields_array)  {
  int ret = 0; 
  for (uint32_t i = 0; i < fields_array.size(); i++)  {
    int each_ret = Put(fields_array[i]);
    if (each_ret != 0)  ret = each_ret;
  }
  return ret; 
}

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

/*
 -1 : id in the slot of less than slot_id
  0 : id in the slot of slot_id
  1 : id in the slot of larger than slot_id
 * */
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


int StrFieldColumnData::Get(
  const uint32_t &id, 
  Field &field_value)  {
  char *str = nullptr;
  uint32_t str_size = 0;
  int ret = Get(id, str, str_size);
  field_value.value = std::string(str, str_size);

  return ret;
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



MultiStrFieldColumnData::MultiStrFieldColumnData() {
  latest_slot_id_ = 0;
  latest_offset_ = 0;
  slot_str_size_ = 0;
  str_max_size_ = 0;
  total_str_count_ = 0;
}

MultiStrFieldColumnData::~MultiStrFieldColumnData()  {
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
}

bool MultiStrFieldColumnData::Init(
  const uint32_t &slot_str_size,
  const uint32_t &str_max_size)  {
  slot_str_size_ = slot_str_size;
  str_max_size_ = str_max_size;
  return ExtendSlotData();
}

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


int MultiStrFieldColumnData::Put(
  const std::vector<std::string> &vec_str,
  const uint32_t &all_str_size)  {
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

    uint32_t total_slot_size = latest_offset_ + all_str_size;
    if (total_slot_size > slot_str_size_)  {

      if (!ExtendSlotData())  {
        LOG(ERROR)<<"can not allocate new slot data!";
        return -4;	
      }
      
      latest_slot_id_++;
      latest_offset_ = 0;
    } 

    char *str_pos = str_data_[latest_slot_id_] + latest_offset_;
    MultiStrUnit *mul_str_ptr = new MultiStrUnit();
    mul_str_ptr->base_offset = latest_offset_;

    for (uint32_t i = 0; i < vec_str.size(); i++)  {
      uint32_t cur_str_size = vec_str[i].size();
      if (cur_str_size > str_max_size_)  {
        LOG(ERROR)<<"Putting string is too large! Max support string size is "<<str_max_size_;
        return -5; 
      }

      memcpy((void *)str_pos, (void *)vec_str[i].c_str(), cur_str_size); 
      mul_str_ptr->str_size_seq.push_back((uint16_t)cur_str_size);    
   
      str_pos += cur_str_size; 
    } 
   
    str_offset_[latest_slot_id_].push_back(mul_str_ptr); 
    max_id_in_slot_[latest_slot_id_] = total_str_count_;
    cur_slot_str_size_[latest_slot_id_] = latest_offset_ + all_str_size; 
    
    if (cur_slot_str_size_[latest_slot_id_] == slot_str_size_)  {
      latest_slot_id_++;
      latest_offset_ = 0;
    }  else  {
      latest_offset_ += all_str_size;
    }
  }
  total_str_count_++;
  return 0; 
}

/*
 -1 : id in the slot of less than slot_id
  0 : id in the slot of slot_id
  1 : id in the slot of larger than slot_id
 * */
int MultiStrFieldColumnData::IdInSlot(
  const uint32_t &id,
  const uint32_t &slot_id)  {
  if (id > max_id_in_slot_[slot_id])  return 1;
  uint32_t start_id = (slot_id == 0) ? 0 : max_id_in_slot_[slot_id - 1] + 1;
  return id < start_id ? -1 : 0;
}


int MultiStrFieldColumnData::Seek(
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

int MultiStrFieldColumnData::Put(const Field &field)  {
  uint32_t total_str_size = 0;
  for (uint32_t i = 0; i< field.mul_str_value.size(); i++)  {
    total_str_size += field.mul_str_value[i].size();
  }
  return Put(field.mul_str_value, total_str_size);
}

int MultiStrFieldColumnData::Get(
  const uint32_t &id,
  Field &field_value)  {
  
  std::vector<char *> vec_ptr;
  std::vector<uint32_t> vec_size;
  int ret = Get(id, vec_ptr, vec_size);

  for (int i = 0; i < vec_ptr.size(); i++)  {
    field_value.mul_str_value.push_back(
      std::string(vec_ptr[i], vec_size[i]));
  }

  return ret;
}

int MultiStrFieldColumnData::Get(
  const uint32_t &id,
  std::vector<char *> &vec_str,
  std::vector<uint32_t> &vec_str_size)  {
  uint32_t slot_id = 0, pos_in_slot = 0;
  if (Seek(id, slot_id, pos_in_slot) != 0)  return -1;

  if (pos_in_slot >= str_offset_[slot_id].size())  return -2;

  MultiStrUnit *mul_str_unit = str_offset_[slot_id][pos_in_slot];

  char *base = str_data_[slot_id] + mul_str_unit->base_offset;
  for (uint32_t i = 0; i < mul_str_unit->str_size_seq.size(); i++)  {
    vec_str.push_back(base);
    uint32_t str_size = (uint32_t)mul_str_unit->str_size_seq[i];
    vec_str_size.push_back(str_size); 
    base += str_size; 
  }
  return 0;
}

}

