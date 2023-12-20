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

#ifndef AWADB_ASYNC_CALL_H_
#define AWADB_ASYNC_CALL_H_

#include <libcuckoo/cuckoohash_map.hh>
#include <grpc/support/log.h>
#include <grpcpp/grpcpp.h>

#include "c_api/api_data/gamma_doc.h"

#include "awadb.pb.h"
#include "awadb.grpc.pb.h"

namespace awadb = tig_gamma;

using grpc::Server;
using grpc::ServerAsyncResponseWriter;
using grpc::ServerBuilder;
using grpc::ServerCompletionQueue;
using grpc::ServerContext;
using grpc::Status;
	
struct CallData {
  // The means of communication with the gRPC runtime for an asynchronous
  // server.
  awadb_grpc::AwaDBServer::AsyncService* service_;
  // The producer-consumer queue where for asynchronous server notifications.
  ServerCompletionQueue* cq_;

  cuckoohash_map<std::string, void *> &engines_;
  cuckoohash_map<std::string, std::string> &db2tables_;
  std::string &data_dir_;
  std::string &log_dir_; 
};

class Call {
 public:
  virtual void Proceed() = 0;
};

// Class encompasing the state and logic needed to serve a create request.
class CreateCall final : public Call {
 public:
  explicit CreateCall(CallData *data) : data_(data), responder_(&ctx_), status_(CREATE) {
      // Invoke the serving logic right away.
    Proceed();
  }

  void Proceed();

 private:
  bool ProcessCreateRequest();
  CallData *data_;
  // Context for the rpc, allowing to tweak aspects of it such as the use
  // of compression, authentication, as well as to send metadata back to the
  // client.
  ServerContext ctx_;

  // What we get from the client.
  awadb_grpc::DBMeta request_;
  // What we send back to the client.
  awadb_grpc::ResponseStatus reply_;

  // The means to get back to the client.
  ServerAsyncResponseWriter<awadb_grpc::ResponseStatus> responder_;

  // Let's implement a tiny state machine with the following states.
  enum CallStatus { CREATE, PROCESS, FINISH };
  CallStatus status_;  // The current serving state.
};


// Class encompasing the state and logic needed to serve a CheckTable request.
class CheckTableCall final : public Call {
 public:
  explicit CheckTableCall(CallData *data) : data_(data), responder_(&ctx_), status_(CREATE) {
      // Invoke the serving logic right away.
    Proceed();
  }

  void Proceed();

 private:
  bool ProcessCheckTableRequest();
  CallData *data_;
  // Context for the rpc, allowing to tweak aspects of it such as the use
  // of compression, authentication, as well as to send metadata back to the
  // client.
  ServerContext ctx_;

  // What we get from the client.
  awadb_grpc::DBTableName request_;
  // What we send back to the client.
  awadb_grpc::TableStatus reply_;

  // The means to get back to the client.
  ServerAsyncResponseWriter<awadb_grpc::TableStatus> responder_;

  // Let's implement a tiny state machine with the following states.
  enum CallStatus { CREATE, PROCESS, FINISH };
  CallStatus status_;  // The current serving state.
};


// Class encompasing the state and logic needed to serve an AddFields request.
class AddFieldsCall final : public Call {
 public:
  explicit AddFieldsCall(CallData *data) : data_(data), responder_(&ctx_), status_(CREATE) {
    // Invoke the serving logic right away.
    Proceed();
  }

  void Proceed();

 private:
  bool ProcessAddFieldsRequest();
  CallData *data_;
  // Context for the rpc, allowing to tweak aspects of it such as the use
  // of compression, authentication, as well as to send metadata back to the
  // client.
  ServerContext ctx_;

  // What we get from the client.
  awadb_grpc::DBMeta request_;
  // What we send back to the client.
  awadb_grpc::ResponseStatus reply_;

  // The means to get back to the client.
  ServerAsyncResponseWriter<awadb_grpc::ResponseStatus> responder_;

