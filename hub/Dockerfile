FROM golang:1.21
WORKDIR /awadb_proxy
COPY go.mod go.sum ./
RUN go mod download
COPY hub_local_proxy.go ./
COPY awadb.io ./
COPY hub ./
RUN go build -o hub_local_proxy hub_local_proxy.go

EXPOSE 8080
CMD ["./hub_local_proxy", "local"]
