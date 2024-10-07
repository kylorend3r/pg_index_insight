# Next Phase

- [x] Ensure the database connections are managed by one function. 
- [x] Add information about replication for unused ones. Because the user has to check all replicas and confirm the index can be dropped.
- [x] Add another command to find exact duplicate indexes. 
- [x] Add another command to obtain indexes older than 1 year(last scan date)
- [x] Add another command to calculate index bloat and generate reindex command. 
- [x] Add another command to dump invalid indexes. 
- [x] Store SQL commands in a seperate folder/file. 
- [x] Create a single report that contains information about indexes easy to drop/fix like unused+redundant, duplicate, and invalid ones.
- [x] Add CSV or JSON export option. 
- [x] Add connection and statement timeouts. 
- [ ] Complete cli helper,documentation and usage texts. 
- [x] Migrate calculations from commands to database files to make command fuctions more simple.
- [x] JSON file names will be generated according to function name
- [ ] Rename the project as pgindexinsight



## Improvement

1. Add exceptions to each function if database connection fails or returns no record. done
2. Function definitions are missing. Add definition to each function. 


