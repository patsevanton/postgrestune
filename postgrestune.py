#!/usr/bin/env python3

# apt install python3-psutil
# apt install python3-pip
# apt-get install python3-psycopg2
# apt-get install python3-packaging

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
from procfs import Proc

coloredlogs.install()
proc = Proc()

logging.basicConfig(level=logging.INFO)

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


test_variable = subprocess.check_output('dmesg',shell=True)
result = re.findall(r'vmware|kvm|xen|vbox|hyper-v', test_variable.decode('utf-8'))
print(result)


if vm.overcommit_memory != 100:
  logging.info("Informational message")
if vm.overcommit_ratio !=2 :
  logging.info("""On Linux 2.6 and later, it is possible to modify the kernel's behavior so that it will not “overcommit” memory.
  Although this setting will not prevent the OOM killer from being invoked altogether, 
  it will lower the chances significantly and will therefore lead to more robust system behavior. 
  This is done by selecting strict overcommit mode via sysctl:
  sysctl -w vm.overcommit_memory=2
  """)

try:
  conn=psycopg2.connect(
    database="postgres",
    user="postgres",
  )
except:
  logging.error("I am unable to connect to the database")

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

logging.debug("This is a debug message")
logging.info("Informational message")
logging.error("An error has happened!")

try:
 cur.execute("select usename from pg_shadow where passwd='md5'||md5(usename||usename);")
except psycopg2.Error as e:
 logging.error("I am unable run query select usename from pg_shadow where passwd='md5'||md5(usename||usename)")

if cur != None:
  for k in cur:
    logging.error("some users account have the username as password : {0}".format(k[0]))

cur.close()
conn.close()
