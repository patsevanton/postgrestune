# postgrestune
Python script to analyse your PostgreSQL database configuration, and give tuning advice
This project is fork https://github.com/jfcoz/postgresqltuner rewrite to Python

### Install requirements: ###
```
apt-get install python-psutil or yum install python2-psutil
apt-get install python-pip or yum install python2-pip
apt-get install python-psycopg2 or yum install python-psycopg2
apt-get install python-packaging or yum install python-packaging
apt-get install python-colorama or yum install python-colorama
```
Add permissions:
```
chmod +x ./postgrestune.py
```
Run:
```
sudo -u postgres ./postgrestune.py
```

# For Russian:
Большую часть (думаю что 90%) оригинального скрипта переписал на Python.
Но малоиспользуемые опции я не написал в Python скрипте (например: .pgpass, ssh и другие).
Если кто-нибудь хочет попрактиковаться: проверить код, переписать в более правильном виде, добавить функциональность из Perl или из общих практик проверки PostgreSQL - милости прошу.
Присылайте Pull request.
Попробуйте проверить PostgreSQL на своих DEV, TEST базах данных.

# For English
Most (I think 90%) of the original script was rewritten in Python.
But little-used options I have not written in a Python script (eg:.pgpass, ssh and others).
If anyone wants to practice: check the code, rewrite it in a more correct form, add functionality from Perl or from General practices of PostgreSQL check-you are welcome.
Send a Pull request.
Try to test PostgreSQL on your DEV, TEST databases.

# Output on test PostgreSQL
```
sudo -u postgres ./postgrestune.py
Connecting to unix socket database template1 with user postgres...
===== OS information =====
[INFO]	 linux_distribution  : Ubuntu 18.04 bionic
[INFO]	 OS total memory     : 7.43 GB
[INFO]	 node                : thinkpad
[INFO]	 release             : 4.15.0-22-generic
[INFO]	 machine             : x86_64
[INFO]	 processor           : x86_64
[BAD]:	Memory overcommitment is allowed on the system. This can lead to OOM Killer killing some PostgreSQL process, which will cause a PostgreSQL server restart (crash recovery)
[INFO]:	sysctl vm.overcommit_ratio=50
[BAD]:	vm.overcommit_ratio is too small, you will not be able to use more than 50*RAM+SWAP for applications
===== General instance informations =====
----- Version -----
[OK]	 You are using last postgresql version 10.4
----- Uptime -----
[INFO]	 PoatgreSQL service uptime: 03h 57m 55s
[WARN]	 Uptime is less than 1 day. ./postgrestune.py result may not be accurate
----- Databases -----
[INFO]	 Database count (except templates): 3
[INFO]	 Database list (except templates): postgres, test, test1
----- Extensions -----
[INFO]	 Number of activated extensions : 1
[INFO]	 Activated extensions : plpgsql
[WARN]:	Extensions pg_stat_statements is disabled
----- Users -----
[WARN]:	some users account have the username as password : test, test1
[INFO]	 Password encryption is enabled
----- Connection information -----
[INFO]	 max_connections: 100
[INFO]	 current used connections: 6 (6%)
[INFO]	 3 are reserved for super user connection (3)%
[INFO]	 Average connection age :  3h 18m 15s
----- Memory usage -----
[INFO]	 configured work_mem 4MB
[INFO]	 Using an average ratio of work_mem buffers by connection of 150% (require from WORK_MEM_PER_CONNECTION_PERCENT in script)
[INFO]	 total work_mem (per connection): 6.0 MB
[INFO]	 shared_buffers: 128MB
[INFO]	 Track activity reserved size : 103
[WARN]	 maintenance_work_mem 64MB is less or equal default value. Increase it to reduce maintenance tasks time
		 Max memory usage:
		 shared_buffers (128MB)
		 + max_connections * work_mem * average_work_mem_buffers_per_connection (100*4.0 MB*150/100 = 600.0 MB)
		 + autovacuum_max_workers * maintenance_work_mem (3*64MB = 192.0 MB)
		 + track activity size (103.0 KB)
[INFO]	 effective_cache_size: 4GB
[INFO]	 Size of all databases : 1.55 GB
[INFO]	 PostgreSQL maximum memory usage: 12.09% of system RAM
[WARN]	 Max possible memory usage for PostgreSQL is less than 60% of system total RAM. On a dedicated host you can increase PostgreSQL buffers to optimize performances.
max memory+effective_cache_size is 65.00% of total RAM
----- Logs -----
[WARN]	 log of long queries is desactivated. It will be more difficult to optimize query performances
[INFO]	 log_statement = none
----- Autovacuum -----
[INFO]	 autovacuum is activated
[INFO]	 autovacuum_max_workers: 3
----- Checkpoint -----
[WARN]:	checkpoint_completion_target (0.5) is low
----- Disk access -----
[OK]:	fsync is on
[OK]:	synchronize_seqscans is on
----- WAL -----
----- Planner -----
[WARN]:	some costs settings are not the defaults : . This can have bad impacts on performance. Use at your own risks
===== Database information for database template1 =====
----- Database size -----
[INFO]:	Database template1 total size : 7.85 MB
[INFO]:	Database template1 tables size : 4.82 MB (61%)
[INFO]:	Database template1 indexes size : 3.03 MB (38%)
----- Tablespace location -----
[BAD]:	Some tablespaces are in PGDATA : /var/lib/postgresql/10/main/tablespace_in_data1, /var/lib/postgresql/10/main/tablespace_in_data
----- Shared buffer hit rate -----
[INFO]:	shared_buffer_heap_hit_rate: 99.42%
[INFO]:	shared_buffer_toast_hit_rate: 71.25%
[INFO]:	shared_buffer_tidx_hit_rate: 88.61%
[INFO]:	shared_buffer_idx_hit_rate: 99.70%
[OK]:	Shared buffer idx hit rate is very good
----- Indexes -----
[OK]:	No invalid indexes
[OK]:	No unused indexes
----- Procedures -----
[OK]:	No procedures with default costs
===== Configuration advices =====
----- checkpoint -----
medium Your checkpoint completion target is too low. Put something nearest from 0.8/0.9 to balance your writes better during the checkpoint interval
----- tablespaces -----
urgent Some tablespaces are in PGDATA. Move them outside of this folder.
----- sysctl -----
urgent set vm.overcommit_memory=2 in /etc/sysctl.conf and run sysctl -p to reload it. This will disable memory overcommitment and avoid postgresql killed by OOM killer.
----- extension -----
low Enable pg_stat_statements to collect statistics on all queries (not only queries longer than log_min_duration_statement in logs)
```