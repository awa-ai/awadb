#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>
#include <iostream>
#include <vector>


#include "c_api/gamma_api.h"
#include "c_api/api_data/gamma_table.h"
#include "c_api/api_data/gamma_doc.h"
#include "search/gamma_engine.h"

namespace awadb = tig_gamma;
namespace py = pybind11;

PYBIND11_MAKE_OPAQUE(std::vector<int>);
PYBIND11_MAKE_OPAQUE(std::vector<std::string>);
PYBIND11_MAKE_OPAQUE(std::vector<float>);


PYBIND11_MAKE_OPAQUE(std::vector<awadb::Doc>);
PYBIND11_MAKE_OPAQUE(std::vector<awadb::ResultItem>);
PYBIND11_MAKE_OPAQUE(std::vector<awadb::Field>);
PYBIND11_MAKE_OPAQUE(std::vector<awadb::SearchResult>);
PYBIND11_MAKE_OPAQUE(std::map<std::string, awadb::Doc>);
PYBIND11_MAKE_OPAQUE(std::vector<awadb::WordsInDoc>);


bool Create(void *engine, awadb::TableInfo &table_info)  {

  int ret = static_cast<awadb::GammaEngine *>(engine)->CreateTable(table_info);
  if (0 == ret) return true;
  return false;
}	

bool LoadFromLocal(void *engine)  {
  int ret = static_cast<awadb::GammaEngine *>(engine)->Load();
  return ret == 0 ? true : false; 
}


