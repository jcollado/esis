# -*- coding: utf-8 -*-
"""Database related tools."""
import logging

from datetime import datetime

import dateutil.parser

from sqlalchemy import (
    Column,
    MetaData,
    Table,
    create_engine,
    inspect,
    select,
    type_coerce,
)
from sqlalchemy.exc import DatabaseError
from sqlalchemy.types import (
    BIGINT,
    BLOB,
    BOOLEAN,
    DATE,
    DATETIME,
    INTEGER,
    NUMERIC,
    SMALLINT,
    TEXT,
    TIMESTAMP,
    TypeDecorator,
)

from esis.util import datetime_to_timestamp

logger = logging.getLogger(__name__)


class Database(object):

    """Generic database object.

    This class is subclassed to provide additional functionality specific to
    artifacts and/or documents.

    :param db_filename: Path to the sqlite database file
    :type db_filename: str

    """

    def __init__(self, db_filename):
        """Connect to database and create session object."""
        self.db_filename = db_filename
        self.engine = create_engine(
            'sqlite:///{}'.format(db_filename),
        )
        self.connection = None
        self.metadata = MetaData(bind=self.engine)

    def connect(self):
        """Create connection."""
        logger.debug('Connecting to SQLite database: %r', self.db_filename)
        self.connection = self.engine.connect()

    def disconnect(self):
        """Close connection."""
        assert not self.connection.closed
        logger.debug(
            'Disconnecting from SQLite database: %r', self.db_filename)
        self.connection.close()

    def __enter__(self):
        """Connect on entering context."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Disconnect on exiting context."""
        self.disconnect()

    def __getitem__(self, table_name):
        """Get table object in database.

        :param table_name: Name of the table
        :type table_name: str
        :return: Table object that can be used in queries
        :rtype: sqlalchemy.schema.Table

        """
        table = self.metadata.tables.get(table_name)
        if table is None:
            table = Table(table_name, self.metadata, autoload=True)
        return table

    def run_quick_check(self):
        """Check database integrity.

        Some files, especially those files created after carving, might not
        contain completely valid data.

        """
        try:
            result = self.connection.execute('PRAGMA quick_check;')
        except DatabaseError:
            return False

        passed = result.fetchone()[0] == 'ok'
        if not passed:
            logger.warning('Integrity check failure: %r', self.db_filename)
        return passed


