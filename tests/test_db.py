# -*- coding: utf-8 -*-
"""Test database functionality."""

import os
import sqlite3
import tempfile
import unittest

from contextlib import closing
from datetime import datetime
from time import time

from mock import (
    MagicMock as Mock,
    patch,
)
from sqlalchemy import (
    Column,
    select,
)
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.types import (
    BIGINT,
    BOOLEAN,
    DATETIME,
    INTEGER,
    NUMERIC,
    SMALLINT,
    TEXT,
    TIMESTAMP,
)

from esis.db import (
    DBReader,
    Database,
    DatetimeDecorator,
    IntegerDecorator,
    TableReader,
    TypeCoercionMixin,
)


class DatabaseTest(unittest.TestCase):

    """Database wrapper test cases."""

    def test_get_table_metadata(self):
        """Table metadata can be retrieved using index notation."""
        with tempfile.NamedTemporaryFile() as db_file:
            with closing(sqlite3.connect(db_file.name)) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(
                        'CREATE TABLE messages (id INTEGER, message TEXT)')

            database = Database(db_file.name)
            table = database['messages']
            schema = {column.name: type(column.type)
                      for column in table.columns}
            self.assertDictEqual(
                schema,
                {'id': INTEGER, 'message': TEXT})

    def test_get_unknown_table_metadata(self):
        """NoSuchTableError raised when table name is not found."""
        with tempfile.NamedTemporaryFile() as db_file:
            with closing(sqlite3.connect(db_file.name)) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(
                        'CREATE TABLE messages (id INTEGER, message TEXT)')

            database = Database(db_file.name)

            with self.assertRaises(NoSuchTableError):
                database['unknown']

    def test_type_error_on_wrong_table_name(self):
        """TypeError raised when table name is not a string."""
        with tempfile.NamedTemporaryFile() as db_file:
            with closing(sqlite3.connect(db_file.name)) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(
                        'CREATE TABLE messages (id INTEGER, message TEXT)')

            database = Database(db_file.name)

            with self.assertRaises(TypeError):
                database[0]

    def test_run_quick_check_passes(self):
        """Quick check passes for SQLite database."""
        with tempfile.NamedTemporaryFile() as db_file:
            with closing(sqlite3.connect(db_file.name)) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(
                        'CREATE TABLE messages (id INTEGER, message TEXT)')

            with Database(db_file.name) as database:
                self.assertTrue(database.run_quick_check())

    def test_run_quick_check_fails(self):
        """Quick check fails for non SQLite database files."""
        with tempfile.NamedTemporaryFile() as db_file:
            db_file.write('this is a text file, not a database file')
            db_file.flush()
            with Database(db_file.name) as database:
                self.assertFalse(database.run_quick_check())

    def test_context_manager(self):
        """Connection is opened/closed when used as a context manager."""
        database = Database(':memory:')

        # Connection is None when database object is created
        self.assertIsNone(database.connection)

        with database:
            # Connection is not closed inside the context
            self.assertFalse(database.connection.closed)

        # Connection is closed outside the context
        self.assertTrue(database.connection.closed)


class DBReaderTest(unittest.TestCase):

    """Database reader test cases."""

    def create_tables(self, db_filename, table_names, fts_table_names=None):
        """Create tables needed for a test case.

        :param db_filename: Path to database file
        :type db_filename: str
        :param table_names: Names of the tables to create
        :type table_names: list(str)
        :param table_names: Names of the FTS tables to create
        :type table_names: list(str)

        """
        with closing(sqlite3.connect(db_filename)) as connection:
            with closing(connection.cursor()) as cursor:
                for table_name in table_names:
                    cursor.execute(
                        'CREATE TABLE {} (id INTEGER)'
                        .format(table_name))

                if fts_table_names is not None:
                    for fts_table_name in fts_table_names:
                        cursor.execute(
                            'CREATE VIRTUAL TABLE {} USING fts3(id INTEGER)'
                            .format(fts_table_name))

    def test_tables(self):
        """Database tables are correctly retrieved."""
        expected_table_names = sorted(
            ['messages', 'calls', 'events', 'pictures'])

        with tempfile.NamedTemporaryFile() as db_file:
            self.create_tables(db_file.name, expected_table_names)
            with Database(db_file.name) as database:
                db_reader = DBReader(database)
                table_names = sorted(db_reader.tables())
                self.assertListEqual(table_names, expected_table_names)

    def test_ignore_fts_tables(self):
        """FTS database tables are ignored."""
        expected_table_names = ['messages', 'calls', 'events', 'pictures']
        fts_table_names = [
            '{}_search'.format(table_name)
            for table_name in expected_table_names]

        with tempfile.NamedTemporaryFile() as db_file:
            self.create_tables(
                db_file.name,
                expected_table_names,
                fts_table_names,
            )

            with Database(db_file.name) as database:
                db_reader = DBReader(database)
                table_names = [table_name for table_name in db_reader.tables()]

                # Check ignored tables are indeed in the database
                master_table = database['sqlite_master']
                query = (
                    select([master_table.c.name])
                    .where(master_table.c.type == 'table')
                )
                result = database.connection.execute(query)
                all_table_names = set(row[0] for row in result.fetchall())
                for table_name in fts_table_names:
                    self.assertIn(table_name, all_table_names)

                self.assertListEqual(
                    sorted(table_names),
                    sorted(expected_table_names))


