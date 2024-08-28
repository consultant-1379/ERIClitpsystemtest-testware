#!/bin/bash
set -x

# basic script to repeat create and remove of snapshots
# usage: nohup sh ./repeat.snapshots.sh &


# function which returns once plan has successfully completed
function plan_successful() {

    litp show_plan | tail -1 |  grep "Successful"
    RETVAL=$?
    until [ $RETVAL -eq 0 ]; do
       sleep 15 
       litp show_plan | tail -1 |  grep "Successful"
       RETVAL=$?   
    done

}

mkdir $HOME/keep_last_known_config
c=1

while true
do

  date

  litp create_snapshot
  plan_successful

  litp create_snapshot -n soak
  plan_successful

  # Store last known config
  cp /var/lib/litp/core/model/LAST_KNOWN_CONFIG $HOME/keep_last_know_config/LAST_KNOWN_CONFIG.$c.1
  cp /var/lib/litp/core/model/LAST_SUCCESSFUL_PLAN_MODEL $HOME/keep_last_know_config/LAST_SUCCESSFUL_PLAN_MODEL.$c.1
  cp /var/lib/litp/core/model/SNAPSHOT_PLAN_snapshot $HOME/keep_last_know_config/SNAPSHOT_PLAN_snapshot.$c.1

  litp remove_snapshot -n soak
  plan_successful

  litp remove_snapshot
  plan_successful

  # Store last known config
  cp /var/lib/litp/core/model/LAST_KNOWN_CONFIG $HOME/keep_last_know_config/LAST_KNOWN_CONFIG.$c.2
  cp /var/lib/litp/core/model/LAST_SUCCESSFUL_PLAN_MODEL $HOME/keep_last_know_config/LAST_SUCCESSFUL_PLAN_MODEL.$c.2
  cp /var/lib/litp/core/model/SNAPSHOT_PLAN_snapshot $HOME/keep_last_know_config/SNAPSHOT_PLAN_snapshot.$c.2

  c=$((c+1))

done 
