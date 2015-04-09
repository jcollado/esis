# -*- coding: utf-8 -*-
"""Elasticsearch client test cases."""

import tempfile
import unittest

from sqlalchemy import types as sql_types

from esis.es import (
    Mapping,
    get_document,
    get_index_action,
)


class MappingTest(unittest.TestCase):

    """Test translation from SQL schema to Elasticsearch mapping."""

    def test_mapping_types(self):
        """Test mapping from sql to Elasticsearch index types."""
        table_schema = {
            'my_bigint': sql_types.BIGINT(),
            'my_boolean': sql_types.BOOLEAN(),
            'my_char': sql_types.CHAR(16),
            'my_clob': sql_types.CLOB(),
            'my_date': sql_types.DATE(),
            'my_datetime': sql_types.DATETIME(),
            'my_decimal': sql_types.DECIMAL(10, 5),
            'my_float': sql_types.FLOAT(),
            'my_integer': sql_types.INTEGER(),
            'my_nchar': sql_types.NCHAR(16),
            'my_nvarchar': sql_types.NVARCHAR(16),
            'my_null': sql_types.NullType(),
            'my_numeric': sql_types.NUMERIC(),
            'my_real': sql_types.REAL(),
            'my_smallint': sql_types.SMALLINT(),
            'my_text': sql_types.TEXT(),
            'my_timestamp': sql_types.TIMESTAMP(),
            'my_varchar': sql_types.VARCHAR(16),
        }
        document_type = 'some_document_type'
        mapping = Mapping(document_type, table_schema)
        self.assertDictEqual(
            mapping.mapping,
            {
                document_type: {
                    'properties': {
                        '_metadata': {
                            'type': 'object',
                            'index': 'no',
                            'properties': {
                                'filename': {
                                    'type': 'string',
                                    'index': 'no',
                                },
                                'table': {
                                    'type': 'string',
                                    'index': 'no',
                                },
                            },
                        },
                        'my_bigint': {'type': 'long'},
                        'my_boolean': {'type': 'boolean'},
                        'my_char': {'type': 'string'},
                        'my_clob': {'type': 'string'},
                        'my_datetime': {'type': 'date'},
                        'my_float': {'type': 'float'},
                        'my_integer': {'type': 'long'},
                        'my_nchar': {'type': 'string'},
                        'my_nvarchar': {'type': 'string'},
                        'my_real': {'type': 'double'},
                        'my_smallint': {'type': 'integer'},
                        'my_text': {'type': 'string'},
                        'my_timestamp': {'type': 'date'},
                        'my_varchar': {'type': 'string'},
                    },
                },
            },
        )


class GetDocumentTest(unittest.TestCase):

    """Get document test cases."""

    def test_metadata_added(self):
        """Metadata is added to the document."""
        db_filename = 'filename'
        table_name = 'table'
        row = {'text': 'some message'}
        document = get_document(db_filename, table_name, row)
        self.assertDictEqual(
            document,
            {
                'text': 'some message',
                '_metadata': {
                    'filename': db_filename,
                    'table': table_name,
                }
            },
        )

    def test_binary_data_removed(self):
        """Binary data removed."""
        db_filename = 'filename'
        table_name = 'table'
        row = {
            'text': 'some message',
            'data': buffer('a'),
        }
        document = get_document(db_filename, table_name, row)
        self.assertDictEqual(
            document,
            {
                'text': 'some message',
                '_metadata': {
                    'filename': db_filename,
                    'table': table_name,
                }
            },
        )

    def test_local_path_removed(self):
        """Local path removed."""
        with tempfile.NamedTemporaryFile() as db_file:
            table_name = 'table'
            row = {
                'text': 'some message',
                'path': 'file://{}'.format(db_file.name),
            }
            document = get_document(db_file.name, table_name, row)
            self.assertDictEqual(
                document,
                {
                    'text': 'some message',
                    '_metadata': {
                        'filename': db_file.name,
                        'table': table_name,
                    }
                },
            )


class GetIndexActionTest(unittest.TestCase):

    """Get index action test cases."""

    def test_get_index_action(self):
        """Get index action for a given row."""
        index_name = 'index'
        document_type = 'message'
        document = {'text': 'some message'}
        action = get_index_action(index_name, document_type, document)
        self.assertDictEqual(
            action,
            {
                '_index': 'index',
                '_type': 'message',
                '_source': {
                    'text': 'some message',
                },
            },
        )

    def test_get_index_action_row_with_id_field(self):
        """Get index action for a row with and _id field."""
        index_name = 'index'
        document_type = 'message'
        document = {
            '_id': 7,
            'text': 'some message',
        }
        action = get_index_action(index_name, document_type, document)
        self.assertDictEqual(
            action,
            {
                '_id': 7,
                '_index': 'index',
                '_type': 'message',
                '_source': {
                    '_id': 7,
                    'text': 'some message',
                },
            },
        )