class IntegerDecoratorTest(unittest.TestCase):

    """Integer decorator test cases."""

    def setUp(self):
        """Create integer decorator object."""
        self.integer_decorator = IntegerDecorator()
        self.dialect = Mock()

    def test_integer(self):
        """Integer should be returned as it is."""
        result = self.integer_decorator.process_result_value(0, self.dialect)
        self.assertEqual(result, 0)

    def test_string_integer(self):
        """Integer in string form should be returned as it is."""
        value = '999999999999999'
        result = self.integer_decorator.process_result_value(
            value, self.dialect)
        self.assertEqual(result, int(value))

    def test_null_string(self):
        """null string should be converted to None."""
        result = self.integer_decorator.process_result_value(
            'null', self.dialect)
        self.assertIsNone(result)

    def test_date_string(self):
        """String containing a date is parsed and converted to a timestamp."""
        result = self.integer_decorator.process_result_value(
            '2014-09-06T11:27:09.000Z', self.dialect)
        self.assertEqual(result, 1410002829)

    def test_other_strings(self):
        """None is returned for other string values."""
        with patch('esis.db.logger'):
            value = self.integer_decorator.process_result_value(
                'other string', self.dialect)

        self.assertIsNone(value)

    def test_other_types(self):
        """None is returned for values of other types."""
        for invalid_value in ((), []):
            with patch('esis.db.logger'):
                value = self.integer_decorator.process_result_value(
                    invalid_value, self.dialect)

            self.assertIsNone(value)


class DatetimeDecoratorTest(unittest.TestCase):

    """Datetime decorator test cases."""

    def setUp(self):
        """Create integer decorator object."""
        self.datetime_decorator = DatetimeDecorator()
        self.dialect = Mock()

    def test_datetime(self):
        """Datetime object is converted to an ISO string."""
        now = datetime.now()

        value = self.datetime_decorator.process_result_value(now, self.dialect)
        self.assertEqual(value, now.isoformat())

    def test_timestamp_seconds(self):
        """Timestamp in seconds is converted to an ISO string."""
        timestamp = int(time())

        value = self.datetime_decorator.process_result_value(
            timestamp, self.dialect)
        self.assertEqual(
            value, datetime.utcfromtimestamp(timestamp).isoformat())

    def test_timestamp_milliseconds(self):
        """Timestamp in milliseconds is converted to an ISO string."""
        timestamp = int(time()) * 1000

        value = self.datetime_decorator.process_result_value(
            timestamp, self.dialect)
        self.assertEqual(
            value, datetime.utcfromtimestamp(timestamp / 1000).isoformat())

    def test_timestamp_microseconds(self):
        """Timestamp in microseconds is converted to an ISO string."""
        timestamp = int(time()) * 1000000

        value = self.datetime_decorator.process_result_value(
            timestamp, self.dialect)
        self.assertEqual(
            value, datetime.utcfromtimestamp(timestamp / 1000000).isoformat())
    def test_invalid_timestamp(self):
        """None is returned if timestamp is out of range."""
        timestamp = 999999999999999999

        with patch('esis.db.logger'):
            value = self.datetime_decorator.process_result_value(
                timestamp, self.dialect)

        self.assertIsNone(value)

    def test_string(self):
        """Datetime string is reformatted as an ISO string if needed."""
        dt_value = datetime(2014, 1, 1)
        value = self.datetime_decorator.process_result_value(
            dt_value.strftime('%Y-%m-%d'), self.dialect)
        self.assertEqual(value, dt_value.isoformat())

    def test_invalid_string(self):
        """None is returned if string cannot be parsed."""
        with patch('esis.db.logger'):
            value = self.datetime_decorator.process_result_value(
                'this is not a datetime', self.dialect)

        self.assertIsNone(value)

    def test_invalid_type(self):
        """None is returned if value type cannot be parsed."""
        for invalid_value in (True, (), []):
            with patch('esis.db.logger'):
                value = self.datetime_decorator.process_result_value(
                    invalid_value, self.dialect)

            self.assertIsNone(value)


