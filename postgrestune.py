#!/usr/bin/env python
from __future__ import print_function

### Install requirements: ###
# apt install python-psutil or yum install python2-psutil
# apt install python-pip or yum install python2-pip
# apt-get install python-psycopg2 or yum install python-psycopg2
# apt-get install python-packaging or yum install python-packaging
# yum install python-colorama

### PostgreSQL major and minor verion: ###
POSTGRESQL_VERSION_MAJOR_CURRENT=None
POSTGRESQL_VERSION_MAJOR_LATEST='10'
POSTGRESQL_VERSION_MINOR_LATEST_10='10.4'
POSTGRESQL_VERSION_MINOR_LATEST_96='9.6.9'
POSTGRESQL_VERSION_MINOR_LATEST_95='9.5.13'
POSTGRESQL_VERSION_MINOR_LATEST_94='9.4.18'
POSTGRESQL_VERSION_MINOR_LATEST_93='9.3.23'
WORK_MEM_PER_CONNECTION_PERCENT=150

#### Import modules: ####
import psutil
import platform
import re
import subprocess
import psycopg2
from packaging import version
import os
import datetime
from colorama import Fore

mem = psutil.virtual_memory()

print(Fore.WHITE   + "=====  OS information  =====")
print(Fore.GREEN + 'INFO: OS total memory     : {0} MB'.format(round(mem.total / 1024**2, 0)))
print(Fore.BLUE  + 'INFO: node                : {0}'.format(platform.node()))
print(Fore.GREEN + 'INFO: release             : {0}'.format(platform.release()))
print(Fore.BLUE  + 'INFO: machine             : {0}'.format(platform.machine()))
print(Fore.BLUE  + 'INFO: processor           : {0}'.format(platform.processor()))
print(Fore.GREEN + 'INFO: linux_distribution  : {0}'.format(platform.linux_distribution()))

try:
  conn=psycopg2.connect(
    database="postgres",
    user="postgres",
  )
except IOError as e:
  print(Fore.RED + "Error {0}".format(e))
cur = conn.cursor()

def cur_execute(sql_query):
  try:
   cur.execute(sql_query)
  except psycopg2.Error as e:
   print("Error {0}".format(e))

  return cur.fetchone()[0]

def get_value_proc(path_of_proc):
    try:
      with open(path_of_proc, 'r') as f:
        value_proc = f.readline().split()[0]
        return(value_proc)
    except IOError as e:
      print(Fore.RED + 'ERROR: %s' % e)

def check_overcommit_memory():
  overcommit_memory = int(get_value_proc('/proc/sys/vm/overcommit_memory'))
  if overcommit_memory != 2:
    print(Fore.YELLOW + "WARN: overcommit_memory: {0}".format(overcommit_memory))
    print(Fore.YELLOW + "WARN: Memory overcommitment is allowed on the system. This can lead to OOM Killer killing some PostgreSQL process, which will cause a PostgreSQL server restart (crash recovery)")
    print(Fore.YELLOW + "WARN: set vm.overcommit_memory=2 in /etc/sysctl.conf and run sysctl -p to reload it. This will disable memory overcommitment and avoid postgresql killed by OOM killer.")

check_overcommit_memory()

def check_overcommit_ratio():
  overcommit_ratio = int(get_value_proc('/proc/sys/vm/overcommit_ratio'))
  if overcommit_ratio <= 50:
    print(Fore.YELLOW + "WARN: overcommit_ratio: {0}".format(overcommit_ratio))
    print(Fore.YELLOW + "WARN: vm.overcommit_ratio is too small, you will not be able to use more than $overcommit_ratio*RAM+SWAP for applications")
  elif overcommit_ratio >= 90:
    print(Fore.YELLOW + "WARN: overcommit_ratio: {0}".format(overcommit_ratio))
    print(Fore.YELLOW + "WARN: vm.overcommit_ratio is too high, you need to keep free space for the kernel")

check_overcommit_ratio()

print(Fore.WHITE + "=====  General instance informations  =====")

