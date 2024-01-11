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

// Hub Local Proxy for local awadb server.
// Suply the RESTFul and gRPC service.
package main

import (
	"os"
        "context"
	"fmt"
        "math"
	"encoding/binary"
	"log"
	"net"
	"time"
	"strings"
	"strconv"
	"errors"
	"google.golang.org/grpc"
        "google.golang.org/grpc/credentials/insecure"
	"github.com/google/uuid"

	awadb_pb "hub/awadb.io/go/pb_grpc"

	"net/http"
	"github.com/gin-gonic/gin"
)

type AwaDBServer struct {
	awadb_pb.AwaDBServerServer
}

func CreateAwaDBClient(addr *string) *awadb_pb.AwaDBServerClient {
	conn, err := grpc.Dial(*addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("did not connect: %v", err)
		return nil
	}
	//defer conn.Close()
	client := awadb_pb.NewAwaDBServerClient(conn)
	return &client
}


func (s *AwaDBServer) AddFields(ctx context.Context, db_meta *awadb_pb.DBMeta) (*awadb_pb.ResponseStatus, error) {
	if local_awadb_client == nil  {
		log.Fatalf("local awadb client is nil!")
	        err  := errors.New("local awadb client is nil!")
		return nil, err
	}
	return (*local_awadb_client).AddFields(ctx, db_meta)
}

func (s *AwaDBServer) AddOrUpdate(ctx context.Context, in *awadb_pb.Documents) (*awadb_pb.ResponseStatus, error) {
	if local_awadb_client == nil  {
		log.Fatalf("local awadb client is nil!")
	        err := errors.New("local awadb client is nil!")
		return nil, err
	}
	return (*local_awadb_client).AddOrUpdate(ctx, in)
}

func (s *AwaDBServer) Get(ctx context.Context, doc_condition *awadb_pb.DocCondition) (*awadb_pb.Documents, error) {
	if local_awadb_client == nil  {
		log.Fatalf("local awadb client is nil!")
	        err := errors.New("local awadb client is nil!")
		return nil, err
	}
	return (*local_awadb_client).Get(ctx, doc_condition)
}

func (s *AwaDBServer) Search(ctx context.Context, search_request *awadb_pb.SearchRequest) (*awadb_pb.SearchResponse, error) {
	if local_awadb_client == nil  {
		log.Fatalf("local awadb client is nil!")
	        err := errors.New("local awadb client is nil!")
		return nil, err
	}
	return (*local_awadb_client).Search(ctx, search_request)
}

func (s *AwaDBServer) Delete(ctx context.Context, doc_condition *awadb_pb.DocCondition) (*awadb_pb.ResponseStatus, error) {
	if local_awadb_client == nil  {
		log.Fatalf("local awadb client is nil!")
	        err := errors.New("local awadb client is nil!")
		return nil, err
	}
	return (*local_awadb_client).Delete(ctx, doc_condition)
}

func (s *AwaDBServer) CheckTable(ctx context.Context, db_table_name *awadb_pb.DBTableName) (*awadb_pb.TableStatus, error) {
	if local_awadb_client == nil  {
		log.Fatalf("local awadb client is nil!")
	        err := errors.New("local awadb client is nil!")
		return nil, err
	}
	return (*local_awadb_client).CheckTable(ctx, db_table_name)
}

func (s *AwaDBServer) Create(ctx context.Context, db_meta *awadb_pb.DBMeta) (*awadb_pb.ResponseStatus, error) {
	if local_awadb_client == nil  {
		log.Fatalf("local awadb client is nil!")
	        err := errors.New("local awadb client is nil!")
		res := &awadb_pb.ResponseStatus {
			Code: awadb_pb.ResponseCode_INTERNAL_ERROR,
			OutputInfo: "local awadb client is nil",
		}
		return res, err
	}
	return (*local_awadb_client).Create(ctx, db_meta)
}

func RunGrpcServer(grpc_port int) error {
	server, err := net.Listen("tcp", fmt.Sprintf(":%d", grpc_port))
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
		return err
	}
	fmt.Printf("server listening at %v\n", server.Addr())

	grpc_server := grpc.NewServer()

	awadb_pb.RegisterAwaDBServerServer(grpc_server, &AwaDBServer{})
	return grpc_server.Serve(server)
}

func IsDecimal(a float64) bool {
	str := fmt.Sprint(a)
	return strings.Contains(str, ".")
}

func Int64tobytes(a int64) []byte {
	b := make([]byte, 8)
        binary.LittleEndian.PutUint64(b, uint64(a))
	return b
}

func Int32tobytes(a int32) []byte {
	b := make([]byte, 4)
        binary.LittleEndian.PutUint32(b, uint32(a))
	return b
}

func Float32tobytes(a float32) []byte {
	bits := math.Float32bits(a)
	res := make([]byte, 4)

	binary.LittleEndian.PutUint32(res, bits)
	return res
}

func AssembleRangeFilters(range_filters *[]*awadb_pb.RangeFilter, filter_value interface{}) bool  {
	switch filter_value.(type) {
	case map[string]interface{}:
		if len(*range_filters) == 0 {
			*range_filters = make([]*awadb_pb.RangeFilter, 0)
		}
		for filter_field_name, filter_field_value := range filter_value.(map[string]interface{}) {
			range_filter := &awadb_pb.RangeFilter{}
			range_filter.LowerValue = make([]byte, 4)
			bits := math.Float32bits((float32)(-9999999))
			binary.LittleEndian.PutUint32(range_filter.LowerValue, bits)

			range_filter.UpperValue = make([]byte, 4)
			bits = math.Float32bits((float32)(99999999))
			binary.LittleEndian.PutUint32(range_filter.UpperValue, bits)

			default_include_lower := false
			default_include_upper := false
			range_filter.IncludeLower = &default_include_lower
			range_filter.IncludeUpper = &default_include_upper

			range_filter.FieldName = &filter_field_name
			is_data_ok := true
			switch filter_field_value.(type)  {
			case map[string]interface{}:
				for range_key, range_value := range filter_field_value.(map[string]interface{})  {
					switch range_value.(type)  {
					case  float64:
						AssignRangeValue(range_value.(float64), range_filter, &range_key)
					default:
						fmt.Println("filter value format error!")
						is_data_ok = false
						continue
					}
				}
			default:
				fmt.Println("filter format error!")
				is_data_ok = false
				continue
			}
			if is_data_ok  {
				*range_filters = append(*range_filters, range_filter)
			}
		}
		if len(*range_filters) == 0 {
			return false
		}
	default:
		fmt.Println("range filters format error!")
		return false
	}
	return true
}

func AssembleVectorQuery(db_table_name *string, vector_query *awadb_pb.VectorQuery, vector_struct map[string]interface{}) bool {
	min_score := (float32)(-1)
	max_score := (float32)(999999)
	vector_query.MinScore = &min_score
	vector_query.MaxScore = &max_score
	boost := (float32)(1.0)
        vector_query.Boost = &boost
	is_boost := true
	vector_query.IsBoost = &is_boost

	for key, value := range vector_struct {
		if key == "min_score" {
			switch value.(type) {
			case float64:
				min_value := (float32)(value.(float64))
				vector_query.MinScore = &min_value
			default:
				fmt.Println("min_score format error!")
			}
		}  else if key == "max_score" {
			switch value.(type) {
			case float64:
				max_value := (float32)(value.(float64))
				vector_query.MaxScore = &max_value
			default:
				fmt.Println("max_score format error!")
			}
		}  else if key == "weight"  {
			switch value.(type) {
			case float64:
				boost_value := (float32)(value.(float64))
				vector_query.Boost = &boost_value
				is_boost := true
				vector_query.IsBoost = &is_boost
			default:
				fmt.Println("weight format error!")
			}
		}  else  { // todo : decide whether the field is valid
			table_fields, ok := checked_tables_schema[*db_table_name]
			if !ok {
				fmt.Println("db table not exist!")
				return false
			}
			field_type, field_ok := (table_fields.(map[string]*awadb_pb.FieldType))[key]
			if !field_ok || *field_type != awadb_pb.FieldType_VECTOR {
				fmt.Println("vector field invalid")
				return false
			}

			switch value.(type) {
			case []any:
				is_all_float := true
				for _, e := range value.([]any) {
					switch e.(type) {
					case float64:
					default:
						is_all_float = false
					}
				}
				if !is_all_float {
					return false
				}
				// check whether the field is valid
				field_name_value := key
				vector_query.FieldName = &field_name_value

				dim := len(value.([]any))
				vector_query.Value = make([]byte, dim * 4)
				idx := 0
				for _, e := range value.([]any) {
					bits := math.Float32bits((float32)(e.(float64)))
					binary.LittleEndian.PutUint32(vector_query.Value[idx * 4: (idx + 1) * 4], bits)
					idx = idx + 1
				}
			default:
				fmt.Println("vector value format error!")
				return false
			}
		}
	}
	return true
}

