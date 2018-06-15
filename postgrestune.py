#!/usr/bin/env python
from __future__ import print_function

# This project is fork https://github.com/jfcoz/postgresqltuner rewrite to Python
#
# postgresqltuner.pl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

### Install requirements: ###
# apt-get install python-psutil or yum install python2-psutil
# apt-get install python-pip or yum install python2-pip
# apt-get install python-psycopg2 or yum install python-psycopg2
# apt-get install python-colorama or yum install python-colorama

### PostgreSQL major and minor verion: ###
POSTGRESQL_VERSION_MAJOR_CURRENT=None
POSTGRESQL_VERSION_MAJOR_LATEST='10'
POSTGRESQL_VERSION_MINOR_LATEST_10='10.4'
POSTGRESQL_VERSION_MINOR_LATEST_96='9.6.9'
POSTGRESQL_VERSION_MINOR_LATEST_95='9.5.13'
POSTGRESQL_VERSION_MINOR_LATEST_94='9.4.18'
POSTGRESQL_VERSION_MINOR_LATEST_93='9.3.23'
WORK_MEM_PER_CONNECTION_PERCENT=150

import imp
try:
  imp.find_module('psycopg2')
except ImportError:
  print('Not found {0} module.'.format('python-psycopg2'))
  print('Run command sudo apt-get install {0} or sudo yum install {0}'.format('python-psycopg2'))
  exit(1)

try:
  imp.find_module('colorama')
except ImportError:
  print('Not found {0} module.'.format('python-colorama'))
  print('Run command sudo apt-get install {0} or sudo yum install {0}'.format('python-colorama'))
  exit(1)

try:
  imp.find_module('pkg_resources')
except ImportError:
  print('Not found {0} module.'.format('python-setuptools'))
  print('Run command sudo apt-get install {0} or sudo yum install {0}'.format('python-setuptools'))
  exit(1)

#### Import modules: ####
import psutil
import platform
import re
import subprocess
import psycopg2
import os
import datetime
from colorama import Fore
import time
import argparse
from pkg_resources import parse_version
import sys

advices={}

def add_advice(category, priority, advice):
  priority_advice={}
  priority_advice[priority] = advice
  advices[category] = priority_advice

def print_header_1(string):
  print(Fore.WHITE + '===== ' + string + ' =====', end='')
  print(Fore.RESET)

def print_header_2(string):
  print(Fore.WHITE + '----- ' + string + ' -----', end='')
  print(Fore.RESET)

def print_report_ok(string):
  print(Fore.GREEN + "[OK]:\t{0}".format(string))

def print_report_warn(string):
  print(Fore.YELLOW + "[WARN]:\t{0}".format(string))

def print_report_bad(string):
  print(Fore.RED + "[BAD]:\t{0}".format(string))

def print_report_info(string):
  print(Fore.WHITE + "[INFO]:\t{0}".format(string))

def print_report_unknown(string):
  print(Fore.CYAN + "[INFO]:\t{0}".format(string))
  
def print_advices():
  print_header_1("Configuration advices");
  for category,priority_advice in advices.iteritems():
    print_header_2(category);
    for priority,advice in priority_advice.iteritems():
      if priority == 'urgent':
        print(Fore.RED + priority,advice)
      elif priority == 'medium':
        print(Fore.YELLOW + priority,advice)
      elif priority == 'low':
        print(Fore.MAGENTA + priority,advice)
    print(Fore.RESET, end='')
  print(Fore.RESET, end='')  

def min_version(min_version):
  if parse_version(postgresql_current_version) < parse_version(min_version):
    # print('{0} < {1}'.format(parse_version(postgresql_current_version), parse_version(min_version)))
    # print('postgresql_current_version < min_version')
    return 0
  else:
    # print('{0} > {1}'.format(parse_version(postgresql_current_version), parse_version(min_version)))
    # print('postgresql_current_version > min_version')
    return 1

def convert_to_byte(size):
  size = size.lower()
  size_byte=None
  if re.search('gb', size):
    size_mb = int(re.sub(r'gb', '', size))*1024
    size_kb = size_mb*1024
    size_byte = size_kb*1024
  elif re.search('mb', size):
    size_kb = int(re.sub(r'mb', '', size))*1024
    size_byte = size_kb*1024
  elif re.search('kb', size):
    size_byte = int(re.sub(r'kb', '', size))*1024
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

def select_one_value(sql_query):
  try:
   cur.execute(sql_query)
  except psycopg2.Error as e:
   print("Error {0}".format(e))
  return cur.fetchone()

def select_one_column(sql_query):
  try:
   cur.execute(sql_query)
  except psycopg2.Error as e:
   print("Error {0}".format(e))
  return cur.fetchall()

