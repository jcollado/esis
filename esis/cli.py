# -*- coding: utf-8 -*-
"""Elastic Search Index & Search."""

import argparse
import logging
import os

logger = logging.getLogger(__name__)

def main():
    """Entry point for the esis.py script."""
    args = parse_arguments()
    args.func(args)

def index(args):
    """Index database information into elasticsearch."""
    logger.debug('Indexing %r...', args.directory)

def search(args):
    """Send query to elasticsearch."""
    logger.debug('Searching %r...', args.query)

def valid_directory(path):
    """Directory validation."""
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(
            '{!r} is not a valid directory'.format(path))

    if not os.access(path, os.R_OK | os.X_OK):
        raise argparse.ArgumentTypeError(
            'not enough permissions to explore {!r}'.format(path))

    return path

def parse_arguments():
    """Parse command line arguments.

    :returns: Parsed arguments
    :rtype: argparse.Namespace

    """
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(help='Subcommands')
    index_parser = subparsers.add_parser('index', help='Index SQLite database files')
    index_parser.add_argument('directory', type=valid_directory, help='Base directory')
    index_parser.set_defaults(func=index)
    search_parser = subparsers.add_parser('search', help='Search indexed data')
    search_parser.add_argument('query', help='Search query')
    search_parser.set_defaults(func=search)
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    main()
