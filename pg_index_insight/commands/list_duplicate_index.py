import os
import psycopg2
import click
from tabulate import tabulate
from ..database import DatabaseManager
from ..queries import SqlQueries


@click.command()
def list_duplicate_indexes():
    """
    Connects to the PostgreSQL database and identifies duplicate B-tree indexes. 
    Duplicate indexes can lead to unnecessary storage consumption and 
    degraded performance, as they provide redundant functionality.

    This function retrieves a list of such duplicate indexes and formats the 
    results into a table displaying the database name, original index name, 
    duplicate index name, and the category of the indexes. 

    If no duplicate indexes are found, the function informs the user and exits.
    """
    try:
        database_query = DatabaseManager()
        duplicate_index_list = database_query.get_duplicate_btree_indexes()
        database_name=os.getenv('DB_NAME')
        if not len(duplicate_index_list)>0:
            click.echo(f'No duplicate index found for database: {database_name}')
            exit(0)
       
        table_formatted_index_result = [
            [
                item["database_name"],
                item["index_name"],
                item["duplicated_index_name"],
                item["category"],
            ]
            for item in duplicate_index_list
        ]
        index_table_headers = [
            "Database Name",
            "Index Name",
            "Duplicate Index Name",
            "Category",
        ]
        index_result_table = tabulate(
            table_formatted_index_result, index_table_headers, tablefmt="psql"
        )
        click.echo(index_result_table)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")
