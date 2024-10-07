import os
import psycopg2
import click
from tabulate import tabulate
from ..database import DatabaseManager
from ..queries import SqlQueries

@click.command()
def list_unused_or_old_indexes():
    """
    Connects to the PostgreSQL database and retrieves unused or redundant indexes. 
    This function queries the database for indexes that are not frequently scanned 
    or are outdated, indicating that they may be redundant. If such indexes are found, 
    it displays them in a tabular format with details including the database name, 
    schema name, index name, size, scan count, last scan date, and other related 
    attributes such as replica status and recovery mode.

    If no unused or redundant indexes are found, the function informs the user 
    and exits gracefully.
    """
    try:
        database_instance = DatabaseManager()
        duplicate_index_list = database_instance.fetch_unused_indexes()
        database_name=os.getenv('DB_NAME')
        if not len(duplicate_index_list)>0:
            click.echo(f'No unused or old index found for database: {database_name}')
            exit(0)
        table_formatted_index_result = [
            [
                item["database_name"],
                item["schema_name"],
                item["index_name"],
                item["index_size"],
                item["index_scan"],
                item["last_scan"],
                item["category"],
                database_instance.replica_node_exists,
                database_instance.recovery_status,
            ]
            for item in duplicate_index_list
        ]
        index_table_headers = [
            "Database Name",
            "Schema Name",
            "Index Name",
            "Index Size",
            "Index Scan Count",
            "Last Scan Date",
            "Category",
            "Replica Node Exists",
            "Database Recovery Mode"
        ]
        index_result_table = tabulate(
            table_formatted_index_result, index_table_headers, tablefmt="psql"
        )
        click.echo(index_result_table)
    except Exception as e:
        click.echo(f"Error: {str(e)}")