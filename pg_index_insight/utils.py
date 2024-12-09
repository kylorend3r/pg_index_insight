import json
import os

def generate_index_report(data, db_name, report_name="index_report", filename='index_report', report_path='/tmp/'):
    """
    Generate a JSON report of index information.

    Parameters:
        data (list of lists): Raw index data where each inner list contains index properties.
        report_name (str): Name of the report.

    Returns:
        str: JSON formatted string representing the index report.
    """
    headers = ['Database Name', 'Schema Name', 'Index Name', 'Index Type','Index Size', 'Category']
    indexes = [dict(zip(headers, row)) for row in data]
    report = {
        "report_name": report_name,
        "database_name": db_name,
        "total_index_count": len(indexes),
        "indexes": indexes
    }
    with open(f'''{report_path}{filename}.json''', 'w') as output_json:
        json.dump(report, output_json, indent=4)
        return True
    return False

def generate_command(category,schema_name,index_name):
    """
    Generate an SQL command based on the category.

    Parameters:
        category (str): The category of the operation ('Bloated' or other).
        schema_name (str): The schema name of the index.
        index_name (str): The name of the index.

    Returns:
        str: The SQL command to execute.
    """
    operation = "REINDEX INDEX CONCURRENTLY" if category == "Bloated" else "DROP INDEX CONCURRENTLY"
    return f"{operation} {schema_name}.{index_name};"