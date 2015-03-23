# -*- coding: utf-8 -*-
"""Elasticsearch related funcionality."""

from sqlalchemy.types import (
    BIGINT,
    BOOLEAN,
    CHAR,
    CLOB,
    DATE,
    DATETIME,
    DECIMAL,
    FLOAT,
    INTEGER,
    NCHAR,
    NUMERIC,
    NVARCHAR,
    NullType,
    REAL,
    SMALLINT,
    TEXT,
    TIME,
    TIMESTAMP,
    VARCHAR,
)


class Mapping(object):

    """ElasticSearch mapping.

    :param table_name: Database table name
    :type table_name: str
    :param table_schema: Database table schema from sqlalchemy
    :type table_schema: dict(str, sqlalchemy.types.*)

    """

    # Mapping from sqlalchemy types to elasticsearch ones
    # Note: The columns that have a type that maps to None, will be removed
    # from the final mapping to let elastic search figure out the type by
    # itself. This is because SQLite works with storage classes and type
    # affinities and it's not always clear what datatype data will really have.
    # In particular, values with NUMERIC affinity might be stored using any of
    # the five available storage classes, so it's not possible to predict for
    # all cases what type of data will be stored without looking at it as
    # elasticsearch does.
    SQL_TYPE_MAPPING = {
        BIGINT: 'long',
        BOOLEAN: 'boolean',
        CHAR: 'string',
        CLOB: 'string',
        DATE: None,
        DATETIME: 'date',
        DECIMAL: None,
        FLOAT: 'float',
        # TODO: Use 'integer' when data is in range
        INTEGER: 'long',
        NCHAR: 'string',
        NVARCHAR: 'string',
        NullType: None,
        NUMERIC: None,
        # TODO: Use 'float' when data is in range
        REAL: 'double',
        SMALLINT: 'integer',
        TEXT: 'string',
        TIME: 'date',  # TODO: Map to something time specific?
        TIMESTAMP: 'date',
        VARCHAR: 'string',
    }

    def __init__(self, table_name, table_schema):
        """Map every column type to an elasticsearch mapping."""
        columns_mapping = {}

        for column_name, column_sql_type in table_schema.iteritems():
            column_mapping = self._get_column_mapping(column_sql_type)

            # Skip columns that don't have an mapping defined and let
            # elasticsearch figure out the mapping itself
            if column_mapping is None:
                continue

            columns_mapping[column_name] = column_mapping

        self.mapping = {
            table_name: {
                'properties': columns_mapping,
            }
        }

    def _get_column_mapping(self, column_sql_type):
        """Return column mapping based on its name and type.

        :param column_sql_type: Database column type
        :type column_sql_type: sqlalchemy.types.*
        :return: Mapping for the given column name and type (if possible)
        :rtype: dict(str) | None

        """
        column_es_type = self.SQL_TYPE_MAPPING[type(column_sql_type)]
        if column_es_type is None:
            return None

        column_mapping = {'type': column_es_type}
        return column_mapping
