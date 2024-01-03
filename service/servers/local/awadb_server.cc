/**
 * Copyright 2023 The AwaDB Authors.
 *
 * This source code is licensed under the Apache License, Version 2.0 license
 * found in the LICENSE file in the root directory of this source tree.
 */

#include <stdlib.h>

#include "util/utils.h"
#include "c_api/gamma_api.h"
#include "awadb_async_call.h"
#include "awadb_server.h"


LocalAsyncServer::LocalAsyncServer(const std::string &data_log_dir) {
  root_data_dir_ = data_log_dir + "/data";
  root_log_dir_ = data_log_dir + "/log";
}

LocalAsyncServer::~LocalAsyncServer() {
  server_->Shutdown();
  // Always shutdown the completion queue after the server.
  cq_->Shutdown();
}

void LocalAsyncServer::Run(const uint16_t &port)  {
  // if root_data_dir_ exists, load first
  if (utils::isFolderExist(root_data_dir_.c_str()))  {
    InitTableEngines();
  }

  std::string server_address = absl::StrFormat("0.0.0.0:%d", port);

  ServerBuilder builder;
  // Listen on the given address without any authentication mechanism.
  builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
  // Register "service_" as the instance through which we'll communicate with
  // clients. In this case it corresponds to an *asynchronous* service.
  builder.RegisterService(&service_);
  // Get hold of the completion queue used for the asynchronous communication
  // with the gRPC runtime.
  cq_ = builder.AddCompletionQueue();
  // Finally assemble the server.
  server_ = builder.BuildAndStart();
  std::cout << "Server listening on " << server_address << std::endl;
  // Proceed to the server's main loop.
  HandleRpcs();
}

void LocalAsyncServer::HandleRpcs()  {
  // Spawn a new CallData instance to serve new clients.
  CallData data{&service_, cq_.get(), table2engine_, db2tables_, root_data_dir_, root_log_dir_};
  new CreateCall(&data);
  new CheckTableCall(&data);
  new QueryTableDetailCall(&data);
  new AddFieldsCall(&data);
  new AddOrUpdateCall(&data);
  new GetCall(&data);
  new SearchCall(&data);
  new DeleteCall(&data);

  void* tag;  // uniquely identifies a request.
  bool ok;
  while (true) {
    // Block waiting to read the next event from the completion queue. The
    // event is uniquely identified by its tag, which in this case is the
    // memory address of a CallData instance.
    // The return value of Next should always be checked. This return value
    // tells us whether there is any kind of event or cq_ is shutting down.
    GPR_ASSERT(cq_->Next(&tag, &ok));
    //GPR_ASSERT(ok);
    if (!ok)  continue;
    static_cast<Call*>(tag)->Proceed();
  }
}

bool LocalAsyncServer::InitTableEngines()  {
  std::vector<std::string> dbs = utils::ls_folder(root_data_dir_, false);
  for (auto &db: dbs)  {
    std::string db_path = root_data_dir_ + "/";
    db_path += db;
    std::vector<std::string> tables = utils::ls_folder(db_path, false);
    std::string table_names = "";
    for (auto &table: tables)  {
      std::string table_data_path = db_path + "/" + table;
      std::string table_log_path = root_log_dir_ + "/" + db + "/" + table;
      void *table_engine = Init(table_log_path.c_str(), table_data_path.c_str());
      if (!table_engine)  {
	std::cout<<"Table "<<table<<" in db "<<db<<" initialize failed!"<<std::endl;
	continue;
      }
      if (0 == Load(table_engine))  {
	std::string key = db + "/" + table;
        table2engine_.insert(key, table_engine);
	if (table_names.length() == 0)  {
	  table_names = table;
	}  else  {
	  table_names += ":";
	  table_names += table;
	}
      }  else  {
	std::cout<<"Table "<<table<<" in db "<<db<<" load failed!"<<std::endl;
      }
    }
    if (!table_names.empty()) {
      db2tables_.insert(db, table_names);
    }
  }
  return true;
}



int main(int argc, char** argv) {
  if (argc < 2 || argc > 3)  {
    std::cout<<"[awadb_server] [data_path] [port]"<<std::endl;
    return -1;
  } 
  std::string data_path(argv[1]);
  uint16_t port = 50005;

  if (argc == 3)  {
    port = (uint16_t)atoi(argv[2]);
  } 

  LocalAsyncServer server(data_path);
  server.Run(port);

  return 0;
}