def get_setting(setting):
  try:
   cur.execute("SHOW " + setting)
  except psycopg2.Error as e:
   print("Error {0}".format(e))
  return cur.fetchone()[0]

def get_value_proc(path_of_proc):
    try:
      with open(path_of_proc, 'r') as f:
        value_proc = f.readline().split()[0]
        return(value_proc)
    except IOError as e:
      print(Fore.RED + '[ERROR]\t %s' % e)

parser = argparse.ArgumentParser(description="postgrestune")
parser.add_argument('-p', '--port', type=int)
parser.add_argument('-d', '--database', default='postgres')
parser.add_argument('--host')
parser.add_argument('-U', '--username', default='postgres')
parser.add_argument('-W', '--password')
args = parser.parse_args()

try:
  if args.host:
    if args.port:
      print("Connecting to {0}:{1} database {2} with user {3}...".format(args.host, args.port, args.database, args.username))
      conn = psycopg2.connect(
        database = args.database,
        user = args.username,
        host = args.host,
        password = args.password,
      )
    else:
      print("Connecting to {0}:{1} database {2} with user {3}...".format(args.host, args.port, args.database, args.username))
      conn = psycopg2.connect(
        database = args.database,
        user = args.username,
        host = args.host,
        port = args.port,
        password = args.password,
      )
  else:
    print("Connecting to {0} database {1} with user {2}...".format('unix socket', args.database, args.username))
    conn = psycopg2.connect(
      database = args.database,
      user = args.username,
    )
except IOError as e:
  print(Fore.RED + "Error {0}".format(e))
cur = conn.cursor()

mem = psutil.virtual_memory()

# Report
# OS version
print_header_1('OS information')
print(Fore.GREEN + '[INFO]\t linux_distribution  : ' + ' '.join(str(p) for p in platform.linux_distribution()))
# OS Memory
print(Fore.GREEN + '[INFO]\t OS total memory     : {0}'.format(format_bytes(mem.total)))
print(Fore.BLUE  + '[INFO]\t node                : {0}'.format(platform.node()))
print(Fore.GREEN + '[INFO]\t release             : {0}'.format(platform.release()))
print(Fore.BLUE  + '[INFO]\t machine             : {0}'.format(platform.machine()))
print(Fore.BLUE  + '[INFO]\t processor           : {0}'.format(platform.processor()))

# Overcommit
def check_overcommit_memory():
  overcommit_memory = int(get_value_proc('/proc/sys/vm/overcommit_memory'))
  if overcommit_memory != 2:
    print_report_bad("Memory overcommitment is allowed on the system. This can lead to OOM Killer killing some PostgreSQL process, which will cause a PostgreSQL server restart (crash recovery)")
    add_advice('sysctl','urgent','set vm.overcommit_memory=2 in /etc/sysctl.conf and run sysctl -p to reload it. This will disable memory overcommitment and avoid postgresql killed by OOM killer.')
    overcommit_ratio = int(get_value_proc('/proc/sys/vm/overcommit_ratio'))
    print_report_info("sysctl vm.overcommit_ratio={0}".format(overcommit_ratio))
    if overcommit_ratio <= 50:
      print_report_bad("vm.overcommit_ratio is too small, you will not be able to use more than {0}*RAM+SWAP for applications".format(overcommit_ratio))
    elif overcommit_ratio > 90:
      print_report_bad("vm.overcommit_ratio is too high, you need to keep free space for the kernel")
  else:
    print_report_ok("vm.overcommit_memory is good : no memory overcommitment")

check_overcommit_memory()

print_header_1('General instance informations')

postgresql_current_version=select_one_value("SELECT version();")[0].split(' ')[1]
POSTGRESQL_VERSION_MAJOR_CURRENT = re.findall(r'(\d{1,3}\.\d{1,3})', postgresql_current_version)[0]

