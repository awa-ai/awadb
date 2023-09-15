#include <iostream>
#include <vector>

#include "c_api/gamma_api.h"
#include "c_api/api_data/gamma_table.h"
#include "c_api/api_data/gamma_doc.h"
#include "search/gamma_engine.h"

namespace awadb = tig_gamma;

bool Create(void *engine, awadb::TableInfo &table_info)  {

  int ret = static_cast<awadb::GammaEngine *>(engine)->CreateTable(table_info);
  if (0 == ret) return true;
  return false;
}	

bool AddNewField(void *engine, awadb::FieldInfo &field_info)  {
  int ret = static_cast<awadb::GammaEngine *>(engine)->AddNewField(field_info);
  return ret >= 0 ? true : false; 
}

bool LoadFromLocal(void *engine)  {
  int ret = static_cast<awadb::GammaEngine *>(engine)->Load();
  return ret == 0 ? true : false; 
}

bool AddDoc(void *engine, awadb::Doc &doc)  {

  int ret = static_cast<awadb::GammaEngine *>(engine)->AddOrUpdate(doc);
  
  return ret == 0 ? true : false;
}

bool AddDocs(
  void *engine,
  awadb::Docs &batch_docs)  {
  awadb::BatchResult batch_results;
  int ret = static_cast<awadb::GammaEngine *>(engine)->AddOrUpdateDocs(batch_docs, batch_results);

  return ret == 0 ? true : false;
}


bool AddTexts(
  void *engine,
  std::vector<awadb::Doc> &docs,
  std::vector<awadb::WordsInDoc> &words_count_in_docs)  {
  awadb::Docs batch_docs;
  for (auto &doc: docs)  {
    batch_docs.AddDoc(doc);
  }

  awadb::BatchResult batch_results;
  int ret = static_cast<awadb::GammaEngine *>(engine)
    ->AddOrUpdateDocs(batch_docs, batch_results, words_count_in_docs);

  return ret == 0 ? true : false;
}

bool Delete(void *engine, std::vector<std::string> &keys)  {
  return static_cast<awadb::GammaEngine *>(engine)->DeleteDocs(keys);
}

bool GetDocs(
  void *engine,
  const std::vector<std::string> &keys,
  std::map<std::string, awadb::Doc> &docs)  {

  int ret = static_cast<awadb::GammaEngine *>(engine)->GetDocs(keys, docs);

  return ret == 0 ? true : false;
}


bool Update(void *engine, awadb::Doc &doc)  {
  int ret = static_cast<awadb::GammaEngine *>(engine)->AddOrUpdate(doc);
  return ret == 0 ? true : false;
}

int DoSearch(void *engine, awadb::Request &request, awadb::Response &results)  {
 
  int ret = static_cast<awadb::GammaEngine *>(engine)->Search(request, results);

  return ret;  
}


void GetFieldsType(void *engine,
  const std::vector<std::string> &fields,
  std::map<std::string, awadb::DataType> &types)  {
  static_cast<awadb::GammaEngine *>(engine)->GetFieldsType(fields, types);
  return;
}	








