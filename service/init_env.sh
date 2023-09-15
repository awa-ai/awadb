#!/bin/bash

# init idl directory
rm -rf idl
mkdir idl

# prepare grpc environment
if [ ! -d grpc ]; then
    git clone -b v1.57.0 https://github.com/grpc/grpc
    cd grpc
    git submodule update --init
    current_path=`pwd`
    mkdir -p cmake/build
    cd cmake/build
    
    cmake ../.. -DgRPC_INSTALL=ON                      \
	        -DCMAKE_BUILD_TYPE=Release             \
                -DCMAKE_INSTALL_PREFIX=$current_path
    make -j4
    make install
    cd ../..
fi

