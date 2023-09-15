#--------------------------------------------
#              AWADB ENGINE
#--------------------------------------------
project(awadb C CXX)
cmake_minimum_required(VERSION 3.17)

list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake/Modules)

option(BUILD_TEST "Build tests" off)
option(BUILD_WITH_GPU "Build awadb with gpu index support" off)
option(BUILD_TOOLS "Build tools" off)
option(BUILD_FAISSLIKE_INDEX "Build faisslike index" off)
option(ENABLE_COVERAGE "Use gcov" off)
option(BUILD_SERVICE "Build awadb service" on)

exec_program(
    "sh"
    ${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party
    ARGS "build.sh" ${BUILD_WITH_GPU})

#ENV VARs
set(THIRDPARTY ${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party)
set(BTREE ${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party/btree)
set(GAMMA_C_API ${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/c_api)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(APPLE)
set(CMAKE_CXX_FLAGS_DEBUG "$ENV{CXXFLAGS} -std=c++14 -mavx2 -msse4 -mpopcnt -lomp -D_FILE_OFFSET_BITS=64 -D_LARGE_FILE -DOPEN_CORE -O0 -w -g3 -gdwarf-4 -undefined dynamic_lookup")
set(CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -std=c++14 -fPIC -fpermissive -m64 -Wall -O3 -mavx2 -msse4 -mpopcnt -lomp -D_FILE_OFFSET_BITS=64 -D_LARGE_FILE -Wformat -Wno-inconsistent-missing-override -Wconstant-conversion -Werror=narrowing -Wno-deprecated")
else(APPLE)
set(CMAKE_CXX_FLAGS_DEBUG "$ENV{CXXFLAGS} -std=c++14 -mavx2 -msse4 -mpopcnt -fopenmp -D_FILE_OFFSET_BITS=64 -D_LARGE_FILE -DOPEN_CORE -O0 -w -g3 -gdwarf-2 -undefined dynamic_lookup")
set(CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -std=c++14 -fPIC -fpermissive -m64 -Wall -O3 -mavx2 -msse4 -mpopcnt -fopenmp -D_FILE_OFFSET_BITS=64 -D_LARGE_FILE -Werror=narrowing -Wno-error=deprecated-declarations -Wno-deprecated-declarations")
endif(APPLE)


if(DEFINED ENV{ROCKSDB_HOME})
    message(STATUS "RocksDB home is set=$ENV{ROCKSDB_HOME}")
    add_definitions(-DWITH_ROCKSDB)
    find_package(RocksDB REQUIRED)
else(DEFINED ENV{ROCKSDB_HOME})
    message(STATUS "RocksDB home isn't set, so store_type=RocksDB is not supported! ")
endif(DEFINED ENV{ROCKSDB_HOME})

if(DEFINED ENV{ZFP_HOME})
    MESSAGE(STATUS "ZFP home is set=$ENV{ZFP_HOME}")
    ADD_DEFINITIONS(-DWITH_ZFP)
    FIND_PACKAGE(ZFP REQUIRED)
else(DEFINED ENV{ZFP_HOME})
    MESSAGE(STATUS "ZFP home isn't set, so COMPRESS is not supported! ")
endif(DEFINED ENV{ZFP_HOME})

if(APPLE)
include_directories(
        /usr/local/include   # clang compiler for omp.h
	)
	
link_directories(
        /usr/local/lib       # clang compiler for libomp
	)
endif(APPLE)

include_directories(
	${CMAKE_CURRENT_SOURCE_DIR}
	${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine
	${THIRDPARTY}
	${BTREE}
	${THIRDPARTY}/faiss
	${RocksDB_INCLUDE_DIR}
	${ZFP_INCLUDE_DIR}
	${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party/zstd/lib     
	${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party/openssl/include
	${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party/TBB/include
	${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party/OpenBLAS)

link_directories(
        ${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party/faiss/build/faiss
	${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party/openssl
	${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party/TBB/build/lib
	${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party/zstd/lib
	${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/third_party/OpenBLAS)


#LINK LIBRARY
find_package(MKL)
if(MKL_FOUND)
    set(LIBRARIES
	-lfaiss_avx2
        ${RocksDB_LIB}
        ${ZFP_LIB}
        $-lcrypto
        -lzstd
        ${MKL_LIBRARIES}
        -ltbb
    )
else()
    set(LIBRARIES
	#-lfaiss_avx2
	-lfaiss 
	${RocksDB_LIB}
        ${ZFP_LIB}
	-lcrypto
        -lzstd
        -lopenblas
        -ltbb
   ) 
endif()

message(STATUS ENABLE_COVERAGE=${ENABLE_COVERAGE})
if(ENABLE_COVERAGE)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-arcs -ftest-coverage")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fprofile-arcs -ftest-coverage")
endif()

if(BUILD_FAISSLIKE_INDEX)
    add_definitions(-DFAISSLIKE_INDEX)
    MESSAGE(STATUS "BUILD_FAISSLIKE_INDEX=ON")
endif(BUILD_FAISSLIKE_INDEX)

#ADDITIONAL SOURCE DIR
aux_source_directory(${THIRDPARTY} DIR_SRCS)
aux_source_directory(${BTREE} DIR_SRCS)
aux_source_directory(${GAMMA_C_API} DIR_SRCS)
aux_source_directory(${GAMMA_C_API}/api_data DIR_SRCS)
aux_source_directory(${THIRDPARTY}/cjson DIR_SRCS)
aux_source_directory(${THIRDPARTY}/easyloggingpp DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/util DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/common DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/search DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/index DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/storage DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/storage/compress DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/index/impl DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/index/impl/hnswlib DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/index/impl/ssg DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/vector DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/realtime DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/table DIR_SRCS)
aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/io DIR_SRCS)

add_definitions(-DHAVE_NETINET_IN_H)
add_definitions(-DFINTEGER=int)

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    message(STATUS "Debug Mode")
    message(STATUS "Flags:" ${CMAKE_CXX_FLAGS_DEBUG})
    add_definitions(-DDEBUG_) 
else(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "build type" FORCE)
    message(STATUS "Release Mode")
    message(STATUS "Flags:" ${CMAKE_CXX_FLAGS_RELEASE})
endif(CMAKE_BUILD_TYPE STREQUAL "Debug")

exec_program(
    "git"
    ${CMAKE_CURRENT_SOURCE_DIR}
    ARGS "log --format='[sha1]:%h [author]:%cn [time]:%ci [branch]:%d' -1"
    OUTPUT_VARIABLE VERSION_SHA1)

add_definitions(-DGIT_SHA1="${VERSION_SHA1}")

if(PERFORMANCE_TESTING STREQUAL "ON")
    message(STATUS "With preformance testing")
    add_definitions(-DPERFORMANCE_TESTING) 
endif(PERFORMANCE_TESTING STREQUAL "ON")

set(LIB_SRCS ${DIR_SRCS} ${RELAYOUT_SRCS})

if(BUILD_WITH_GPU)
    message(STATUS "With GPU")
    add_definitions(-DBUILD_GPU) 
    set(GAMMA_GPU ${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/index/impl/gpu)

    aux_source_directory(${GAMMA_GPU} DIR_SRCS)

    include(cmake/Modules/gpu/CUDA.cmake)
    
    file(GLOB_RECURSE FAISS_GPU_HEADERS ${GAMMA_GPU}/*.h)
    file(GLOB_RECURSE FAISS_GPU_CPP ${GAMMA_GPU}/*.cpp)
    file(GLOB_RECURSE FAISS_GPU_CC ${GAMMA_GPU}/*.cc)
    file(GLOB_RECURSE FAISS_GPU_CUH ${GAMMA_GPU}/*.cuh)
    file(GLOB_RECURSE FAISS_GPU_CU ${GAMMA_GPU}/*.cu)

    include_directories(
        ${GAMMA_GPU}
        ${FAISS_INCLUDE_DIR}
        ${CUDA_INCLUDE_DIRS}
    )

    CUDA_ADD_LIBRARY(awa SHARED 
    ${FAISS_GPU_HEADERS}
    ${FAISS_GPU_CPP}
    ${FAISS_GPU_CC}
    ${FAISS_GPU_CUH}
    ${FAISS_GPU_CU}
    ${LIB_SRCS})

    target_link_libraries(awa 
    ${LIBRARIES}
    -lcublas 
    /usr/local/cuda/lib64/libcudart.so
    )

else(BUILD_WITH_GPU)
	add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/pybind11)
	pybind11_add_module(awa SHARED ${CMAKE_CURRENT_SOURCE_DIR}/awadb/interface/awadb_python_interface.cpp ${LIB_SRCS})
	target_link_libraries(awa PUBLIC ${LIBRARIES})

endif(BUILD_WITH_GPU)

install(TARGETS awa 
	LIBRARY	DESTINATION	lib 
	ARCHIVE	DESTINATION	lib)

install(FILES ${GAMMA_C_API}/gamma_api.h DESTINATION include/gamma)
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/index DESTINATION include/gamma FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/common DESTINATION include/gamma FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/realtime DESTINATION include/gamma FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/search DESTINATION include/gamma FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/io DESTINATION include/gamma FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/table DESTINATION include/gamma FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/util DESTINATION include/gamma FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/storage DESTINATION include/gamma FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/vector DESTINATION include/gamma FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/c_api DESTINATION include/gamma FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/idl/fbs-gen/c DESTINATION include/gamma/idl/fbs-gen FILES_MATCHING PATTERN "*.h")
install(DIRECTORY ${PROJECT_SOURCE_DIR}/awadb/db_engine/third_party DESTINATION include/gamma FILES_MATCHING PATTERN "*.h" PATTERN "*.hh")

if(BUILD_SERVICE)
    get_filename_component(awadb_proto "${CMAKE_CURRENT_SOURCE_DIR}/service/protos/awadb.proto" ABSOLUTE)
    get_filename_component(awadb_proto_path "${awadb_proto}" PATH)

    exec_program(
        "sh"
        ${CMAKE_CURRENT_SOURCE_DIR}/service
        ARGS "init_env.sh")

    # Generated sources
    set(awadb_proto_srcs "${CMAKE_CURRENT_SOURCE_DIR}/service/idl/awadb.pb.cc")
    set(awadb_proto_hdrs "${CMAKE_CURRENT_SOURCE_DIR}/service/idl/awadb.pb.h")
    set(awadb_grpc_srcs "${CMAKE_CURRENT_SOURCE_DIR}/service/idl/awadb.grpc.pb.cc")
    set(awadb_grpc_hdrs "${CMAKE_CURRENT_SOURCE_DIR}/service/idl/awadb.grpc.pb.h")
    set(_PROTOBUF_PROTOC ${CMAKE_CURRENT_SOURCE_DIR}/service/grpc/bin/protoc)
    set(_GRPC_CPP_PLUGIN_EXECUTABLE ${CMAKE_CURRENT_SOURCE_DIR}/service/grpc/bin/grpc_cpp_plugin)
    add_custom_command(
        OUTPUT "${awadb_proto_srcs}" "${awadb_proto_hdrs}" "${awadb_grpc_srcs}" "${awadb_grpc_hdrs}"
        COMMAND ${_PROTOBUF_PROTOC}
        ARGS --grpc_out "${CMAKE_CURRENT_SOURCE_DIR}/service/idl"
          --cpp_out "${CMAKE_CURRENT_SOURCE_DIR}/service/idl"
          -I "${awadb_proto_path}"
          --plugin=protoc-gen-grpc="${_GRPC_CPP_PLUGIN_EXECUTABLE}"
          "${awadb_proto}"
        DEPENDS "${awadb_proto}")

    # Include generated *.pb.h files
    include_directories("${CMAKE_CURRENT_SOURCE_DIR}/service/idl")

    include_directories("${CMAKE_CURRENT_SOURCE_DIR}/service/grpc/include")

    find_package(Threads REQUIRED)

    option(protobuf_MODULE_COMPATIBLE TRUE)
    find_package(Protobuf CONFIG REQUIRED)
    message(STATUS "Using protobuf ${Protobuf_VERSION}")

    set(_PROTOBUF_LIBPROTOBUF protobuf::libprotobuf)
    set(_REFLECTION gRPC::grpc++_reflection)
  
    # Find gRPC installation
    # Looks for gRPCConfig.cmake file installed by gRPC's cmake installation.
    find_package(gRPC CONFIG REQUIRED)
    message(STATUS "Using gRPC ${gRPC_VERSION}")

    set(_GRPC_GRPCPP gRPC::grpc++)

    # awadb_grpc_proto
    add_library(awadb_grpc_proto
      ${awadb_grpc_srcs}
      ${awadb_grpc_hdrs}
      ${awadb_proto_srcs}
      ${awadb_proto_hdrs})

    link_directories(${CMAKE_CURRENT_SOURCE_DIR}/service/grpc/lib)

    target_link_libraries(awadb_grpc_proto
      ${_REFLECTION}
      ${_GRPC_GRPCPP}
      ${_PROTOBUF_LIBPROTOBUF})

    aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/service/servers/local AWADB_SERVER_SRCS)

    # Targets awadb_(client|server)
    add_executable(awadb_server
        ${AWADB_SERVER_SRCS}
	${LIB_SRCS})

    target_link_libraries(awadb_server
	${LIBRARIES}
        awadb_grpc_proto
        ${_REFLECTION}
        ${_GRPC_GRPCPP}
        ${_PROTOBUF_LIBPROTOBUF})

endif(BUILD_SERVICE)

if(BUILD_TEST)
    add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/tests)
endif(BUILD_TEST)

if(BUILD_TOOLS)
    add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/awadb/db_engine/tools)
endif(BUILD_TOOLS)
