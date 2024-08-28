#!/bin/bash

# script to extract date from resource utilisation logs

# # Usage:
# ./extract.time.sh 
#
# # Output
# output written to comma separated files
#

# grep for date in top file
grep -e "GMT" -e "IST" log_top_MS > MS.date.extracted.top.csv 
grep -e "GMT" -e "IST" log_ps_mem_MS > MS.date.extracted.mem.csv 
grep -e "GMT" -e "IST" log_free_MS > MS.date.extracted.free.csv 

grep -e "GMT" -e "IST" log_top_SC1 > SC1.date.extracted.top.csv 
grep -e "GMT" -e "IST" log_ps_mem_SC1 > SC1.date.extracted.mem.csv 
grep -e "GMT" -e "IST" log_free_SC1 > SC1.date.extracted.free.csv 

grep -e "GMT" -e "IST" log_top_SC2 > SC2.date.extracted.top.csv 
grep -e "GMT" -e "IST" log_ps_mem_SC2 > SC2.date.extracted.mem.csv 
grep -e "GMT" -e "IST" log_free_SC2 > SC2.date.extracted.free.csv 


