/**
 * Copyright 2023 The AwaDB Authors.
 *
 * This source code is licensed under the Apache License, Version 2.0 license
 * found in the LICENSE file in the root directory of this source tree.
 */

#pragma once

#include <string>
#include <map>

#include "c_api/api_data/gamma_doc.h"

namespace tig_gamma  {

const int kDefaultListSize = 128;

class DocDetail  {
 public:
  DocDetail()  {
    ids_list_ = nullptr;
    freqs_list_ = nullptr;
    ids_len_= 0;
    list_capacity_ = 0; 
  }

  ~DocDetail()  {
    if (ids_list_)  {
      delete ids_list_;
      ids_list_ = nullptr;
    }
    if (freqs_list_)  {
      delete freqs_list_;
      freqs_list_ = nullptr;
    }
    ids_len_ = 0;
    list_capacity_ = 0;
  }

  int Init();

  int Add(const uint32_t &id, const uint8_t &freq);

  int Seek(const uint32_t &docid, size_t &pos);

  uint32_t *ids_list_;
  uint8_t *freqs_list_;

  size_t ids_len_;
  size_t list_capacity_;
};	


class AwadbRetrieval  {
 public:
  AwadbRetrieval(const std::string &path);
  ~AwadbRetrieval();
  
  bool AddDoc(const uint32_t &docid,
    WordsInDoc &words_in_doc);

  int Retrieve(const std::vector<std::string> &query,
    std::vector<int> &docids);

 private:
  std::string path_;
  std::map<std::string, DocDetail *> inverted_list_;

};

}

