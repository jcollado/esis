# -*- coding: utf-8 -*-
"""Elastic Search Index & Search."""

import argparse


def main():
    """Entry point for the esis.py script."""
    args = parse_arguments()
    print args

def parse_arguments():
    """Parse command line arguments.

    :returns: Parsed arguments
    :rtype: argparse.Namespace

    """
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(help='Subcommands')
    index = subparsers.add_parser('index', help='Index SQLite database files')
    index.add_argument('directory', help='Base directory')
    search = subparsers.add_parser('search', help='Search indexed data')
    search.add_argument('query', help='Search query')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    main()
