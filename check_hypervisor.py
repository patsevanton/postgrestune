#!/usr/bin/env python

import subprocess
import re

def get_value_proc(path_of_proc):
    try:
      with open(path_of_proc, 'r') as f:
        value_proc = f.readline().split()[0]
        return(value_proc)
    except IOError as e:
        print('ERROR: %s' % e)
        logging.error("Error {0}".format(e))

def used_sys_block():
  proc_sys_block = [os.listdir('/sys/block')][0]
  exclude_sys_block = ('loop', 'sr0')
  used_sys_block = [x for x in proc_sys_block if not x.startswith(exclude_sys_block)]
  print('used_sys_block', used_sys_block)
  return used_sys_block

# https://serverfault.com/questions/693348/what-does-it-mean-when-linux-has-no-i-o-scheduler
def iter_sys_block_scheduler(self):
  for iter_sys_block in self.used_sys_block():
    print('iter_sys_block', iter_sys_block)
    print('/proc/sys/block/' + iter_sys_block + '/queue/scheduler')
    iter_sys_block_scheduler = get_value_proc('/sys/block/' + iter_sys_block + '/queue/scheduler')
    print('iter_sys_block_scheduler', iter_sys_block_scheduler)
    return iter_sys_block_scheduler

dmesg_output = subprocess.check_output('dmesg',shell=True)
hypervisor = set(re.findall(r'vmware|kvm|xen|vbox|hyper-v', dmesg_output.decode('utf-8')))
if len(hypervisor) > 1:
  logging.error("hypervisor in dmesg more 1")
elif len(hypervisor) == 1:
  print("Check scheduler")
else:
  print("Running on physical machine")
