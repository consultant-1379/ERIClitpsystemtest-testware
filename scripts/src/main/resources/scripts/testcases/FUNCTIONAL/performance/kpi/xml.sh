#!/bin/bash

# This script measures the time to load an XML deployment file.
#
# An argument can be added to set the number of times this will run.
# An average time is then output.
#
# Sample Commands
#
# sh xml.sh merge 10
# sh xml.sh replace 10
#

date
action=$1
count=$2

if [ "$action" == "merge" ]; then

  echo "performing xml merge"

elif [ "$action" ==  "replace" ]; then

  echo "performing xml replace"
else

  echo "only option merge or replace is supported"
  exit

fi

if [ -z "$2" ];then
  echo "No argument for count provided - setting to 1"
  count=1
fi
#echo "DEBUG: Count is $count"

# ensure debug is disabled for accurate comparison to previous sprints
litp update -p /litp/logging -o force_debug=false


echo "export the deployment"
litp export -p / -f newdep.xml

load="litp load -p / -f newdep.xml --$action"

totaltime=0
for ((c=1;c<=$count;c++));do

  out=$(time ($load)  2>&1 1>/dev/null)
  rc=$?

  if [ $rc -ne 0 ]; then
      echo "ERROR : litpd failed to load XML with return code $rc, the command returned : $out"
      exit
  else
     echo $out
     load_time=$(echo $out | awk '{print $2}')
     echo "Time taken to perform xml $action is $load_time"
     load_time1=$(echo $load_time | tr -d [a-z])
     #echo "DEBUG: stripped is $load_time1"
     totaltime=$(bc <<< "scale=3;$totaltime+$load_time1")
     #echo "DEBUG: Total is $totaltime"

  fi
  avg_loadtime=$(bc <<< "scale=3;$totaltime/$c")
  echo "Average time to perform XML $action is $avg_loadtime seconds"  
  sleep 10

done