func AssembleTermFilters(term_filters []*awadb_pb.TermFilter, filter_value interface{}) bool  {
	switch filter_value.(type)  {
	case map[string]interface{}:
		if len(term_filters) == 0 {
			term_filters = make([]*awadb_pb.TermFilter, 0)
	        }
		for filter_field_name, filter_field_value := range filter_value.(map[string]interface{})  {
			term_filter := &awadb_pb.TermFilter{}
			term_filter.FieldName = &filter_field_name
                        // todo : check filter is ok?			
			is_data_ok := true
			has_operator := false
			switch filter_field_value.(type)  {
			case map[string]interface{}:
				for range_key, range_value := range filter_field_value.(map[string]interface{})  {
					if range_key == "value"  {
						switch range_value.(type) {
						case string:
							str_value, ok := range_value.(string)
							if ok  {
								term_filter.Value = &str_value
							}
						default:
							is_data_ok = false
						}
					}  else if range_key == "operator"  {
						switch range_value.(type) {
						case string:
							has_operator = true
							if range_value.(string) == "or"  {
								op_value := int32(1)
								term_filter.IsUnion = &op_value
							} else if range_value.(string) == "and"  {
								op_value := int32(0)
								term_filter.IsUnion = &op_value
							} else  {
								is_data_ok = false
							}
						default:
							is_data_ok = false
						}
					}  else  {
						is_data_ok = false
					}
				}
			default:
				fmt.Println("term filter format error!")
				is_data_ok = false
				continue
			}
			if is_data_ok  {
				if !has_operator  {
					op_value := int32(1)
					term_filter.IsUnion = &op_value
				}
				term_filters = append(term_filters, term_filter)
			}
		}

		if len(term_filters) == 0 {
			return false
	        }
	default:
		fmt.Println("term filter format error!")
		return false
	}
	return true
}


func AssignRangeValue(value float64, range_filter *awadb_pb.RangeFilter, value_type *string) {
        if *value_type != "eq" && *value_type != "lt" && *value_type != "lte" && *value_type != "gt" && *value_type != "gte"  {
		fmt.Println("filter parameter error!")
		return
	}
	if IsDecimal(value)  {
		if *value_type == "lt" || *value_type == "lte" {
			range_filter.UpperValue = Float32tobytes((float32)(value))
		}  else if *value_type == "gt" || *value_type == "gte"  {
			range_filter.LowerValue = Float32tobytes((float32)(value))
		}  else if  *value_type == "eq"  {
			range_filter.LowerValue = Float32tobytes((float32)(value))
			range_filter.UpperValue = Float32tobytes((float32)(value))
		}
	}  else  {
		if *value_type == "lt" || *value_type == "lte" {
			range_filter.UpperValue = Int32tobytes(int32(value))
		}  else if *value_type == "gt" || *value_type == "gte"  {
			range_filter.LowerValue = Int32tobytes(int32(value))
		}  else if *value_type == "eq"  {
			range_filter.UpperValue = Int32tobytes(int32(value))
			range_filter.LowerValue = Int32tobytes(int32(value))
		}
	}

	if *value_type == "lte" {
		include_upper := true
		range_filter.IncludeUpper = &include_upper
	}  else if *value_type == "lt" {
		include_upper := false
		range_filter.IncludeUpper = &include_upper
	}  else if *value_type == "gte" {
		include_lower := true
		range_filter.IncludeLower = &include_lower
	}  else if *value_type == "gt"  {
		include_lower := false
		range_filter.IncludeLower = &include_lower
	}  else if *value_type == "eq"  {
		include_upper := true
		range_filter.IncludeUpper = &include_upper
		include_lower := true
		range_filter.IncludeLower = &include_lower
	}
}

func AssembleTableFields(field_meta *awadb_pb.FieldMeta, field_struct map[string]interface{}, c *gin.Context) (bool, bool)  {
	is_primary_key := false
	is_vector_field := false
	for field_key, field_value := range field_struct {
		if field_key == "name"  {
			switch field_value.(type) {
			case string:
				field_name := field_value.(string)
				field_meta.Name = &field_name
				if *field_meta.Name == "_id" {
					is_primary_key = true
				}
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Field name error":"field name should be string!"})
				return false, false
			}
		}  else if field_key == "type"  {
			switch field_value.(type) {
			case string:
				field_value_str := field_value.(string)
				field_type := awadb_pb.FieldType_INT
				if field_value_str == "string"  {
					field_type = awadb_pb.FieldType_STRING
				}  else if field_value_str == "int" {
					field_type = awadb_pb.FieldType_INT
				}  else if field_value_str == "long" {
					field_type = awadb_pb.FieldType_LONG
				}  else if field_value_str == "float" {
					field_type = awadb_pb.FieldType_FLOAT
				}  else if field_value_str == "double" {
					field_type = awadb_pb.FieldType_DOUBLE
				}  else if field_value_str == "vector" {
					field_type = awadb_pb.FieldType_VECTOR
					is_vector_field = true
				}  else if field_value_str == "multi_string" {
					field_type = awadb_pb.FieldType_MULTI_STRING
				}  else {
					c.JSON(http.StatusBadRequest, gin.H{"Field type error":"field type value wrong!"})
					return false, false
				}
				field_meta.Type = &field_type
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Field type error":"field type should be string!"})
				return false, false
			}
		}  else if field_key == "desc"  {
			switch field_value.(type)  {
			case string:
				desc := field_value.(string)
				field_meta.Desc = &desc
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Field desc format error":"field description should be string!"})
				return false, false
			}
		}  else if field_key == "index"  {
			switch field_value.(type)  {
			case bool:
				index := field_value.(bool)
				field_meta.IsIndex = &index
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Field index format error":"field index should be bool!"})
				return false, false
			}
		}  else if field_key == "store"  {
			switch field_value.(type)  {
			case bool:
				store := field_value.(bool)
				field_meta.IsStore = &store
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Field store error":"field store should be bool!"})
				return false, false
			}
		}  else if field_key == "dimension" {
			switch field_value.(type)  {
			case float64:
				dim := (int32)(field_value.(float64))
				if dim <= 0  {
					c.JSON(http.StatusBadRequest, gin.H{"Dimension error":"vector dimension should be int!"})
					return false, false
				}
				if field_meta.VecMeta == nil  {
					field_meta.VecMeta = &awadb_pb.VectorMeta{}
				}
				field_meta.VecMeta.Dimension = &dim
				field_type := awadb_pb.FieldType_FLOAT
				field_meta.VecMeta.DataType = &field_type
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Dimension format error":"vector dimension should be int!"})
				return false, false
			}
		}  else if field_key == "normalization" {
			switch field_value.(type)  {
			case bool:
				if field_meta.VecMeta == nil  {
					field_meta.VecMeta = &awadb_pb.VectorMeta{}
				}
				bool_value := field_value.(bool)
				field_meta.VecMeta.IsNormalization = &bool_value
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Normalization error":"vector normalization should be bool!"})
				return false, false
			}
		}  else if field_key == "embedding_model" {
			switch field_value.(type)  {
			case string:
				string_value := field_value.(string)
				field_meta.EmbeddingModel = &string_value
			default:
				c.JSON(http.StatusBadRequest, gin.H{"embedding_model format error":"embedding model parameter error!"})
				return false, false
			}
		}  else if field_key == "words_tokenizer"  {
			switch field_value.(type) {
			case string:
				string_value := field_value.(string)
				field_meta.WordsTokenizer = &string_value
			default:
				c.JSON(http.StatusBadRequest, gin.H{"words_tokenizer format error":"words_tokenizer parameter error!"})
				return false, false
			}
		}  else  {
			fmt.Println("Invalid field key", field_key)
		}
	}
	if *field_meta.Type == awadb_pb.FieldType_VECTOR  {
		if field_meta.VecMeta == nil || *field_meta.VecMeta.Dimension <= 0 {
			c.JSON(http.StatusBadRequest, gin.H{"Error":"Vector format error!Please check"})
			return false, false
		}
	}
	return is_primary_key, is_vector_field
}

