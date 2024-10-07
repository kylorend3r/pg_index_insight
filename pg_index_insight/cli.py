import click


from .commands.list_unused_old_indexes import list_unused_or_old_indexes
from .commands.list_invalid_index import list_invalid_indexes
from .commands.list_duplicate_index import list_duplicate_indexes
from .commands.list_inefficient_indexes import list_inefficient_or_redundant_indexes
from .commands.list_bloated_indexes import list_bloated_btree_indexes

@click.group()
def main():
    """
    The main entry point for the pg_index_purifier CLI Tool. 

    This command line interface provides various utilities to analyze and 
    manage PostgreSQL indexes, helping users identify and eliminate 
    inefficient, invalid, unused, or bloated indexes. 

    Available commands include:
    - list_unused_or_old_indexes: Lists indexes that are no longer in use.
    - list_invalid_indexes: Identifies indexes that are misconfigured or corrupted.
    - list_duplicate_indexes: Finds duplicate B-tree indexes.
    - list_inefficient_or_redundant_indexes: Reports on indexes that are underperforming.
    - list_bloated_btree_indexes: Detects indexes with excessive unused space.

    To use this tool, invoke it from the command line and specify a command.
    """
    pass


main.add_command(list_unused_or_old_indexes)
main.add_command(list_invalid_indexes)
main.add_command(list_duplicate_indexes)
main.add_command(list_inefficient_or_redundant_indexes)
main.add_command(list_bloated_btree_indexes)

if __name__ == '__main__':
    main()
