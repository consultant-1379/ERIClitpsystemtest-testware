#!/bin/bash

# simple script to extract total memory used from output of:
#   ps -eo rss | awk '{sum=sum+$1}END{print sum}'
#
# # Usage:
# ./extract.total.usedmem.sh 
#
# # Output
# outputs total used memory to a csv file
#

grep -v GMT log_mem_MS | grep -v IST > extracted.ms_used_mem.csv
grep -v GMT log_mem_SC1 | grep -v IST > extracted.node1_used_mem.csv
grep -v GMT log_mem_SC2 | grep -v IST > extracted.node2_used_mem.csv







