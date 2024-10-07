rm -rf pg_index_insight.egg-info

pip install -e .
pg_index_insight list-unused-or-old-indexes
pg_index_insight list-invalid-indexes
pg_index_insight list-duplicate-indexes
pg_index_insight list-inefficient-or-redundant-indexes
pg_index_insight list-bloated-btree-indexes

