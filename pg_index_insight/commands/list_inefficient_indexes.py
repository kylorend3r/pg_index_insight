import click
import os
from tabulate import tabulate
import time
from ..database import DatabaseManager
from ..utils import generate_index_report


@click.command()
@click.option("--json", is_flag=True, help="Export output to JSON file.")
def list_inefficient_or_redundant_indexes(json):
    """
    Connects to the PostgreSQL database and identifies inefficient indexes, 
    which may include unused or invalid indexes that do not contribute to query 
    performance effectively. 

    This function retrieves such indexes from the database and formats the 
    results into a table displaying the database name, index name, and category. 
    If the user requests a JSON export, the function generates a report with 
    the results, naming the file based on the current time and database name.

    If no inefficient indexes are found, the function informs the user and exits. 
    If the JSON report generation fails, a corresponding error message is displayed.
    
    Parameters:
        json (bool): A flag indicating whether to export the results as a JSON report.
    """
    try:
        database_query = DatabaseManager()
        indexResult = database_query.get_unused_and_invalid_indexes()
        database_name=os.getenv('DB_NAME')
        if not len(indexResult)>0:
            click.echo(f'No inefficient index found for database: {database_name}')
            exit(0)
        table_formatted_index_result = [
            [item["database_name"], item["index_name"], item["category"]]
            for item in indexResult
        ]
        index_table_headers = ["Database Name", "Index Name", "Category"]
        report_time = str.replace(str(time.time()), ".", "_")
        json_report_name=f'''{database_name}_inefficient_index_{report_time}'''
        index_result_table = tabulate(
            table_formatted_index_result, index_table_headers, tablefmt="psql"
        )
        if json:
            jsonReport = generate_index_report(
                table_formatted_index_result, filename=json_report_name
            )
            if not jsonReport:
                click.echo(f"Failed to export json")
        click.echo(index_result_table)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")
