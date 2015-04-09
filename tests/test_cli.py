# -*- coding: utf-8 -*-
"""Command Line Interface test cases."""

import os
import tempfile
import unittest

from esis.cli import (
    clean,
    count,
    index,
    parse_arguments,
    search,
)


class ParseArgumentsTest(unittest.TestCase):

    """Parse arguments test case."""

    def test_index_command(self):
        """Search command."""
        temp_directory = tempfile.mkdtemp()
        try:
            args = parse_arguments(['index', temp_directory])
            self.assertEqual(args.directory, temp_directory)
            self.assertEqual(args.func, index)
        finally:
            os.rmdir(temp_directory)

    def test_search_command(self):
        """Search command."""
        args = parse_arguments(['search', 'query'])
        self.assertEqual(args.query, 'query')
        self.assertEqual(args.func, search)

    def test_count_command(self):
        """Count command."""
        args = parse_arguments(['count'])
        self.assertEqual(args.func, count)

    def test_clean_command(self):
        """Clean command."""
        args = parse_arguments(['clean'])
        self.assertEqual(args.func, clean)
