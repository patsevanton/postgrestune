#!/usr/bin/env python
from __future__ import print_function

from colorama import Fore

advices={}
priority_advice = {}

def print_header_1(string):
  print(Fore.WHITE + '===== ' + string + ' =====', end='')
  print(Fore.RESET)

def print_header_2(string):
  print(Fore.WHITE + '----- ' + string + ' -----', end='')
  print(Fore.RESET)

def add_advice(category, priority, advice):
  # print('add_advice:')
  # print('category - {0}, priority - {1}, advice - {2}'.format(category, priority, advice))
  # priority_advice[priority] = advice
  priority_advice.update({priority:advice})
  # print('priority_advice - {0}'.format(priority_advice))
  advices[category] = priority_advice
  # print('advices - {0}'.format(advices))
  for category,priority_advice in advices.iteritems():
    print('category - {0}, priority_advice - {1}'.format(category,priority_advice))
    print_header_2(category);
    for priority,advice in priority_advice.iteritems():
      print('priority - {0}, advice - {1}'.format(priority,advice))
  
def print_advices():
  print()
  print('print_advices:')
  print_header_1("Configuration advices");
  for category,priority_advice in advices.iteritems():
    print('category - {0}, priority_advice - {1}'.format(category,priority_advice))
    print_header_2(category);
    for priority,advice in priority_advice.iteritems():
      print('priority - {0}, advice - {1}'.format(priority,advice))
      if priority == 'urgent':
        print(Fore.RED + priority,advice)
      elif priority == 'medium':
        print(Fore.YELLOW + priority,advice)
      elif priority == 'low':
        print(Fore.MAGENTA + priority,advice)
    print(Fore.RESET, end='')
  print(Fore.RESET, end='')  


add_advice('sysctl','urgent','advice1')
add_advice('sysctl','urgent','advice2')

print_advices()