def check_postgresql_version():
  postgresql_version=cur_execute("SELECT version();").split(' ')[1]
  POSTGRESQL_VERSION_MAJOR_CURRENT = re.findall(r'(\d{1,3}\.\d{1,3})', postgresql_version)[0]

  if version.parse(POSTGRESQL_VERSION_MAJOR_CURRENT) < version.parse(POSTGRESQL_VERSION_MAJOR_LATEST):
    print(Fore.YELLOW + "WARN: Latest major version postgres is: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    print(Fore.YELLOW + "INFO: You used not latest major version postgres: {0}".format(POSTGRESQL_VERSION_MAJOR_CURRENT))
    if POSTGRESQL_VERSION_MAJOR_CURRENT == '9.6':
      if version.parse(postgresql_version) < version.parse(POSTGRESQL_VERSION_MINOR_LATEST_96):
        print(Fore.RED + "WARN: You used not latest version postgres: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    elif POSTGRESQL_VERSION_MAJOR_CURRENT == '9.5':
      if version.parse(postgresql_version) < version.parse(POSTGRESQL_VERSION_MINOR_LATEST_95):
        print(Fore.RED + "WARN: You used not latest version postgres: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    elif POSTGRESQL_VERSION_MAJOR_CURRENT == '9.4':
      if version.parse(postgresql_version) < version.parse(POSTGRESQL_VERSION_MINOR_LATEST_94):
        print(Fore.RED + "WARN: You used not latest version postgres: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    elif POSTGRESQL_VERSION_MAJOR_CURRENT == '9.3':
      if version.parse(postgresql_version) < version.parse(POSTGRESQL_VERSION_MINOR_LATEST_93):
        print(Fore.RED + "WARN: You used not latest version postgres: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
  else:
    if version.parse(postgresql_version) < version.parse(POSTGRESQL_VERSION_MINOR_LATEST_10):
      print(Fore.RED + "WARN: You used not latest postgres version: {0}".format(POSTGRESQL_VERSION_MINOR_LATEST_10))
  return POSTGRESQL_VERSION_MAJOR_CURRENT

POSTGRESQL_VERSION_MAJOR_CURRENT = check_postgresql_version()

def check_username_equal_password():
  try:
   cur.execute("select usename from pg_shadow where passwd='md5'||md5(usename||usename);")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))

  if cur != None:
    for k in cur:
      print(Fore.RED + "ERROR: some users account have the username as password : {0}".format(k[0]))

check_username_equal_password()

print(Fore.WHITE + "-----  Extensions  -----")

def check_pg_stat_statements():
  available_pg_stat_statements=cur_execute("SELECT * FROM pg_available_extensions WHERE name = 'pg_stat_statements' and installed_version is not null;")
  if available_pg_stat_statements == None:
    print(Fore.RED + "ERROR: Extensions pg_stat_statements is disabled")
    print(Fore.YELLOW + "WARN: Enable pg_stat_statements to collect statistics on all queries (not only queries longer than log_min_duration_statement in logs)")
    print(Fore.YELLOW + "WARN: Add the following entries to your postgres.conf: shared_preload_libraries = 'pg_stat_statements'")
    print(Fore.YELLOW + "WARN: restart the PostgreSQL daemon and run 'create extension pg_stat_statements' on your database")

check_pg_stat_statements()

print(Fore.WHITE + "-----  Connection information  -----")

def max_connections():
  return int(cur_execute("SELECT setting FROM pg_settings WHERE name = 'max_connections';"))

print(Fore.BLUE + "INFO: max_connections: {}".format(max_connections()))

def current_connections():
  return int(cur_execute("SELECT count(*) FROM pg_stat_activity;"))

current_connections_percent=current_connections()*100/max_connections()

print(Fore.BLUE + "INFO: current used connections: {} ({}%)".format(current_connections(),current_connections_percent))

def check_current_connections_percent():
  if current_connections_percent > 90:
    print(Fore.RED + 'ERROR: You are using more that 90% or your connection. Increase max_connections before saturation of connection slots')
  elif current_connections_percent > 70:
    print(Fore.YELLOW + 'WARN: You are using more than 70% or your connection. Increase max_connections before saturation of connection slots')    

check_current_connections_percent()

def superuser_reserved_connections():
  return int(cur_execute("show superuser_reserved_connections;"))

def superuser_reserved_connections_ratio():
  superuser_reserved_connections_ratio=superuser_reserved_connections()*100/max_connections()
  if superuser_reserved_connections() == 0:
    print(Fore.RED + "No connection slot is reserved for superuser. In case of connection saturation you will not be able to connect to investigate or kill connections")
  elif superuser_reserved_connections_ratio > 20:
    print(Fore.YELLOW + "{0} of connections are reserved for super user. This is too much and can limit other users connections".format(superuser_reserved_connections_ratio))
  else:
    print(Fore.GREEN + "superuser_reserved_connections are reserved for super user {0} connection".format(superuser_reserved_connections()))

superuser_reserved_connections_ratio()

def average_connection_age():
  return int(cur_execute("select extract(epoch from avg(now()-backend_start)) as age from pg_stat_activity;"))

def convert_time(sec): 
    td = datetime.timedelta(seconds=sec) 
    return td.seconds/3600, (td.seconds/60)%60, td.seconds%60

average_connection_seconds=average_connection_age()

def check_average_connection_age(seconds):
  h,m,s = convert_time(average_connection_age())
  print(Fore.GREEN + 'INFO: Average connection age : {:2.0f}h {:2.0f}m {:2.0f}s'.format(h,m,s))
  if seconds < 60:
    print(Fore.RED + "WARN: Average connection age is less than 1 minute. Use a connection pooler to limit new connection/seconds")
  elif seconds < 600:
    print(Fore.YELLOW + "WARN: Average connection age is less than 10 minutes. Use a connection pooler to limit new connection/seconds")

check_average_connection_age(average_connection_seconds)

print(Fore.WHITE + "-----  Memory usage  -----")

def work_mem():
  try:
   cur.execute("show work_mem;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  return cur.fetchone()[0]

def convert_to_byte(size):
  size_byte=None
  if re.search('gb', size, re.IGNORECASE):
    size_mb = int(re.sub(r'gb', '', size, flags=re.IGNORECASE))*1024
    size_kb = size_mb*1024
    size_byte = size_kb*1024
  elif re.search('mb', size, re.IGNORECASE):
    size_kb = int(re.sub(r'mb', '', size, flags=re.IGNORECASE))*1024
    size_byte = size_kb*1024
  elif re.search('kb', size, re.IGNORECASE):
    size_byte = int(re.sub(r'kb', '', size, flags=re.IGNORECASE))*1024
  return size_byte

def format_bytes(bytes_num):
    sizes = [ "B", "KB", "MB", "GB", "TB" ]
 
    i = 0
    dblbyte = bytes_num
 
    while (i < len(sizes) and  bytes_num >= 1024):
            dblbyte = bytes_num / 1024.0
            i = i + 1
            bytes_num = bytes_num / 1024
 
    return str(round(dblbyte, 2)) + " " + sizes[i]

work_mem_total=convert_to_byte(work_mem())*WORK_MEM_PER_CONNECTION_PERCENT/100*max_connections();
print(Fore.GREEN + "INFO: configured work_mem {0}".format(work_mem()))
print(Fore.GREEN + "INFO: Using an average ratio of work_mem buffers by connection of {0}".format(WORK_MEM_PER_CONNECTION_PERCENT))
print(Fore.GREEN + "INFO: total work_mem (per connection): {}".format(format_bytes(convert_to_byte(work_mem())*WORK_MEM_PER_CONNECTION_PERCENT/100)))

def shared_buffers():
  try:
   cur.execute("show shared_buffers;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  return cur.fetchone()[0]

print(Fore.GREEN + "INFO: shared_buffers: {}".format(shared_buffers()));

def autovacuum_max_workers():
  return int(cur_execute("show autovacuum_max_workers;"))

def max_worker_processes():
  return int(cur_execute("show max_worker_processes;"))

max_processes = max_connections() + autovacuum_max_workers()

if POSTGRESQL_VERSION_MAJOR_CURRENT >= '9.4':
  max_processes = max_processes + max_worker_processes()

print(Fore.GREEN + "Track activity reserved size : " + str(max_processes))

def track_activity_query_size():
  return int(cur_execute("show track_activity_query_size;"))

track_activity_size = track_activity_query_size()*max_processes

def maintenance_work_mem():
  try:
   cur.execute("show maintenance_work_mem;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  return cur.fetchone()[0]

maintenance_work_mem_total = convert_to_byte(maintenance_work_mem()) * autovacuum_max_workers()

if convert_to_byte(maintenance_work_mem()) <= 64*1024*1024:
  print(Fore.YELLOW + "WARN: maintenance_work_mem {} is less or equal default value. Increase it to reduce maintenance tasks time".format(maintenance_work_mem()))
else:
  print(Fore.GREEN + "INFO: maintenance_work_mem = {}".format(maintenance_work_mem()))

max_memory=convert_to_byte(shared_buffers())+work_mem_total+maintenance_work_mem_total+track_activity_size

temp_variable1 = max_connections()*convert_to_byte(work_mem())*WORK_MEM_PER_CONNECTION_PERCENT/100
temp_variable2 = format_bytes(autovacuum_max_workers() * convert_to_byte(maintenance_work_mem()))

print(Fore.WHITE + "\t\t Max memory usage:")
print(Fore.WHITE + "\t\t shared_buffers ({})".format(shared_buffers()))
print(Fore.WHITE + "\t\t + max_connections * work_mem * average_work_mem_buffers_per_connection ", end='')
print(Fore.WHITE + "({0}*{1}*{2}/100 = {3})".format(max_connections(),
  format_bytes(convert_to_byte(work_mem())),WORK_MEM_PER_CONNECTION_PERCENT,format_bytes(temp_variable1)))
print(Fore.WHITE + "\t\t + autovacuum_max_workers * maintenance_work_mem ", end='')
print(Fore.WHITE + "({0}*{1} = {2})".format(autovacuum_max_workers(),maintenance_work_mem(),temp_variable2))
print(Fore.WHITE + "\t\t + track activity size ", end='')
print(Fore.WHITE + "({0})".format(format_bytes(track_activity_size)))

print(Fore.RESET)

cur.close()
conn.close()
