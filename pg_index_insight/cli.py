import click
import os
from tabulate import tabulate
import time
from .utils import generate_index_report
from .utils import generate_command
from .database import DatabaseManager as DatabaseManager

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

@click.command()
@click.option('--dry-run', is_flag=True, help="Perform a dry run without making any changes.")
def list_invalid_indexes(dry_run):
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
            if dry_run:
                click.echo(f'''The following queries might be run on database: {database_name} to remove invalid indexes. Please run the commands wisely.''')
                for index in invalid_indexes:
                    command_executed=generate_command(index['category'],index['schema_name'],index['index_name'])
                    click.echo(command_executed)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")


@click.command()
@click.option("--json", is_flag=True, help="Export output to JSON file.")
@click.option('--dry-run', is_flag=True, help="Perform a dry run without making any changes.")
def list_unemployed_indexes(json,dry_run):
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
        duplicate_unique_indexes_result=database_query.fetch_duplicate_unique_indexes() 
        duplicate_btree_indexes_result=database_query.fetch_duplicate_indexes()
        database_name=os.getenv('DB_NAME')
        if len(indexResult)==0 and len(duplicate_unique_indexes_result)==0 and len(duplicate_btree_indexes_result)==0:
            click.echo(f'No inefficient index found for database: {database_name}')
            exit(0)
        table_formatted_index_result = [
            [item["database_name"], item["schema_name"],item["index_name"],item["index_size"], item["category"]]
            for item in indexResult
        ]
        # append duplicate unique indexes
        for unique_index in duplicate_unique_indexes_result:
            table_formatted_index_result.append([
                database_name,
                unique_index[0],
                unique_index[2],
                unique_index[4],
                "Duplicate Unique Index"
            ])

        # append duplicate btree indexes
        for btree_index in duplicate_btree_indexes_result:
            table_formatted_index_result.append([
                database_name,
                btree_index[0],
                btree_index[2],
                btree_index[4],
                "Duplicate Btree Index"
            ])
        index_table_headers = ["Database Name","Schema Name", "Index Name","Index Size", "Category"]
        report_time = str.replace(str(time.time()), ".", "_")
        json_report_name=f'''{database_name}_inefficient_index_{report_time}'''
        sorted_desc_index_list = sorted(table_formatted_index_result, key=lambda x: x[3],reverse=True)
        index_result_table = tabulate(
            sorted_desc_index_list, index_table_headers, tablefmt="psql"
        )
        if json:
            jsonReport = generate_index_report(
                sorted_desc_index_list, filename=json_report_name
            )
            if not jsonReport:
                click.echo(f"Failed to export json")
        click.echo(index_result_table)
        if dry_run:
            click.echo(f'''The following queries might be run on database: {database_name}. Please run the commands wisely.''')
            for index in indexResult:
                command_executed=generate_command(index['category'],index['schema_name'],index['index_name'])
                click.echo(command_executed)
            for index in duplicate_unique_indexes_result:
                command_executed=generate_command(index[3],index[0],index[2])
                click.echo(command_executed)
            
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.command()
@click.option("--json", is_flag=True, help="Export output to JSON file.")
@click.option('--dry-run', is_flag=True, help="Perform a dry run without making any changes.")
@click.option('--bloat-threshold', type=int, default=50, help="Set the bloat threshold percentage for indexes.")
def list_bloated_btree_indexes(json,dry_run,bloat_threshold):
    """
    Connects to the PostgreSQL database and identifies bloated B-tree indexes. 
    Bloated indexes occur when the index structure has a significant amount of 
    unused space, which can lead to inefficient query performance and wasted 
    storage resources.

    This function retrieves bloated index information and formats the results 
    into a table displaying the database name, index name, and category. 
    If the user requests a JSON export, the function generates a report with 
    the results, naming the file based on the current time and database name.

    If no bloated indexes are found, the function informs the user and exits. 
    If the JSON report generation fails, a corresponding error message is displayed.

    Parameters:
        json (bool): A flag indicating whether to export the results as a JSON report.
    """
    try:
        databaseConnection = DatabaseManager()
        indexResult = databaseConnection.get_bloated_indexes(bloat_threshold)
        database_name=os.getenv('DB_NAME')
        if not len(indexResult)>0:
            click.echo(f'No bloated index found for database: {database_name}')
            exit(0)
        table_formatted_index_result = [
            [item["database_name"],item["schema_name"], item["index_name"],item["bloat_ratio"],item["category"]]
            for item in indexResult
        ]
        index_table_headers = ["Database Name","Schema Name","Index Name","Bloat Ratio", "Category"]
        report_time = str.replace(str(time.time()), ".", "_")
        json_report_name=f'''{database_name}_bloated_index_{report_time}'''
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

        if dry_run:
            click.echo(f'''The following queries might be run on database: {database_name}. Please run the commands wisely.''')
            for index in indexResult:
                command_executed=generate_command(index['category'],index['schema_name'],index['index_name'])
                click.echo(command_executed)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@click.group()
def main():
    """
    The main entry point for the pgindexinsight CLI Tool. 

    This command line interface provides various utilities to analyze and 
    manage PostgreSQL indexes, helping users identify and eliminate 
    inefficient, invalid, unused, or bloated indexes. 

    Available commands include:
    - list_unused_or_old_indexes: Lists indexes that are no longer in use.
    - list_invalid_indexes: Identifies indexes that are misconfigured or corrupted.
    - list_duplicate_indexes: Finds duplicate B-tree indexes.
    - list_unemployed_indexes: Reports on indexes that are underperforming.
    - list_bloated_btree_indexes: Detects indexes with excessive unused space.

    To use this tool, invoke it from the command line and specify a command.
    """
    pass


main.add_command(list_bloated_btree_indexes)
main.add_command(list_unemployed_indexes)
main.add_command(list_invalid_indexes)
main.add_command(list_unused_or_old_indexes)

if __name__ == '__main__':
    main()