class TypeCoercionMixinTest(unittest.TestCase):

    """Type coercion mixin test cases."""

    def setUp(self):
        """Create coercion object from the mixin."""
        self.coercer = TypeCoercionMixin()

    def test_numeric_coerced_to_text(self):
        """Numeric columns are coerced to text columns."""
        columns = self.coercer._coerce([
            Column('column', NUMERIC()),
            Column('column', BOOLEAN()),
            Column('column', INTEGER()),
            Column('column', BIGINT()),
            Column('column', SMALLINT()),
            Column('column', DATETIME()),
            Column('column', TIMESTAMP()),
        ])

        column_types = [type(column.type) for column in columns]

        self.assertListEqual(
            column_types,
            [
                TEXT,
                IntegerDecorator,
                IntegerDecorator,
                IntegerDecorator,
                IntegerDecorator,
                DatetimeDecorator,
                DatetimeDecorator,
            ])


class TableReaderTest(unittest.TestCase):

    """Table reader test cases."""

    @classmethod
    def setUpClass(cls):
        """Create test database.

        Database is reused between test cases because they just read data
        without chaning the database in any way.

        """
        with tempfile.NamedTemporaryFile(delete=False) as cls.db_file:
            with closing(sqlite3.connect(cls.db_file.name)) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(
                        'CREATE TABLE messages (id INTEGER, message TEXT);')

                    cls.message_values = [
                        (1, 'one message'),
                        (2, 'another message'),
                        (3, 'one more message')]
                    cursor.executemany(
                        'INSERT INTO messages VALUES(?, ?);',
                        cls.message_values)

                    cursor.execute(
                        'CREATE TABLE calls (_id INTEGER, number TEXT);')
                    cls.call_values = [
                        (1, '123456789'),
                        (2, '234567890'),
                        (3, '345678901')]
                    cursor.executemany(
                        'INSERT INTO calls VALUES(?, ?);',
                        cls.call_values)

                    cursor.execute(
                        'CREATE TABLE events (_id INTEGER, description TEXT);')
                    cls.event_values = [
                        (1, 'holiday'),
                        (2, 'meeting'),
                        (1, 'reminder')]
                    cursor.executemany(
                        'INSERT INTO events VALUES(?, ?);',
                        cls.event_values)

                    cursor.execute(
                        'CREATE TABLE pictures '
                        '(id INTEGER, raw_data BLOB);')
                    cls.picture_values = [
                        (1, ''),
                        (2, ''),
                        (3, '')]
                    cursor.executemany(
                        'INSERT INTO pictures VALUES(?, ?);',
                        cls.picture_values)
                connection.commit()

            cls.database = Database(cls.db_file.name)
            cls.database.connect()

    @classmethod
    def tearDownClass(cls):
        """Close database connection."""
        cls.database.disconnect()
        os.remove(cls.db_file.name)

    def assert_schema(self, table_name, expected_values):
        """Assert each column type is of the expected type.

        :param table_name: Database table name
        :type table_name: str
        :param expected_values: Expected column name and column type
        :type expected_values: list(tuple(str, sqlalchemy.types.*))

        """
        table_reader = TableReader(self.database, table_name)
        schema = table_reader.get_schema()
        self.assertEqual(len(schema), len(expected_values))
        for column_name, column_type in expected_values:
            self.assertEqual(
                type(schema[column_name]), column_type)

    def test_get_schema(self):
        """Table schema can be retrieved correctly."""
        expected_values = [
            ('id', INTEGER),
            ('message', TEXT),
        ]
        self.assert_schema('messages', expected_values)

    def test_get_schema_with_unique_id(self):
        """_id column is present when values are unique."""
        expected_values = [
            ('_id', INTEGER),
            ('number', TEXT),
        ]
        self.assert_schema('calls', expected_values)

    def test_get_schema_with_non_unique_id(self):
        """_id column is ignored when values are not unique."""
        expected_values = [
            ('description', TEXT),
        ]
        self.assert_schema('events', expected_values)

    def test_get_schema_with_blob_columns(self):
        """blob columns are ignored."""
        expected_values = [
            ('id', INTEGER),
        ]
        self.assert_schema('pictures', expected_values)

    def test_rows(self):
        """All table rows are traversed."""
        table_reader = TableReader(self.database, 'messages')

        self.assertListEqual(
            list(table_reader.rows()),
            self.message_values)
