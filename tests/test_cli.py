# -*- coding: utf-8 -*-
"""Command Line Interface test cases."""

import argparse
import logging
import os
import tempfile
import unittest

from mock import (
    MagicMock as Mock,
    patch,
)

from esis.cli import (
    clean,
    count,
    index,
    main,
    parse_arguments,
    search,
)

class MainTests(unittest.TestCase):

    """Main function test cases."""

    def setUp(self):
        """Patch parse_arguments function."""
        self.parse_arguments_patcher = patch('esis.cli.parse_arguments')
        self.parse_arguments = self.parse_arguments_patcher.start()

        self.logging_patcher = patch('esis.cli.logging')
        self.logging_patcher.start()

    def test_func_called(self):
        """Command function is called."""
        argv = Mock()
        function = Mock()
        args = argparse.Namespace(
            log_level=logging.WARNING,
            func=function,
        )
        self.parse_arguments.return_value = args
        main(argv)
        function.assert_called_once_with(args)

    def tearDown(self):
        """Undo the patching."""
        self.parse_arguments_patcher.stop()
        self.logging_patcher.stop()


class CommandFunctionTests(unittest.TestCase):

    """Command function test cases."""

    def setUp(self):
        """Patch elasticsearch client."""
        self.patcher = patch('esis.cli.Client')
        client_cls = self.patcher.start()
        self.client = client_cls()

    def test_index(self):
        """Index command function."""
        directory = 'some directory'
        args = argparse.Namespace(directory=directory)
        index(args)
        self.client.index.assert_called_once_with(directory)

    def test_search(self):
        """Search command function."""
        query = 'some query'
        args = argparse.Namespace(query=query)
        self.client.search.side_effect = [
            ['result_1', 'result_2'],
            ['result_3', 'result_4'],
        ]
        search(args)
        self.client.search.assert_called_once_with(query)

    def test_count(self):
        """Count command function."""
        args = argparse.Namespace()
        count(args)
        self.client.count.assert_called_once_with()

    def test_clean(self):
        """Clean command function."""
        args = argparse.Namespace()
        clean(args)
        self.client.clean.assert_called_once_with()

    def tearDown(self):
        """Undo the patching."""
        self.patcher.stop()


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
