#!/bin/bash
set -x
# Resume soak test
#
# Resumes a plan 500 times
# It will fail each time
# Then removes invalid item and recreates and reruns plan
#  final plan is expected to pass
#
# Usage:
# nohup ./repeat.resume.sh &

# function which returns once plan has successfully completed
function plan_successful() {

    litp show_plan | tail -1 |  grep "Successful"
    RETVAL=$?
    until [ $RETVAL -eq 0 ]; do
       sleep 2 
       litp show_plan | tail -1 |  grep "Successful"
       RETVAL=$?   
    done
}

# function which returns once plan has FAILED
function plan_failed() {

    litp show_plan | tail -1 |  grep "Failed"
    RETVAL=$?
    until [ $RETVAL -eq 0 ]; do
       sleep 2 
       litp show_plan | tail -1 |  grep "Failed"
       RETVAL=$?   
    done
}

litp update -p /deployments/d1/clusters/c1/nodes/n2/configs/sysctl/params/sysctl_enm4 -o value="Ak1core.%e.pid%p.usr%u.sig%s.tim%t"
litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_enm4 -o value="Ak1core.%e.pid%p.usr%u.sig%s.tim%t"
litp create -t sysparam -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_wrong -o  key="fs.wrong" value="26289444"
litp create_plan
litp show_plan
litp run_plan

for (( c=1; c<=500; c++ ))
do

  date
  litp version --all

  # call function which waits for plan to fail
  plan_failed

  # resume plan
  litp run_plan --resume
  litp show_plan

  sleep 20
done 

litp remove -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_wrong
litp create_plan
litp run_plan --resume
plan_successful

echo "Test passed"





