# -*- coding: utf-8 -*-
"""Filesystem functionality."""
import logging
import os

import magic

from sqlalchemy.exc import OperationalError

from esis.db import Database


logger = logging.getLogger(__name__)


class TreeExplorer(object):

    """Look for sqlite files in a tree an return the valid ones.

    :param directory: Base directory for the tree to be explored.
    :type directory: str
    :param blacklist: List of relative directories to skip
    :type blacklist: list(str)

    """

    def __init__(self, directory, blacklist=None):
        """Initialize tree explorer."""
        self.directory = directory
        self.blacklist = blacklist if blacklist is not None else []

    def paths(self):
        """Return paths to valid databases found under directory.

        :return: Paths to valid datbases
        :rtype: list(str)

        """
        db_paths = self._explore()
        logger.debug(
            '%d database paths found under %s:\n%s',
            len(db_paths),
            self.directory,
            '\n'.join(os.path.relpath(db_path, self.directory)
                      for db_path in db_paths))

        # Filter out files that don't pass sqlite's quick check
        # that just can't be opened
        valid_paths = []
        for db_path in db_paths:
            try:
                with Database(db_path) as database:
                    if database.run_quick_check():
                        valid_paths.append(db_path)
            except OperationalError:
                logger.warning('Unable to open: %s', db_path)
                continue

        logger.debug(
            '%d database paths passed the integrity check:\n%s',
            len(valid_paths),
            '\n'.join(os.path.relpath(valid_path, self.directory)
                      for valid_path in valid_paths))
        return valid_paths

    def _explore(self):
        """Walk from base directory and yield files that match pattern."""
        db_paths = []
        for (dirpath, dirnames, filenames) in os.walk(self.directory):
            logger.debug('Exploring %s...', dirpath)

            # Check if any subdirectory is blacklisted
            blacklisted_dirnames = [
                dirname
                for dirname in dirnames
                if os.path.relpath(
                    os.path.join(dirpath, dirname),
                    self.directory,
                ) in self.blacklist
            ]
            if blacklisted_dirnames:
                logger.debug(
                    'Subdirectories blacklisted: %s', blacklisted_dirnames)
            for blacklisted_dirname in blacklisted_dirnames:
                # Note: if dirnames is updated in place, os.walk will recurse
                # only in the remaining directories
                dirnames.remove(blacklisted_dirname)

            # Check if any filename is a sqlite database
            for filename in filenames:
                db_path = os.path.join(dirpath, filename)
                if 'SQLite' in magic.from_file(db_path):
                    db_paths.append(db_path)

        return db_paths
