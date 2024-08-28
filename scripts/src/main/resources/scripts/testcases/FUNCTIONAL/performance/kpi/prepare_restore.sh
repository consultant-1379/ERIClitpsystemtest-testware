#!/bin/bash


# This script measures the time for prepare_restore operation
#
# Sample Command
#
# sh prepare_restore.sh
#


# Function which checks if a snapshot exists
function check_for_snapshot() {

   check_snap="litp show -p /snapshots/snapshot"
   echo $check_snap
   snap_out=$($check_snap)
   rc=$?
   echo $snap_out
}



main() { 
date

echo "Ensure that there is a snapshot on the system"
check_for_snapshot

if [ $rc -ne 0 ]; then
 echo "No snapshot exists. Run create snapshot"
 create_snap="litp create_snapshot"
 echo $create_snap
 snapped=$($create_snap)
 sleep 40s
fi

while [ $rc -ne 0 ]
do
 check_for_snapshot
 sleep 5s
done


echo "Now run prepare restore"
prepare_res="litp prepare_restore"
echo $prepare_res
out=$(time ($prepare_res)  2>&1 1>/dev/null)
rc=$?

if [ $rc -ne 0 ]; then
  echo "ERROR : prepare_restore failed with return code $rc, the command returned : $out"
else
  echo $out
  cmd_time=$(echo $out | awk '{print $2}')
  echo "Time for prepare_restore is $cmd_time"
fi
}

#### do not execute the code if we are being asked to source only ##
if [ "${1}" != "--source-only" ]; then

  main "${@}" 

fi 

