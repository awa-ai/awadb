/**
 * Copyright 2023 The AwaDB Authors.
 *
 * This source code is licensed under the Apache License, Version 2.0 license
 * found in the LICENSE file in the root directory of this source tree.
 */

#include "util/log.h"
#include "awadb_retrieval.h"

namespace tig_gamma  {

int DocDetail::Init()  {
  ids_list_ = new uint32_t[kDefaultListSize];
  freqs_list_ = new uint8_t[kDefaultListSize];
  list_capacity_ = kDefaultListSize;
  if (nullptr == ids_list_ || nullptr == freqs_list_)  return -1;
  return 0;
}

int DocDetail::Add(const uint32_t &id, const uint8_t &freq)  {
  if (ids_len_ >= list_capacity_)  {
    list_capacity_ += kDefaultListSize;
    uint32_t *tmp_ids = new uint32_t[list_capacity_];
    uint8_t *tmp_freqs = new uint8_t[list_capacity_];
    if (!tmp_ids || !tmp_freqs)  {
      fprintf(stderr, "can not allocate new memory!\n"); 
      return -1;
    } 
    memcpy((void *)tmp_ids, (void *)ids_list_, ids_len_ * sizeof(uint32_t));
    memcpy((void *)tmp_freqs, (void *)freqs_list_, ids_len_ * sizeof(uint8_t));
    delete[] ids_list_;
    delete[] freqs_list_;
    ids_list_ = tmp_ids;
    freqs_list_ = tmp_freqs;
  } 
  
  ids_list_[ids_len_] = id;
  freqs_list_[ids_len_] = freq;
  ids_len_++;
  return 0;
}

int DocDetail::Seek(const uint32_t &docid, size_t &pos)  {
  int expect_docid = -1;
  int len = ids_len_;
  while (true)  {
    if (pos >= len)  return -1;
    if (ids_list_[pos] >= docid)  {
      expect_docid = (int)ids_list_[pos];
      pos++;
      break;
    }  
    pos++; 
  }
  return expect_docid;
}

AwadbRetrieval::AwadbRetrieval(const std::string &path) : path_(path) {
}

AwadbRetrieval::~AwadbRetrieval()  {
  for (auto &iter: inverted_list_)  {
    if (iter.second)  {
      delete iter.second;
      iter.second = nullptr;
    }
  }	  
  inverted_list_.clear();
}

bool AwadbRetrieval::AddDoc(
  const uint32_t &docid, 
  WordsInDoc &words_in_doc)  {

  bool ret = true;
  std::vector<WordCount>::iterator iter = words_in_doc.WordCounts().begin(); 
  for (; iter != words_in_doc.WordCounts().end(); iter++)  {
    if (inverted_list_.find(iter->word) == inverted_list_.end())  {
      DocDetail *item = new DocDetail();
      if (0 != item->Init())  {
	ret = false;
        LOG(ERROR)<<"word "<<iter->word.c_str()<<" init invert list error!";
        break; 
      }
      inverted_list_[iter->word] = item;
    }

    if (0 != inverted_list_[iter->word]->Add(docid, (uint8_t)iter->count))  {
      ret = false;
      break;
    }
  }
  return ret;  
}


int AwadbRetrieval::Retrieve(
  const std::vector<std::string> &query,
  std::vector<int> &docids)  {

  int ret = 0;
  uint32_t start_docid = 0;
  size_t base_no = 0;
  for (size_t i = 0; i < query.size(); i++)  {
    if (inverted_list_.find(query[i]) == inverted_list_.end())  {
      ret = -1;
      return ret;
    }
    
    uint32_t tmp_docid = inverted_list_[query[i]]->ids_list_[0];
    if (tmp_docid > start_docid)  {
      start_docid = tmp_docid;
      base_no = i;
    }
  }

  size_t query_count = query.size();
  size_t pos_array[query_count];
  memset((void *)pos_array, 0, query_count * sizeof(size_t));
 
  size_t count = 0;
  int next_docid = -1;
  while (true)  { 
    while (count < query_count)  {
      if (base_no == count)  { count++; continue; }
      next_docid = inverted_list_[query[count]]->Seek(start_docid, pos_array[count]);
      if (next_docid == -1)  return docids.size();
      else if (next_docid == start_docid) count++;
      else  {
        start_docid = next_docid;
	base_no = count;
	count = 0;
      }
    }
    if (count == query_count) {
      docids.push_back((int)start_docid);
      int next_docid = inverted_list_[query[base_no]]->Seek(start_docid, pos_array[base_no]);
      if (next_docid == -1)  return docids.size();
      start_docid = (uint32_t)next_docid;
      count = 0;
    }
  }
  return docids.size();
}



}
