# -*- coding: utf-8 -*-
"""Test database functionality."""

import sqlite3
import tempfile
import unittest

from contextlib import closing

from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.types import (
    INTEGER,
    TEXT,
)

from esis.db import Database


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
