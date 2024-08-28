#!/bin/bash
##################
#
# This script will measure the time taken to perform the create and remove snapshot operations
#
# Sample Commands
#
# sh snapshot.sh 
#
#

. /tmp/kpi/prepare_restore.sh --source-only



date
# enable debug logging in litp
litp update -p /litp/logging -o force_debug=true

# Function which creates a snapshot
function create_snapshot() {

   echo "#### RUN CREATE SNAPSHOT ####"
   d=$(date +%T)
   echo $d
   create_snap="litp create_snapshot"
   echo $create_snap
   run_createsnap=$($create_snap)
   rc=?
   echo $run_createsnap

}

# Function which removes a snapshot
function remove_snapshot() {

   echo "#### RUN REMOVE SNAPSHOT ####"
   d=$(date +%T)
   echo $d
   remove_snap="litp remove_snapshot"
   echo $remove_snap
   run_removesnap=$($remove_snap)
   rc=$?
   echo $run_removesnap
}

# Function which checks if the snapshot plan has completed
function check_snapshot_plan() {

  show_plan="litp show_plan -a"
  echo $show_plan
  do_check=$($show_plan |grep Status)
  echo $do_check
  
  if [[ $do_check == *"Successful"* ]]; then 
    echo "snapshot plan is successful"
    done=true
 
  elif [[ $do_check == *"Failed"* ]]; then
    echo "snapshot plan has failed"
    exit

  else 
    echo "snapshot plan is still running"
    done=false
 fi 
}

echo "Check if there is a snapshot on the system"
check_for_snapshot

if [ $rc -ne 0 ]; then
 echo "No snapshot exists. Run create snapshot"
 create_snapshot
else 
 echo "Snapshot exists. Run remove_snapshot"
 remove_snapshot
fi

# Wait for Snapshot plan to progress
echo "Waiting for snapshot plan to run......."
sleep 30s

# Check if the snapshot plan has been completed successfully :
done=false
while [ $done = 'false' ]
do
 check_snapshot_plan
 sleep 10s
done

# Check messages log for the completion time and measure against the start time 
check_messages=$(grep 'INFO:  Plan execution successful' /var/log/messages | tail -1)
count=$(echo "$check_messages" |grep -o 'INFO:  Plan execution successful' | wc -l)
if [[  $count != 1 ]]; then
  echo "ERROR: The string 'INFO:  Plan execution successful' was found $count times in /var/log/messages. Cannot determine completion time."
else
  echo $check_messages
  completed=$(echo $check_messages | awk '{print $3}')
  echo $completed

  begin=$(date -d "$d" +"%s")
  end=$(date -d "$completed" +"%s")

  duration=$(date -d "0 $end sec - $begin sec" +"%M:%S")
  echo "Snapshot operation took $duration"
fi


# Disable debug logging
litp update -p /litp/logging -o force_debug=false

