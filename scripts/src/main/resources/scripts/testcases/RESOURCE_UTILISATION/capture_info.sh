#!/bin/bash
set -ax
# Script to record number of file descriptors, number of threads and list of open files (lsof)
# Writes output to files in /tmp
#
# Usage:
# ./capture_info.sh $1
#
# Args
#   $1 - pid of litpd service
#

if [ "$#" -ne 1 ]; then
    echo "One argument expected - pid of litpd service"
    exit 
fi

# Record number of file descriptors
# And full listing of file descriptors
outputfile_fd=/tmp/log_fd_MS
dir='/proc/'$1/'fd'

date >> $outputfile_fd
cd $dir
num_fd=`ls | wc -l`
echo 'num descriptors:' $num_fd >> $outputfile_fd
ls -ls  >> $outputfile_fd


# Record number of threads - measured in two different ways
outputfile_threads=/tmp/log_threads_MS
dir='/proc/'$1/'task'

cd $dir
num_threads1=`ls | wc -l`

cp /proc/$1/status /tmp/status
num_threads2=`grep Threads /tmp/status | cut -f 2 -d ':'`

date >> $outputfile_threads
echo 'num threads from task directory:' $num_threads1 >> $outputfile_threads
echo 'num threads from status file:' $num_threads2 >> $outputfile_threads

# Record list of open files
outputfile_sockets=/tmp/log_sockets_MS
date >> $outputfile_sockets
/usr/sbin/lsof | grep $1 | grep python >> $outputfile_sockets
num_open_files=`/usr/sbin/lsof | grep $1  | grep python | wc -l`
echo 'num open files from lsof:' $num_open_files >> $outputfile_sockets
