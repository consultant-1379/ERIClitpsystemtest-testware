#!/bin/bash

# script to extract uptime from top output
#
# # Usage:
# ./extract.uptime.cpu.top.sh 
#
# # Output
# output written to comma separated file
#

# grep for top line of info
grep "load average" log_top_CPU_MS > MS.date.extracted.top.extracted.txt

# cut out uptime
cut -c18-25 MS.date.extracted.top.extracted.txt > MS.date.extracted.top.extracted.csv