func AssembleDoc(
	db_name *string,
	table_name *string,
	doc *awadb_pb.Document,
	doc_struct map[string]interface{},
	table_existed *bool)  bool {
	has_primary_key := false
	id_type := "string"
	vec_fields := make(map[*string]*awadb_pb.VectorMeta)
	for field_name, field_value := range doc_struct {
		field := &awadb_pb.Field{}
		each_field_name := field_name
		field.Name = &each_field_name
		if field_name == "_id"  {
			has_primary_key = true
			switch field_value.(type)  {
			case float64:
				if IsDecimal(field_value.(float64)) {
					fmt.Println("doc primary key should not be decimal!")
					return false
				}  else  {
					doc.Id = Int64tobytes((int64)(field_value.(float64)))
					id_type = "long"
					field_type := awadb_pb.FieldType_LONG
					field.Type = &field_type
					field.Value = doc.Id
				}
			case string:
				doc.Id = []byte(field_value.(string))
				field_type := awadb_pb.FieldType_STRING
				field.Type = &field_type
				field.Value = doc.Id

			default:
				fmt.Println("doc primary key format error!")
				return false
			}
		} else {
			if len(doc.Fields) == 0 {
				doc.Fields = make([]*awadb_pb.Field, 0)
			}
			switch field_value.(type) {
			case float64:
				if IsDecimal(field_value.(float64))  {
					field.Value = Float32tobytes((float32)(field_value.(float64)))
				        field_type := awadb_pb.FieldType_FLOAT
					field.Type = &field_type
				}  else {
					field.Value = Int32tobytes((int32)(field_value.(float64)))
				        field_type := awadb_pb.FieldType_INT
					field.Type = &field_type
				}
			case bool:
				field_type := awadb_pb.FieldType_INT
				field.Type = &field_type
				if field_value.(bool) == true  {
					field.Value = Int32tobytes(1)
				}  else {
					field.Value = Int32tobytes(0)
				}
			case string:
				field.Value = []byte(field_value.(string))
				field_type := awadb_pb.FieldType_STRING
				field.Type = &field_type
			case []any:
				is_all_string := true
				is_all_float := true
				for _, e := range field_value.([]any) {
					switch e.(type) {
					case string:
						is_all_float = false
					case float64:
						is_all_string = false
					default:
						is_all_float = false
						is_all_string = false
					}
				}
				if (is_all_string && is_all_float) || (!is_all_string && !is_all_float) {
					return false
				}
				if is_all_string && !is_all_float  {
					field_type := awadb_pb.FieldType_MULTI_STRING
					field.Type = &field_type
					if len(field.MulStrValue) == 0 {
						field.MulStrValue = make([]string, 0)
					}
					for _, e := range field_value.([]any) {
						field.MulStrValue = append(field.MulStrValue, e.(string))
					}
				} else if !is_all_string && is_all_float  {
					field_type := awadb_pb.FieldType_VECTOR
					field.Type = &field_type
					dim := len(field_value.([]any))
					field.Value = make([]byte, dim * 4)
					idx := 0
					for _, e := range field_value.([]any) {
						bits := math.Float32bits((float32)(e.(float64)))
						binary.LittleEndian.PutUint32(field.Value[idx * 4: (idx + 1) * 4], bits)
						idx = idx + 1
					}
					if !(*table_existed)  {
						vec_meta := &awadb_pb.VectorMeta{}
						data_type := awadb_pb.FieldType_FLOAT
						vec_meta.DataType = &data_type
						dim_value := (int32)(dim)
						vec_meta.Dimension = &dim_value
						is_normalization := false
						vec_meta.IsNormalization = &is_normalization
						store_type := "Mmap"
						vec_meta.StoreType = &store_type
						store_param := "{\"cache_size\" : 2000}"
						vec_meta.StoreParam = &store_param
						vec_fields[field.Name] = vec_meta
					}
				}
			default:
				fmt.Println("field value format error!")
				return false
			}
			if *table_existed  {
				db_table_name := *db_name + "/" + *table_name
				field_schema := checked_tables_schema[db_table_name].(map[string]*awadb_pb.FieldType)
				field_type, ok := field_schema[*field.Name]
				if !ok || *field_type != *field.Type  {
					if *field_type == awadb_pb.FieldType_LONG && *field.Type == awadb_pb.FieldType_INT  {
						field.Value = Int64tobytes((int64)(field_value.(float64)))
				                field_type := awadb_pb.FieldType_LONG
					        field.Type = &field_type
					}  else if *field_type == awadb_pb.FieldType_INT && *field.Type == awadb_pb.FieldType_LONG {
						field.Value = Int32tobytes((int32)(field_value.(float64)))
				                field_type := awadb_pb.FieldType_INT
					        field.Type = &field_type
					}  else  {
						return false
					}
				}
			}
		}
		doc.Fields = append(doc.Fields, field)
	}

	if !has_primary_key {
		uuid, err := uuid.NewUUID()
		if err != nil  {
			fmt.Println("Generate unique id failed!")
			return false
		}
		doc.Id = []byte(uuid.String())

		field := &awadb_pb.Field{}
		each_field_name := "_id"
		field.Name = &each_field_name
		field_type := awadb_pb.FieldType_STRING
		field.Type = &field_type
		field.Value = doc.Id
		doc.Fields = append(doc.Fields, field)
	}

	if !(*table_existed) {
		db_meta := &awadb_pb.DBMeta{}
		db_meta.DbName = db_name
		db_meta.TablesMeta = make([]*awadb_pb.TableMeta, 1)
		db_meta.TablesMeta[0] = &awadb_pb.TableMeta{}
		db_meta.TablesMeta[0].Name = table_name
		fields_num := len(doc.Fields)
		db_meta.TablesMeta[0].FieldsMeta = make([]*awadb_pb.FieldMeta, fields_num)
		table_fields := make(map[string]*awadb_pb.FieldType)
		primary_key_name := "_id"
		primary_key := &primary_key_name

		if id_type == "string" {
			field_type := awadb_pb.FieldType_STRING
			table_fields[*primary_key] = &field_type
		} else if id_type == "long" {
			field_type := awadb_pb.FieldType_LONG
			table_fields[*primary_key] = &field_type
		}

		field_idx := 0
		for _, field_meta := range doc.Fields {
			db_meta.TablesMeta[0].FieldsMeta[field_idx] = &awadb_pb.FieldMeta{}
			db_meta.TablesMeta[0].FieldsMeta[field_idx].Name = field_meta.Name
			db_meta.TablesMeta[0].FieldsMeta[field_idx].Type = field_meta.Type

			table_fields[*field_meta.Name] = field_meta.Type
			is_index := true
			if *field_meta.Type != awadb_pb.FieldType_STRING {
				db_meta.TablesMeta[0].FieldsMeta[field_idx].IsIndex = &is_index
			}  else {
				is_index = false
				db_meta.TablesMeta[0].FieldsMeta[field_idx].IsIndex = &is_index
			}
			is_store := true
			db_meta.TablesMeta[0].FieldsMeta[field_idx].IsStore = &is_store
			if *field_meta.Type == awadb_pb.FieldType_VECTOR {
				db_meta.TablesMeta[0].FieldsMeta[field_idx].VecMeta = vec_fields[field_meta.Name]
			}
			field_idx = field_idx + 1
		}

                if local_awadb_client != nil  {
			ctx, cancel := context.WithTimeout(context.Background(), time.Second)
			defer cancel()

			_, err := (*local_awadb_client).Create(ctx, db_meta)
			if err != nil  {
				fmt.Println("create table failed :", err.Error())
				return false
			}
		}  else  {
			fmt.Println("awadb server client has error!")
			return false
		}


		db_table_name := *db_name + "/" + *table_name
		checked_tables_schema[db_table_name] = table_fields
	}
	return true
}

