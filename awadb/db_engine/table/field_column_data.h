/**
 * Copyright 2023 The AwaDB Authors.
 *
 * This source code is licensed under the Apache License, Version 2.0 license
 * found in the LICENSE file in the root directory of this source tree.
 */

#pragma once

#include <vector>
#include "storage/storage_manager.h"

namespace tig_gamma  {

class FixedFieldColumnData  {
 public:
  FixedFieldColumnData(const std::string &name);
  ~FixedFieldColumnData();

  bool Init(const std::string &root_path, const DataType &element_type);

  //int Put(const Field &field);
  int Put(Field &field);
  //int Put(const std::vector<Field> &fields_array);
  int Put(std::vector<Field> &fields_array);

  int Get(const uint32_t &id, Field &field_value); 

  int Get(const std::vector<uint32_t> &ids,
    std::vector<Field> &field_value_array); 

  
  uint32_t GetCurMaxId()  {
    return max_id_;
  }
  

 private:
  //std::vector<char *> data_;
  //uint32_t slot_element_count_;
  std::string name_;  
  uint32_t element_size_;
  std::string root_path_; 
  uint32_t max_id_;

  StorageManager *storage_mgr_;
};	

class StrFieldColumnData  {
 public:
  StrFieldColumnData(const std::string &name);
  ~StrFieldColumnData();
 
  //bool Init(const uint32_t &slot_str_size, const uint32_t &str_max_size);
  bool Init(const std::string &root_path);
  
  int Put(const Field &field);
  int Put(const std::vector<Field> &fields_array);

  int Get(const uint32_t &id, Field &field_value); 
  int Get(const std::vector<uint32_t> &ids,
    std::vector<Field> &field_value_array); 

  uint32_t GetCurMaxId()  {
    return total_str_count_;
  }


  //int Put(const std::string &str);

  //int Get(const uint32_t &id, char *&str, uint32_t &str_size);

 private:

  //bool ExtendSlotData();
  //int IdInSlot(const uint32_t &id, const uint32_t &slot_id);
  //int Seek(const uint32_t &id, uint32_t &slot_id, uint32_t &pos_in_slot);

  //std::vector<char *> str_data_;
  //std::vector<std::vector<uint32_t>> str_offset_;
  //std::vector<uint32_t> cur_slot_str_size_; 
  //std::vector<uint32_t> max_id_in_slot_;

  //uint32_t latest_slot_id_;
  //uint32_t latest_offset_; 
  //uint32_t slot_str_size_;
  //uint32_t str_max_size_;
  std::string name_;
  std::string root_path_;
  uint32_t element_size_; 
  uint32_t total_str_count_;
  StorageManager *storage_mgr_;
};

/*
struct MultiStrUnit  {
  MultiStrUnit()  { base_offset = 0; }
  ~MultiStrUnit()  {
    base_offset = 0;
    str_size_seq.clear(); 
  }

  uint32_t base_offset;
  std::vector<uint16_t> str_size_seq; 
};	
*/

class MultiStrFieldColumnData  {
 public:
  MultiStrFieldColumnData(const std::string &name);
  ~MultiStrFieldColumnData();

  //bool Init(const uint32_t &slot_str_size, const uint32_t &str_max_size);
  bool Init(const std::string &root_path);
   
  //int Put(const std::vector<std::string> &vec_str, const uint32_t &all_str_size);

  //int Get(const uint32_t &id, std::vector<char *> &vec_str, std::vector<uint32_t> &vec_str_size);


  int Put(const Field &field);
  
  int Get(const uint32_t &id, Field &field_value); 

  uint32_t GetCurMaxId()  {
    return total_str_count_;
  }

 private:

  /*
  bool ExtendSlotData();
  int IdInSlot(const uint32_t &id, const uint32_t &slot_id);
  int Seek(const uint32_t &id, uint32_t &slot_id, uint32_t &pos_in_slot);

  std::vector<char *> str_data_;
  std::vector<std::vector<MultiStrUnit *>> str_offset_;
  std::vector<uint32_t> cur_slot_str_size_; 
  std::vector<uint32_t> max_id_in_slot_;


  uint32_t latest_slot_id_;
  uint32_t latest_offset_; 
  uint32_t slot_str_size_;
  uint32_t str_max_size_;
  */

  std::string name_;
  std::string root_path_;
  uint32_t element_size_; 
  uint32_t total_str_count_;
  StorageManager *storage_mgr_;

};

}

