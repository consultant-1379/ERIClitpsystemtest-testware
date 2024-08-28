#!/bin/bash

# Assumption is that the package/tarball had been scp'd from .30 to /tmp
# This will be added to the script later.

# Sample Commands
#
# sh import.sh iso ERICenm_CXP9027091-1.10.57.iso
# sh import.sh rpm java-1.6.0-openjdk-1.6.0.0-1.41.1.10.4.el6.x86_64.rpm
# sh import.sh tarball ERICrhel_CXP9026826-3.0.5.tar.gz
#


media=$1
name=$2
os_path=/var/www/html/6/updates/x86_64/Packages/

function check_litp_availability() {

  show_item=$(litp show -p /ms)
  ready=$?
}


echo "Entering arguments $1 , $2"

if [ $1 = "rpm" ]; then

  echo "#### Import an RPM #####"
  cmd="litp import $2 3pp"

elif [ $1 = "tarball" ]; then

  echo "#### Import an OS Tarball #####"
  /bin/tar -xvzf $2 --directory /tmp/kpi/ > untar_log.out
  # Note : need code to extract the 3.0.5 from name
  # Hardcoded for now
  cmd="litp import /tmp/kpi/RHEL/RHEL6_6.z-3.0.5/packages $os_path"

elif [ $1 = "iso" ]; then

  echo "### Import an ISO ###"
  
  # make a mount dirctory 
  newdir="mkdir /mnt3"
  echo $newdir
  out=$($newdir)

  # mount the iso into this directory
  mount="mount $2 /mnt3 -o loop"
  echo $mount
  out=$($mount)

  # Run import_iso
  cmd="litp import_iso /mnt3"

else

  echo "Only option rpm, tarball or iso is supported"
  exit

fi

echo $cmd
d=$(date +%T)
echo "Start Time : $d"
import=$(time ($cmd)  2>&1 1>/dev/null)
rc=$?

if [ $rc -ne 0 ]; then
  echo "ERROR : import command failed with return code $rc, the command returned : $import"

elif [ $1 = "iso" ]; then

  # wait for at least 4 mins before checking if litp is out of maintenance mode
  # expected time for completion is over 4 mins
  sleep 240
  check_litp_availability
  while [ $ready -ne 0 ] 
  do
    check_litp_availability
    sleep 20
  done

  # Check messages log for the completion time and measure against the start time 
  check_messages=$(grep 'INFO: ISO Importer is finished, exiting with 0' /var/log/messages | tail -1)

  count=$(echo $check_messages |grep -o 'INFO: ISO Importer is finished, exiting with 0' | wc -l)
  if [[  $count != 1 ]]; then
    echo "ERROR: The string 'INFO: ISO Importer is finished, exiting with 0' was found $count times in /var/log/messages. Cannot determine completion time."
  else
    echo "Log indicating end of operation: $check_messages"
    completed=$(echo $check_messages | awk '{print $3}')
    echo "Completion Time: $completed"

    begin=$(date -d "$d" +"%s")
    end=$(date -d "$completed" +"%s")

    duration=$(date -d "0 $end sec - $begin sec" +"%M:%S")
    echo "Import ISO operation took $duration"
  fi

else

  echo $import
  importtime=$(echo $import | awk '{print $2}')
  echo "Time for importing of $1 is $importtime"

fi
