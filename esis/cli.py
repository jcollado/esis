# -*- coding: utf-8 -*-
"""Elastic Search Index & Search."""

import argparse
import logging
import os

from pprint import (
    pformat,
    pprint,
)

from esis.es import Client

logger = logging.getLogger(__name__)

def main():
    """Entry point for the esis.py script."""
    args = parse_arguments()
    configure_logging(args.log_level)
    args.func(args)

def index(args):
    """Index database information into elasticsearch."""
    client = Client()
    client.index(args.directory)

def search(args):
    """Send query to elasticsearch."""
    client = Client()
    hit_counter = 0
    for hits in client.search(args.query):
        for hit in hits:
            hit_counter += 1
            print('{}: {}\n'.format(hit_counter, pformat(hit)))

    print('{} results found'.format(hit_counter))

def count(_args):
    """Print indexed documents information."""
    client = Client()
    pprint(client.count())

def clean(_args):
    """Remove all indexed documents."""
    client = Client()
    client.clean()

def valid_directory(path):
    """Directory validation."""
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(
            '{!r} is not a valid directory'.format(path))

    if not os.access(path, os.R_OK | os.X_OK):
        raise argparse.ArgumentTypeError(
            'not enough permissions to explore {!r}'.format(path))

    return path

def configure_logging(log_level):
    """Configure logging based on command line argument.

    :param log_level: Log level passed form the command line
    :type log_level: int

    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Log to sys.stderr using log level
    # passed through command line
    log_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    log_handler.setFormatter(formatter)
    log_handler.setLevel(log_level)
    root_logger.addHandler(log_handler)

    # Disable elasticsearch extra verbose logging
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.INFO)


def parse_arguments():
    """Parse command line arguments.

    :returns: Parsed arguments
    :rtype: argparse.Namespace

    """
    parser = argparse.ArgumentParser(description=__doc__)
    log_levels = ['debug', 'info', 'warning', 'error', 'critical']
    parser.add_argument(
        '-l', '--log-level',
        dest='log_level',
        choices=log_levels,
        default='warning',
        help=('Log level. One of {0} or {1} '
              '(%(default)s by default)'
              .format(', '.join(log_levels[:-1]), log_levels[-1])))

    subparsers = parser.add_subparsers(help='Subcommands')

    index_parser = subparsers.add_parser('index', help='Index SQLite database files')
    index_parser.add_argument('directory', type=valid_directory, help='Base directory')
    index_parser.set_defaults(func=index)

    search_parser = subparsers.add_parser('search', help='Search indexed data')
    search_parser.add_argument('query', help='Search query')
    search_parser.set_defaults(func=search)

    count_parser = subparsers.add_parser('count', help='Indexed documents information')
    count_parser.set_defaults(func=count)

    clean_parser = subparsers.add_parser('clean', help='Remove all indexed documents')
    clean_parser.set_defaults(func=clean)

    args = parser.parse_args()
    args.log_level = getattr(logging, args.log_level.upper())
    return args

if __name__ == '__main__':
    main()
