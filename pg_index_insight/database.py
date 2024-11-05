import os
import psycopg2
from .queries import SqlQueries
import logging

class DatabaseManager:
    """
    A class to manage database connections and operations related to PostgreSQL.

    This class handles connecting to the PostgreSQL database, retrieving information 
    about indexes (such as unused, invalid, duplicate, and bloated indexes), and 
    collecting facts about the database's state (like recovery status and replication).

    Attributes:
        connection (psycopg2.connection): The connection object for the PostgreSQL database.
        replica_node_exists (bool): Indicates if a replica node exists.
        recovery_status (bool): The recovery status of the database.

    Methods:
        connect(): Establishes a database connection using environment variables.
        close(): Closes the database connection.
        collect_facts(): Collects and stores facts about the database's state.
        get_unused_and_invalid_indexes(): Retrieves unused, invalid, and duplicate indexes.
        get_bloated_indexes(): Identifies bloated B-tree indexes in the database.
        fetch_invalid_indexes(): Identifies invalid indexes that require attention.
        fetch_unused_indexes(): Retrieves indexes that have not been used in a specified timeframe.
    """
    logger = logging.getLogger("pgindexinsight")
    logger.setLevel(logging.WARNING)  # Set default logging level to DEBUG
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Set console log level (can adjust to DEBUG if needed)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    MIN_SUPPORTED_VERSION = 16
    SYSTEM_DATABASE_LIST = ['postgres','template0','template1']
    def __init__(self):
        self.connection = None
        self.replica_node_exists = None
        self.recovery_status = None
        self.database_version=None
        self.collect_facts()

    def connect(self):
        """Initializes the DatabaseManager and collects database facts."""
        if not (os.getenv('DB_NAME') not in DatabaseManager.SYSTEM_DATABASE_LIST):
            raise ValueError(f"System databases is not allowed to be analyzed")
        if self.connection is None:
            try:
                host = os.getenv("DB_HOST", "localhost")
                port = os.getenv("DB_PORT", "5432")
                dbname = os.getenv("DB_NAME")
                user = os.getenv("DB_USER")
                password = os.getenv("DB_PASSWORD")

                if not all([dbname, user, password]):
                    raise ValueError(
                        "Missing one or more required environment variables: DB_NAME, DB_USER, DB_PASSWORD"
                    )
                self.connection = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password,
                    connect_timeout=10,
                    options="-c statement_timeout=5000",
                    application_name="pgindexinsight",
                )
                self.connection.autocommit = True
                self.check_superuser()
            except Exception as e:
                raise ConnectionError(f"Error connecting to the database: {str(e)}")

        return self.connection

    def check_superuser(self):
        """Checks if the connected user is a superuser and logs a debug message."""
        try:
            with self.connection.cursor() as cur:
                cur.execute("SELECT current_setting('is_superuser')")
                is_superuser = cur.fetchone()[0]
                if is_superuser == 'on':
                    DatabaseManager.logger.warning("Connected as a superuser.")
                else:
                    DatabaseManager.logger.info("Connected as a regular user.")
        except Exception as e:
            DatabaseManager.logger.error(f"Failed to check superuser status: {e}")


    def close(self):
        """Closes the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def collect_facts(self):
        """Collects and sets database recovery and replication status."""
        database_connection = self.connect()
        with database_connection.cursor() as db_cursor:
            db_cursor.execute("select pg_is_in_recovery()")
            recovery_status = db_cursor.fetchall()
            recovery_status = recovery_status[0][0]
            self.recovery_status = recovery_status
            db_cursor.execute(
                f"""select count(*) as physical_repl_count from pg_replication_slots where slot_type='physical' and active is true """
            )
            replica_count = db_cursor.fetchall()
            replica_count = replica_count[0][0]
            if replica_count > 0:
                self.replica_node_exists = True
            else:
                self.replica_node_exists = False
            db_cursor.execute('select version()')
            database_version=db_cursor.fetchall()
            database_version=float(str(database_version[0][0]).split(' ')[1])
            self.database_version=database_version
    
    def _check_version_supported(self):
        """Ensures that the database version is supported."""
        if self.database_version < self.MIN_SUPPORTED_VERSION:
            raise ValueError(f"PostgreSQL version {self.MIN_SUPPORTED_VERSION}.0 and higher is supported.")

    
    def get_unused_and_invalid_indexes(self):
        """Retrieves a list of unused, invalid, and duplicate indexes in the database."""
        self._check_version_supported()
        try:
            conn = self.connect()

            with conn.cursor() as cur:
                final_result = []

                cur.execute(SqlQueries.find_unused_redundant_indexes())
                unused_redundant_result = cur.fetchall()
                for row in unused_redundant_result:
                    final_result.append(
                        {
                            "database_name": os.getenv("DB_NAME"),
                            "schema_name": row[0],
                            "index_name": row[2],
                            "index_size": row[4],
                            "category": "Unused&Redundant Index",
                        }
                    )

                cur.execute(SqlQueries.find_invalid_indexes())
                invalid_result = cur.fetchall()
                for row in invalid_result:
                    final_result.append(
                        {
                            "database_name": os.getenv("DB_NAME"),
                            "schema_name": row[0],
                            "index_name": row[2],
                            "index_size": row[4],
                            "category": "Invalid Index",
                        }
                    )
                if len(final_result) == 0:
                    return []
                return final_result

        except Exception as e:
            print(f"No Result, Failed due to: {e}")
        finally:
            self.close()

    def get_bloated_indexes(self,bloat_threshold):
        """Finds duplicate B-tree indexes in the database."""
        self._check_version_supported()
        try:
            conn = self.connect()
            with conn.cursor() as cur:
                cur.execute(SqlQueries.calculate_btree_bloat())
                bloated_indexes = cur.fetchall()
                bloatedIndexList = []
                for index in bloated_indexes:
                    indexModel = {
                        "database_name": index[0],
                        "schema_name": index[1],
                        "index_name": index[3],
                        "bloat_ratio": float(format(index[9], ".1f")),
                        "category": "Bloated",
                    }
                    if indexModel.get("bloat_ratio") > bloat_threshold:
                        bloatedIndexList.append(indexModel)
                return bloatedIndexList

        except Exception as e:
            print(f"No Result, Failed due to: {e}")
        finally:
            self.close()

    def fetch_invalid_indexes(self):
        """Identifies invalid indexes that may need to be cleaned or rebuilt."""
        self._check_version_supported()
        database_connection = self.connect()
        with database_connection.cursor() as database_cursor:
            database_cursor.execute(SqlQueries.find_invalid_indexes())
            invalid_indexes = database_cursor.fetchall()
            invalid_index_list = []
            for index in invalid_indexes:
                invalid_index_dict = {
                    "database_name": os.getenv("DB_NAME"),
                    "schema_name": index[0],
                    "index_name": index[2],
                    "index_size": index[4],
                    "category": "Invalid Index.",
                }
                invalid_index_list.append(invalid_index_dict)

        return invalid_index_list

    def fetch_unused_indexes(self):
        """Retrieves indexes that have not been used in over a specified timeframe."""
        self._check_version_supported()
        database_connection = self.connect()
        with database_connection.cursor() as database_cursor:
            database_cursor.execute(SqlQueries.find_unused_indexes())
            old_indexes = database_cursor.fetchall()
            old_index_list = []
            for index in old_indexes:
                old_index_dict = {
                    "database_name": os.getenv("DB_NAME"),
                    "schema_name": index[0],
                    "index_name": index[2],
                    "index_size": index[4],
                    "index_scan": index[3],
                    "last_scan": index[5],
                    "category": "Unused/Retired Index",
                }
                old_index_list.append(old_index_dict)
        return old_index_list

    def fetch_duplicate_unique_indexes(self):
        """Retrieves unique indexes have being duplicated"""
        self._check_version_supported()
        database_connection = self.connect()
        current_indexes = set()
        duplicate_unique_indexes = []
        with database_connection.cursor() as database_cursor:
            database_cursor.execute(SqlQueries.find_duplicate_constraints())
            unique_indexes = database_cursor.fetchall()
            for index in unique_indexes:
                index_columns=str(index[3]).split(' ')[8]
                schema_name=index[0]
                table_name=index[1]
                index_record=(schema_name,table_name,index_columns)
                if index_record in current_indexes:
                    # if index record has been found in current_indexes list append index to duplicate_unique_indexes list.
                    duplicate_unique_indexes.append(index)
                else:
                    # if index record has not been found in current indexes add index_record to current_indexes list to 
                    # compare later.
                    current_indexes.add(index_record)
        return duplicate_unique_indexes

    def fetch_duplicate_indexes(self):
        """Retrieves unique indexes have being duplicated"""
        self._check_version_supported()
        database_connection = self.connect()
        current_indexes = set()
        duplicate_unique_indexes = []
        with database_connection.cursor() as database_cursor:
            database_cursor.execute(SqlQueries.find_duplicate_btrees())
            unique_indexes = database_cursor.fetchall()
            for index in unique_indexes:
                index_columns=str(index[3]).split(' ')[7]
                schema_name=index[0]
                table_name=index[1]
                index_record=(schema_name,table_name,index_columns)
                if index_record in current_indexes:
                    # if index record has been found in current_indexes list append index to duplicate_unique_indexes list.
                    duplicate_unique_indexes.append(index)
                else:
                    # if index record has not been found in current indexes add index_record to current_indexes list to 
                    # compare later.
                    current_indexes.add(index_record)
        return duplicate_unique_indexes