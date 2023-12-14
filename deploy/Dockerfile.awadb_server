FROM docker.io/gcc:latest

RUN  mkdir /usr/awadb

RUN  mkdir /usr/awadb/lib

ADD lib/libfaiss.so /usr/awadb/lib

ADD lib/libopenblas.so.0 /usr/awadb/lib

ADD lib/libtbb.so.12 /usr/awadb/lib

ADD lib/libzstd.so.1 /usr/awadb/lib

ADD awadb_server /usr/awadb

ENV LD_LIBRARY_PATH /usr/awadb/lib:$LD_LIBRARY_PATH

WORKDIR /usr/awadb

#RUN  gcc test.cpp -o test

CMD ["./awadb_server", ".", "10000"]

