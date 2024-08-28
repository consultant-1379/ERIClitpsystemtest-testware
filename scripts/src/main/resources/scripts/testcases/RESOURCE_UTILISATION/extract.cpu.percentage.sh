#!/bin/bash

# script to extract CPU stats from header of top output.
# extracts:
# percentage CPU idle
# percentage CPU used by system processes
# percentage CPU used by user processes
# percentage CPU time spent in wait
# percentage CPU time spent on niced processes
#
# # Usage:
# ./extract.cpu.percentage.sh 
#
# # Output
# output written to comma separated files
#
# TODO - would be more robust if it used tokens rather than columns


grep "%id" log_top_CPU_SC2 > cpu.stats.txt
cut -c35-39 cpu.stats.txt > SC2_cpu.idle.csv
cut -c9-12 cpu.stats.txt > SC2_cpu.user.csv
cut -c19-21 cpu.stats.txt > SC2_cpu.system.csv
cut -c45-48 cpu.stats.txt > SC2_cpu.wait.csv
cut -c26-30 cpu.stats.txt > SC2_cpu.nice.csv

grep "%id" log_top_CPU_SC1 > cpu.stats.txt
cut -c35-39 cpu.stats.txt > SC1_cpu.idle.csv
cut -c9-12 cpu.stats.txt > SC1_cpu.user.csv
cut -c19-21 cpu.stats.txt > SC1_cpu.system.csv
cut -c45-48 cpu.stats.txt > SC1_cpu.wait.csv
cut -c26-30 cpu.stats.txt > SC1_cpu.nice.csv

grep "%id" log_top_CPU_MS > cpu.stats.txt
cut -c35-39 cpu.stats.txt > MS_cpu.idle.csv
cut -c9-12 cpu.stats.txt > MS_cpu.user.csv
cut -c19-21 cpu.stats.txt > MS_cpu.system.csv
cut -c45-48 cpu.stats.txt > MS_cpu.wait.csv
cut -c26-30 cpu.stats.txt > MS_cpu.nice.csv

