#!/bin/bash

# script to extract vsz, res, cpu and %MEM from file of batch top info
# output is sent to new csv files
#
# # Usage:
# ./extract.pid.fromtop.sh $1
#
# Args
#   $1 - pid or process name
#

if [ "$#" -ne 1 ]; then
    echo "One argument expected - pid or process name"
    exit 
fi


# input pid or process name
echo "extracting info for" $1

# grep for pid in top file

grep $1 log_top_MS  > extracted.top.txt

# cut out vsz from top
cut -c23-28 extracted.top.txt > $1.vsz.extracted.top.csv

# cut out res from top
cut -c29-33 extracted.top.txt > $1.res.extracted.top.csv

# cut out cpu from top
cut -c41-45 extracted.top.txt > $1.cpu.extracted.top.csv

# cut out %MEM from top
cut -c46-51 extracted.top.txt > $1.mem.extracted.top.csv

