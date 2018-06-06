#!/usr/bin/env python3

# apt install python3-psutil
# apt install python3-pip
# apt-get install python3-psycopg2
# apt-get install python3-packaging
# pip3 install procfs
# pip3 install coloredlogs

POSTGRESQL_VERSION_MAJOR_LATEST='10'
POSTGRESQL_VERSION_MINOR_LATEST_10='10.4'
POSTGRESQL_VERSION_MINOR_LATEST_96='9.6.9'
POSTGRESQL_VERSION_MINOR_LATEST_95='9.5.13'
POSTGRESQL_VERSION_MINOR_LATEST_94='9.4.18'
POSTGRESQL_VERSION_MINOR_LATEST_93='9.3.23'

#import psutil
import platform
import re
import subprocess
import psycopg2
from packaging import version
import logging
import coloredlogs
import os

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



proc_sys_block = [os.listdir('/sys/block')][0]
exclude_sys_block = ('loop', 'sr0')
used_sys_block = [x for x in proc_sys_block if not x.startswith(exclude_sys_block)]
print('used_sys_block', used_sys_block)

dmesg_output = subprocess.check_output('dmesg',shell=True)
hypervisor = set(re.findall(r'vmware|kvm|xen|vbox|hyper-v', dmesg_output.decode('utf-8')))
if len(hypervisor) > 1:
  logging.error("hypervisor in dmesg more 1")
elif len(hypervisor) == 1:
  print("Check scheduler")
else:
  print("Running on physical machine")


def get_int_proc(path_of_proc):
    try:
      with open(path_of_proc, 'r') as f:
        int_proc = int(f.readline().split()[0])
        return(int_proc)
    except IOError as e:
        print('ERROR: %s' % e)
        logging.error("Error {0}".format(e))

overcommit_memory = get_int_proc('/proc/sys/vm/overcommit_memory')
if overcommit_memory != 2:
  logging.info("overcommit_memory: {0}".format(overcommit_memory))
  logging.info("""Memory overcommitment is allowed on the system. 
    This can lead to OOM Killer killing some PostgreSQL process,
    which will cause a PostgreSQL server restart (crash recovery)""")
  logging.info("""set vm.overcommit_memory=2 in /etc/sysctl.conf and run sysctl -p to reload it. 
    This will disable memory overcommitment and avoid postgresql killed by OOM killer.""")

overcommit_ratio = get_int_proc('/proc/sys/vm/overcommit_ratio')
if overcommit_ratio <= 50:
  logging.info("overcommit_ratio: {0}".format(overcommit_ratio))
  logging.info("""vm.overcommit_ratio is too small, 
    you will not be able to use more than $overcommit_ratio*RAM+SWAP for applications""")
elif overcommit_ratio >= 90:
  logging.info("overcommit_ratio: {0}".format(overcommit_ratio))
  logging.info("vm.overcommit_ratio is too high, you need to keep free space for the kernel")

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

try:
 cur.execute("SELECT version();")
except psycopg2.Error as e:
 logging.error("I am unable run query SELECT version();")

postgresql_version=cur.fetchone()[0].split(' ')[1]
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

# logging.debug("This is a debug message")
# logging.info("Informational message")
# logging.error("An error has happened!")

try:
 cur.execute("select usename from pg_shadow where passwd='md5'||md5(usename||usename);")
except psycopg2.Error as e:
 logging.error("I am unable run query select usename from pg_shadow where passwd='md5'||md5(usename||usename)")

if cur != None:
  for k in cur:
    logging.error("some users account have the username as password : {0}".format(k[0]))

cur.close()
conn.close()
