#!/usr/bin/env python3

### Install requirements: ###
# apt install python3-psutil
# apt install python3-pip
# apt-get install python3-psycopg2
# apt-get install python3-packaging
# pip3 install procfs
# pip3 install coloredlogs

### PostgreSQL major and minor verion: ###
POSTGRESQL_VERSION_MAJOR_CURRENT=None
POSTGRESQL_VERSION_MAJOR_LATEST='10'
POSTGRESQL_VERSION_MINOR_LATEST_10='10.4'
POSTGRESQL_VERSION_MINOR_LATEST_96='9.6.9'
POSTGRESQL_VERSION_MINOR_LATEST_95='9.5.13'
POSTGRESQL_VERSION_MINOR_LATEST_94='9.4.18'
POSTGRESQL_VERSION_MINOR_LATEST_93='9.3.23'
WORK_MEM_PER_CONNECTION_PERCENT=100

#### Import modules: ####
# import psutil
import platform
import re
import subprocess
import psycopg2
from packaging import version
import logging
import coloredlogs
import os
import datetime

coloredlogs.install()

logging.basicConfig(format = '%(levelname)-8s %(message)s', level = logging.DEBUG)
logging.getLogger("postgrestune")

# mem = psutil.virtual_memory()
# print( 'OS total memory     : {0} MB'.format(round(mem.total / 1024**2, 0)))
# print( 'system              : {0}'.format(platform.system()))
# print( 'node                : {0}'.format(platform.node()))
# print( 'release             : {0}'.format(platform.release()))
# print( 'version             : {0}'.format(platform.version()))
# print( 'machine             : {0}'.format(platform.machine()))
# print( 'processor           : {0}'.format(platform.processor()))
# print( 'dist                : {0}'.format(platform.dist()))
# print( 'linux_distribution  : {0}'.format(platform.linux_distribution()))

try:
  conn=psycopg2.connect(
    database="postgres",
    user="postgres",
  )
except IOError as e:
  print('ERROR: %s' % e)
  logging.error("Error {0}".format(e))
  # logging.error("I am unable to connect to the database")
cur = conn.cursor()

def cur_execute(sql_query):
  try:
   cur.execute(sql_query)
  except psycopg2.Error as e:
   logging.error("Error {0}".format(e))

  return cur.fetchone()[0]

def get_value_proc(path_of_proc):
    try:
      with open(path_of_proc, 'r') as f:
        value_proc = f.readline().split()[0]
        return(value_proc)
    except IOError as e:
        print('ERROR: %s' % e)
        logging.error("Error {0}".format(e))

def check_overcommit_memory():
  overcommit_memory = int(get_value_proc('/proc/sys/vm/overcommit_memory'))
  if overcommit_memory != 2:
    logging.info("overcommit_memory: {0}".format(overcommit_memory))
    logging.info("Memory overcommitment is allowed on the system. This can lead to OOM Killer killing some PostgreSQL process, which will cause a PostgreSQL server restart (crash recovery)")
    logging.info("set vm.overcommit_memory=2 in /etc/sysctl.conf and run sysctl -p to reload it. This will disable memory overcommitment and avoid postgresql killed by OOM killer.")

check_overcommit_memory()

def check_overcommit_ratio():
  overcommit_ratio = int(get_value_proc('/proc/sys/vm/overcommit_ratio'))
  if overcommit_ratio <= 50:
    logging.info("overcommit_ratio: {0}".format(overcommit_ratio))
    logging.info("vm.overcommit_ratio is too small, you will not be able to use more than $overcommit_ratio*RAM+SWAP for applications")
  elif overcommit_ratio >= 90:
    logging.info("overcommit_ratio: {0}".format(overcommit_ratio))
    logging.info("vm.overcommit_ratio is too high, you need to keep free space for the kernel")

check_overcommit_ratio()

def check_pg_stat_statements():
  available_pg_stat_statements=cur_execute("SELECT * FROM pg_available_extensions WHERE name = 'pg_stat_statements' and installed_version is not null;")
  if available_pg_stat_statements == None:
    logging.error("Extensions pg_stat_statements is disabled")
    logging.info("Enable pg_stat_statements to collect statistics on all queries (not only queries longer than log_min_duration_statement in logs)")
    logging.info("Add the following entries to your postgres.conf: shared_preload_libraries = 'pg_stat_statements'")
    logging.info("restart the PostgreSQL daemon and run 'create extension pg_stat_statements' on your database")

check_pg_stat_statements()

