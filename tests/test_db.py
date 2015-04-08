# -*- coding: utf-8 -*-
"""Test database functionality."""

import sqlite3
import tempfile
import unittest

from contextlib import closing

from mock import MagicMock as Mock
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.types import (
    INTEGER,
    TEXT,
)

from esis.db import (
    Database,
    IntegerDecorator,
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
        """Quick check fails for non SQLite dtabase files."""
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
        self.assertIsNone(
            self.integer_decorator.process_result_value(
                'other string', self.dialect))

    def test_other_types(self):
        """None is returned for values of other types."""
        for invalid_value in ((), []):
            self.assertIsNone(
                self.integer_decorator.process_result_value(
                    invalid_value, self.dialect))
