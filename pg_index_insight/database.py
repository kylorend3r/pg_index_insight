import os
import yaml
import psycopg2
import re
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
        run_query(): Executes a list of SQL queries on the connected PostgreSQL database.
        collect_facts(): Collects and stores facts about the database's state.
        get_unused_and_invalid_indexes(): Retrieves unused, invalid, and duplicate indexes.
        get_bloated_indexes(): Identifies bloated B-tree indexes in the database.
        fetch_invalid_indexes(): Identifies invalid indexes that require attention.
        fetch_unused_indexes(): Retrieves indexes that have not been used in a specified timeframe.
    """
    logger = logging.getLogger("pgindexinsight")
    logger.setLevel(logging.WARNING)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    MIN_SUPPORTED_VERSION = 16
    SYSTEM_DATABASE_LIST = ['postgres', 'template0', 'template1']


    def __init__(self, config_file="db_config.yaml",db_name=None):
        self.connection = None
        self.replica_node_exists = None
        self.recovery_status = None
        self.database_version = None
        self.config = self.load_config(config_file,db_name)
        self.dbname = self.config.get("dbname")
        self.collect_facts()

    def load_config(self, config_file, db_name):
        """Loads database configuration for a specific database from a YAML file."""
        try:
            with open(config_file, 'r') as file:
                all_configs = yaml.safe_load(file)['databases']
                for db_config in all_configs:
                    if db_config['name'] == db_name:
                        return db_config
            raise ValueError(f"Database with name '{db_name}' not found in configuration file.")
        except Exception as e:
            raise FileNotFoundError(f"Failed to load configuration file {config_file}: {e}")

    def connect(self):
        """Initializes the DatabaseManager and collects database facts."""
        if self.connection is None:
            try:
                host = self.config.get("host", "localhost")
                port = self.config.get("port", "5432")
                dbname = self.config.get("dbname")
                user = self.config.get("user")
                password = self.config.get("password")
                if not all([dbname, user, password]):
                    raise ValueError("Missing one or more required database configurations in the YAML file.")
                if dbname in DatabaseManager.SYSTEM_DATABASE_LIST:
                    raise ValueError(f"System databases are not allowed to be analyzed: {dbname}")

                self.connection = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password,
                    connect_timeout=10,
                    options="-c statement_timeout=600s -c lock_timeout=5s -c log_statement=all",
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

    def run_query(self, queries):
        """Run query against Postgresql database. It takes list of queries."""
        for query in queries:
            database_connection = self.connect()
            with database_connection.cursor() as db_cursor:
                try:
                    pattern = r"^(DROP INDEX CONCURRENTLY|REINDEX INDEX CONCURRENTLY)\b"
                    is_query_valid = bool(re.match(pattern, query.strip(), re.IGNORECASE))
                    if not is_query_valid:
                        DatabaseManager.logger.warning(
                            "The query sent is not valid to be executed database.Please review the generated query.")
                        DatabaseManager.logger.info(query)
                        return False
                    db_cursor.execute(query)
                    self.close()
                    DatabaseManager.logger.warning("Executed the query and closing connection")
                except Exception as e:
                    print(f"Error: {str(e)}")
                    return False

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
            database_version = db_cursor.fetchall()
            database_version = float(str(database_version[0][0]).split(' ')[1])
            self.database_version = database_version

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
                            "database_name": self.dbname,
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
                            "database_name": self.dbname,
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

    def get_bloated_indexes(self, bloat_threshold):
        """Returns indxes which have bloat ratio is greater than bloat_threshold."""
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
                    "database_name": self.dbname,
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
                    "database_name": self.dbname,
                    "schema_name": index[0],
                    "index_name": index[2],
                    "index_size": index[4],
                    "index_scan": index[3],
                    "category": "Unused Index",
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
                index_columns = str(index[3]).split(' ')[8]
                schema_name = index[0]
                table_name = index[1]
                index_record = (schema_name, table_name, index_columns)
                if index_record in current_indexes:
                    # if index record has been found in current_indexes list append index to duplicate_unique_indexes list.
                    duplicate_unique_indexes.append(index)
                else:
                    # if index record has not been found in current indexes add index_record to current_indexes list to
                    # compare later.
                    current_indexes.add(index_record)
        return duplicate_unique_indexes

    def fetch_duplicate_indexes(self):
        """Retrieves btree indexes have being duplicated"""
        self._check_version_supported()
        database_connection = self.connect()
        current_indexes = set()
        duplicate_unique_indexes = []
        with database_connection.cursor() as database_cursor:
            database_cursor.execute(SqlQueries.find_duplicate_btrees())
            unique_indexes = database_cursor.fetchall()
            for index in unique_indexes:
                index_columns = str(index[3]).split(' ')[7]
                schema_name = index[0]
                table_name = index[1]
                index_record = (schema_name, table_name, index_columns)
                if index_record in current_indexes:
                    # if index record has been found in current_indexes list append index to duplicate_unique_indexes list.
                    duplicate_unique_indexes.append(index)
                else:
                    # if index record has not been found in current indexes add index_record to current_indexes list to
                    # compare later.
                    current_indexes.add(index_record)
        return duplicate_unique_indexes