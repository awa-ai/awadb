#!/bin/bash


OS_TYPE='Linux'
system=`uname`
if [ "$system" == "Darwin" ]; then
    OS_TYPE='MacOS'
fi


# Download and install openblas
if [ ! -d OpenBLAS ]; then
    wget https://github.com/xianyi/OpenBLAS/archive/refs/tags/v0.3.23.tar.gz 
    tar -xf v0.3.23.tar.gz
    mv OpenBLAS-0.3.23 OpenBLAS 
    cd OpenBLAS
    make -j4
    make install
    cd ..
    rm v0.3.23.tar.gz
fi

# Install faiss
if [ ! -d faiss ]; then
    tar -xf faiss-1.7.1.tar.gz
    mv faiss-1.7.1 faiss
    cd faiss
    c_compiler=`which gcc`
    cxx_compiler=`which g++`
    current_path=`pwd`
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$current_path/../OpenBLAS
    cmake -DCMAKE_CXX_COMPILER=$cxx_compiler -DCMAKE_C_COMPILER=$c_compiler -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=ON -DFAISS_OPT_LEVEL=avx2 -B build .
    make -C build -j4 faiss
    cd ..
fi


# Download and install openssl
if [ ! -d openssl ]; then
    wget --no-check-certificate  https://www.openssl.org/source/old/1.0.2/openssl-1.0.2u.tar.gz
    tar -xf openssl-1.0.2u.tar.gz
    mv openssl-1.0.2u openssl
    cd openssl
    # if MacOS
    if [ "$OS_TYPE" == "MacOS" ]; then
        ./Configure darwin64-x86_64-cc
    else
        ./config -fPIC
    fi
    make -j4
    cd ..
    rm openssl-1.0.2u.tar.gz
fi

# Download and install tbb

if [ ! -d TBB ]; then
    wget --no-check-certificate https://github.com/oneapi-src/oneTBB/archive/refs/tags/v2021.9.0.tar.gz
    tar -xf v2021.9.0.tar.gz
    mv oneTBB-2021.9.0 TBB
    cd TBB
    cmake -B build .
    make -C build -j4 tbb

    tbb_build_dir=`ls -l build/*/lib* | head -1 | awk -F'/' '{print $2}'`
    if [ -z "$tbb_build_dir" ]; then
        echo "tbb build failed"
    else
        mv build/$tbb_build_dir build/lib
    fi
    cd ..
    rm v2021.9.0.tar.gz
fi

# Download and install zstd
if [ ! -d zstd ]; then
    wget --no-check-certificate https://github.com/facebook/zstd/archive/refs/tags/v1.5.5.tar.gz
    tar -xf v1.5.5.tar.gz
    mv zstd-1.5.5 zstd
    cd zstd
    make -j4
    # if MacOS
    if [ "$OS_TYPE" == "MacOS" ]; then
        mkdir -p lib/shared_lib
        mv lib/lib*.dylib lib/shared_lib
    fi

    cd ..
    rm v1.5.5.tar.gz
fi

