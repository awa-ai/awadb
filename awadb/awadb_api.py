from __future__ import annotations

from enum import Enum
from abc import ABC, abstractmethod

DEFAULT_DB_NAME = "default"
DOC_PRIMARY_KEY_NAME = "_id"
DEFAULT_TOPN = 10

class MetricType(Enum):
    L2 = 1
    INNER_PRODUCT = 2

class AwaAPI(ABC):
    """Interface for AwaDB Python Client"""
    
    @abstractmethod
    def list(
        self,
        db_name: Optional[str] = None,
        table_name: Optional[str] = None,
    ):
        """List the db or tables in db.

        Args:
            db_name: Database name, default to None.
            table_name: Table name, default to None.

        Returns: 
            If db_name is None and table_name is None, return all the databases.
            if db_name is None and table_name is not None, return empty list.
            If table_name is None, db_name is not None, return all tables in db_name.
            If neither db_name nor table_name is None, return the schema of the table. 
        """

    @abstractmethod
    def drop(
        self,
        db_name: str,
        table_name: Optional[str] = None,
    ) -> bool:
        """Drop the db or the table in db.

        Args:
            db_name: Database name, default to None.
            table_name: Table name, default to None.

        Returns: 
            If table_name is None, and there are no tables in database "db_name",
            the database can be dropped successfully, otherwise failed.
        """

    @abstractmethod
    def add(
        self,
        table_name: str,
        docs,
        db_name: str = DEFAULT_DB_NAME,
    ) -> bool:
        """Add documents into the specified table.
           If table not existed, it will be created automatically.

        Args:
            table_name: The specified table for search and storage.
            
            docs: The adding documents which can be described as dict or list of dicts.
                    Each key-value pair in dict is a field of document.
            
            db_name: Database name, default to DEFAULT_DB_NAME.

        Returns:
            Success or failure of adding the documents into the specified table.
        """
   
    @abstractmethod
    def search(
        self,
        table_name: str,
        query,
        db_name: str = DEFAULT_DB_NAME,
        topn: int = DEFAULT_TOPN,
        filters: Optional[dict] = None,
        include_fields: Optional[Set[str]] = None,
        brute_force_search: bool = False,
        metric_type: MetricType = MetricType.L2,
        mul_vec_weight: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ):
        """Vector search in the specified table.

        Args: 
            table_name: The specified table for search.

            query: Input query, including vector or text.

            db_name: Database name, default to DEFAULT_DB_NAME.

            topn: The topn nearest neighborhood documents to return.

            filters (Optional[dict]): Filter by fields. Defaults to None.

            E.g. `{"color" : "red", "price": 4.20}`. Optional.

            E.g. `{"max_price" : 15.66, "min_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<'price'<15.66).

            E.g. `{"maxe_price" : 15.66, "mine_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<='price'<=15.66).

            include_fields: The fields whether included in the search results.

            brute_force_search: Brute force search or not. Default to not.
                                        If vectors not indexed, automatically to use brute force search.

            metric_type: The distance type of computing vectors. Default to L2.

            mul_vec_weight: Multiple vector field search weights. Default to None.

            E.g. `{'f1': 2.0, 'f2': 1.0}`  vector field f1 weight is 2.0, vector field f2 weight is 1.0.

            Notice that field f1 and f2 should have the same dimension compared to vec_query.

            kwargs: Any possible extended parameters.

        Returns:
            Results of searching.
        """
        
    @abstractmethod
    def get(
        self,
        table_name: str,
        db_name: str = DEFAULT_DB_NAME,
        ids: Optional[list] = None,
        filters: Optional[dict] = None,
        include_fields: Optional[Set[str]] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ):
        """Get documents of the primary keys in the the specified table.

        Args:
            table_name: The specified table for search and storage.

            db_name: Database name, default to DEFAULT_DB_NAME.

            ids: The primary keys of the queried documents.

            filters: Filter by fields. Defaults to None.

            E.g. `{"color" : "red", "price": 4.20}`. Optional.

            E.g. `{"max_price" : 15.66, "min_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<'price'<15.66).

            E.g. `{"maxe_price" : 15.66, "mine_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<='price'<=15.66).

            include_fields: The fields whether included in the get results.

            limit: The limited return results.

        Returns:
            The detailed information of the queried documents.
        """
       
    @abstractmethod
    def delete(
        self,
        table_name: str,
        db_name: str = DEFAULT_DB_NAME,
        ids: Optional[list] = None,
        filters: Optional[dict] = None, 
        **kwargs: Any,
    ) -> bool:
        """Delete docs in the specified table.

        Args:
            table_name: The specified table for deleting.

            db_name: Database name, default to DEFAULT_DB_NAME.

            ids: The primary keys of the deleted documents.

            filters: Filter by fields. Defaults to None.

            E.g. `{"color" : "red", "price": 4.20}`. Optional.

            E.g. `{"max_price" : 15.66, "min_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<'price'<15.66).

            E.g. `{"maxe_price" : 15.66, "mine_price": 4.20}`

            `price` is the metadata field, means range filter(4.20<='price'<=15.66).
        Returns:
            True of False of the deleting operation.
        """