  // Let's implement a tiny state machine with the following states.
  enum CallStatus { CREATE, PROCESS, FINISH };
  CallStatus status_;  // The current serving state.
};

  // Class encompasing the state and logic needed to serve an AddOrUpdate request.
class AddOrUpdateCall final : public Call {
 public:
  explicit AddOrUpdateCall(CallData *data) : data_(data), responder_(&ctx_), status_(CREATE) {
   // Invoke the serving logic right away.
   Proceed();
  }

  void Proceed();

 private:
  bool ProcessAddOrUpdateRequest();
  CallData *data_;
  // Context for the rpc, allowing to tweak aspects of it such as the use
  // of compression, authentication, as well as to send metadata back to the
  // client.
  ServerContext ctx_;

  // What we get from the client.
  awadb_grpc::Documents request_;
  // What we send back to the client.
  awadb_grpc::ResponseStatus reply_;

  // The means to get back to the client.
  ServerAsyncResponseWriter<awadb_grpc::ResponseStatus> responder_;

  // Let's implement a tiny state machine with the following states.
  enum CallStatus { CREATE, PROCESS, FINISH };
  CallStatus status_;  // The current serving state.
};

// Class encompasing the state and logic needed to serve a Get request.
class GetCall final : public Call {
 public:
  explicit GetCall(CallData *data) : data_(data), responder_(&ctx_), status_(CREATE) {
    // Invoke the serving logic right away.
    Proceed();
  }

  void Proceed();

 private:
  void ProcessGetRequest();

  void AddFields(
    awadb_grpc::Document *doc,
    std::vector<awadb::Field> &fields);
  
  CallData *data_;
  // Context for the rpc, allowing to tweak aspects of it such as the use
  // of compression, authentication, as well as to send metadata back to the
  // client.
  ServerContext ctx_;

  // What we get from the client.
  awadb_grpc::DocCondition request_;
  // What we send back to the client.
  awadb_grpc::Documents reply_;

  // The means to get back to the client.
  ServerAsyncResponseWriter<awadb_grpc::Documents> responder_;

  // Let's implement a tiny state machine with the following states.
  enum CallStatus { CREATE, PROCESS, FINISH };
  CallStatus status_;  // The current serving state.
};

// Class encompasing the state and logic needed to serve a Search request.
class SearchCall final : public Call {
 public:
  explicit SearchCall(CallData *data) : data_(data), responder_(&ctx_), status_(CREATE) {
    // Invoke the serving logic right away.
    Proceed();
  }

  void Proceed();

 private:
  void ProcessSearchRequest();
  CallData *data_;
  // Context for the rpc, allowing to tweak aspects of it such as the use
  // of compression, authentication, as well as to send metadata back to the
  // client.
  ServerContext ctx_;

  // What we get from the client.
  awadb_grpc::SearchRequest request_;
  // What we send back to the client.
  awadb_grpc::SearchResponse reply_;

  // The means to get back to the client.
  ServerAsyncResponseWriter<awadb_grpc::SearchResponse> responder_;

  // Let's implement a tiny state machine with the following states.
  enum CallStatus { CREATE, PROCESS, FINISH };
  CallStatus status_;  // The current serving state.
};


// Class encompasing the state and logic needed to serve a Search request.
class DeleteCall final : public Call {
 public:
  explicit DeleteCall(CallData *data) : data_(data), responder_(&ctx_), status_(CREATE) {
    // Invoke the serving logic right away.
    Proceed();
  }

  void Proceed();

 private:
  bool ProcessDeleteRequest();
  CallData *data_;
  // Context for the rpc, allowing to tweak aspects of it such as the use
  // of compression, authentication, as well as to send metadata back to the
  // client.
  ServerContext ctx_;

  // What we get from the client.
  awadb_grpc::DocCondition request_;
  // What we send back to the client.
  awadb_grpc::ResponseStatus reply_;

  // The means to get back to the client.
  ServerAsyncResponseWriter<awadb_grpc::ResponseStatus> responder_;

  // Let's implement a tiny state machine with the following states.
  enum CallStatus { CREATE, PROCESS, FINISH };
  CallStatus status_;  // The current serving state.
};


#endif
