import os
import psycopg2
from .queries import SqlQueries


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
        get_duplicate_btree_indexes(): Finds duplicate B-tree indexes in the database.
        fetch_invalid_indexes(): Identifies invalid indexes that require attention.
        fetch_unused_indexes(): Retrieves indexes that have not been used in a specified timeframe.
    """
    def __init__(self):
        self.connection = None
        self.replica_node_exists = None
        self.recovery_status = None
        self.collect_facts()

    def connect(self):
        """Initializes the DatabaseManager and collects database facts."""
        if self.connection is None:
            try:
                host = os.getenv("DB_HOST", "localhost")
                port = os.getenv("DB_PORT", "5432")
                dbname = os.getenv("DB_NAME")
                user = os.getenv("DB_USER")
                password = os.getenv("DB_PASSWORD")

                # Ensure required variables are set
                if not all([dbname, user, password]):
                    raise ValueError(
                        "Missing one or more required environment variables: DB_NAME, DB_USER, DB_PASSWORD"
                    )

                # Connect to PostgreSQL
                self.connection = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=dbname,
                    user=user,
                    password=password,
                    connect_timeout=10,
                    options="-c statement_timeout=5000 -c log_statement=all",
                    application_name="pgindexinsight",
                )
                self.connection.autocommit = True
            except Exception as e:
                raise ConnectionError(f"Error connecting to the database: {str(e)}")

        return self.connection

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

    def get_unused_and_invalid_indexes(self):
        """Retrieves a list of unused, invalid, and duplicate indexes in the database."""
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
                            "index_name": row[2],
                            "category": "Unused and Redundant Index",
                        }
                    )

                cur.execute(SqlQueries.find_invalid_indexes())
                invalid_result = cur.fetchall()
                for row in invalid_result:
                    final_result.append(
                        {
                            "database_name": os.getenv("DB_NAME"),
                            "index_name": row[2],
                            "category": "Invalid Index",
                        }
                    )

                cur.execute(SqlQueries.find_exact_duplicate_index())
                duplicates_result = cur.fetchall()
                for row in duplicates_result:
                    final_result.append(
                        {
                            "database_name": os.getenv("DB_NAME"),
                            "index_name": row[0],
                            "category": "Duplicate Index",
                        }
                    )

                if len(final_result) == 0:
                    return "No results found."
                return final_result

        except Exception as e:
            print(f"No Result, Failed due to: {e}")
        finally:
            self.close()

    def get_bloated_indexes(self):
        """Finds duplicate B-tree indexes in the database."""
        try:
            conn = self.connect()
            with conn.cursor() as cur:
                cur.execute(SqlQueries.calculate_btree_bloat())
                bloated_indexes = cur.fetchall()
                bloatedIndexList = []
                for index in bloated_indexes:
                    indexModel = {
                        "database_name": index[0],
                        "index_name": index[3],
                        "bloat_ratio": float(format(index[9], ".1f")),
                        "category": "High Bloated Index(Greater Then >60). Consider re-indexing",
                    }
                    if indexModel.get("bloat_ratio") > 60:
                        bloatedIndexList.append(indexModel)
                return bloatedIndexList

        except Exception as e:
            print(f"No Result, Failed due to: {e}")
        finally:
            self.close()

    def get_duplicate_btree_indexes(self):
        database_connection = self.connect()
        with database_connection.cursor() as database_cursor:
            database_cursor.execute(SqlQueries.find_exact_duplicate_index())
            duplicate_indexes = database_cursor.fetchall()
            duplicated_index_list = []
            for index in duplicate_indexes:
                duplicate_index_dict = {
                    "database_name": os.getenv("DB_NAME"),
                    "index_name": index[0],
                    "duplicated_index_name": index[1],
                    "category": "Duplicated Index.One of them can be removed.",
                }
                duplicated_index_list.append(duplicate_index_dict)

        return duplicated_index_list

    def fetch_invalid_indexes(self):
        """Identifies invalid indexes that may need to be cleaned or rebuilt."""
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
                    "category": "Invalid index. Please clean the index.",
                }
                invalid_index_list.append(invalid_index_dict)

        return invalid_index_list

    def fetch_unused_indexes(self):
        """Retrieves indexes that have not been used in over a specified timeframe."""
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
                    "category": "The index has not been scanned more than 1 year or unused",
                }
                old_index_list.append(old_index_dict)
        return old_index_list