class DBReader(object):

    """Iterate through all db tables and rows easily.

    :param database: Database to traverse
    :type database: esis.db.Database

    """

    # Name suffixes for the shadow tables that support full text search
    FTS_SUFFIXES = (
        'content',
        'segdir',
        'segments',
        'stat',
        'docsize',
    )

    def __init__(self, database):
        """Connect to database and get table metadata."""
        self.database = database

        master_table = Table('sqlite_master', database.metadata, autoload=True)
        query = (
            select([master_table.c.name])
            .where(master_table.c.type == 'table')
        )
        result = database.connection.execute(query)
        all_table_names = set(row[0] for row in result.fetchall())

        ignored_table_names = ['sqlite_master']
        sequence_table_name = 'sqlite_sequence'
        if sequence_table_name in all_table_names:
            ignored_table_names.append(sequence_table_name)
        fts_table_names = self._get_fts_table_names(all_table_names)
        ignored_table_names.extend(fts_table_names)
        logger.debug(
            '%d tables ignored: %r',
            len(ignored_table_names),
            ', '.join(sorted(ignored_table_names)))

        ignored_table_names = set(ignored_table_names)
        table_names = all_table_names - ignored_table_names
        self._reflect(table_names)

        self.db_tables = [
            database.metadata.tables[table_name]
            for table_name in table_names
        ]
        logger.info('%d tables found', len(self.db_tables))

    def _reflect(self, table_names):
        """Get table metadata through reflection.

        sqlalchemy already provides a reflect method, but it will stop at the
        first failure, while this method will try to get as much as possible.

        :param table_names: Table names to inspect
        :type table_names: list(str)

        """
        inspector = inspect(self.database.engine)
        for table_name in table_names:
            columns = []
            for column_data in inspector.get_columns(table_name):
                # Rename 'type' to 'type_' to create column object
                column_type = column_data.pop('type', None)
                column_data['type_'] = column_type
                columns.append(Column(**column_data))
            Table(table_name, self.database.metadata, *columns)

    def _get_fts_table_names(self, all_table_names):
        """Get a list of FTS-related table names.

        :param all_table_names: The names for all tables in the database
        :type all_table_names: set(str)

        """
        master_table = Table('sqlite_master', self.database.metadata, autoload=True)
        query = (
            select([master_table.c.name])
            .where(master_table.c.sql.like('%USING fts%'))
        )
        result = self.database.connection.execute(query)
        fts_table_names = [row[0] for row in result.fetchall()]

        shadow_table_names = []
        for fts_table_name in fts_table_names:
            for suffix in self.FTS_SUFFIXES:
                shadow_table_name = '{}_{}'.format(fts_table_name, suffix)
                if shadow_table_name in all_table_names:
                    shadow_table_names.append(shadow_table_name)

        return fts_table_names + shadow_table_names

    def tables(self):
        """Generator that traverses all tables in a database.

        :return: Table name
        :rtype: str

        """
        for index, table in enumerate(self.db_tables):
            logger.info(
                '(%d/%d) Traversing %r...',
                index + 1, len(self.db_tables), table.name)

            yield table.name


class IntegerDecorator(TypeDecorator):

    """An integer class that translates 'null' values to None.

    This is needed because some tables use 'null' instead of NULL and elastic
    search fails to index documents with strings where integers should be
    found.

    """

    impl = INTEGER

    def process_result_value(self, value, _dialect):
        """Translate 'null' to None if needed."""
        if value == 'null' or value is None:
            return None

        if isinstance(value, basestring):
            # Convert strings with only digits to integers
            if value.isdigit():
                return int(value)

            try:
                # Try to parse date as return timestamp
                value_dt = dateutil.parser.parse(value)
            except (TypeError, ValueError, OverflowError):
                # Ignore parsing errors and log warning below
                pass
            else:
                value = int(datetime_to_timestamp(value_dt))

        # Return None by default if value cannot be parsed as integer
        if not isinstance(value, (int, long)):
            logger.warning('Invalid integer value: %s', value)
            return None

        return value


class DatetimeDecorator(TypeDecorator):

    """A datetime class that translates data to ISO strings.

    The reason ISO strings are used instead of datetime objects or integer
    timestamps is because is what elasticsearch handles as a datetime value.
    Internally it seems to store it as an integer timestamp, but that's
    transparent to the user.

    """

    impl = TEXT

    def process_result_value(self, value, _dialect):
        """Translate datetime/timestamp to ISO string."""
        # Keep a copy of the original value just in case it's needed to log a
        # warning later
        original_value = value

        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, (int, long)) and not isinstance(value, bool):
            # Try to parse timestamp in seconds, millisecons and microseconds
            for timestamp in (value, value / 1000, value / 1000000):
                try:
                    value = datetime.utcfromtimestamp(timestamp).isoformat()
                except ValueError:
                    pass
                else:
                    break
        elif isinstance(value, basestring):
            # Parse datetime string and re-format it as an ISO string
            try:
                value = dateutil.parser.parse(value).isoformat()
            except (TypeError, ValueError):
                # Ignore parsing errors and log warning below
                value = None

        # Return None by default if no ISO string could be generated
        if not isinstance(value, str):
            logger.warning('Invalid datetime value: %s', original_value)
            return None

        return value