def check_postgresql_version():
  postgresql_version=cur_execute("SELECT version();").split(' ')[1]
  POSTGRESQL_VERSION_MAJOR_CURRENT = re.findall(r'(\d{1,3}\.\d{1,3})', postgresql_version)[0]
  print(postgresql_version)

  if version.parse(POSTGRESQL_VERSION_MAJOR_CURRENT) < version.parse(POSTGRESQL_VERSION_MAJOR_LATEST):
    logging.info("You used not major postgres latest version: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    logging.info("You used postgres major version: {0}".format(POSTGRESQL_VERSION_MAJOR_CURRENT))
    if POSTGRESQL_VERSION_MAJOR_CURRENT == '9.6':
      if version.parse(postgresql_version) < version.parse(POSTGRESQL_VERSION_MINOR_LATEST_96):
        logging.error("You used not latest postgres version: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    elif POSTGRESQL_VERSION_MAJOR_CURRENT == '9.5':
      if version.parse(postgresql_version) < version.parse(POSTGRESQL_VERSION_MINOR_LATEST_95):
        logging.error("You used not latest postgres version: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    elif POSTGRESQL_VERSION_MAJOR_CURRENT == '9.4':
      if version.parse(postgresql_version) < version.parse(POSTGRESQL_VERSION_MINOR_LATEST_94):
        logging.error("You used not latest postgres version: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    elif POSTGRESQL_VERSION_MAJOR_CURRENT == '9.3':
      if version.parse(postgresql_version) < version.parse(POSTGRESQL_VERSION_MINOR_LATEST_93):
        logging.error("You used not latest postgres version: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
  else:
    if version.parse(postgresql_version) < version.parse(POSTGRESQL_VERSION_MINOR_LATEST_10):
      logging.error("You used not latest postgres version: {0}".format(POSTGRESQL_VERSION_MINOR_LATEST_10))
  return POSTGRESQL_VERSION_MAJOR_CURRENT

POSTGRESQL_VERSION_MAJOR_CURRENT = check_postgresql_version()

def check_username_equal_password():
  try:
   cur.execute("select usename from pg_shadow where passwd='md5'||md5(usename||usename);")
  except psycopg2.Error as e:
   logging.error("Error {0}".format(e))

  if cur != None:
    for k in cur:
      logging.error("some users account have the username as password : {0}".format(k[0]))

check_username_equal_password()

def max_connections():
  return int(cur_execute("SELECT setting FROM pg_settings WHERE name = 'max_connections';"))

def current_connections():
  return int(cur_execute("SELECT count(*) FROM pg_stat_activity;"))

current_connections_percent=current_connections()*100/max_connections()

def check_current_connections_percent():
  if current_connections_percent > 90:
    logging.error('You are using more that 90% or your connection. Increase max_connections before saturation of connection slots')
  elif current_connections_percent > 70:
    logging.warning('You are using more than 70% or your connection. Increase max_connections before saturation of connection slots')    

check_current_connections_percent()

def superuser_reserved_connections():
  return int(cur_execute("show superuser_reserved_connections;"))

superuser_reserved_connections()

def superuser_reserved_connections_ratio():
  superuser_reserved_connections_ratio=superuser_reserved_connections()*100/max_connections()
  if superuser_reserved_connections == 0:
    logging.error("No connection slot is reserved for superuser. In case of connection saturation you will not be able to connect to investigate or kill connections")
  elif superuser_reserved_connections_ratio > 20:
    logging.warning("{0} of connections are reserved for super user. This is too much and can limit other users connections".format(superuser_reserved_connections_ratio))
  else:
    logging.info("superuser_reserved_connections are reserved for super user {0}%".format(superuser_reserved_connections_ratio))

superuser_reserved_connections_ratio()

def average_connection_age():
  return int(cur_execute("select extract(epoch from avg(now()-backend_start)) as age from pg_stat_activity;"))

def convert_time(sec): 
    td = datetime.timedelta(seconds=sec) 
    return td.seconds/3600, (td.seconds/60)%60, td.seconds%60

average_connection_seconds=average_connection_age()

def check_average_connection_age(seconds):
  h,m,s = convert_time(average_connection_age())
  logging.info('Average connection age : {:2.0f}h {:2.0f}m {:2.0f}s'.format(h,m,s))
  if seconds < 60:
    logging.error("Average connection age is less than 1 minute. Use a connection pooler to limit new connection/seconds")
  elif seconds < 600:
    logging.warning("Average connection age is less than 10 minutes. Use a connection pooler to limit new connection/seconds")

check_average_connection_age(average_connection_seconds)

def work_mem():
  try:
   cur.execute("show work_mem;")
  except psycopg2.Error as e:
   logging.error("Error {0}".format(e))
  return int(re.sub(r'MB', '', cur.fetchone()[0]))

work_mem_total=work_mem()*WORK_MEM_PER_CONNECTION_PERCENT/100*max_connections();
logging.info("configured work_mem_total {0}".format(work_mem_total))
logging.info("Using an average ratio of work_mem buffers by connection of {0}".format(WORK_MEM_PER_CONNECTION_PERCENT))
logging.info("total work_mem (per connection): {}".format(work_mem()*WORK_MEM_PER_CONNECTION_PERCENT/100))


def autovacuum_max_workers():
  return int(cur_execute("show autovacuum_max_workers;"))

def max_worker_processes():
  return int(cur_execute("show max_worker_processes;"))

max_processes=max_connections() + autovacuum_max_workers()

if POSTGRESQL_VERSION_MAJOR_CURRENT >= '9.4':
  max_processes = max_processes + max_worker_processes()

print('max_processes', max_processes)

def track_activity_query_size():
  return int(cur_execute("show track_activity_query_size;"))

track_activity_size=track_activity_query_size()*max_processes

def maintenance_work_mem():
  try:
   cur.execute("show maintenance_work_mem;")
  except psycopg2.Error as e:
   logging.error("Error {0}".format(e))
  return int(re.sub(r'MB', '', cur.fetchone()[0]))

maintenance_work_mem_total=maintenance_work_mem()*autovacuum_max_workers();

if maintenance_work_mem() <= 64*1024*1024:
  logging.warning("maintenance_work_mem {}MB is less or equal default value. Increase it to reduce maintenance tasks time".format(maintenance_work_mem()))
else:
  logging.info("maintenance_work_mem = {}".format(maintenance_work_mem))

def shared_buffers():
  try:
   cur.execute("show shared_buffers;")
  except psycopg2.Error as e:
   logging.error("Error {0}".format(e))
  return int(re.sub(r'MB', '', cur.fetchone()[0]))

logging.info("shared_buffers: {}".format(shared_buffers()));

cur.close()
conn.close()
