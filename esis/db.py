"""Database related tools."""
import logging

from sqlalchemy import (
    Column,
    MetaData,
    Table,
    create_engine,
    inspect,
)
from sqlalchemy.exc import DatabaseError

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
        logger.debug('Connecting to SQLite database: %s', self.db_filename)
        self.connection = self.engine.connect()

    def disconnect(self):
        """Close connection."""
        assert not self.connection.closed
        logger.debug(
            'Disconnecting from SQLite database: %s', self.db_filename)
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
            logger.warning('Integrity check failure: %s', self.db_filename)
        return passed

    def reflect(self):
        """Get table metadata through reflection.

        sqlalchemy already provides a reflect method, but it will stop at the
        first failure, while this method will try to get as much as possible.

        """
        inspector = inspect(self.engine)
        for table_name in inspector.get_table_names():
            columns = []
            for column_data in inspector.get_columns(table_name):
                # Rename 'type' to 'type_' to create column object
                column_type = column_data.pop('type', None)
                column_data['type_'] = column_type
                columns.append(Column(**column_data))
            Table(table_name, self.metadata, *columns)
