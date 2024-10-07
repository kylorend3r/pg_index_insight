import os
import psycopg2
import click
from tabulate import tabulate
from ..database import DatabaseManager
from ..queries import SqlQueries

@click.command()

def list_invalid_indexes():
    """
    Connects to the PostgreSQL database and retrieves invalid indexes. 
    Invalid indexes typically refer to indexes that are misconfigured, 
    corrupted, or otherwise ineffective in optimizing queries.

    This function queries the database for such invalid indexes and, 
    if found, displays them in a table with details including the database name, 
    schema name, index name, size, and a category indicating the type of invalidity.

    If no invalid indexes are found, the function informs the user and exits.
    """

    try:
        database_query=DatabaseManager()
        invalid_indexes=database_query.fetch_invalid_indexes()
        database_name=os.getenv('DB_NAME')
        if not len(invalid_indexes)>0:
            click.echo(f'No invalid index found for database: {database_name}')
            exit(0)
       
        if not len(invalid_indexes)==0:
            
            table_formatted_index_result = [
                [
                    item["database_name"],
                    item["schema_name"],
                    item["index_name"],
                    item["index_size"],
                    item["category"],
                ]
                for item in invalid_indexes
            ]
            index_table_headers = [
                "Database Name",
                "Schema Name",
                "Index Name",
                "Index Size",
                "Category",
            ]
            index_result_table = tabulate(
                table_formatted_index_result, index_table_headers, tablefmt="psql"
            )
            click.echo(index_result_table)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")