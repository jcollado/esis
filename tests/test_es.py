# -*- coding: utf-8 -*-
"""Elasticsearch client test cases."""

import unittest

from sqlalchemy import types as sql_types

from esis.es import Mapping


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
