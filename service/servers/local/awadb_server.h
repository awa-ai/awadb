/*
 *
 * Copyright 2023 AwaDB authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

#ifndef AWADB_SERVER_H_
#define AWADB_SERVER_H_

#include <iostream>
#include <memory>
#include <string>
#include <thread>
#include <libcuckoo/cuckoohash_map.hh>

#include "absl/flags/flag.h"
#include "absl/flags/parse.h"
#include "absl/strings/str_format.h"

#include <grpc/support/log.h>
#include <grpcpp/grpcpp.h>


#include "awadb.grpc.pb.h"

ABSL_FLAG(uint16_t, port, 50051, "Server port for the service");

using grpc::Server;
using grpc::ServerAsyncResponseWriter;
using grpc::ServerBuilder;
using grpc::ServerCompletionQueue;
using grpc::ServerContext;
using grpc::Status;

class LocalAsyncServer final {
 public:
  LocalAsyncServer(const std::string &data_log_dir);

  ~LocalAsyncServer();
    
  // There is no shutdown handling in this code.
  void Run(const uint16_t &port);

 private:
  
  // This can be run in multiple threads if needed.
  void HandleRpcs();

  bool InitTableEngines();
  std::unique_ptr<ServerCompletionQueue> cq_;
  awadb_grpc::AwaDBServer::AsyncService service_;
  std::unique_ptr<Server> server_;
  std::string root_data_dir_;
  std::string root_log_dir_; 
  cuckoohash_map<std::string, void *> table2engine_;
};

#endif

