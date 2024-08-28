#!/bin/bash

# This script measures the time for a litpd service restart.
#
# An argument can be added to set the number of times this will run.
# An average time is then output.
#
# Sample Command
#
# sh litpd_restart.sh 10
#

date
count=$1
if [ $# -eq 0 ];then 
  echo "No argument for count provided - setting to 1"
  count=1
fi
#echo "DEBUG: Count is $count"

echo "Restart the litpd service"
restart="/sbin/service litpd restart"
#echo $restart

# ensure debug is disabled for accurate comparison to previous sprints
litp update -p /litp/logging -o force_debug=false


totaltime=0
for ((c=1;c<=$count;c++));do

  out=$(time ($restart)  2>&1 1>/dev/null)
  rc=$?

  if [ $rc -ne 0 ]; then
      echo "ERROR : litpd service failed to restart with return code $rc, the command returned : $out"
      exit
  else
     echo $out
     restart_time=$(echo $out | awk '{print $2}')
     echo "Time taken to restart the litpd service is $restart_time"
     res_time1=$(echo $restart_time | tr -d [a-z])
     #echo "DEBUG: stripped is $res_time1"
     totaltime=$(bc <<< "scale=3;$totaltime+$res_time1")
     #echo "DEBUG: Total is $totaltime"

  fi
  avg_restime=$(bc <<< "scale=3;$totaltime/$c")
  echo "Average time to restart the litpd service is $avg_restime seconds"  
  sleep 30

done

