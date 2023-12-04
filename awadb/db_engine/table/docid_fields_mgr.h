/**
 * Copyright 2023 The AwaDB Authors.
 *
 * This source code is licensed under the Apache License, Version 2.0 license
 * found in the LICENSE file in the root directory of this source tree.
 */

#pragma once

#include <map>
#include <thread>
#include "c_api/api_data/gamma_doc.h"
#include "c_api/api_data/gamma_table.h"

#include "field_column_data.h"


namespace tig_gamma  {

class DocidFieldsMgr  {
 public:
  DocidFieldsMgr();
  ~DocidFieldsMgr();

  bool Init(
    const uint32_t &block_docs_num,
    const std::string &root_path);

  int AddField(const FieldInfo &field_info, const uint8_t &fid);
  int Put(const uint32_t &docid, std::vector<Field> &fields); 
  int Get(const uint32_t &docid, std::vector<Field> &fields);
  int Get(const uint32_t &docid, Field &field);
  size_t FieldsSize()  { return size_; }

  int GetAllFields(const uint32_t &docid, std::vector<Field> &fields); 

  int GetAllFields(std::vector<FieldInfo> &fields);

  bool ContainField(const std::string &field_name)  {
    return fid_name2id_.find(field_name) == fid_name2id_.end() ? false : true;
  }

  int GetFieldId(const std::string &field_name)  {
    return fid_name2id_.find(field_name) == fid_name2id_.end() ? -1 : (int)fid_name2id_[field_name];
  }

  int GetFieldName(const uint8_t &fid, std::string &name)  {
    if (fid_id2name_.find(fid) == fid_id2name_.end())  return -1;
    name = fid_id2name_[fid];
    return 0; 
  }

  bool GetFieldType(const std::string &field_name,
    DataType &type)  {
    if (!ContainField(field_name))  return false;
    type = fid_name2type_[field_name];
    return true;
  } 

  std::map<std::string, uint8_t> fid_name2id_;

 private:
  int Get(const uint32_t &docid, const uint8_t field_id);
  int Put(const uint32_t &docid, const std::vector<uint8_t> &field_ids, const std::vector<uint32_t> &field_posids); 
  
  int Find(const uint8_t &fid, const char *fid_values_ptr, const uint32_t &fids_size); 
  void Destroy(char ** &ptr, const uint32_t &size, bool destroy_all);
 
  bool Load(const std::string &file_path);
  bool Dump(const std::string &file_path, uint32_t &flushed_size);
  void Flush();

  char **docid_fields_map_;
  uint32_t capacity_;
  uint32_t size_;
  uint32_t last_flushed_size_;
  uint32_t field_id_bytes_;
  uint32_t field_pos_bytes_;

  uint8_t fields_size_;
  uint32_t block_docs_num_;
  std::string root_path_;
  std::string persist_file_;

  std::map<uint8_t, std::string> fid_id2name_;
  std::map<std::string, DataType> fid_name2type_;
  std::map<std::string, bool> fid2index_;

  std::map<std::string, FixedFieldColumnData *> fixed_field_map_;
  std::map<std::string, StrFieldColumnData *> str_field_map_;
  std::map<std::string, MultiStrFieldColumnData *> mul_str_field_map_;

  std::thread flush_thread_;

};	


}