func CheckTableFromServer(db *string, table *string) (*awadb_pb.TableStatus, error) {
	db_table := &awadb_pb.DBTableName{}
	db_table.DbName = db
	db_table.TableName = table

	if local_awadb_client != nil  {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		table_status, err := (*local_awadb_client).CheckTable(ctx, db_table)
		if err != nil  {
			fmt.Println("Check table failed :", err.Error())
			return nil, err
		}
		return table_status, nil
	}

	err  := errors.New("local awadb client is nil!")
	return nil, err
}

func QueryTableDetail(db *string, table *string) (*awadb_pb.TableDetail, error) {
	db_table := &awadb_pb.DBTableName{}
	db_table.DbName = db
	db_table.TableName = table

	if local_awadb_client != nil  {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()
		table_detail, err := (*local_awadb_client).QueryTableDetail(ctx, db_table)
		if err != nil  {
			fmt.Println("Query table detail failed :", err.Error())
			return nil, err
		}
		return table_detail, nil
	}

	err  := errors.New("local awadb client is nil!")
	return nil, err
}

func DocsToJson(docs *awadb_pb.Documents, c *gin.Context) {
	if docs.DbName == nil || docs.TableName == nil  {
		c.JSON(http.StatusBadRequest, gin.H{"Error":"Db or table is empty in results!"})
		return
	}
	json_docs := make(map[string]interface{})
	json_docs["Db"] = *docs.DbName
	json_docs["Table"] = *docs.TableName
	docs_struct := make([]map[string]interface{}, 0)
	for _, doc := range docs.Docs {
		json_doc := make(map[string]interface{})
		for _, field := range doc.Fields {
			if *field.Type == awadb_pb.FieldType_STRING {
				json_doc[*field.Name] = string(field.Value)
			}  else if *field.Type == awadb_pb.FieldType_INT {
				num, err := strconv.ParseInt(string(field.Value), 10, 32)
				if err != nil {
					panic(err)
				}
				json_doc[*field.Name] = num
			}  else if *field.Type == awadb_pb.FieldType_FLOAT {
				num, err := strconv.ParseFloat(string(field.Value), 32)
				if err != nil {
					panic(err)
				}
				json_doc[*field.Name] = num
			}  else if *field.Type == awadb_pb.FieldType_LONG {
				num, err := strconv.ParseInt(string(field.Value), 10, 64)
				if err != nil {
					panic(err)
				}
				json_doc[*field.Name] = num
			}  else if *field.Type == awadb_pb.FieldType_MULTI_STRING {
				//MulStrValue []string
				//json_doc[*field.Name] = 
			}  else if *field.Type == awadb_pb.FieldType_VECTOR {
				json_doc[*field.Name] = string(field.Value)
			}
		}
		docs_struct = append(docs_struct, json_doc)
	}
	json_docs["Docs"] = docs_struct
	c.JSON(http.StatusOK, json_docs)
}

func TableDetailToJson(db_name *string, table_name *string, table_detail *awadb_pb.TableDetail, c *gin.Context) {
	if table_detail == nil {
		c.JSON(http.StatusBadRequest, gin.H{"Error":"TableDetail is nil!"})
		return
	}
	json_docs := make(map[string]interface{})
	json_docs["Db"] = *db_name
	json_docs["Table"] = *table_name
	json_docs["CurrentDocs"] = *table_detail.CurrentValidDocs
	json_docs["TotalDocs"] = *table_detail.TotalDocs
	json_docs["DeletedDocs"] = *table_detail.DeletedDocs
	//json_docs["TableMemBytes"] = *table_detail.TableMemBytes
	//json_docs["VectorIndexBytes"] = *table_detail.VectorsIndexBytes
        //json_docs["VectorMemBytes"] = *table_detail.VectorsMemBytes
        //json_docs["FiltersIndexBytes"] = *table_detail.FiltersIndexBytes
        //json_docs["BitmapMemBytes"] = *table_detail.BitmapMemBytes
	c.JSON(http.StatusOK, json_docs)
	return
}

func SearchResultsToJson(res *awadb_pb.SearchResponse, c *gin.Context) {
	results := make(map[string]interface{})
	results["Db"] = *res.DbName
	results["Table"] = *res.TableName
	results_struct := make(map[string]interface{})
	for _, result := range res.Results {
		results_struct["ResultSize"] = *result.Total
		results_struct["Msg"] = *result.Msg

		result_items := make([]map[string]interface{}, 0)
		for _, result_item := range result.ResultItems {
			item_struct := make(map[string]interface{})
			item_struct["score"] = result_item.Score

			for _, field := range result_item.Fields {
				if *field.Type == awadb_pb.FieldType_INT  {
					num, err := strconv.ParseInt(string(field.Value), 10, 32)
					if err != nil {
						panic(err)
					}
					item_struct[*field.Name] = num
				} else if *field.Type == awadb_pb.FieldType_FLOAT {
					num, err := strconv.ParseFloat(string(field.Value), 32)
					if err != nil {
						panic(err)
					}
					item_struct[*field.Name] = num
				} else if *field.Type == awadb_pb.FieldType_LONG {
					num, err := strconv.ParseInt(string(field.Value), 10, 64)
					if err != nil {
						panic(err)
					}
					item_struct[*field.Name] = num
				} else if *field.Type == awadb_pb.FieldType_STRING {
					item_struct[*field.Name] = string(field.Value)
				} else if *field.Type == awadb_pb.FieldType_MULTI_STRING {
				} else if *field.Type == awadb_pb.FieldType_VECTOR {
				}
			}
			result_items = append(result_items, item_struct)
		}
		results_struct["ResultItems"] = result_items
	}
	results["SearchResults"] = results_struct
	//c.JSON(http.StatusOK, results)
	c.JSON(http.StatusOK, gin.H(results))
}


