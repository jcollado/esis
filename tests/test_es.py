# -*- coding: utf-8 -*-
"""Elasticsearch client test cases."""

import hashlib
import tempfile
import unittest

from mock import (
    MagicMock as Mock,
    patch,
)
from sqlalchemy import types as sql_types

from esis.es import (
    Client,
    Mapping,
    get_document,
    get_index_action,
)


class ClientTest(unittest.TestCase):

    """Elasticsearch client wrapper test cases."""

    def setUp(self):
        """Patch elasticsearch class and create client object."""
        self.patcher = patch('esis.es.Elasticsearch')
        self.elasticsearch_cls = self.patcher.start()
        self.client = Client(host='localhost', port=9200)

    def test_index(self):
        """Index directory wrapper."""
        directory = 'some directory'
        self.client._index_directory = Mock()

        self.client.index(directory)
        self.client._index_directory.assert_called_once_with(directory)

    @patch('esis.es.Database')
    @patch('esis.es.TreeExplorer')
    def test_index_directory(self, tree_explorer_cls, database_cls):
        """Index directory."""
        tree_explorer_cls().paths.return_value = ['path_1', 'path_2', 'path_3']
        self.client._recreate_index = Mock()
        documents_indexed_per_database = [1, 2, 3]
        self.client._index_database = Mock(
            side_effect=documents_indexed_per_database)

        directory = 'some directory'
        self.assertEqual(
            self.client._index_directory(directory),
            sum(documents_indexed_per_database),
        )

    def test_recreate_index_that_exists(self):
        """Index is deleted and then created."""
        indices = self.elasticsearch_cls().indices
        indices.exists.return_value = True

        index_name = 'abcd'
        self.client._recreate_index(index_name)
        indices.delete.assert_called_once_with(index_name)
        indices.create.assert_called_once_with(index_name)

    def test_recreate_index_that_does_not_exist(self):
        """Index is created."""
        indices = self.elasticsearch_cls().indices
        indices.exists.return_value = False

        index_name = 'abcd'
        self.client._recreate_index(index_name)
        self.assertFalse(indices.delete.called)
        indices.create.assert_called_once_with(index_name)

    @patch('esis.es.DBReader')
    def test_index_database(self, db_reader_cls):
        """Index a database completely."""
        database = Mock()
        db_reader = db_reader_cls()
        db_reader.tables.return_value = ('calls', 'messages', 'pictures')
        documents_indexed_per_table = (1, 2, 3)
        self.client._index_table = Mock(
            side_effect=documents_indexed_per_table)

        documents_indexed = self.client._index_database(database)
        db_reader_cls.assert_called_with(database)
        self.assertEqual(documents_indexed, sum(documents_indexed_per_table))

    @patch('esis.es.elasticsearch.helpers.bulk')
    @patch('esis.es.Mapping')
    def test_index_table(self, mapping_cls, bulk_mock):
        """Index a database table."""
        indices = self.elasticsearch_cls().indices
        mapping = mapping_cls()
        rows = [
            {'id': 1, 'number': '123456789'},
            {'id': 2, 'number': '234567890'},
            {'id': 3, 'number': '345678901'},
        ]
        bulk_mock.return_value = (len(rows), [])

        db_path = 'some path'
        table_name = 'calls'
        table_reader = Mock()
        table_reader.rows.return_value = rows
        table_reader.database.db_filename = db_path
        table_reader.table.name = table_name
        documents_indexed = self.client._index_table(table_reader)
        indices.put_mapping.assert_called_once_with(
            index=self.client.INDEX_NAME,
            doc_type=hashlib.md5(
                '{}:{}'.format(db_path, table_name).encode('utf-8')).hexdigest(),
            body=mapping.mapping)
        self.assertEqual(documents_indexed, len(rows))

    @patch('esis.es.elasticsearch.helpers.bulk')
    @patch('esis.es.Mapping')
    def test_index_table_with_some_failures(self, mapping_cls, bulk_mock):
        """Index a database table with some failures handled."""
        indices = self.elasticsearch_cls().indices
        mapping = mapping_cls()
        rows = [
            {'id': 1, 'number': '123456789'},
            {'id': 2, 'number': '234567890'},
            {'id': 3, 'number': '345678901'},
        ]
        indexed_rows = 1
        bulk_mock.return_value = (indexed_rows, ['some error'])

        db_path = 'some path'
        table_name = 'calls'
        table_reader = Mock()
        table_reader.rows.return_value = rows
        table_reader.database.db_filename = db_path
        table_reader.table.name = table_name
        with patch('esis.es.logger'):
            documents_indexed = self.client._index_table(table_reader)
        indices.put_mapping.assert_called_once_with(
            index=self.client.INDEX_NAME,
            doc_type=hashlib.md5(
                '{}:{}'.format(db_path, table_name).encode('utf-8')).hexdigest(),
            body=mapping.mapping)
        self.assertEqual(
            documents_indexed,
            indexed_rows,
        )

    def test_search(self):
        """Search using text query."""
        self.elasticsearch_cls().search.return_value = {
            'hits': {
                'total': 10,
                'hits': [1, 2, 3, 4],
            },
            '_scroll_id': 'abcd'
        }
        self.elasticsearch_cls().scroll.side_effect = [
            {'hits': {'hits': [5, 6, 7]}},
            {'hits': {'hits': [8, 9, 10]}},
            {'hits': {'hits': []}},
        ]

        query = 'this is the query'
        hits = list(self.client.search(query))

        self.assertListEqual(
            hits,
            [[1, 2, 3, 4], [5, 6, 7], [8, 9, 10]])

    def test_clean(self):
        """Clean indices."""
        self.client.clean()
        indices = self.elasticsearch_cls().indices
        indices.delete.assert_called_once_with(index='_all')

    def test_count(self):
        """Return indexed documents."""
        expected_count = {
            '_shards': {
                'failed': 0,
                'successful': 0,
                'total': 0,
            },
            'count': 0,
        }

        self.elasticsearch_cls().count.return_value = expected_count
        self.assertDictEqual(self.client.count(), expected_count)

    def tearDown(self):
        """Undo the patching."""
        self.patcher.stop()


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
            'data': b'a',
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
