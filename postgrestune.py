#!/usr/bin/env python3

#apt install python3-psutil
#apt install python3-pip

#import psutil
import platform
import re
import subprocess
import psycopg2

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


# test_variable = subprocess.check_output('dmesg',shell=True)
# result = re.findall(r'vmware|kvm|xen|vbox|hyper-v', test_variable)
# print(result)



try:
    conn=psycopg2.connect(
 	database="template1",
  	user="postgres",
  	host="/var/run/postgresql/",
  	)
except:
    print("I am unable to connect to the database")