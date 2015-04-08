# -*- coding: utf-8 -*-
"""Test cases for the filesystem functionaliy in search."""
import os
import shutil
import sqlite3
import tempfile
import unittest

from contextlib import closing

from esis.fs import TreeExplorer


class TreeExplorerTest(unittest.TestCase):

    """Tree explorer test cases."""

    def setUp(self):
        """Initialize internal status needed for test case."""
        # Directory where test data should be created
        self.directory = tempfile.mkdtemp()
        self.sqlite_db_filenames = []

    def tearDown(self):
        """Remove files created for the test case."""
        shutil.rmtree(self.directory)

    def create_directory(self, directory, metadata):
        """Create directory of test data based on metadata.

        :param directory: Directory under which files should be created
        :type directory: str
        :param metadata: File names, types and subdirectories to create
        :type metadata: dict(str)

        """
        for basename, value in metadata.iteritems():
            if isinstance(value, str):
                filename = os.path.join(directory, basename)
                create_method = getattr(
                    self, 'create_{}_file'.format(value))
                create_method(filename)
            elif isinstance(value, dict):
                subdirectory = os.path.join(directory, basename)
                os.mkdir(subdirectory)
                self.create_directory(subdirectory, value)
            else:
                raise TypeError(
                    'Unexpected metadata. {}: {}'.format(basename, value))

    def create_text_file(self, filename):
        """Create text file using the given name.

        :param filename: Path to the file that should be created
        :type filename: str

        """
        with open(filename, 'w') as file_:
            file_.write('this is a text file')

    def create_sqlite_file(self, filename):
        """Create sqlite file using the given name.

        :param filename: Path to the file that should be created
        :type filename: str

        """
        with closing(sqlite3.connect(filename)) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute('CREATE TABLE messages (id INTEGER)')
        self.sqlite_db_filenames.append(filename)

    def test_paths(self):
        """SQLite database files are found under the given path."""
        metadata = {
            'a': 'text',
            'b': 'sqlite',
            'subdir': {
                'c': 'text',
                'd': 'sqlite',
                'subsubdir': {
                    'e': 'text',
                    'f': 'sqlite',
                }
            },
        }
        self.create_directory(self.directory, metadata)

        tree_explorer = TreeExplorer(self.directory)
        self.assertListEqual(
            sorted(tree_explorer.paths()),
            sorted(self.sqlite_db_filenames),
        )

    def test_blacklist(self):
        """Blacklisted directories are skipped."""
        metadata = {
            'a': 'text',
            'b': 'sqlite',
            'carving': {
                'c': 'text',
                'd': 'sqlite',
                'subdir': {
                    'e': 'text',
                    'f': 'sqlite',
                }
            },
        }
        self.create_directory(self.directory, metadata)

        tree_explorer = TreeExplorer(self.directory, blacklist=['carving'])
        self.assertListEqual(
            tree_explorer.paths(),
            [os.path.join(self.directory, 'b')],
        )
