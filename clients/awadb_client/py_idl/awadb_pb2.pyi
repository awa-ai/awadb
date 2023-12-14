from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class FieldType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    INT: _ClassVar[FieldType]
    LONG: _ClassVar[FieldType]
    FLOAT: _ClassVar[FieldType]
    DOUBLE: _ClassVar[FieldType]
    STRING: _ClassVar[FieldType]
    MULTI_STRING: _ClassVar[FieldType]
    VECTOR: _ClassVar[FieldType]

class MultiVectorLogicOp(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    AND: _ClassVar[MultiVectorLogicOp]
    OR: _ClassVar[MultiVectorLogicOp]

class SearchResultCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    SUCCESS: _ClassVar[SearchResultCode]
    INDEX_NOT_TRAINED: _ClassVar[SearchResultCode]
    SEARCH_ERROR: _ClassVar[SearchResultCode]
    DB_NOT_FOUND: _ClassVar[SearchResultCode]
    TABLE_NOT_FOUND: _ClassVar[SearchResultCode]

class ResponseCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    INPUT_PARAMETER_ERROR: _ClassVar[ResponseCode]
    OK: _ClassVar[ResponseCode]
    TIME_OUT: _ClassVar[ResponseCode]
    INTERNAL_ERROR: _ClassVar[ResponseCode]
    NETWORK_ERROR: _ClassVar[ResponseCode]
INT: FieldType
LONG: FieldType
FLOAT: FieldType
DOUBLE: FieldType
STRING: FieldType
MULTI_STRING: FieldType
VECTOR: FieldType
AND: MultiVectorLogicOp
OR: MultiVectorLogicOp
SUCCESS: SearchResultCode
INDEX_NOT_TRAINED: SearchResultCode
SEARCH_ERROR: SearchResultCode
DB_NOT_FOUND: SearchResultCode
TABLE_NOT_FOUND: SearchResultCode
INPUT_PARAMETER_ERROR: ResponseCode
OK: ResponseCode
TIME_OUT: ResponseCode
INTERNAL_ERROR: ResponseCode
NETWORK_ERROR: ResponseCode

class DBName(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class TableName(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class DBTableName(_message.Message):
    __slots__ = ["db_name", "table_name"]
    DB_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    db_name: str
    table_name: str
    def __init__(self, db_name: _Optional[str] = ..., table_name: _Optional[str] = ...) -> None: ...

class DBMeta(_message.Message):
    __slots__ = ["db_name", "desc", "tables_meta"]
    DB_NAME_FIELD_NUMBER: _ClassVar[int]
    DESC_FIELD_NUMBER: _ClassVar[int]
    TABLES_META_FIELD_NUMBER: _ClassVar[int]
    db_name: str
    desc: str
    tables_meta: _containers.RepeatedCompositeFieldContainer[TableMeta]
    def __init__(self, db_name: _Optional[str] = ..., desc: _Optional[str] = ..., tables_meta: _Optional[_Iterable[_Union[TableMeta, _Mapping]]] = ...) -> None: ...

class FieldMeta(_message.Message):
    __slots__ = ["name", "type", "is_index", "is_store", "reindex", "vec_meta"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    IS_INDEX_FIELD_NUMBER: _ClassVar[int]
    IS_STORE_FIELD_NUMBER: _ClassVar[int]
    REINDEX_FIELD_NUMBER: _ClassVar[int]
    VEC_META_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: FieldType
    is_index: bool
    is_store: bool
    reindex: bool
    vec_meta: VectorMeta
    def __init__(self, name: _Optional[str] = ..., type: _Optional[_Union[FieldType, str]] = ..., is_index: bool = ..., is_store: bool = ..., reindex: bool = ..., vec_meta: _Optional[_Union[VectorMeta, _Mapping]] = ...) -> None: ...

class TableNames(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[_Iterable[str]] = ...) -> None: ...

class TableMeta(_message.Message):
    __slots__ = ["name", "desc", "fields_meta"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESC_FIELD_NUMBER: _ClassVar[int]
    FIELDS_META_FIELD_NUMBER: _ClassVar[int]
    name: str
    desc: str
    fields_meta: _containers.RepeatedCompositeFieldContainer[FieldMeta]
    def __init__(self, name: _Optional[str] = ..., desc: _Optional[str] = ..., fields_meta: _Optional[_Iterable[_Union[FieldMeta, _Mapping]]] = ...) -> None: ...

class TableStatus(_message.Message):
    __slots__ = ["is_existed", "exist_table"]
    IS_EXISTED_FIELD_NUMBER: _ClassVar[int]
    EXIST_TABLE_FIELD_NUMBER: _ClassVar[int]
    is_existed: bool
    exist_table: DBMeta
    def __init__(self, is_existed: bool = ..., exist_table: _Optional[_Union[DBMeta, _Mapping]] = ...) -> None: ...

class VectorMeta(_message.Message):
    __slots__ = ["data_type", "dimension", "store_type", "store_param", "has_source"]
    DATA_TYPE_FIELD_NUMBER: _ClassVar[int]
    DIMENSION_FIELD_NUMBER: _ClassVar[int]
    STORE_TYPE_FIELD_NUMBER: _ClassVar[int]
    STORE_PARAM_FIELD_NUMBER: _ClassVar[int]
    HAS_SOURCE_FIELD_NUMBER: _ClassVar[int]
    data_type: FieldType
    dimension: int
    store_type: str
    store_param: str
    has_source: bool
    def __init__(self, data_type: _Optional[_Union[FieldType, str]] = ..., dimension: _Optional[int] = ..., store_type: _Optional[str] = ..., store_param: _Optional[str] = ..., has_source: bool = ...) -> None: ...

class DocCondition(_message.Message):
    __slots__ = ["db_name", "table_name", "ids", "filter_fields", "include_all_fields", "not_include_fields", "limit"]
    class FilterFieldsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    DB_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    IDS_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELDS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_ALL_FIELDS_FIELD_NUMBER: _ClassVar[int]
    NOT_INCLUDE_FIELDS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    db_name: str
    table_name: str
    ids: _containers.RepeatedScalarFieldContainer[bytes]
    filter_fields: _containers.ScalarMap[str, str]
    include_all_fields: bool
    not_include_fields: _containers.RepeatedScalarFieldContainer[str]
    limit: int
    def __init__(self, db_name: _Optional[str] = ..., table_name: _Optional[str] = ..., ids: _Optional[_Iterable[bytes]] = ..., filter_fields: _Optional[_Mapping[str, str]] = ..., include_all_fields: bool = ..., not_include_fields: _Optional[_Iterable[str]] = ..., limit: _Optional[int] = ...) -> None: ...

class Field(_message.Message):
    __slots__ = ["name", "value", "type", "source", "mul_str_value"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    MUL_STR_VALUE_FIELD_NUMBER: _ClassVar[int]
    name: str
    value: bytes
    type: FieldType
    source: str
    mul_str_value: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., value: _Optional[bytes] = ..., type: _Optional[_Union[FieldType, str]] = ..., source: _Optional[str] = ..., mul_str_value: _Optional[_Iterable[str]] = ...) -> None: ...

class Document(_message.Message):
    __slots__ = ["id", "fields"]
    ID_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    id: bytes
    fields: _containers.RepeatedCompositeFieldContainer[Field]
    def __init__(self, id: _Optional[bytes] = ..., fields: _Optional[_Iterable[_Union[Field, _Mapping]]] = ...) -> None: ...

class Documents(_message.Message):
    __slots__ = ["db_name", "table_name", "docs"]
    DB_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    DOCS_FIELD_NUMBER: _ClassVar[int]
    db_name: str
    table_name: str
    docs: _containers.RepeatedCompositeFieldContainer[Document]
    def __init__(self, db_name: _Optional[str] = ..., table_name: _Optional[str] = ..., docs: _Optional[_Iterable[_Union[Document, _Mapping]]] = ...) -> None: ...

class TermFilter(_message.Message):
    __slots__ = ["field_name", "value", "is_union"]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    IS_UNION_FIELD_NUMBER: _ClassVar[int]
    field_name: str
    value: str
    is_union: int
    def __init__(self, field_name: _Optional[str] = ..., value: _Optional[str] = ..., is_union: _Optional[int] = ...) -> None: ...

class RangeFilter(_message.Message):
    __slots__ = ["field_name", "lower_value", "upper_value", "include_lower", "include_upper"]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    LOWER_VALUE_FIELD_NUMBER: _ClassVar[int]
    UPPER_VALUE_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_LOWER_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_UPPER_FIELD_NUMBER: _ClassVar[int]
    field_name: str
    lower_value: str
    upper_value: str
    include_lower: bool
    include_upper: bool
    def __init__(self, field_name: _Optional[str] = ..., lower_value: _Optional[str] = ..., upper_value: _Optional[str] = ..., include_lower: bool = ..., include_upper: bool = ...) -> None: ...

class VectorQuery(_message.Message):
    __slots__ = ["field_name", "value", "min_score", "max_score", "boost", "is_boost", "retrieval_type"]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    MIN_SCORE_FIELD_NUMBER: _ClassVar[int]
    MAX_SCORE_FIELD_NUMBER: _ClassVar[int]
    BOOST_FIELD_NUMBER: _ClassVar[int]
    IS_BOOST_FIELD_NUMBER: _ClassVar[int]
    RETRIEVAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    field_name: str
    value: bytes
    min_score: float
    max_score: float
    boost: float
    is_boost: bool
    retrieval_type: str
    def __init__(self, field_name: _Optional[str] = ..., value: _Optional[bytes] = ..., min_score: _Optional[float] = ..., max_score: _Optional[float] = ..., boost: _Optional[float] = ..., is_boost: bool = ..., retrieval_type: _Optional[str] = ...) -> None: ...

class SearchRequest(_message.Message):
    __slots__ = ["db_name", "table_name", "vec_queries", "page_text_queries", "term_filters", "range_filters", "topn", "retrieval_params", "online_log_level", "brute_force_search", "is_pack_all_fields", "pack_fields", "mul_vec_logic_op", "is_l2"]
    DB_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    VEC_QUERIES_FIELD_NUMBER: _ClassVar[int]
    PAGE_TEXT_QUERIES_FIELD_NUMBER: _ClassVar[int]
    TERM_FILTERS_FIELD_NUMBER: _ClassVar[int]
    RANGE_FILTERS_FIELD_NUMBER: _ClassVar[int]
    TOPN_FIELD_NUMBER: _ClassVar[int]
    RETRIEVAL_PARAMS_FIELD_NUMBER: _ClassVar[int]
    ONLINE_LOG_LEVEL_FIELD_NUMBER: _ClassVar[int]
    BRUTE_FORCE_SEARCH_FIELD_NUMBER: _ClassVar[int]
    IS_PACK_ALL_FIELDS_FIELD_NUMBER: _ClassVar[int]
    PACK_FIELDS_FIELD_NUMBER: _ClassVar[int]
    MUL_VEC_LOGIC_OP_FIELD_NUMBER: _ClassVar[int]
    IS_L2_FIELD_NUMBER: _ClassVar[int]
    db_name: str
    table_name: str
    vec_queries: _containers.RepeatedCompositeFieldContainer[VectorQuery]
    page_text_queries: _containers.RepeatedScalarFieldContainer[str]
    term_filters: _containers.RepeatedCompositeFieldContainer[TermFilter]
    range_filters: _containers.RepeatedCompositeFieldContainer[RangeFilter]
    topn: int
    retrieval_params: str
    online_log_level: str
    brute_force_search: bool
    is_pack_all_fields: bool
    pack_fields: _containers.RepeatedScalarFieldContainer[str]
    mul_vec_logic_op: MultiVectorLogicOp
    is_l2: bool
    def __init__(self, db_name: _Optional[str] = ..., table_name: _Optional[str] = ..., vec_queries: _Optional[_Iterable[_Union[VectorQuery, _Mapping]]] = ..., page_text_queries: _Optional[_Iterable[str]] = ..., term_filters: _Optional[_Iterable[_Union[TermFilter, _Mapping]]] = ..., range_filters: _Optional[_Iterable[_Union[RangeFilter, _Mapping]]] = ..., topn: _Optional[int] = ..., retrieval_params: _Optional[str] = ..., online_log_level: _Optional[str] = ..., brute_force_search: bool = ..., is_pack_all_fields: bool = ..., pack_fields: _Optional[_Iterable[str]] = ..., mul_vec_logic_op: _Optional[_Union[MultiVectorLogicOp, str]] = ..., is_l2: bool = ...) -> None: ...

class ResultItem(_message.Message):
    __slots__ = ["score", "fields"]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    score: float
    fields: _containers.RepeatedCompositeFieldContainer[Field]
    def __init__(self, score: _Optional[float] = ..., fields: _Optional[_Iterable[_Union[Field, _Mapping]]] = ...) -> None: ...

class SearchResult(_message.Message):
    __slots__ = ["total", "msg", "result_items"]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    RESULT_ITEMS_FIELD_NUMBER: _ClassVar[int]
    total: int
    msg: str
    result_items: _containers.RepeatedCompositeFieldContainer[ResultItem]
    def __init__(self, total: _Optional[int] = ..., msg: _Optional[str] = ..., result_items: _Optional[_Iterable[_Union[ResultItem, _Mapping]]] = ...) -> None: ...

class SearchResponse(_message.Message):
    __slots__ = ["db_name", "table_name", "results", "online_log_message", "result_code"]
    DB_NAME_FIELD_NUMBER: _ClassVar[int]
    TABLE_NAME_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    ONLINE_LOG_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RESULT_CODE_FIELD_NUMBER: _ClassVar[int]
    db_name: str
    table_name: str
    results: _containers.RepeatedCompositeFieldContainer[SearchResult]
    online_log_message: str
    result_code: SearchResultCode
    def __init__(self, db_name: _Optional[str] = ..., table_name: _Optional[str] = ..., results: _Optional[_Iterable[_Union[SearchResult, _Mapping]]] = ..., online_log_message: _Optional[str] = ..., result_code: _Optional[_Union[SearchResultCode, str]] = ...) -> None: ...

class ResponseStatus(_message.Message):
    __slots__ = ["code", "output_info"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_INFO_FIELD_NUMBER: _ClassVar[int]
    code: ResponseCode
    output_info: str
    def __init__(self, code: _Optional[_Union[ResponseCode, str]] = ..., output_info: _Optional[str] = ...) -> None: ...
