#!/usr/bin/env python

import psutil
import platform
import sysctl

mem = psutil.virtual_memory()
print( 'OS total memory     : {0} MB'.format(round(mem.total / 1024**2, 0)))
print( 'system              : {0}'.format(platform.system()))
print( 'node                : {0}'.format(platform.node()))
print( 'release             : {0}'.format(platform.release()))
print( 'version             : {0}'.format(platform.version()))
print( 'machine             : {0}'.format(platform.machine()))
print( 'processor           : {0}'.format(platform.processor()))
print( 'dist                : {0}'.format(platform.dist()))
print( 'linux_distribution  : {0}'.format(platform.linux_distribution()))

vm.overcommit_memory = sysctl.filter('vm.overcommit_memory')[0]
print(vm.overcommit_memory)