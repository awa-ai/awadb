// Code generated by the FlatBuffers compiler. DO NOT EDIT.

package gamma_api

import "strconv"

type DataType int8

const (
	DataTypeINT    DataType = 0
	DataTypeLONG   DataType = 1
	DataTypeFLOAT  DataType = 2
	DataTypeDOUBLE DataType = 3
	DataTypeSTRING DataType = 4
	DataTypeVECTOR DataType = 5
)

var EnumNamesDataType = map[DataType]string{
	DataTypeINT:    "INT",
	DataTypeLONG:   "LONG",
	DataTypeFLOAT:  "FLOAT",
	DataTypeDOUBLE: "DOUBLE",
	DataTypeSTRING: "STRING",
	DataTypeVECTOR: "VECTOR",
}

var EnumValuesDataType = map[string]DataType{
	"INT":    DataTypeINT,
	"LONG":   DataTypeLONG,
	"FLOAT":  DataTypeFLOAT,
	"DOUBLE": DataTypeDOUBLE,
	"STRING": DataTypeSTRING,
	"VECTOR": DataTypeVECTOR,
}

func (v DataType) String() string {
	if s, ok := EnumNamesDataType[v]; ok {
		return s
	}
	return "DataType(" + strconv.FormatInt(int64(v), 10) + ")"
}