func RunHttpServer(http_port int) error {
	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	r.POST("/create", func(c *gin.Context) {
		json := make(map[string]interface{})
		err := c.BindJSON(&json)
		if err != nil  {
			fmt.Printf("bind error:%v\n", err)
			c.JSON(http.StatusBadRequest, gin.H{"Server error":"Bind json error!"})
		}  else  {
			db_meta := &awadb_pb.DBMeta{}

			db_value, ok := json["db"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"DB Name error":"DB name should be specified!"})
				return
			}
			switch db_value.(type) {
			case string:
				db_name := db_value.(string)
				db_meta.DbName = &db_name
			default:
				fmt.Println("DB name not specified, use default db")
				default_db_name := "default"
				db_meta.DbName = &default_db_name
			}

			table_value, ok := json["table"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"Table name should be specified!"})
				return
			}
			switch table_value.(type) {
			case string:
				if len(db_meta.TablesMeta) == 0 {
					db_meta.TablesMeta = make([]*awadb_pb.TableMeta, 1)
					db_meta.TablesMeta[0] = &awadb_pb.TableMeta{}
				}
				value_str := table_value.(string)
				db_meta.TablesMeta[0].Name = &value_str
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Error":"table should be string!"})
				return
			}

			desc_value, ok := json["desc"]
			if ok {
				switch desc_value.(type) {
				case string:
					value_str := desc_value.(string)
					db_meta.TablesMeta[0].Desc = &value_str
				default:
					c.JSON(http.StatusBadRequest, gin.H{"Error":"table description should be string!"})
					return
				}

			}

			fields_value, ok := json["fields"]
			if !ok  {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"fields should be specified!"})
				return
			}

			has_primary_key := false
			has_vector_field := false
			switch fields_value.(type) {
			case []any:
				db_meta.TablesMeta[0].FieldsMeta = make([]*awadb_pb.FieldMeta, 0)
				for _, field := range fields_value.([]any)  {
					switch field.(type) {
					case map[string]interface{}:
						field_meta := &awadb_pb.FieldMeta{}
						is_primary_key, is_vector_field := AssembleTableFields(field_meta, field.(map[string]interface{}), c)
						if is_primary_key {
							has_primary_key = true
						}
						if is_vector_field {
							has_vector_field = true
						}
						db_meta.TablesMeta[0].FieldsMeta = append(db_meta.TablesMeta[0].FieldsMeta, field_meta)
					default:
						c.JSON(http.StatusBadRequest, gin.H{"Error":"fields format error!"})
						return
					}
				}
			case map[string]interface{}:
				db_meta.TablesMeta[0].FieldsMeta = make([]*awadb_pb.FieldMeta, 0)
				field_meta := &awadb_pb.FieldMeta{}
				is_primary_key, is_vector_field := AssembleTableFields(field_meta, fields_value.(map[string]interface{}), c)
				if is_primary_key {
					has_primary_key = true
				}
				if is_vector_field {
					has_vector_field = true
				}

				db_meta.TablesMeta[0].FieldsMeta = append(db_meta.TablesMeta[0].FieldsMeta, field_meta)

			default:
				c.JSON(http.StatusBadRequest, gin.H{"Error":"fields format error!"})
				return
			}
			if !has_vector_field {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"Not include vector field!"})
				return
			}
			if !has_primary_key {
				field_meta := &awadb_pb.FieldMeta{}
			        primary_key := "_id"
				field_meta.Name = &primary_key
				field_type := awadb_pb.FieldType_STRING
				field_meta.Type = &field_type
				is_value := true
				field_meta.IsIndex = &is_value
				field_meta.IsStore = &is_value
				db_meta.TablesMeta[0].FieldsMeta = append(db_meta.TablesMeta[0].FieldsMeta, field_meta)
			}

			if local_awadb_client != nil  {
				ctx, cancel := context.WithTimeout(context.Background(), time.Second)
				defer cancel()

				status, err := (*local_awadb_client).Create(ctx, db_meta)
				if err != nil  {
					c.JSON(http.StatusBadRequest, gin.H{"Create table failed :":err.Error()})
					return
				}
				if status.Code == awadb_pb.ResponseCode_INPUT_PARAMETER_ERROR {
					c.JSON(http.StatusOK, gin.H{"Message": "Input parameters error!",})
				} else if status.Code == awadb_pb.ResponseCode_INTERNAL_ERROR {
					c.JSON(http.StatusBadRequest, gin.H{"Message": "Internal server error!",})
				} else if status.Code == awadb_pb.ResponseCode_TABLE_EXIST {
					c.JSON(http.StatusOK, gin.H{"Message": "Table exist!",})
				} else if status.Code == awadb_pb.ResponseCode_OK {
					c.JSON(http.StatusOK, gin.H{"Message": "Create table success!",})
				} else {
					c.JSON(http.StatusBadRequest, gin.H{"Message": "Unknown error!",})
				}
			}  else  {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"awadb server client has error!"})
			}
		}
	})

        r.POST("/add", func(c *gin.Context) {
		json := make(map[string]interface{})
		err := c.BindJSON(&json)
		if err != nil  {
			fmt.Printf("bind error:%v\n", err)
		}  else  {
			docs := &awadb_pb.Documents{}

			db_value, ok := json["db"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"DB Name error":"DB name should be specified!"})
				return
			}
			switch db_value.(type) {
			case string:
				db_name := db_value.(string)
				docs.DbName = &db_name
			default:
				fmt.Println("DB name not specified, use default db")
				default_db_name := "default"
				docs.DbName = &default_db_name
			}

			table_value, ok := json["table"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"Table name error":"table name should be specified!"})
				return
			}
			switch table_value.(type) {
			case string:
				table_name := table_value.(string)
				docs.TableName = &table_name
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Table name error":"Table name should be string!"})
				return
			}

			db_table_name := *docs.DbName + "/" + *docs.TableName
			_, ok = checked_tables_schema[db_table_name]
                        table_existed := true

			if !ok  {
				table_status, err := CheckTableFromServer(docs.DbName, docs.TableName)
				if err != nil  {
					c.JSON(http.StatusBadRequest, gin.H{"Error:": err.Error()})
					return
				}
				if !table_status.IsExisted { // create
					table_existed = false
				} else {
					for _, table_meta := range table_status.ExistTable.TablesMeta {
						table_fields := make(map[string]*awadb_pb.FieldType)
						for _, field_meta := range table_meta.FieldsMeta {
							table_fields[*field_meta.Name] = field_meta.Type
						}
						checked_tables_schema[db_table_name] = table_fields
					}
				}
			}

			docs_value, ok := json["docs"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"Documents error":"Documents should be specified!"})
				return
			}
			switch docs_value.(type) {
			case []any:
				docs.Docs = make([]*awadb_pb.Document, 0)
				for _, doc_json := range docs_value.([]any)  {
					switch doc_json.(type) {
					case map[string]interface{}:
						doc := &awadb_pb.Document{}
						ret := AssembleDoc(docs.DbName, docs.TableName, doc, doc_json.(map[string]interface{}), &table_existed)
						if !ret {
							fmt.Println("Error: this document format error, it can not be added!!!")
							continue
						}
						table_existed = true
						docs.Docs = append(docs.Docs, doc)
					default:
						fmt.Println("doc format error!")
						continue
					}
				}
			case map[string]interface{}:
				docs.Docs = make([]*awadb_pb.Document, 0)
				doc := &awadb_pb.Document{}
				ret := AssembleDoc(docs.DbName, docs.TableName, doc, docs_value.(map[string]interface{}), &table_existed)
				if !ret {
					c.JSON(http.StatusBadRequest, gin.H{"Error":"Docs format error!"})
					return
				}
				docs.Docs = append(docs.Docs, doc)
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Error":"Docs format error!"})
				return
			}

			if local_awadb_client != nil  {
				ctx, cancel := context.WithTimeout(context.Background(), time.Second)
				defer cancel()

				_, err := (*local_awadb_client).AddOrUpdate(ctx, docs)
				if err != nil  {
					c.JSON(http.StatusBadRequest, gin.H{"Add docs failed :": err.Error()})
					return
				}
				c.JSON(http.StatusOK, gin.H{"message": "Add docs success!",})
			}  else  {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"awadb server client has error!"})
			}
		}
	})

	r.POST("/search", func(c *gin.Context) {
		json := make(map[string]interface{})
		err := c.BindJSON(&json)
		if err != nil  {
			fmt.Printf("bind error:%v\n", err)
		}  else  {
			search_request := &awadb_pb.SearchRequest{}
			retrieval_params := "{\"metric_type\":\"L2\"}"
			search_request.RetrievalParams = &retrieval_params
			default_is_l2 := true
			default_topn := int32(10)
			default_brute_force_search := false
			search_request.IsL2 = &default_is_l2
			search_request.Topn = &default_topn
			search_request.BruteForceSearch = &default_brute_force_search

			db_value, ok := json["db"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"DB name should be specified!"})
				return
			}
			switch db_value.(type) {
			case string:
				db_name := db_value.(string)
				search_request.DbName = &db_name
			default:
				fmt.Println("DB name not specified, use default db")
				default_db_name := "default"
				search_request.DbName = &default_db_name
			}

			table_value, ok := json["table"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"table name should be specified!"})
				return
			}
			switch table_value.(type) {
			case string:
				table_name := table_value.(string)
				search_request.TableName = &table_name
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Error":"Table name should be string!"})
				return
			}

			db_table_name := *search_request.DbName + "/" + *search_request.TableName
			_, ok = checked_tables_schema[db_table_name]

			if !ok  {
				table_status, err := CheckTableFromServer(search_request.DbName, search_request.TableName)
				if err != nil  {
					c.JSON(http.StatusBadRequest, gin.H{"Error:": err.Error()})
					return
				}
				if !table_status.IsExisted {
					c.JSON(http.StatusBadRequest, gin.H{"Error:": "Searched table not exist!"})
					return
				} else {
					for _, table_meta := range table_status.ExistTable.TablesMeta {
						table_fields := make(map[string]*awadb_pb.FieldType)
						for _, field_meta := range table_meta.FieldsMeta {
							table_fields[*field_meta.Name] = field_meta.Type
						}
						checked_tables_schema[db_table_name] = table_fields
					}
				}
			}

			vector_value, ok := json["vector_query"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"Vector query should be specified!"})
				return
			}
			switch vector_value.(type) {
			case []any:
				for _, e := range vector_value.([]any)  {
					switch e.(type) {
					case map[string]interface{}:
						vec_query := &awadb_pb.VectorQuery{}
						ret := AssembleVectorQuery(&db_table_name, vec_query, e.(map[string]interface{}))
						if !ret  {
							c.JSON(http.StatusBadRequest, gin.H{"Error":"Vector format error!"})
							return
						}
						if len(search_request.VecQueries) == 0  {
							search_request.VecQueries = make([]*awadb_pb.VectorQuery, 0)
						}

						search_request.VecQueries = append(search_request.VecQueries, vec_query)
					default:
						c.JSON(http.StatusBadRequest, gin.H{"Error":"Vector format error!"})
						return
					}
				}
			case map[string]interface{}:
				vec_query := &awadb_pb.VectorQuery{}
				ret := AssembleVectorQuery(&db_table_name, vec_query, vector_value.(map[string]interface{}))
				if !ret  {
					c.JSON(http.StatusBadRequest, gin.H{"Error":"Vector format error!"})
					return
				}
				if len(search_request.VecQueries) == 0  {
					search_request.VecQueries = make([]*awadb_pb.VectorQuery, 0)
				}

				search_request.VecQueries = append(search_request.VecQueries, vec_query)
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Error":"Vector format error!"})
				return
			}

			filters_value, ok := json["filters"]
			if ok {
				switch filters_value.(type) {
				case map[string]interface{}:
					for filter_name, filter_value := range filters_value.(map[string]interface{})  {
						if  filter_name == "range_filters"  {
							AssembleRangeFilters(&search_request.RangeFilters, filter_value)
						}  else if filter_name == "term_filters"  {
							AssembleTermFilters(search_request.TermFilters, filter_value)
						}  else  {
							fmt.Println("filter format error!")
						}
					}
				default:
					fmt.Println("filter format error!")
				}
			}

			pack_fields_value, ok := json["pack_fields"]
			if ok {
				switch pack_fields_value.(type) {
				case string:
					search_request.PackFields = make([]string, 0)
					search_request.PackFields = append(search_request.PackFields, pack_fields_value.(string))
				case []any:
					search_request.PackFields = make([]string, 0)
					for _, e := range pack_fields_value.([]any) {
						switch e.(type)  {
						case  string:
							search_request.PackFields = append(search_request.PackFields, e.(string))
						default:
							fmt.Println("pack fields format error!")
						}
					}
				default:
					fmt.Println("pack fields format error!")
					pack_all_fields := true
					search_request.IsPackAllFields = &pack_all_fields
				}
			}  else  {
				table_fields, field_ok := checked_tables_schema[db_table_name]
				if field_ok  {
					search_request.PackFields = make([]string, 0)
					for field_name, field_type := range table_fields.(map[string]*awadb_pb.FieldType)  {
						if *field_type != awadb_pb.FieldType_VECTOR  {
							search_request.PackFields = append(search_request.PackFields, field_name)
						}
					}
				}
			}

			topn_value, ok := json["topn"]
			if ok {
				switch topn_value.(type)  {
				case float64:
					if IsDecimal(topn_value.(float64))  {
						fmt.Println("topn parameter error!")
						default_topn := int32(10)
						search_request.Topn = &default_topn
					}  else  {
						tmp_topn_value := (int32)(topn_value.(float64))
						search_request.Topn = &tmp_topn_value
					}
				default:
					fmt.Println("topn parameter error!")
					default_topn := int32(10)
					search_request.Topn = &default_topn
				}
			}

			is_brute_search, ok := json["force_brute_search"]
			if ok {
				switch is_brute_search.(type)  {
				case bool:
					bool_value := is_brute_search.(bool)
					search_request.BruteForceSearch = &bool_value
				default:
					fmt.Println("force_brute_search parameter error!")
					brute_force_search := false
					search_request.BruteForceSearch = &brute_force_search
				}
			}

			metric_type, ok := json["metric_type"]
			if ok {
				is_l2 := true
				switch metric_type.(type)  {
				case string:
					if metric_type.(string) == "L2"  {
						search_request.IsL2 = &is_l2
					} else if metric_type.(string) == "InnerProduct" {
						is_l2 = false
						search_request.IsL2 = &is_l2

						retrieval_params := "{\"metric_type\":\"InnerProduct\"}"
						search_request.RetrievalParams = &retrieval_params
					}  else  {
						fmt.Println("metric_type parameter error!")
						search_request.IsL2 = &is_l2
					}
				default:
					fmt.Println("metric_type format error!")
					search_request.IsL2 = &is_l2
				}
			}

			if local_awadb_client != nil  {
				ctx, cancel := context.WithTimeout(context.Background(), time.Second)
				defer cancel()

				results, err := (*local_awadb_client).Search(ctx, search_request)
				if err != nil  {
					c.JSON(http.StatusBadRequest, gin.H{"Search failed :": err.Error()})
					return
				}

				SearchResultsToJson(results, c)
			}  else  {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"awadb server client has error!"})
			}
		}
	})

	r.POST("/get", func(c *gin.Context) {
		json := make(map[string]interface{})
		err := c.BindJSON(&json)
		if err != nil  {
			fmt.Printf("bind error:%v\n", err)
		}  else  {
			condition := &awadb_pb.DocCondition{}

			default_limit := int32(10)
			condition.Limit = &default_limit

			include_all_fields := true
			condition.IncludeAllFields = &include_all_fields

			has_ids := false
			has_filters := false

			db_value, ok := json["db"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"DB name should be specified!"})
				return
			}
			switch db_value.(type) {
			case string:
				db_name := db_value.(string)
				condition.DbName = db_name
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Error":"DB name should be specified!"})
				return
			}

			table_value, ok := json["table"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"table name should be specified!"})
				return
			}
			switch table_value.(type) {
			case string:
				table_name := table_value.(string)
				condition.TableName = table_name
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Error":"Table name should be string!"})
				return
			}

			ids_value, ok := json["ids"]
			if ok {
				switch ids_value.(type)  {
				case []any:
					id_format := true
					id_type_string := false
					id_type_long := false
					ids_array := make([]any, 0)
					for _, e := range ids_value.([]any) {
						switch e.(type)  {
						case  float64:
							if IsDecimal(e.(float64)) {
								fmt.Println("id should not be decimal")
								continue
							}
							id_type_long = true
							ids_array = append(ids_array, e)
						case string:
							id_type_string = true
							ids_array = append(ids_array, e)
						default:
							id_format = false
						}
					}
					if id_format == false  {
						c.JSON(http.StatusBadRequest, gin.H{"Error":"ids format error!"})
						return
					}
					if (!id_type_long && !id_type_string) || (id_type_long && id_type_string)  {
						c.JSON(http.StatusBadRequest, gin.H{"Error":"ids format not consistant!"})
						return
					}
					if id_type_string && !id_type_long  {
						has_ids = true
						for _, id_string := range ids_array  {
							condition.Ids = append(condition.Ids, []byte(id_string.(string)))
						}
					}

					if !id_type_string && id_type_long  {
						has_ids = true
						for _, id_long := range ids_array  {
							condition.Ids = append(condition.Ids,  Int64tobytes((int64)(id_long.(float64))))
						}
					}
				case string:
					condition.Ids = append(condition.Ids, []byte(ids_value.(string)))
					has_ids = true
				case float64:
					condition.Ids = append(condition.Ids,  Int64tobytes((int64)(ids_value.(float64))))
					has_ids = true
				default:
					c.JSON(http.StatusBadRequest, gin.H{"Error":"ids format error!"})
					return
				}
			}

			filters_value, ok := json["filters"]
			if ok {
				for filter_name, filter_value := range filters_value.(map[string]interface{})  {
					if  filter_name == "range_filters"  {
						if AssembleRangeFilters(&condition.RangeFilters, filter_value) {
							has_filters = true
						}
					}  else if filter_name == "term_filters"  {
						if AssembleTermFilters(condition.TermFilters, filter_value) {
							has_filters = true
						}
					}  else  {
						c.JSON(http.StatusBadRequest, gin.H{"Error":"filter format error!"})
						return
					}
				}
			}

			pack_fields_value, ok := json["pack_fields"]
			if ok {
				switch pack_fields_value.(type) {
				case string:
					condition.PackFields = make([]string, 0)
					condition.PackFields = append(condition.PackFields, pack_fields_value.(string))
				case []any:
					condition.PackFields = make([]string, 0)
					for _, e := range pack_fields_value.([]any) {
						switch e.(type)  {
						case  string:
							condition.PackFields = append(condition.PackFields, e.(string))
						default:
							fmt.Println("pack fields format error!")
						}
					}
				default:
					fmt.Println("pack fields format error!")
				}
			}

			limit, ok := json["limit"]
			if ok {
				switch limit.(type)  {
				case float64:
					if IsDecimal(limit.(float64))  {
						fmt.Println("limit parameter error!")
					}  else  {
						limit_value := int32(limit.(float64))
						condition.Limit = &limit_value
					}
				default:
					fmt.Println("limit parameter error!")
				}
			}

			if !has_ids && !has_filters  {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"ids and filters should be specified one of them!"})
				return
			}

			if len(condition.Ids) > 0  {
				if len(condition.RangeFilters) > 0  {
					condition.RangeFilters = condition.RangeFilters[:0]
				}
				if len(condition.TermFilters) > 0 {
					condition.TermFilters = condition.TermFilters[:0]
				}
			}

			if local_awadb_client != nil  {
				ctx, cancel := context.WithTimeout(context.Background(), time.Second)
				defer cancel()

				docs, err := (*local_awadb_client).Get(ctx, condition)
				if err != nil  {
					c.JSON(http.StatusBadRequest, gin.H{"Get docs failed :": err.Error()})
					return
				}
				if docs == nil {
					fmt.Println("get docs is nil")
				}
				DocsToJson(docs, c)
				//c.JSON(http.StatusOK, gin.H{"message": "Get docs success!",})
			}  else  {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"awadb server client has error!"})
			}
		}
	})

	r.POST("/delete", func(c *gin.Context) {
		json := make(map[string]interface{})
		err := c.BindJSON(&json)
		if err != nil  {
			fmt.Printf("bind error:%v\n", err)
		}  else  {
			condition := &awadb_pb.DocCondition{}

			has_ids := false
			has_filters := false

			db_value, ok := json["db"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"DB name should be specified!"})
				return
			}
			switch db_value.(type) {
			case string:
				db_name := db_value.(string)
				condition.DbName = db_name
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Error":"DB name should be specified!"})
				return
			}

			table_value, ok := json["table"]
			if !ok {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"table name should be specified!"})
				return
			}
			switch table_value.(type) {
			case string:
				table_name := table_value.(string)
				condition.TableName = table_name
			default:
				c.JSON(http.StatusBadRequest, gin.H{"Error":"Table name should be string!"})
				return
			}

			ids_value, ok := json["ids"]
			if ok {
				switch ids_value.(type)  {
				case []any:
					id_format := true
					id_type_string := false
					id_type_long := false
					ids_array := make([]any, 0)
					for _, e := range ids_value.([]any) {
						switch e.(type)  {
						case  float64:
							if IsDecimal(e.(float64)) {
								fmt.Println("id should not be decimal")
								continue
							}
							id_type_long = true
							ids_array = append(ids_array, e)
						case string:
							id_type_string = true
							ids_array = append(ids_array, e)
						default:
							id_format = false
						}
					}
					if id_format == false  {
						c.JSON(http.StatusBadRequest, gin.H{"Error":"ids format error!"})
						return
					}
					if (!id_type_long && !id_type_string) || (id_type_long && id_type_string)  {
						c.JSON(http.StatusBadRequest, gin.H{"Error":"ids format not consistant!"})
						return
					}
					if id_type_string && !id_type_long  {
						has_ids = true
						for _, id_string := range ids_array  {
							condition.Ids = append(condition.Ids, []byte(id_string.(string)))
						}
					}

					if !id_type_string && id_type_long  {
						has_ids = true
						for _, id_long := range ids_array  {
							condition.Ids = append(condition.Ids,  Int64tobytes((int64)(id_long.(float64))))
						}
					}
				case string:
					condition.Ids = append(condition.Ids, []byte(ids_value.(string)))
					has_ids = true
				case float64:
					condition.Ids = append(condition.Ids,  Int64tobytes((int64)(ids_value.(float64))))
					has_ids = true
				default:
					c.JSON(http.StatusBadRequest, gin.H{"Error":"ids format error!"})
					return
				}
			}

			filters_value, ok := json["filters"]
			if ok {
				for filter_name, filter_value := range filters_value.(map[string]interface{})  {
					if  filter_name == "range_filters"  {
						if AssembleRangeFilters(&condition.RangeFilters, filter_value) {
							has_filters = true
						}
					}  else if filter_name == "term_filters"  {
						if AssembleTermFilters(condition.TermFilters, filter_value) {
							has_filters = true
						}
					}  else  {
						c.JSON(http.StatusBadRequest, gin.H{"Error":"filter format error!"})
						return
					}
				}
			}

			if !has_ids && !has_filters  {
				c.JSON(http.StatusOK, gin.H{"Message":"ids and filters should be specified one of them!"})
				return
			}

			if len(condition.Ids) > 0  {
				if len(condition.RangeFilters) > 0  {
					condition.RangeFilters = condition.RangeFilters[:0]
				}
				if len(condition.TermFilters) > 0 {
					condition.TermFilters = condition.TermFilters[:0]
				}
			}

			if local_awadb_client != nil  {
				ctx, cancel := context.WithTimeout(context.Background(), time.Second)
				defer cancel()

				_, err := (*local_awadb_client).Delete(ctx, condition)
				if err != nil  {
					c.JSON(http.StatusBadRequest, gin.H{"Delete docs failed :": err.Error()})
					return
				}
				c.JSON(http.StatusOK, gin.H{"message": "Delete docs success!",})
			}  else  {
				c.JSON(http.StatusBadRequest, gin.H{"Error":"awadb server client has error!"})
			}
		}
	})

	r.POST("/list", func(c *gin.Context) {
		json := make(map[string]interface{})
		err := c.BindJSON(&json)
		if err != nil  {
			fmt.Printf("bind error:%v\n", err)
			c.JSON(http.StatusBadRequest, gin.H{"Error:": err})
		}  else  {
			db_name := ""
			table_name := ""
			db_value, ok := json["db"]
			if !ok {
				log.Println("DB name not specified!")
			}  else {
				switch db_value.(type) {
				case string:
					db_name = db_value.(string)
				default:
					log.Println("DB name format error!")
				}
		        }

			table_value, ok := json["table"]
			if !ok {
				log.Println("Table name not specified!")
			}  else {
				switch table_value.(type) {
				case string:
					table_name = table_value.(string)
				default:
					log.Println("Table name format error!")
				}
			}

			if len(db_name) == 0 || len(table_name) == 0  {
				table_status, err := CheckTableFromServer(&db_name, &table_name)
				if err != nil  {
					c.JSON(http.StatusBadRequest, gin.H{"Error:": err.Error()})
					return
				}
				if len(db_name) == 0  {
					results := make(map[string][]string)
					results["DBs"] = table_status.DbNames
					c.JSON(http.StatusOK, results)
					return
				} else {
					results := make(map[string]interface{})
					results["Db"] = db_name
					tables := make([]string, 0)
					if table_status.ExistTable == nil {
						results["Tables"] = tables
						c.JSON(http.StatusOK, results)
						return
					}
					for _, table_meta := range table_status.ExistTable.TablesMeta {
						tables = append(tables, *table_meta.Name)
					}
					results["Tables"] = tables
					c.JSON(http.StatusOK, results)
					return
				}
			}
			db_table_name := db_name + "/" + table_name
			_, ok = checked_tables_schema[db_table_name]
                        results := make(map[string]interface{})
			results["Db"] = db_name
			results["Table"] = table_name

			if !ok  {
				table_status, err := CheckTableFromServer(&db_name, &table_name)
				if err != nil  {
					c.JSON(http.StatusBadRequest, gin.H{"Error:": err.Error()})
					return
				}
				if !table_status.IsExisted {
					c.JSON(http.StatusOK, results)
					return
				} else {
					if table_status.ExistTable == nil {
						c.JSON(http.StatusOK, results)
						return
					}
					for _, table_meta := range table_status.ExistTable.TablesMeta {
					        if table_name != *table_meta.Name {
							continue
						}
						table_fields := make(map[string]*awadb_pb.FieldType)
					        json_fields := make(map[string]string)
						for _, field_meta := range table_meta.FieldsMeta {
							table_fields[*field_meta.Name] = field_meta.Type
							switch *field_meta.Type {
							case awadb_pb.FieldType_INT:
								json_fields[*field_meta.Name] = "int"
							case awadb_pb.FieldType_LONG:
								json_fields[*field_meta.Name] = "long"
							case awadb_pb.FieldType_FLOAT:
								json_fields[*field_meta.Name] = "float"
							case awadb_pb.FieldType_DOUBLE:
								json_fields[*field_meta.Name] = "double"
							case awadb_pb.FieldType_STRING:
								json_fields[*field_meta.Name] = "string"
							case awadb_pb.FieldType_MULTI_STRING:
								json_fields[*field_meta.Name] = "multi_string"
							case awadb_pb.FieldType_VECTOR:
								json_fields[*field_meta.Name] = "vector"
							case awadb_pb.FieldType_KEYWORD:
								json_fields[*field_meta.Name] = "keyword"
							}
						}
						checked_tables_schema[db_table_name] = table_fields
						results["Fields"] = json_fields
					}
				}
				c.JSON(http.StatusOK, results)
				return
			}
			json_fields := make(map[string]string)
			for key, value := range checked_tables_schema[db_table_name].(map[string]*awadb_pb.FieldType) {
				switch *value {
				case awadb_pb.FieldType_INT:
					json_fields[key] = "int"
				case awadb_pb.FieldType_LONG:
					json_fields[key] = "long"
				case awadb_pb.FieldType_FLOAT:
					json_fields[key] = "float"
				case awadb_pb.FieldType_DOUBLE:
					json_fields[key] = "double"
				case awadb_pb.FieldType_STRING:
					json_fields[key] = "string"
				case awadb_pb.FieldType_MULTI_STRING:
					json_fields[key] = "multi_string"
				case awadb_pb.FieldType_VECTOR:
					json_fields[key] = "vector"
				case awadb_pb.FieldType_KEYWORD:
					json_fields[key] = "keyword"
				}
			}
			results["Fields"] = json_fields
			c.JSON(http.StatusOK, results)
			return
		}
	})

        r.POST("/count", func(c *gin.Context) {
		json := make(map[string]interface{})
		err := c.BindJSON(&json)
		if err != nil  {
			log.Printf("bind error:%v\n", err)
			c.JSON(http.StatusBadRequest, gin.H{"Error:": err})
			return
		}  else  {
			db_name := ""
			table_name := ""
			db_value, ok := json["db"]
			if !ok {
				log.Println("DB name not specified!")
				c.JSON(http.StatusBadRequest, gin.H{"Error:": "DB name not specified!"})
				return
			}  else {
				switch db_value.(type) {
				case string:
					db_name = db_value.(string)
				default:
					log.Println("DB name format error!")
					c.JSON(http.StatusBadRequest, gin.H{"Error:": "DB name format error!"})
					return
				}
		        }

			table_value, ok := json["table"]
			if !ok {
				log.Println("Table name not specified!")
				c.JSON(http.StatusBadRequest, gin.H{"Error:": "Table name not specified!"})
				return
			}  else {
				switch table_value.(type) {
				case string:
					table_name = table_value.(string)
				default:
					log.Println("Table name format error!")
					c.JSON(http.StatusBadRequest, gin.H{"Error:": "Table name format error!"})
					return
				}
			}

			table_detail, err := QueryTableDetail(&db_name, &table_name)

			if err != nil  {
				c.JSON(http.StatusBadRequest, gin.H{"Error:": err.Error()})
				return
			}
			if !table_detail.QueryStatus {
				c.JSON(http.StatusOK, gin.H{"Message": "Query result none!",})
				return
			}
			TableDetailToJson(&db_name, &table_name, table_detail, c)
		}
	})

	r.POST("/drop", func(c *gin.Context) {
		obj := struct {
			Db	string	`json:"db"`
			Table	string	`json:"table"`
		}{}

		err := c.BindJSON(&obj)
		if err != nil  {
			fmt.Println(err)
                        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}  else  {
			fmt.Println(obj)
		}
	})

	addr := "0.0.0.0:" + strconv.Itoa(http_port)
	return r.Run(addr)
}