## Version
print_header_2('Version');
def check_postgresql_version():
  if parse_version(POSTGRESQL_VERSION_MAJOR_CURRENT) < parse_version(POSTGRESQL_VERSION_MAJOR_LATEST):
    print(Fore.YELLOW + "[WARN]\t Latest major version postgres is: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    print(Fore.YELLOW + "[INFO]\t You used not latest major version postgres: {0}".format(POSTGRESQL_VERSION_MAJOR_CURRENT))
    if POSTGRESQL_VERSION_MAJOR_CURRENT == '9.6':
      if parse_version(postgresql_current_version) < parse_version(POSTGRESQL_VERSION_MINOR_LATEST_96):
        print(Fore.RED + "[WARN]\t You used not latest version postgres: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    elif POSTGRESQL_VERSION_MAJOR_CURRENT == '9.5':
      if parse_version(postgresql_current_version) < parse_version(POSTGRESQL_VERSION_MINOR_LATEST_95):
        print(Fore.RED + "[WARN]\t You used not latest version postgres: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    elif POSTGRESQL_VERSION_MAJOR_CURRENT == '9.4':
      if parse_version(postgresql_current_version) < parse_version(POSTGRESQL_VERSION_MINOR_LATEST_94):
        print(Fore.RED + "[WARN]\t You used not latest version postgres: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
    elif POSTGRESQL_VERSION_MAJOR_CURRENT == '9.3':
      if parse_version(postgresql_current_version) < parse_version(POSTGRESQL_VERSION_MINOR_LATEST_93):
        print(Fore.RED + "[WARN]\t You used not latest version postgres: {0}".format(POSTGRESQL_VERSION_MAJOR_LATEST))
  else:
    print(Fore.GREEN + "[OK]\t You are using last postgresql version {0}".format(POSTGRESQL_VERSION_MAJOR_CURRENT))
    if parse_version(postgresql_current_version) < parse_version(POSTGRESQL_VERSION_MINOR_LATEST_10):
      print(Fore.RED + "[WARN]\t You used not latest postgres version: {0}".format(POSTGRESQL_VERSION_MINOR_LATEST_10))
  return POSTGRESQL_VERSION_MAJOR_CURRENT

POSTGRESQL_VERSION_MAJOR_CURRENT = check_postgresql_version()

## Uptime
print_header_2('Uptime');

def get_pid_postgresql():
  for proc in psutil.process_iter():
    if sys.version_info < (2, 7):
      if proc.name == 'postgres' or proc.name == 'postmaster':
        if '-D' in proc.cmdline:
          return int(proc._pid)
    else:
      if proc.name() == 'postgres' or proc.name() == 'postmaster':
        if '-D' in proc.cmdline():
          return int(proc._pid)

def get_time_running_pid(pid):
  p = psutil.Process(pid)
  if sys.version_info < (2, 7):
    return time.time() - p.create_time
  else:
    return time.time() - p.create_time()

pid_postgresql = get_pid_postgresql()
timestamp_running_postgresql = get_time_running_pid(pid_postgresql)
print(Fore.GREEN + '[INFO]\t PoatgreSQL service uptime: ' + time.strftime("%Hh %Mm %Ss", time.gmtime(timestamp_running_postgresql)))

if timestamp_running_postgresql < 24*60*60:
    print(Fore.YELLOW + "[WARN]\t Uptime is less than 1 day. " + __file__ + " result may not be accurate")

# ## Database count (except template)
print_header_2('Databases');

def select_database():
  try:
   cur.execute("SELECT datname FROM pg_database WHERE NOT datistemplate AND datallowconn;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  list_databases = [i[0] for i in cur.fetchall()]
  print(Fore.GREEN + '[INFO]\t Database count (except templates): {0}'.format(len(list_databases)))
  print(Fore.GREEN + '[INFO]\t Database list (except templates): ' + ', '.join(str(p) for p in list_databases))
  
select_database()

print_header_2('Extensions');

def select_extensions():
  try:
   cur.execute("select extname from pg_extension")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  list_extensions = [i[0] for i in cur.fetchall()]
  print(Fore.GREEN + '[INFO]\t Number of activated extensions : {0}'.format(len(list_extensions)))
  print(Fore.GREEN + '[INFO]\t Activated extensions : ' + ', '.join(str(p) for p in list_extensions))
  
select_extensions()

def check_pg_stat_statements():
  available_pg_stat_statements=select_one_value("SELECT * FROM pg_available_extensions WHERE name = 'pg_stat_statements' and installed_version is not null;")
  if available_pg_stat_statements == None:
    print_report_warn("Extensions pg_stat_statements is disabled")
    add_advice("extension","low","Enable pg_stat_statements to collect statistics on all queries (not only queries longer than log_min_duration_statement in logs)")

check_pg_stat_statements()

# print('-----  Users  -----')
print_header_2('Users');

def check_username_equal_password():
  try:
   cur.execute("select usename from pg_shadow where passwd='md5'||md5(usename||usename);")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  if cur != None:
    users_account = [i[0] for i in cur.fetchall()]
    print_report_warn('some users account have the username as password : ' + ', '.join(str(p) for p in users_account))
  else:
    print_report_ok('No user with password=username')

check_username_equal_password()

def password_encryption():
  try:
   cur.execute("show password_encryption;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  config_password_encryption = cur.fetchone()[0]
  if password_encryption == 'off':
    print(Fore.RED + '[ERROR]\t Password encryption is disable by default. Password will not be encrypted until explicitely asked')
  else:
    print(Fore.GREEN + '[INFO]\t Password encryption is enabled')

password_encryption()

print_header_2('Connection information');

def max_connections():
  return int(select_one_value("SELECT setting FROM pg_settings WHERE name = 'max_connections';")[0])

print(Fore.BLUE + "[INFO]\t max_connections: {0}".format(max_connections()))

def current_connections():
  return int(select_one_value("SELECT count(*) FROM pg_stat_activity;")[0])

current_connections_percent=current_connections()*100/max_connections()

print(Fore.BLUE + "[INFO]\t current used connections: {0} ({1}%)".format(current_connections(),current_connections_percent))

def check_current_connections_percent():
  if current_connections_percent > 90:
    print(Fore.RED + '[ERROR]\t You are using more that 90% or your connection. Increase max_connections before saturation of connection slots')
  elif current_connections_percent > 70:
    print(Fore.YELLOW + '[WARN]\t You are using more than 70% or your connection. Increase max_connections before saturation of connection slots')    

check_current_connections_percent()

def superuser_reserved_connections():
  return int(select_one_value("show superuser_reserved_connections;")[0])

def superuser_reserved_connections_ratio():
  superuser_reserved_connections_ratio=superuser_reserved_connections()*100/max_connections()
  if superuser_reserved_connections() == 0:
    print(Fore.RED + "[ERROR]\t No connection slot is reserved for superuser. In case of connection saturation you will not be able to connect to investigate or kill connections")
  elif superuser_reserved_connections_ratio > 20:
    print(Fore.YELLOW + "[WARN]\t {0} of connections are reserved for super user. This is too much and can limit other users connections".format(superuser_reserved_connections_ratio))
  else:
    print(Fore.GREEN + "[INFO]\t {0} are reserved for super user connection ({1})%".format(superuser_reserved_connections(),superuser_reserved_connections_ratio))

superuser_reserved_connections_ratio()

def average_connection_age():
  return int(select_one_value("select extract(epoch from avg(now()-backend_start)) as age from pg_stat_activity;")[0])

def convert_time(sec): 
    td = datetime.timedelta(seconds=sec) 
    return td.seconds/3600, (td.seconds/60)%60, td.seconds%60

average_connection_seconds=average_connection_age()

def check_average_connection_age(seconds):
  h,m,s = convert_time(average_connection_age())
  print(Fore.GREEN + '[INFO]\t Average connection age : {0:2.0f}h {1:2.0f}m {2:2.0f}s'.format(h,m,s))
  if seconds < 60:
    print(Fore.RED + "[WARN]\t Average connection age is less than 1 minute. Use a connection pooler to limit new connection/seconds")
  elif seconds < 600:
    print(Fore.YELLOW + "[WARN]\t Average connection age is less than 10 minutes. Use a connection pooler to limit new connection/seconds")

check_average_connection_age(average_connection_seconds)

print_header_2('Memory usage');

def work_mem():
  try:
   cur.execute("show work_mem;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  return cur.fetchone()[0]

work_mem_total=convert_to_byte(work_mem())*WORK_MEM_PER_CONNECTION_PERCENT/100*max_connections();
print(Fore.GREEN + "[INFO]\t configured work_mem {0}".format(work_mem()))
print(Fore.GREEN + "[INFO]\t Using an average ratio of work_mem buffers by connection of {0}% (require from WORK_MEM_PER_CONNECTION_PERCENT in script)".format(WORK_MEM_PER_CONNECTION_PERCENT))
print(Fore.GREEN + "[INFO]\t total work_mem (per connection): {0}".format(format_bytes(convert_to_byte(work_mem())*WORK_MEM_PER_CONNECTION_PERCENT/100)))

def shared_buffers():
  try:
   cur.execute("show shared_buffers;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  return cur.fetchone()[0]

print(Fore.GREEN + "[INFO]\t shared_buffers: {0}".format(shared_buffers()));

def autovacuum_max_workers():
  return int(select_one_value("show autovacuum_max_workers;")[0])

def max_worker_processes():
  return int(select_one_value("show max_worker_processes;")[0])

max_processes = max_connections() + autovacuum_max_workers()

if POSTGRESQL_VERSION_MAJOR_CURRENT >= '9.4':
  max_processes = max_processes + max_worker_processes()

print(Fore.GREEN + "[INFO]\t Track activity reserved size : " + str(max_processes))

def track_activity_query_size():
  return int(select_one_value("show track_activity_query_size;")[0])

track_activity_size = track_activity_query_size()*max_processes

def maintenance_work_mem():
  try:
   cur.execute("show maintenance_work_mem;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  return cur.fetchone()[0]

maintenance_work_mem_total = convert_to_byte(maintenance_work_mem()) * autovacuum_max_workers()

if convert_to_byte(maintenance_work_mem()) <= 64*1024*1024:
  print(Fore.YELLOW + "[WARN]\t maintenance_work_mem {0} is less or equal default value. Increase it to reduce maintenance tasks time".format(maintenance_work_mem()))
else:
  print(Fore.GREEN + "[INFO]\t maintenance_work_mem = {0}".format(maintenance_work_mem()))

max_memory=convert_to_byte(shared_buffers())+work_mem_total+maintenance_work_mem_total+track_activity_size

temp_variable1 = max_connections()*convert_to_byte(work_mem())*WORK_MEM_PER_CONNECTION_PERCENT/100
temp_variable2 = format_bytes(autovacuum_max_workers() * convert_to_byte(maintenance_work_mem()))

print(Fore.WHITE + "\t\t Max memory usage:")
print(Fore.WHITE + "\t\t shared_buffers ({0})".format(shared_buffers()))
print(Fore.WHITE + "\t\t + max_connections * work_mem * average_work_mem_buffers_per_connection ", end='')
print(Fore.WHITE + "({0}*{1}*{2}/100 = {3})".format(max_connections(),
  format_bytes(convert_to_byte(work_mem())),WORK_MEM_PER_CONNECTION_PERCENT,format_bytes(temp_variable1)))
print(Fore.WHITE + "\t\t + autovacuum_max_workers * maintenance_work_mem ", end='')
print(Fore.WHITE + "({0}*{1} = {2})".format(autovacuum_max_workers(),maintenance_work_mem(),temp_variable2))
print(Fore.WHITE + "\t\t + track activity size ", end='')
print(Fore.WHITE + "({0})".format(format_bytes(track_activity_size)))

def effective_cache_size():
  try:
   cur.execute("show effective_cache_size;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  return cur.fetchone()[0]

print(Fore.GREEN + "[INFO]\t effective_cache_size: {0}".format(effective_cache_size()));

def all_databases_size():
  try:
   cur.execute("select sum(pg_database_size(datname)) from pg_database;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  return cur.fetchone()[0]

print(Fore.GREEN + "[INFO]\t Size of all databases : {0}".format(format_bytes(int(all_databases_size()))))

shared_buffers_usage = int(all_databases_size())/convert_to_byte(shared_buffers())
if shared_buffers_usage < 0.7:
  print(Fore.YELLOW + "[WARN]\t shared_buffer is too big for the total databases size, memory is lost")

percent_postgresql_max_memory = max_memory*100./mem.total
print(Fore.BLUE + "[INFO]\t PostgreSQL maximum memory usage: {0:.2f}%".format(percent_postgresql_max_memory) + " of system RAM")

if percent_postgresql_max_memory > 100:
  print(Fore.RED + "BAD: Max possible memory usage for PostgreSQL is more than system total RAM. Add more RAM or reduce PostgreSQL memory")
elif percent_postgresql_max_memory > 80:
  print(Fore.YELLOW + "[WARN]\t Max possible memory usage for PostgreSQL is more than 90% of system total RAM.")
elif percent_postgresql_max_memory < 60:
  print(Fore.YELLOW + "[WARN]\t Max possible memory usage for PostgreSQL is less than 60% of system total RAM. On a dedicated host you can increase PostgreSQL buffers to optimize performances.")
else:
  print(Fore.GREEN + "[INFO]\t Max possible memory usage for PostgreSQL is good")

track_activity_ratio = track_activity_size*100/mem.total
if track_activity_ratio > 1:
  print(Fore.YELLOW + "Track activity reserved size is more than 1% of your RAM")
  print(Fore.YELLOW + "track_activity","low","Your track activity reserved size is too high. Reduce track_activity_query_size and/or max_connections")

percent_mem_usage=(max_memory + convert_to_byte(effective_cache_size()))*100/mem.total
print(Fore.BLUE + "max memory+effective_cache_size is {0:.2f}%".format(percent_mem_usage) + " of total RAM")

if percent_mem_usage < 60 and shared_buffers_usage > 1:
  print(Fore.YELLOW + "Increase shared_buffers and/or effective_cache_size to use more memory")
elif percent_mem_usage > 90:
  print(Fore.YELLOW + "the sum of max_memory and effective_cache_size is too high, the planer can find bad plans if system cache is smaller than expected")  

def log_min_duration_statement():
  try:
   cur.execute("show log_min_duration_statement;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  return cur.fetchone()[0]

## Logs
print_header_2('Logs');

if log_min_duration_statement() == '-1':
  print(Fore.YELLOW + "[WARN]\t log of long queries is desactivated. It will be more difficult to optimize query performances")
elif log_min_duration_statement < 1000:
  print(Fore.RED + "[BAD]\t log_min_duration_statement=" + log_min_duration_statement() + ": all requests of more than 1 sec will be written in log. It can be disk intensive (I/O and space)")
else:
  print(Fore.GREEN + "[INFO]\t long queries will be logged")

# log_statement
log_statement=get_setting('log_statement')
if log_statement == 'all':
  print(Fore.RED + "[BAD]\t log_statement=all : this is very disk intensive and only usefull for debug")
elif log_statement == 'mod':
  print(Fore.YELLOW + "[WARN]\t log_statement=mod : this is disk intensive")
else:
  print(Fore.GREEN + "[INFO]\t log_statement = " + log_statement)

## Autovacuum
print_header_2('Autovacuum');

if get_setting('autovacuum') == 'on':
  print(Fore.GREEN + "[INFO]\t autovacuum is activated")
  autovacuum_max_workers = get_setting('autovacuum_max_workers')
  print(Fore.GREEN + "[INFO]\t autovacuum_max_workers: " + autovacuum_max_workers)
else:
  print(Fore.RED + "[BAD]:\t autovacuum is not activated. This is bad except if you known what you do.")

## Checkpoint
print_header_2("Checkpoint")
checkpoint_completion_target=float(get_setting('checkpoint_completion_target'))
if checkpoint_completion_target < 0.5:
  print_report_bad("checkpoint_completion_target ({0}) is lower than default (0.5)".format(checkpoint_completion_target))
  add_advice("checkpoint","urgent","Your checkpoint completion target is too low. Put something nearest from 0.8/0.9 to balance your writes better during the checkpoint interval")
elif checkpoint_completion_target >= 0.5 and checkpoint_completion_target <= 0.7:
  print_report_warn("checkpoint_completion_target ({0}) is low".format(checkpoint_completion_target))
  add_advice("checkpoint","medium","Your checkpoint completion target is too low. Put something nearest from 0.8/0.9 to balance your writes better during the checkpoint interval")
elif checkpoint_completion_target >= 0.7 and checkpoint_completion_target <= 0.9:
  print_report_ok("checkpoint_completion_target ({0}) OK".format(checkpoint_completion_target))
elif checkpoint_completion_target > 0.9 and checkpoint_completion_target < 1:
  print_report_warn("checkpoint_completion_target ({0}) is too near to 1".format(checkpoint_completion_target))
  add_advice("checkpoint","medium","Your checkpoint completion target is too high. Put something nearest from 0.8/0.9 to balance your writes better during the checkpoint interval")
else:
  print_report_bad("checkpoint_completion_target too high ({0})".format(checkpoint_completion_target))

## Disk access
print_header_2("Disk access")
fsync=get_setting('fsync')
if fsync == 'on':
  print_report_ok("fsync is on")
else:
  print_report_bad("fsync is off. You can loss data in case of crash")
  add_advice("checkpoint","urgent","set fsync to on. You can loose data in case of database crash !")
if get_setting('synchronize_seqscans') == 'on':
  print_report_ok("synchronize_seqscans is on")
else:
  print_report_warn("synchronize_seqscans is off")
  add_advice("seqscan","medium","set synchronize_seqscans to synchronize seqscans and reduce disks I/O")

# WAL / PITR
print_header_2("WAL")
wal_level=get_setting('wal_level')
if wal_level == 'minimal':
  print_report_bad("The wal_level minimal does not allow PITR backup and recovery")
  add_advice("backup","urgent","Configure your wal_level to a level which allow PITR backup and recovery")

## Planner
print_header_2("Planner");
def costs_settings():
  try:
   cur.execute("select name from pg_settings where name like '%cost%' and setting<>boot_val;")
  except psycopg2.Error as e:
   print(Fore.RED + "Error {0}".format(e))
  if cur != None:
    ModifiedCosts = [i[0] for i in cur.fetchall()]
    if len(ModifiedCosts) > 0:
      print_report_warn("some costs settings are not the defaults : " + ', '.join(str(p) for p in ModifiedCosts) + ". This can have bad impacts on performance. Use at your own risks")
    else:
      print_report_ok("costs settings are defaults")

costs_settings()

# Database information
print_header_1("Database information for database {0}".format(args.database));

## Database size
print_header_2("Database size");
sum_total_relation_size=int(select_one_value("select sum(pg_total_relation_size(schemaname||'.'||quote_ident(tablename))) from pg_tables")[0])
print_report_info("Database {0} total size : {1}".format(args.database,format_bytes(sum_total_relation_size)))
sum_table_size=int(select_one_value("select sum(pg_table_size(schemaname||'.'||quote_ident(tablename))) from pg_tables")[0])
sum_index_size=sum_total_relation_size-sum_table_size
table_percent=sum_table_size*100/sum_total_relation_size
index_percent=sum_index_size*100/sum_total_relation_size
print_report_info("Database {0} tables size : {1} ({2}%)".format(args.database,format_bytes(sum_table_size), table_percent))
print_report_info("Database {0} indexes size : {1} ({2}%)".format(args.database,format_bytes(sum_index_size), index_percent))

## Tablespace location
print_header_2("Tablespace location");
if (min_version('9.2')):
  cur.execute("select spcname,pg_tablespace_location(oid) from pg_tablespace where pg_tablespace_location(oid) like (select setting from pg_settings where name='data_directory')||'/%';")
  list_tablespace_in_data_dir = cur.fetchall()
  dict_tablespace_in_data_dir = dict((y, x) for x, y in list_tablespace_in_data_dir)
  if len(list_tablespace_in_data_dir) == 0:
    print_report_ok("No tablespace in PGDATA");
  else:
    print_report_bad("Some tablespaces are in PGDATA : " + ', '.join(path_tablespace for path_tablespace in dict_tablespace_in_data_dir))
    add_advice('tablespaces','urgent','Some tablespaces are in PGDATA. Move them outside of this folder.')
else:
  print_report_unknown("This check is not supported before 9.2")

## Shared buffer usage
print_header_2("Shared buffer hit rate");
### Heap hit rate
shared_buffer_heap_hit_rate = float(select_one_value("select sum(heap_blks_hit)*100/(sum(heap_blks_read)+sum(heap_blks_hit)+1) from pg_statio_all_tables ;")[0])
print_report_info("shared_buffer_heap_hit_rate: {0:.2f}%".format(shared_buffer_heap_hit_rate))
### TOAST hit rate
shared_buffer_toast_hit_rate = float(select_one_value("select sum(toast_blks_hit)*100/(sum(toast_blks_read)+sum(toast_blks_hit)+1) from pg_statio_all_tables ;")[0])
print_report_info("shared_buffer_toast_hit_rate: {0:.2f}%".format(shared_buffer_toast_hit_rate))

# Tidx hit rate
shared_buffer_tidx_hit_rate = float(select_one_value("select sum(tidx_blks_hit)*100/(sum(tidx_blks_read)+sum(tidx_blks_hit)+1) from pg_statio_all_tables ;")[0])
print_report_info("shared_buffer_tidx_hit_rate: {0:.2f}%".format(shared_buffer_tidx_hit_rate))

# Idx hit rate
shared_buffer_idx_hit_rate = float(select_one_value("select sum(idx_blks_hit)*100/(sum(idx_blks_read)+sum(idx_blks_hit)+1) from pg_statio_all_tables ;")[0])
print_report_info("shared_buffer_idx_hit_rate: {0:.2f}%".format(shared_buffer_idx_hit_rate))
if shared_buffer_idx_hit_rate > 99.99:
  print_report_info("shared buffer idx hit rate too high. You can reducte shared_buffer if you need")
elif shared_buffer_idx_hit_rate > 98:
  print_report_ok("Shared buffer idx hit rate is very good")
elif shared_buffer_idx_hit_rate>90:
  print_report_warn("Shared buffer idx hit rate is quite good. Increase shared_buffer memory to increase hit rate")
else:
  print_report_bad("Shared buffer idx hit rate is too low. Increase shared_buffer memory to increase hit rate")

## Indexes
print_header_2("Indexes");
# Invalid indexes
invalid_indexes=select_one_column("select relname from pg_index join pg_class on indexrelid=oid where indisvalid=false")
if len(invalid_indexes) > 0:
  print_report_bad("There are invalid indexes in the database : @Invalid_indexes")
  add_advice("index","urgent","You have invalid indexes in the database. Please check/rebuild them")
else:
  print_report_ok("No invalid indexes")
# Unused indexes
unused_indexes = None
if min_version('9.0'):
  unused_indexes = select_one_column("select indexrelname from pg_stat_user_indexes where idx_scan=0 and not exists (select 1 from pg_constraint where conindid=indexrelid)")
else:
  unused_indexes = select_one_column("select indexrelname from pg_stat_user_indexes where idx_scan=0")
if len(unused_indexes) > 0:
  print_report_warn("Some indexes are unused since last statistics: @Unused_indexes")
  add_advice("index","medium","You have unused indexes in the database since last statistics. Please remove them if they are never use")
else:
  print_report_ok("No unused indexes")

## Procedures 
print_header_2("Procedures");
# Procedures with default cost
default_cost_procs = select_one_column("select n.nspname||'.'||p.proname from pg_catalog.pg_proc p left join pg_catalog.pg_namespace n on n.oid = p.pronamespace where pg_catalog.pg_function_is_visible(p.oid) and n.nspname not in ('pg_catalog','information_schema') and p.prorows<>1000 and p.procost<>10")
if len(default_cost_procs) > 0:
  print_report_warn("Some user procedures does not have custom cost and rows settings : @Default_cost_procs")
  add_advice("proc","low","You have custom procedures with default cost and rows setting. Please reconfigure them with specific values to help the planer")
else:
  print_report_ok("No procedures with default costs")

print_advices()

print(Fore.RESET, end='')

cur.close()
conn.close()

# Check CPU times
cpu_user_percent_list = []
cpu_nice_percent_list = []
cpu_system_percent_list = []
cpu_idle_percent_list = []
cpu_iowait_percent_list = []
cpu_irq_percent_list = []
cpu_softirq_percent_list = []

for i in range(10):
  sum_cpu_times = psutil.cpu_times().user + psutil.cpu_times().nice + psutil.cpu_times().system + psutil.cpu_times().idle + psutil.cpu_times().iowait + psutil.cpu_times().irq + psutil.cpu_times().softirq + psutil.cpu_times().steal + psutil.cpu_times().guest + psutil.cpu_times().guest_nice
  cpu_user_percent_list.append(psutil.cpu_times().user*100/sum_cpu_times)
  cpu_nice_percent_list.append(psutil.cpu_times().nice*100/sum_cpu_times)
  cpu_system_percent_list.append(psutil.cpu_times().system*100/sum_cpu_times)
  cpu_idle_percent_list.append(psutil.cpu_times().idle*100/sum_cpu_times)
  cpu_iowait_percent_list.append(psutil.cpu_times().iowait*100/sum_cpu_times)
  cpu_irq_percent_list.append(psutil.cpu_times().irq*100/sum_cpu_times)
  cpu_softirq_percent_list.append(psutil.cpu_times().softirq*100/sum_cpu_times)


cpu_user_percent_avg = reduce(lambda x, y: x + y, cpu_user_percent_list) / len(cpu_user_percent_list)
cpu_nice_percent_avg = reduce(lambda x, y: x + y, cpu_nice_percent_list) / len(cpu_nice_percent_list)
cpu_system_percent_avg = reduce(lambda x, y: x + y, cpu_system_percent_list) / len(cpu_system_percent_list)
cpu_idle_percent_avg = reduce(lambda x, y: x + y, cpu_idle_percent_list) / len(cpu_idle_percent_list)
cpu_iowait_percent_avg = reduce(lambda x, y: x + y, cpu_iowait_percent_list) / len(cpu_iowait_percent_list)
cpu_irq_percent_avg = reduce(lambda x, y: x + y, cpu_irq_percent_list) / len(cpu_irq_percent_list)
cpu_softirq_percent_avg = reduce(lambda x, y: x + y, cpu_softirq_percent_list) / len(cpu_softirq_percent_list)

if (cpu_user_percent_avg + cpu_nice_percent_avg) > 80:
  print("When the CPU user time usage is above 80%, the user may experience lag. Such high CPU usage indicates insufficient processing power. Either the CPU needs to be upgraded")

if cpu_system_percent_avg > 50:
  print("Warning: Try upgrade/reinstall system, upgrade kernel, check logs, dmesg. If the problem exists in kernel, you should narrow down a problem using a profiler such as OProfile or perf.")

if cpu_iowait_percent_avg > 30:
  print("the processes in state 'D' drive up the load average and are in iowait. Active swapping could do that; so could a bad disk or a hung NFS mount. You should reduce your memory footprint or add RAM, so you swap less. You should also check for bad disks & wires.")

if cpu_irq_percent_avg > 15:
  print("Find CPU with high IRQ using mpstat -P ALL. Check /proc/interrupts on this CPU. Check dmesg this kernel module. Advice: 1) disabling the software that uses that card, and see if the interrupts decrease. 2) removing that card from the system, and unloading the driver, and see if there's improvement. 3) move that card to another slot and see if that helps. 4) check for updated drivers or patches for the software.")

if cpu_softirq_percent_avg > 10:
  print("Try use https://github.com/strizhechenko/netutils-linux - A suite of utilities simplilfying linux networking stack performance troubleshooting and tuning.")

