# -*- coding: utf-8 -*-
"""Elasticsearch related funcionality."""
import hashlib
import logging
import os
import time

from urlparse import urlparse

import elasticsearch.helpers

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError

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

from esis.fs import TreeExplorer
from esis.db import (
    DBReader,
    Database,
    TableReader,
)


logger = logging.getLogger(__name__)

class Client(object):

    """Elasticsearch client wrapper."""

    def __init__(self):
        """Create low level client."""
        self.es_client = Elasticsearch()

    def index(self, directory):
        """Index all the information available in a directory.

        In elasticsearch there will be an index for each database and a
        document type for each table in the database.

        :param directory: Directory that should be indexed
        :type directory: str

        """
        logger.debug('Indexing %r...', directory)
        start = time.time()
        documents_indexed = self._index_directory(directory)
        end = time.time()
        logger.info('%d documents indexed in %.2f seconds',
                    documents_indexed, end-start)

    def _index_directory(self, directory):
        """Index all databases under a given directory.

        :param directory: Path to the directory to explore
        :type directory: str
        :return: Documents indexed for this directory
        :rtype: int

        """
        documents_indexed = 0

        tree_explorer = TreeExplorer(directory)
        for db_path in tree_explorer.paths():
            index_name = get_index_name(db_path)
            self._recreate_index(index_name)
            with Database(db_path) as database:
                documents_indexed += self._index_database(index_name, database)

        return documents_indexed

    def _recreate_index(self, index_name):
        """Recreate elasticsearch index.

        It's checked that the index exists before trying to delete it to avoid
        failures.

        :param index_name: Elasticsearch index to delete
        :type index_name: str

        """
        logger.debug('Recreating index (%s)...', index_name)
        if self.es_client.indices.exists(index_name):
            self.es_client.indices.delete(index_name)
        self.es_client.indices.create(index_name)

    def _index_database(self, index_name, database):
        """Index all tables in a database file.

        :param index_name: Elasticsearch index name
        :type index_name: str
        :param database: Database to be indexed
        :type database: :class:`esis.db.Database`
        :return: Documents indexed for this database
        :rtype: int

        """
        # Recreate index for the given database
        documents_indexed = 0

        logger.debug('Populating index (%s)...', index_name)
        db_reader = DBReader(database)

        # Index the content of every database table
        for table_name in db_reader.tables():
            table_reader = TableReader(database, table_name)
            documents_indexed += self._index_table(
                index_name, table_name, table_reader)

        return documents_indexed

    def _index_table(self, index_name, table_name, table_reader):
        """Index all rows in a database table.

        :param index_name: Elasticsearch index to use when indexing documents
        :type index_name: str
        :table_name: Table name for which rows are indexed in elasticsearch
        :type table: str
        :param table_reader: Object to iterate through all rows in a table
        :type table_reader: :class:`esis.db.TableReader`
        :return: Documents indexed for this table
        :rtype: int

        """
        documents_indexed = 0

        # TODO: Transform table name to avoid names not allowed in elasticsearch
        document_type = table_name

        # Translate database schema into an elasticsearch mapping
        table_schema = table_reader.get_schema()
        table_mapping = Mapping(table_name, table_schema)
        try:
            self.es_client.indices.put_mapping(
                index=index_name,
                doc_type=document_type,
                body=table_mapping.mapping)
        except RequestError as exception:
            logger.error(exception)

        actions = (
            get_index_action(index_name, document_type, row)
            for row in table_reader.rows()
        )
        documents_indexed, errors = elasticsearch.helpers.bulk(
            self.es_client, actions)

        if errors:
            logger.warning('Indexing errors reported: %s', errors)

        return documents_indexed

    def search(self, query):
        """Yield all documents that match a given query.

        :param query: A simple query with data to search in elasticsearch
        :type query: str
        :return: Records that matched the query as returned by elasticsearch
        :rtype: list(dict)

        """
        logger.debug('Searching %r...', query)
        body = {
            'query': {
                'match': {
                    '_all': query,
                },
            },
        }

        response = self.es_client.search(
            body=body,
            scroll='5m',
            size=100,
        )

        hits_info = response['hits']
        hits_total = hits_info['total']
        logger.info('%d documents matched', hits_total)
        hits = hits_info['hits']
        yield hits

        if '_scroll_id' in response:
            scroll_id = response['_scroll_id']

            while True:
                response = self.es_client.scroll(
                    scroll_id=scroll_id,
                    scroll='5m',
                )
                hits = response['hits']['hits']
                if not hits:
                    break

                yield hits

    def count(self):
        """Return indexed documents information.

        :returns: Indexed documents information
        :rtype: dict

        """
        return self.es_client.count()

    def clean(self):
        """Remove all indexed documents."""
        self.es_client.indices.delete(index='_all')


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

def get_index_name(path):
    """Get index name for a database file.

    :param path: Path to file to be indexed
    :type path: str
    :return: Index name for the DB file
    :rtype: str

    """
    # There's a limit in elasticsearch index name length and there are some
    # characters that are not allowed. Using an md5 hash seems to be a
    # reasonable way to get to a unique index name for each database file.
    index_name = hashlib.md5(path).hexdigest()
    return index_name

def get_index_action(index_name, document_type, row):
    """Generate index action for a given database row.

    :param index_name: Elasticsearch index to use
    :type index_name: str
    :param document_type: Elasticsearch document type to use
    :type index_name: str
    :param row: The row to be indexed in elasticsearch
    :type row: sqlalchemy.engine.result.RowProxy
    :return: Action to be passed in bulk request
    :rtype: dict

    """
    source = dict(row)

    # Avoid indexing binary data
    for field_name, field_data in source.items():
        # Avoid indexing binary data
        if isinstance(field_data, buffer):
            logger.debug('%r field discarded before indexing', field_name)
            del source[field_name]

        # Avoid indexing local paths
        elif isinstance(field_data, basestring):
            url = urlparse(field_data)
            if (url.scheme == 'file'
                    and os.path.exists(url.path)):
                logger.debug(
                    '%r field discarded before indexing', field_name)
                del source[field_name]

    action = {
        '_index': index_name,
        '_type': document_type,
        '_source': source,
    }

    # Use the same _id field in elasticsearch as in the database table
    if '_id' in source:
        action['_id'] = source['_id']

    return action

