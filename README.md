# pg_index_insight

**pg_index_insight** is a command-line interface (CLI) tool designed to help PostgreSQL users analyze and improve the efficiency of their database indexes. This tool highlights inefficient indexes to optimize space utilization, vacuum operations, and overall database performance.

## Why 

`pg_index_insight` is designed to be a simple and effective tool for ensuring your PostgreSQL indexes are efficient. Here are a few reasons why you might prefer using this CLI tool:

- **No extensions required**: Unlike some PostgreSQL performance tools, `pg_index_insight` does not require you to install any database extensions. This keeps your database clean and avoids the complexity of extension management.
  
- **Custom queries without hassle**: With `pg_index_insight`, you can easily run queries to assess index efficiency without needing to modify or set up complex exporters like in Prometheus.

- **Straightforward**: The tool is user-friendly and designed for simplicity. If you’re looking for a tool that allows you to inspect your database's indexes with minimal setup, this CLI will serve your needs well.

- **Portable**: As a standalone CLI tool, you can run it on any environment where you have access to your PostgreSQL database. No additional software or extensive configurations are necessary.


## Features

- Analyze index usage and detect redundant indexes.
- Generate reports on index efficiency.
- Support for JSON export of results.
- Easy-to-use command-line interface.


## Requirements

- Python 3.6 or higher
- PostgreSQL 9.6 or higher
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Clone the repository:

```bash
   git clone https://github.com/yourusername/pg_index_insight.git
   cd pg_index_insight
```

2. Set up a virtual environment (optional but recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3.Install the required packages:

```bash
pip install -r requirements.txt
pip install -e .

```
## Usage

To use pg_index_insight, simply run the following command in your terminal:

```bash
pg_index_insight [command] [options]
```

```bash
pg_index_insight list-invalid-indexes
pg_index_insight list-duplicate-indexes
pg_index_insight list-inefficient-or-redundant-indexes
pg_index_insight list-bloated-btree-indexes 
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




