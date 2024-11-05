# pgindexinsight
pgindexinsight is a command-line interface (CLI) tool designed to help PostgreSQL users analyze and optimize the efficiency of their database indexes. The tool highlights inefficient indexes, offering insights to improve space utilization, vacuum operations, and overall database performance without the need for external extensions or packages.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

# Why Choose pgindexinsight?
pgindexinsight offers a simple yet powerful way to ensure that your PostgreSQL indexes are running efficiently. Here are key reasons to choose this tool:

- No Extensions or Packages Required: Unlike other PostgreSQL performance tools, pgindexinsight doesn’t require the installation of any database extensions or other packages. It keeps your database setup clean and reduces complexity.
- No Need to Memorize Index Queries: The tool uses pre-defined queries to analyze your indexes, so you don’t have to recall or memorize the correct index analysis queries every time. This provides a hassle-free experience for database inspection.
- Minimal Setup: The tool is easy to install and use. Whether you're a beginner or a seasoned database administrator, pgindexinsight is designed to make index management intuitive and straightforward.
- Portable & Lightweight: As a standalone CLI tool, pgindexinsight can be run in any environment with PostgreSQL access. There’s no dependency on external software, so you can freely install or remove it whenever needed.

## Key Features
1. Index Usage Analysis: Detect redundant, unused, or bloated indexes and ensure your database operates efficiently.
2. Comprehensive Reporting: Generate detailed reports on index health, usage, and redundancy.
3. JSON Export Support: Easily export the results of your analyses in JSON format for further processing or integration with other systems.
4. User-Friendly CLI: The tool is designed with ease of use in mind, allowing database administrators and developers to get started with minimal effort.

## Benefits

- Keep your PostgreSQL database clean: No need to install or manage third-party database extensions.
- Flexible: Run the tool only when needed, and easily remove it afterward if no longer required.
- Empowers Database Administrators: Get valuable insights into your index usage to optimize performance and space, without any extra overhead.


# Requirements

- Python 3.6 or higher
- PostgreSQL 16 or higher
- Required Python packages (listed in `requirements.txt`)

# Installation

## Installation from Source

1. Clone the repository:

```bash
git clone https://github.com/yourusername/pg_index_insight.git
cd pg_index_insight
```

2. Set up a virtual environment (optional but recommended):

```bash
python3 -m venv venv
source venv/bin/activate
```

3.Install the required packages:

```bash
pip install -r requirements.txt
pip install -e .

```

## ⚠️ **Warning**

**Please ensure that you are working with proper python virtual env! It is not an obligation but strongly suggested.**

## Configure PostgreSQL User

pgindexinsight requires a user which can connect to the database that will be scanned. Therefore, the following example reveals the minimum privileges. Before executing pgindexinsight please ensure that the user has enough privileges.In addition to this please confirm pg_hba.conf allows the connection.

```sql
GRANT SELECT ON TABLE pg_stat_user_indexes TO pg_index_insight_user;
GRANT SELECT ON TABLE pg_index TO pg_index_insight_user;
GRANT SELECT ON TABLE pg_class TO pg_index_insight_user;
GRANT SELECT ON TABLE pg_namespace TO pg_index_insight_user;
GRANT SELECT ON TABLE pg_attribute TO pg_index_insight_user;
GRANT SELECT ON TABLE pg_stats TO pg_index_insight_user;
GRANT SELECT ON TABLE pg_indexes TO pg_index_insight_user;
```

## Configure Environment Variables

Before using this tool, you need to configure some environment variables. These variables are essential for connecting to your PostgreSQL database. Set them by running the following commands in your terminal:

```bash
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="your_db_name"
export DB_USER="your_user"
export DB_PASSWORD="your_pass"
```

# Usage

```bash
pgindexinsight [command] [options]
```

## Examples

```bash
pgindexinsight list-unused-or-old-indexes
pgindexinsight list-invalid-indexes
pgindexinsight list_unemployed_indexes
pgindexinsight list-bloated-btree-indexes
```

### Available Commands

- `list-unused-or-old-indexes`: Lists unused or outdated indexes.
- `list-invalid-indexes`: Identifies invalid indexes.
    - Options:
        - --dry-run: Display actions without executing them.
- `list-unemployed-indexes`: Lists unused indexes.
    - Options:
        - --dry-run: Display actions without executing them.
        - --json: Export output to a JSON file.

- `list-bloated-btree-indexes`: Reports on bloated B-tree indexes.
    - Options:
        - --dry-run: Display actions without executing them.
        - --json: Export output to a JSON file.
        - --bloat-threshold INTEGER: Set the bloat threshold percentage (default is 50%).

Example Output for `list-unemployed-indexes`

```bash
+-----------------+---------------+-------------------------------+--------------+------------------------+
| Database Name   | Schema Name   | Index Name                    | Index Size   | Category               |
|-----------------+---------------+-------------------------------+--------------+------------------------|
| benchmark_v1    | public        | idx_test_v7                   | 545 MB       | Unused&Redundant Index |
| benchmark_v1    | public        | idx_test_v6                   | 545 MB       | Unused&Redundant Index |
| benchmark_v1    | public        | idx_test_v5                   | 545 MB       | Unused&Redundant Index |
| benchmark_v1    | public        | idx_test_v6                   | 545 MB       | Duplicate Btree Index  |
| benchmark_v1    | public        | idx_test_v5                   | 545 MB       | Duplicate Btree Index  |
| benchmark_v1    | sales         | orders_2023_q2_order_date_idx | 16 kB        | Unused&Redundant Index |
| benchmark_v1    | public        | pgbench_accounts_pkey_v2      | 1285 MB      | Duplicate Unique Index |
| benchmark_v1    | public        | idx_test_data                 | 0 bytes      | Unused&Redundant Index |
| benchmark_v1    | public        | idx_test_data                 | 0 bytes      | Invalid Index          |
+-----------------+---------------+-------------------------------+--------------+------------------------+
```

## Contributing
Contributions are welcome! If you have suggestions for improvements or would like to report a bug, please open an issue or submit a pull request.

1. Fork the repository.
2. Create your feature branch:
```bash
git checkout -b feature/YourFeatureName
```
3. Commit your changes:
```bash
git commit -m 'Add some feature'
```
4. Push to the branch:
```bash
git push origin feature/YourFeatureName
```
5. Open a pull request.