class TypeCoercionMixin(object):

    """A mixin to transform database values.

    This is useful to get safe values from sqlalchemy when data types are not
    very well defined in SQLite.
    """

    # Column type coercions to avoid errors when getting values of a different
    # type due to sqlite's flexibility in that regard
    COERCIONS = {
        # This is because NUMERIC type affinity in SQLite can use any
        # storage class, so the safer option is to cast it to a string
        NUMERIC: TEXT,

        # Translate the 'null' string to None to avoid indexing failures
        BOOLEAN: IntegerDecorator,
        INTEGER: IntegerDecorator,
        BIGINT: IntegerDecorator,
        SMALLINT: IntegerDecorator,

        # Translate integer timestamps to ISO formatted strings
        DATE: DatetimeDecorator,
        DATETIME: DatetimeDecorator,
        TIMESTAMP: DatetimeDecorator,
    }

    def _coerce_column_type(self, column):
        """Coerce some column type.

        :param column: Column to examine
        :type column: sqlalchemy.sql.schema.Column
        :return: Coerced column (if needed)
        :rtype: sqlalchemy.sql.elements.Label | sqlalchemy.sql.schema.Column

        """
        for from_type, to_type in self.COERCIONS.iteritems():
            if isinstance(column.type, from_type):
                # Preserve column name despite of the type coercion
                return type_coerce(column, to_type).label(column.name)

        # Don't coerce values if not really needed
        return column

    def _coerce(self, columns):
        """Coerce multiple columns types.

        This is useful to use in select queries to make sure all columns will
        return safe values.

        :param columns: Columns to examine
        :type column: list(sqlalchemy.sql.schema.Column)
        :return: Coerced columns (if needed)
        :rtype: list(
            sqlalchemy.sql.elements.Label | sqlalchemy.sql.schema.Column)

        """
        return [self._coerce_column_type(column) for column in columns]


class TableReader(TypeCoercionMixin):

    """Iterate over all rows easily.

    :param database: Database being explored
    :type database: esis.db.Database
    :param table: Database table
    :type table: sqlalchemy.sql.schema.Table

    """

    def __init__(self, database, table_name):
        """Initialize reader object."""
        self.database = database
        self.table = database[table_name]

        # Filter out columns that are not going to be indexed
        # - BLOB: more investigation needed on how that works with
        # elasticsearch
        ignored_column_names = [
            column.name
            for column in self.table.columns
            if isinstance(column.type, BLOB)
        ]

        # Ignore '_id' column unless it has unique values
        # This is because '_id' is used by elasticsearch and using the same
        # one in multiple documents will result in those being overwritten
        if '_id' in (column.name for column in self.table.columns):
            query = select([self.table.c['_id']]).count()
            row_count = self.database.connection.execute(query).scalar()
            distinct_query = (
                select([self.table.c['_id']]).distinct().count())
            distinct_row_count = (
                self.database.connection.execute(distinct_query).scalar())
            if row_count != distinct_row_count:
                ignored_column_names.append('_id')

        if len(ignored_column_names) > 0:
            logger.debug(
                '%d columns ignored: %s',
                len(ignored_column_names),
                ', '.join(sorted(ignored_column_names)))
            ignored_column_names = set(ignored_column_names)

        self.columns = [
            column
            for column in self.table.columns
            if column.name not in ignored_column_names
        ]
        logger.debug(
            '%d columns found: %s',
            len(self.columns),
            ', '.join(column.name for column in self.columns))

    def get_schema(self):
        """Return table schema.

        :return: Column names and their type
        :rtype: dict(str, sqlalchemy.types.*)

        """
        return {column.name: column.type
                for column in self.columns}

    def rows(self):
        """Generator that traverses all rows in a table.

        :return: All rows in the table
        :rtype: generator(sqlalchemy.engine.result.RowProxy)

        """
        if self.columns:
            query = select(self._coerce(self.columns))
            result = self.database.connection.execute(query)
            rows = result.fetchall()
            logger.debug('%d rows found', len(rows))
            for row in rows:
                yield row