func Usage()  {
	fmt.Println("local [grpc_port] [http_port] [local_awadb_port]")
}

//default grpc server port
var grpc_port = 50005
//default http server port
var http_port = 8080
//default local awadb server port
var local_awadb_port = 10000
//local awadb client
var local_awadb_client *awadb_pb.AwaDBServerClient = nil

var checked_tables_schema = make(map[string]interface{})


//local grpc_port http_port local_awadb_port
func main() {
	args_size := len(os.Args)
	if args_size <= 1 || args_size > 5  {
		fmt.Println("Input Parameters error!\n")
		Usage()
                return
	}

	if os.Args[1] == "local"  {
		if args_size == 5  {
			grpc_port_tmp, err := strconv.Atoi(os.Args[2])
			if err != nil  {
				fmt.Println("grpc server port should be number!\n")
				Usage()
				return
			}
			grpc_port = grpc_port_tmp
			http_port_tmp, err := strconv.Atoi(os.Args[3])
			if err != nil  {
				fmt.Println("http server port should be number!\n")
				Usage()
				return
			}
			http_port = http_port_tmp
			local_awadb_tmp, err := strconv.Atoi(os.Args[4])
			if err != nil  {
				fmt.Println("awadb server port should be number!\n")
				Usage()
				return
			}
			local_awadb_port = local_awadb_tmp
		}  else if args_size == 4  {
			grpc_port_tmp, err := strconv.Atoi(os.Args[2])
			if err != nil  {
				fmt.Println("grpc server port should be number!\n")
				Usage()
				return
			}
			grpc_port = grpc_port_tmp
			http_port_tmp, err := strconv.Atoi(os.Args[3])
			if err != nil  {
				fmt.Println("http server port should be number!\n")
				Usage()
				return
			}
			http_port = http_port_tmp
		}  else if args_size == 3  {
			grpc_port_tmp, err := strconv.Atoi(os.Args[2])
			if err != nil  {
				fmt.Println("grpc server port should be number!\n")
				Usage()
				return
			}
			grpc_port = grpc_port_tmp
		}  else if args_size == 2  {
			fmt.Println("grpc port default to 50005; http port default to 8080")
		}  else  {
			fmt.Println("Input Parameters error!\n")
			Usage()
			return
		}
		//local_awadb_addr := "0.0.0.0:" + strconv.Itoa(local_awadb_port)
		local_awadb_addr := "awadb:" + strconv.Itoa(local_awadb_port)
		local_awadb_client = CreateAwaDBClient(&local_awadb_addr)
	}  else {
		fmt.Println("Input Parameters error!\n")
		Usage()
                return
	}

	errs := make(chan error)
	go func()  {
		err := RunGrpcServer(grpc_port)
		if err != nil  {
			errs <- err
		}
	}()

	go func()  {
		err := RunHttpServer(http_port)
		if err != nil  {
			errs <- err
		}
	}()

	select {
	case err := <-errs:
		log.Fatalf("Run Server err: %v", err)
	}
}
