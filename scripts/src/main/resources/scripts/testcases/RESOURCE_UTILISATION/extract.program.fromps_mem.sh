#!/bin/bash

# script to extract memory from ps_mem.py output for a given program
#
# # Usage:
# ./extract.program.fromps_mem.sh $1
#
# Args
#   $1 - program name
#

if [ "$#" -ne 1 ]; then
    echo "One argument expected - program name"
    exit 
fi

# input program name
echo "extracting info for" $1

# grep for name in top file
grep $1 log_ps_mem_MS  > extracted.ms_mem.txt

# cut out memory
cut -c24-30 extracted.ms_mem.txt > $1.extracted.ms_mem.csv