bool AddDoc(void *engine, const std::string &name, awadb::Doc &doc)  {

  int ret = static_cast<awadb::GammaEngine *>(engine)->AddOrUpdate(doc);
  
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


PYBIND11_MODULE(awa, m) {
    m.doc() = "AwaDB Python SDK";

    py::bind_vector<std::vector<std::string>>(m, "StrVec");
    py::bind_vector<std::vector<float>>(m, "FloatVec");
    py::enum_<awadb::DataType>(m, "DataType")
	.value("INT", awadb::DataType::INT)
	.value("LONG", awadb::DataType::LONG)
	.value("FLOAT", awadb::DataType::FLOAT)
	.value("DOUBLE", awadb::DataType::DOUBLE)
	.value("STRING", awadb::DataType::STRING)
	.value("VECTOR", awadb::DataType::VECTOR)
	.export_values();
    
    py::class_<awadb::VectorInfo>(m, "VectorInfo").def(py::init<>())
	.def_readwrite("name", &awadb::VectorInfo::name)
	.def_readwrite("data_type", &awadb::VectorInfo::data_type)
	.def_readwrite("is_index", &awadb::VectorInfo::is_index)
	.def_readwrite("dimension", &awadb::VectorInfo::dimension)
	.def_readwrite("model_id", &awadb::VectorInfo::model_id)
	.def_readwrite("store_type", &awadb::VectorInfo::store_type)
	.def_readwrite("store_param", &awadb::VectorInfo::store_param)
	.def_readwrite("has_source", &awadb::VectorInfo::has_source);

    py::class_<awadb::FieldInfo>(m, "FieldInfo").def(py::init<>())
	.def_readwrite("name", &awadb::FieldInfo::name)
	.def_readwrite("data_type", &awadb::FieldInfo::data_type)
	.def_readwrite("is_index", &awadb::FieldInfo::is_index);


    py::class_<awadb::TableInfo>(m, "TableInfo").def(py::init<>())
        .def("Name", &awadb::TableInfo::Name)
        .def("SetName", (void(awadb::TableInfo::*)(const std::string &)) &awadb::TableInfo::SetName)
        .def("IsCompress", &awadb::TableInfo::IsCompress)
        .def("SetCompress", (void(awadb::TableInfo::*)(int)) &awadb::TableInfo::SetCompress)
        .def("Fields", &awadb::TableInfo::Fields)
        .def("AddField", (void(awadb::TableInfo::*)(awadb::FieldInfo &)) &awadb::TableInfo::AddField)
        .def("VectorInfos", &awadb::TableInfo::VectorInfos)
        .def("AddVectorInfo", (void(awadb::TableInfo::*)(awadb::VectorInfo &)) &awadb::TableInfo::AddVectorInfo)
        .def("IndexingSize", &awadb::TableInfo::IndexingSize)
        .def("SetIndexingSize", (void(awadb::TableInfo::*)(int)) &awadb::TableInfo::SetIndexingSize)
        .def("RetrievalType", &awadb::TableInfo::RetrievalType)
        .def("SetRetrievalType", (void(awadb::TableInfo::*)(const std::string &)) &awadb::TableInfo::SetRetrievalType)
        .def("RetrievalParam", &awadb::TableInfo::RetrievalParam)
        .def("SetRetrievalParam", (void(awadb::TableInfo::*)(const std::string &)) &awadb::TableInfo::SetRetrievalParam)
        .def("RetrievalTypes", &awadb::TableInfo::RetrievalTypes)
        .def("RetrievalParams", &awadb::TableInfo::RetrievalParams);

    py::class_<awadb::Field>(m, "Field").def(py::init<>())
	.def_readwrite("name", &awadb::Field::name)
	.def_readwrite("value", &awadb::Field::value)
	.def_readwrite("source", &awadb::Field::source)
	.def_readwrite("datatype", &awadb::Field::datatype)
        .def("GetVecData", (void(awadb::Field::*)(std::vector<float> &)) &awadb::Field::GetVecData);

    py::class_<awadb::Doc>(m, "Doc").def(py::init<>())
	.def("AddField", (void(awadb::Doc::*)(const awadb::Field &)) &awadb::Doc::AddField)
        .def("Key", &awadb::Doc::Key)
        .def("SetKey", (void(awadb::Doc::*)(const std::string &)) &awadb::Doc::SetKey)
        .def("TableFields", &awadb::Doc::TableFields)
        .def("VectorFields", &awadb::Doc::VectorFields);

    py::class_<awadb::WordCount>(m, "WordCount").def(py::init<>())
	.def_readwrite("word", &awadb::WordCount::word)
        .def_readwrite("count", &awadb::WordCount::count);

    py::class_<awadb::WordsInDoc>(m, "WordsInDoc").def(py::init<>())
	.def("AddWordCount", (void(awadb::WordsInDoc::*)(const awadb::WordCount &)) &awadb::WordsInDoc::AddWordCount)
        .def("WordCounts", &awadb::WordsInDoc::WordCounts);
    
    py::class_<awadb::TermFilter>(m, "TermFilter").def(py::init<>())
        .def_readwrite("field", &awadb::TermFilter::field)
	.def_readwrite("value", &awadb::TermFilter::value)
	.def_readwrite("is_union", &awadb::TermFilter::is_union);

    py::class_<awadb::RangeFilter>(m, "RangeFilter").def(py::init<>())
        .def_readwrite("field", &awadb::RangeFilter::field)
	.def_readwrite("lower_value", &awadb::RangeFilter::lower_value)
	.def_readwrite("upper_value", &awadb::RangeFilter::upper_value)
	.def_readwrite("include_lower", &awadb::RangeFilter::include_lower)
	.def_readwrite("include_upper", &awadb::RangeFilter::include_upper);


    py::class_<awadb::VectorQuery>(m, "VectorQuery").def(py::init<>())
        .def_readwrite("name", &awadb::VectorQuery::name)
	.def_readwrite("value", &awadb::VectorQuery::value)
	.def_readwrite("min_score", &awadb::VectorQuery::min_score)
	.def_readwrite("max_score", &awadb::VectorQuery::max_score)
	.def_readwrite("boost", &awadb::VectorQuery::boost)
	.def_readwrite("has_boost", &awadb::VectorQuery::has_boost)
	.def_readwrite("retrieval_type", &awadb::VectorQuery::retrieval_type);


    py::class_<awadb::Request>(m, "Request").def(py::init<>())
	.def("ReqNum", &awadb::Request::ReqNum)
        .def("SetReqNum", (void(awadb::Request::*)(int)) &awadb::Request::SetReqNum)
        .def("TopN", &awadb::Request::TopN)
	.def("SetTopN", (void(awadb::Request::*)(int)) &awadb::Request::SetTopN)
	.def("BruteForceSearch", &awadb::Request::BruteForceSearch)
	.def("SetBruteForceSearch", (void(awadb::Request::*)(int)) &awadb::Request::SetBruteForceSearch)
	.def("AddVectorQuery", (void(awadb::Request::*)(awadb::VectorQuery &)) &awadb::Request::AddVectorQuery)
	.def("AddPageText", (void(awadb::Request::*)(const std::string &)) &awadb::Request::AddPageText)
	.def("AddField", (void(awadb::Request::*)(const std::string &)) &awadb::Request::AddField)
	.def("AddRangeFilter", (void(awadb::Request::*)(awadb::RangeFilter &)) &awadb::Request::AddRangeFilter)
	.def("AddTermFilter", (void(awadb::Request::*)(awadb::TermFilter &)) &awadb::Request::AddTermFilter)
	.def("VecFields", &awadb::Request::VecFields)
	.def("PageTexts", &awadb::Request::PageTexts)
	.def("Fields", &awadb::Request::Fields)
	.def("RangeFilters", &awadb::Request::RangeFilters)
	.def("TermFilters", &awadb::Request::TermFilters)
	.def("SetRetrievalParams", (void(awadb::Request::*)(const std::string &)) &awadb::Request::SetRetrievalParams)
	.def("RetrievalParams", &awadb::Request::RetrievalParams)
	.def("SetOnlineLogLevel", (void(awadb::Request::*)(const std::string &)) &awadb::Request::SetOnlineLogLevel)
	.def("OnlineLogLevel", &awadb::Request::OnlineLogLevel)
	.def("SetL2Sqrt", (void(awadb::Request::*)(bool)) &awadb::Request::SetL2Sqrt)
	.def("L2Sqrt", &awadb::Request::L2Sqrt);


    py::enum_<awadb::SearchResultCode>(m, "SearchResultCode")
	.value("SUCCESS", awadb::SearchResultCode::SUCCESS)
	.value("INDEX_NOT_TRAINED", awadb::SearchResultCode::INDEX_NOT_TRAINED)
	.value("SEARCH_ERROR", awadb::SearchResultCode::SEARCH_ERROR)
	.export_values();

    py::class_<awadb::ResultItem>(m, "ResultItem").def(py::init<>())
        .def_readwrite("score", &awadb::ResultItem::score)
	.def_readwrite("names", &awadb::ResultItem::names)
	.def_readwrite("values", &awadb::ResultItem::values)
	.def_readwrite("extra", &awadb::ResultItem::extra)
        .def("GetVecData", (void(awadb::ResultItem::*)(const std::string &, std::vector<float> &)) &awadb::ResultItem::GetVecData);
     

    py::class_<awadb::SearchResult>(m, "SearchResult").def(py::init<>())
        .def_readwrite("total", &awadb::SearchResult::total)
	.def_readwrite("result_code", &awadb::SearchResult::result_code)
	.def_readwrite("msg", &awadb::SearchResult::msg)
	.def_readwrite("result_items", &awadb::SearchResult::result_items);
     

    py::class_<awadb::Response>(m, "Response").def(py::init<>())
        .def("AddResults", (void(awadb::Response::*)(const awadb::SearchResult &)) &awadb::Response::AddResults)
        .def("Results", &awadb::Response::Results)
        .def("PackResults", (void(awadb::Response::*)(std::vector<std::string> &)) &awadb::Response::PackResults);

    py::bind_vector<std::vector<awadb::Doc>>(m, "DocsVec");
    py::bind_vector<std::vector<awadb::Field>>(m, "FieldsVec");
    py::bind_vector<std::vector<awadb::ResultItem>>(m, "ResultItemsVec");
    py::bind_vector<std::vector<awadb::SearchResult>>(m, "SearchResultVec");

    py::bind_map<std::map<std::string, awadb::Doc>>(m, "DocsMap");
    py::bind_vector<std::vector<awadb::WordsInDoc>>(m, "WordsCount");

    m.def("Init", &Init, "Init engine");   
    m.def("Close", &Close, "Close engine");   
    m.def("Create", &Create, "Create Table");   
    m.def("LoadFromLocal", &LoadFromLocal, "Load Table");
    m.def("AddDoc", &AddDoc, "Add Or UpdateDoc");   
    m.def("AddTexts", &AddTexts, "Add Or Update Texts and Embeddings");
    m.def("Delete", &Delete, "Delete Document");
    m.def("GetDocs", &GetDocs, "GetDocs");
    m.def("Update", &Update, "Update");
    m.def("DoSearch", &DoSearch, "DoSearch");

}
