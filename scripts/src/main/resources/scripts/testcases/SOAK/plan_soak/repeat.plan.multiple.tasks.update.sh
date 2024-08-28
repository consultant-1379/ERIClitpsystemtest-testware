#!/bin/bash
set -x
# Plan soak test hardwired for system .105
#
# Usage:
#  nohup ./repeat.plan.multiple.tasks.update.sh [param1] &
#  param1: if this is true then all litp commands are logged to a text file
#
#
#   Every other plan creates snapshots
#   Every other plan performs operations that can't be done with snaps:
#     On first iteration adds /software to MS model
#     Creates a new MN FS for first 20 iterations
#     Creates two new MS FS for first 20 iterations
#     Increases size of a MS FS for iterations 2-21
#     Increases the size of MN root file system for first 40 iterations
#     Increases the size of SFS file system for first 40 iterations
#     Increases the size of VxVM disks for the first 40 iterations
#     Increases the size of a VxVM FS for the first 40 iterations
#     Increases the size of a MS KS file system for first 40 iterations
#     Increases the size of LVM disks MS and MN for the first 20 iterations
#     Changes snap_size, backup_snap_size and snap_external every other iteration 
#   Changes which prompt a node reboot are only run on every other plan:
#     Updates ipv4 on mgmt network on node2 
#     Updates ipv6 on mgmt network on node1
#   Updates bond params
#   Updates bridge params
#   Removes/adds an interface - taken out 11/05/17 as interface needed for VA SFS mounts - removal of interface not supported anyway
#   Updates ipv4 and ipv6 on vlan on non mgmt on node1
#   Adds/removes SFS managed, SFS unmanaged and NFS mount on node2 
#   Changes ip4vallowed_clients on an export
#   Adds/removes a number of packages on node2
#   Adds/updates/removes aliases - including duplicate aliases
#   Adds/updates/removes sysparams
#   Adds/updates/removes logrotate rules
#   Adds/updates/removes ETHTOOL_OPTS
#   Updates VCS parameters
#   Adds/updates/removes a SG dependency_list
#   Adds/removes trigger items
#   Changes yum-repository from base_url to ms_url_path and back again
#   Updates multicast_snooping
#   Changes the sfs-virtual-server for a nfs-mount
#   Adds/removes LVM FS mount_points
#   Once every 10 plans adds/updates/removes firewalls
#   Updates cleanup_command on service
#   Adds VIPs to services for first 20 iterations
#   Updates critical_service
#   For first 5 plans adds a vxvm physical device
#   Once every 8 plans - removes SG (ricci)
#   Once every 8 plans - adds SG (anseo)
#   Once every 8 plans - adds a new SG VM
#   Once every 8 plans - contracts SG (anseo) node list 
#   Once every 8 plans - contracts SG VM node list 
#   Once every 8 plans - expands SG (anseo) node list 
#   Once every 8 plans - expands SG VM node list
#   Once every 8 plans - removes SG (anseo)
#   Once every 8 plans - removes a SG VM
#   Once every 8 plans - adds SG (ricci)
#   Once every 3 plans - removes MS VM
#   Once every 3 plans - updates MS VM
#   Once every 3 plans - removes MS VM
#   Once every 3 plans - updates MS VM
#   Migrate a SG from one node to another and back 
#   Adds a new VCS clustered_service and deactivates an existing one
#   Adds/removes items from MS and MN VM
#   Changes SG VM image
#   Changes MS VM image
#   Adds/removes vcs-network-host
#   Add SFS Pools at iteration 5 and 10
#   Change default_nic_monitor to mii and then back again every 10 plans
#   Change bond from miinon to arp and back again and update arp params
#   Add, remove and update vm-ram-mount on MS and MN VM
#   Add, remove and update vm-custom-script VMs
#   Generate replacement Config Task 
#   Changes ntp-service on node1.
#   On first iteration - removes pxe_boot_only param and adds eth0 to bond0
#   Updates value of vcs_seed_threshold
#   Once every 10 plans it runs a short plan with no locks
#
#   If flag, failplan_flag, is set then 1 in 5 plans will initially fail and then be resumed
#   If flag, log_flag, is set then all litp commands are logged in a text file
#
#   It also:
#      checks that a new package cannot be created while a plan is running
#      checks that the model cannot be restored while a plan is running
#      changes to maintance mode and back again and checks that a new package cannot be created in maintance mode
#      makes changes and restores the model model
#
# TODO error handling
# TODO remove hardwire of ipaddresses
# TODO seperate out some functions to a different file

# Set to true to initially fail 1 in 5 plans
 failplan_flag=true

EXPECTED_ERROR="Operation not allowed while plan is running"
EXPECTED_MAINTENANCE_ERROR="LITP is in maintenance mode"
EXPECTED_RESTORE_ERROR="Operation not allowed while plan is running"

ipaddress1=10.44.86.108
ipaddress2=10.44.86.107

ext_ipaddress1=10.44.235.130
ext_ipaddress2=10.44.235.141

vlan_ipaddress1=10.44.235.119
vlan_ipaddress2=10.44.235.118

node2_eth1_mac='2C:59:E5:3F:34:EC'
node2_data_ipaddress1=10.44.235.143
node2_data_ipaddress2=10.44.235.142

ms_ipv6_834="fdde:4d7e:d471:0000::0834:105:0100/64"

b0_ip6address1='fdde:4d7e:d471:0001::0835:105:0201/64'
b0_ip6address2='fdde:4d7e:d471:0001::0835:105:0200/64'

b0_v836_ip6address1='fdde:4d7e:d471:0002::0836:105:0200/64'
b0_v836_ip6address2='fdde:4d7e:d471:0002::0836:105:0201/64'
b0_v836_ip4address1='10.44.86.184'
b0_v836_ip4address2='10.44.86.182'

# Intial size of FS
lvm_initial_size=8204
sfs_initial_size=300
vxvm_initial_size=500
vxvm_disk_initial_size=21000
ks_varlog_initial_size=20
ms_lvm_disk_initial_size=565400
mn_lvm_disk0_initial_size=28672
mn_lvm_disk1_initial_size=10280

#vxvm
hd_vxvm_soak[1]=6006016011602d00021ec5c47256e511
hd_vxvm_soak[2]=6006016011602d00aea94ad57256e511
hd_vxvm_soak[3]=6006016011602d008a03b3eb7256e511
hd_vxvm_soak[4]=6006016011602d00f40c94fb7256e511
hd_vxvm_soak[5]=6006016011602d00e62e0c0b7356e511


traf1_vip[1]="10.19.105.108"
traf1_vip[2]="10.19.105.109"
traf1_vip[3]="10.19.105.110"
traf1_vip[4]="10.19.105.111"
traf1_vip[5]="10.19.105.112"
traf1_vip[6]="10.19.105.113"
traf1_vip[7]="10.19.105.114"
traf1_vip[8]="10.19.105.115"

traf1_vip_ipv6[1]="fdde:4d7e:d471:19::105:108/64"
traf1_vip_ipv6[2]="fdde:4d7e:d471:19::105:109/64"
traf1_vip_ipv6[3]="fdde:4d7e:d471:19::105:110/64"
traf1_vip_ipv6[4]="fdde:4d7e:d471:19::105:111/64"
traf1_vip_ipv6[5]="fdde:4d7e:d471:19::105:112/64"
traf1_vip_ipv6[6]="fdde:4d7e:d471:19::105:113/64"
traf1_vip_ipv6[7]="fdde:4d7e:d471:19::105:114/64"
traf1_vip_ipv6[8]="fdde:4d7e:d471:19::105:115/64"

traf2_vip[1]="10.20.105.108"
traf2_vip[2]="10.20.105.109"
traf2_vip[3]="10.20.105.110"
traf2_vip[4]="10.20.105.111"

ms_vm2_net1_1="10.46.85.4"
ms_vm2_ipv6_834_1="fdde:4d7e:d471:0000::0834:105:0102/64"

ms_vm2_net1_2="10.46.85.5"
ms_vm2_ipv6_834_2="fdde:4d7e:d471:0000::0834:105:0103/64"

ms_vm2_net2="10.46.85.66"
ms_vm2_net3="10.46.85.132"
ms_vm2_net4="10.46.85.195"

ms_vm1_ipv6_834_1="fdde:4d7e:d471:0000::0834:105:0101/64"
ms_vm1_net1_1="10.46.85.3"
ms_vm1_mgmt_1="10.44.86.109"
ms_vm1_ipv6_mgmt_1="fdde:4d7e:d471:0001::0835:105:0101/64"

VM_net1vm_ip[0]="10.46.85.10"
VM_net1vm_ip[1]="10.46.85.11"

ipv6_834_gateway="fdde:4d7e:d471:0:0:834:0:1"
net1vm_gw="10.46.85.1"

sfs_virt_serv2=10.44.235.32
sfs_network_name=data
sfs_fs_ipv4allowed_clients="10.44.235.111,10.44.235.141,10.44.235.142,10.44.235.143"
sfs_fs1_ipv4allowed_clients1="10.44.235.111,10.44.235.141,10.44.235.142,10.44.235.143"
sfs_fs1_ipv4allowed_clients2="10.44.235.111,10.44.235.141,10.44.235.142"
sfs_fs2_ipv4allowed_clients1="10.44.235.111,10.44.235.141,10.44.235.142,10.44.235.143"
sfs_fs2_ipv4allowed_clients2="10.44.235.111,10.44.235.141,10.44.235.142"


OLD SFS SERVER values
#sfs_virt_serv2=10.44.86.31
#sfs_network_name=mgmt
#sfs_fs3_ipv4allowed_clients="10.44.86.105,10.44.86.106,10.44.86.107,10.44.86.108"
#sfs_fs_ipv4allowed_clients="10.44.86.105,10.44.86.106,10.44.86.107,10.44.86.108"
#sfs_fs1_ipv4allowed_clients1="10.44.86.105,10.44.86.106,10.44.86.107,10.44.86.108"
#sfs_fs1_ipv4allowed_clients2="10.44.86.105,10.44.86.106,10.44.86.107"
#sfs_fs2_ipv4allowed_clients1="10.44.86.105,10.44.86.106,10.44.86.107,10.44.86.108"
#sfs_fs2_ipv4allowed_clients2="10.44.86.105,10.44.86.106,10.44.86.107"

# 
# function which runs litp command
#  if log_flag is set then command is also logged to a text file
#
SOAK_LOG=/tmp/soak_log.csv
function _litp() {
  if [ "$log_flag" = true ]; then
    # We'll log the command before it's run, but let the output go to STDOUT
    echo "$(date +%s.%N), /usr/bin/litp ${@}" &> >(tee -a ${SOAK_LOG})
    /usr/bin/litp "${@}"
  else
    /usr/bin/litp "${@}"
  fi
}


# function which creates and runs a plan which will fail
# it then resumes the plan once - it will fail again
# and then corrects model
function run_failplan() {

  # add a sysparam with an invalid key
  _litp create -t sysparam -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_wrong -o  key="fs.wrong" value="26289444"
  _litp create_plan
  _litp show_plan
  _litp run_plan

  # call function which waits for plan to fail
  plan_failed

  # resume plan
  _litp run_plan --resume
  _litp show_plan
  sleep 30
  # call function which waits for plan to fail
  plan_failed

  _litp remove -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_wrong 

}


# function which attempts an add while plan is running
# this should not be allowed - an error should be returned
function add_while_plan_is_running() {
  stderror_string="$(_litp create -t package -p /software/items/zip -o name=zip 2>&1 > /dev/null)"

  if [[ $stderror_string != *$EXPECTED_ERROR* ]]
  then
    echo "**** Unexpected error on create during plan   *****";
    exit
  fi
}

# function which attempts an create while in maintenance mode
function add_while_plan_in_maintenance() {
  stderror_string="$(_litp create -t package -p /software/items/zip -o name=zip 2>&1 > /dev/null)"

  if [[ $stderror_string != *$EXPECTED_MAINTENANCE_ERROR* ]]
  then
    echo "**** Unexpected error in maintenance mode   *****";
    exit
  fi
}

# function which attempts a restore while plan is running
#  this should not be allowed - an error should be returned
function restore_while_plan_is_running() {
  stderror_string="$(_litp restore_model 2>&1 > /dev/null)"

  if [[ $stderror_string != *$EXPECTED_RESTORE_ERROR* ]]
  then
    echo "**** Unexpected error on restore during plan   *****";
    exit
  fi
}


# function which returns once plan has successfully completed
function plan_successful() {

    _litp show_plan | tail -1 |  grep "Successful"
    RETVAL=$?
    until [ $RETVAL -eq 0 ]; do
       sleep 2 
       _litp show_plan | tail -1 |  grep "Successful"
       RETVAL=$?   
    done
}

# function which returns once plan has FAILED
function plan_failed() {

    _litp show_plan | tail -1 |  grep "Failed"
    RETVAL=$?
    until [ $RETVAL -eq 0 ]; do
       sleep 2 
       _litp show_plan | tail -1 |  grep "Failed"
       RETVAL=$?   
    done
}


# Read command line argument - use it to set log_flag
# If argument is not set or not equal to true then set log_flag to false
if [ "$1" = true ]; then
   log_flag=true
else
   log_flag=false
fi


####################################################
# PREREQ Section
# These items need to be set up for the test to run

# create alias
_litp create -t alias-cluster-config -p /deployments/d1/clusters/c1/configs/alias_config
_litp create -p /deployments/d1/clusters/c1/configs/alias_config/aliases/alias2 -t alias -o alias_names="alias.2" address="10.44.86.106"
_litp create -p /deployments/d1/clusters/c1/configs/alias_config/aliases/alias2_ipv6 -t alias -o alias_names="alias.2.ipv6" address="fdde:4d7e:d471:0001::0835:105:0200"

_litp create -t alias -p /ms/configs/alias_config/aliases/alias2 -o alias_names="alias.2" address="10.44.86.106"
_litp create -t alias -p /ms/configs/alias_config/aliases/alias2_ipv6 -o alias_names="alias.2.ipv6" address="fdde:4d7e:d471:0001::0835:105:0200"
_litp create -t alias -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/alias4 -o alias_names="alias.4" address="10.44.86.106"
_litp create -t alias -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/alias4_ipv6 -o alias_names="alias.4.ipv6" address="fdde:4d7e:d471:0001::0835:105:0200"

# add firewall cluster firewall
_litp create -t firewall-rule -p /deployments/d1/clusters/c1/configs/fw_config/rules/fw_test_update -o name="701 test" dport="1614" 
  
# add firewall config for a node (node1):
_litp create -t firewall-rule -p /deployments/d1/clusters/c1/nodes/n1/configs/fw_config/rules/fw_test_update -o name="201 test" dport="1615" 

# add firwall config for ms
_litp create -t firewall-rule -p /ms/configs/fw_config/rules/fw_test_update -o name="301 test" dport="1616"

# remove sysparams added at install
_litp remove -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_custom
_litp remove -p /deployments/d1/clusters/c1/nodes/n2/configs/sysctl/params/sysctl_custom
_litp remove -p /ms/configs/sysctl/params/sysctl_custom

# Add a new sfs-virtual-server
_litp create -t sfs-virtual-server -p /infrastructure/storage/storage_providers/sfs_service_sp1/virtual_servers/vs2 -o name="virtserv2" ipv4address=${sfs_virt_serv2}

# Add new sfs-filesystem and export and mounts
_litp create -t sfs-filesystem -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl1/file_systems/managed3 -o path="/vx/ST105-managed3" size="40M" snap_size=200 cache_name=105cache1
_litp create -t sfs-export -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl1/file_systems/managed3/exports/ex1 -o  ipv4allowed_clients=${sfs_fs_ipv4allowed_clients} options="rw,no_root_squash" 
_litp create -t nfs-mount -p /infrastructure/storage/nfs_mounts/managed3 -o export_path="/vx/ST105-managed3" provider="virtserv2" mount_point="/SFSmanaged3" mount_options="soft" network_name="${sfs_network_name}"
_litp inherit -p /deployments/d1/clusters/c1/nodes/n2/file_systems/managed3 -s /infrastructure/storage/nfs_mounts/managed3
_litp inherit -p /deployments/d1/clusters/c1/nodes/n1/file_systems/managed3 -s /infrastructure/storage/nfs_mounts/managed3
_litp inherit -p /ms/file_systems/managed3 -s /infrastructure/storage/nfs_mounts/managed3

# Add a new MS VM (RHEL 7 - LITPCDS-12816)
_litp create -t vm-service -p /ms/services/msfmmed2 -o service_name=msfmmed2 image_name=rhel_7 cpus=2 ram=512M internal_status_check=off
_litp create -t vm-network-interface -p /ms/services/msfmmed2/vm_network_interfaces/net1 -o network_name=net1vm device_name=eth0 host_device=brnet1vm ipaddresses=${ms_vm2_net1_1} 
_litp create -t vm-network-interface -p /ms/services/msfmmed2/vm_network_interfaces/net2 -o network_name=834 device_name=eth1 host_device=br1 ipv6addresses=${ms_vm2_ipv6_834} gateway6=${ipv6_834_gateway}
_litp create -t vm-network-interface -p /ms/services/msfmmed2/vm_network_interfaces/net3 -o network_name=net2vm device_name=eth2 host_device=brnet2vm ipaddresses=${ms_vm2_net2}
_litp create -t vm-network-interface -p /ms/services/msfmmed2/vm_network_interfaces/net4 -o network_name=net3vm device_name=eth3 host_device=brnet3vm ipaddresses=${ms_vm2_net3}
_litp create -t vm-network-interface -p /ms/services/msfmmed2/vm_network_interfaces/net5 -o network_name=net4vm device_name=eth4 host_device=brnet4vm ipaddresses=${ms_vm2_net4}
# vm-alias
_litp create -t vm-alias -p /ms/services/msfmmed2/vm_aliases/ms1 -o alias_names="ms1105" address=10.46.85.2
_litp create -t vm-alias -p /ms/services/msfmmed2/vm_aliases/ntp -o alias_names="ntp" address=10.46.86.30
_litp create -t vm-alias -p /ms/services/msfmmed2/vm_aliases/node1 -o alias_names="node1" address=${VM_net1vm_ip[0]}
_litp create -t vm-alias -p /ms/services/msfmmed2/vm_aliases/node2 -o alias_names="node2" address=${VM_net1vm_ip[1]}
_litp create -t vm-alias -p /ms/services/msfmmed2/vm_aliases/ms1_ipv6 -o alias_names="ms1105.ipv6" address="fdde:4d7e:d471:0001::0835:105:0100"
# vm repo
_litp create -t vm-yum-repo -p /ms/services/msfmmed2/vm_yum_repos/repo1 -o name=repo1 base_url="http://ms1105/REPO1"
# vm package
_litp create -t vm-package -p /ms/services/msfmmed2/vm_packages/3pp-irish-hello -o name=3PP-irish-hello 
# vm-disk 
_litp create -t vm-disk -p /ms/services/msfmmed2/vm_disks/vm_disk1 -o host_volume_group=vg1 host_file_system=fs1 mount_point=/vm_data_dir
# key
_litp create -t vm-ssh-key -p  /ms/services/msfmmed2/vm_ssh_keys/support_key1 -o ssh_key="ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAxHQW3vVqhTikufpmOc+4XuJcCVscL4eDi3ahLKuj61tdjfPN0+HF8fJh+4ckpOpttCoZwM1AaBwyZx1H4t1K78E9CBEPwb9ftd57h/eFD9CnPtRIIg1eVEqGNNvhh6tAobEFSAQ1AuBrO5ye+pPGEXlXSb5ZU9ZYYJg4wAhNFlVX6zWCq6BqvzTQ7h4YFK4Bk8ACFOMD10N7rQEo6TVIyzkKoW0/HV61o537YFRav0kw9ZFyqS9jjWtui08GR1yIyhXb2jOiw20B5BnyaG3CR+tBmK6+EXzLVdf2D+3Lpf6nV2X76O5jd4OG5XW0NOOaXbAcqCzPQ39fwwBzgag6Sw== root@Ms1105"


# create new vm-image
litp create -t vm-image -p /software/images/rhel_6_img -o name="rhel_6" source_uri="http://ms1105/images/RHEL_6_image.qcow2"

# Add SG on one node TORF-124980 
_litp create -t vcs-clustered-service -p /deployments/d1/clusters/c1/services/SG_12 -o active=1 standby=0 name=PAR_SG12 online_timeout=50 offline_timeout=110 node_list=n1 
_litp create -t service -p /software/services/SG_12 -o service_name="test-lsb-12"
_litp inherit -p /deployments/d1/clusters/c1/services/SG_12/applications/SG_12 -s /software/services/SG_12
_litp create -t package -p /software/items/testpkg12 -o name=EXTR-lsbwrapper12
_litp inherit -p /software/services/SG_12/packages/pkg12 -s /software/items/testpkg12
_litp create -t ha-service-config -p /deployments/d1/clusters/c1/services/SG_12/ha_configs/config -o clean_timeout=90 startup_retry_limit=10 

# Add SG on one node TORF-128825 
_litp create -t vcs-clustered-service -p /deployments/d1/clusters/c1/services/SG_13 -o active=1 standby=0 name=PAR_SG13 online_timeout=50 offline_timeout=110 node_list=n1 
_litp create -t service -p /software/services/SG_13 -o service_name="test-lsb-13"
_litp inherit -p /deployments/d1/clusters/c1/services/SG_13/applications/SG_13 -s /software/services/SG_13
_litp create -t package -p /software/items/testpkg13 -o name=EXTR-lsbwrapper13
_litp inherit -p /software/services/SG_13/packages/pkg13 -s /software/items/testpkg13
_litp create -t ha-service-config -p /deployments/d1/clusters/c1/services/SG_13/ha_configs/config -o clean_timeout=90 startup_retry_limit=10 

# Set up packages for another new SG TORF-128825
_litp create -t service -p /software/services/SG_13new -o service_name="test-lsb-13"
_litp inherit -p /software/services/SG_13new/packages/pkg13 -s /software/items/testpkg13

# create images
litp create -t vm-image -p /software/images/rhel_7_img -o name="rhel_7" source_uri="http://ms1105/images/RHEL_7_image.qcow2"
/usr/bin/md5sum /var/www/html/images/RHEL_7_image.qcow2 | cut -d ' ' -f 1 > /var/www/html/images/RHEL_7_image.qcow2.md5
/usr/bin/md5sum /var/www/html/images/RHEL_6_image.qcow2 | cut -d ' ' -f 1 > /var/www/html/images/RHEL_6_image.qcow2.md5

# END PREREQ Section
####################################################

file_op_count=0

for (( c=1; c<=10000; c++ ))
do

  date
  litp version --all

  # Set params
  n2=$((c%2))
  n3=$((c%3))
  n4=$((c%4))
  n5=$((c%5))
  n6=$((c%6))
  n8=$((c%8))
  n10=$((c%10))
  n20=$((c%20))

  # Every other plan - create snapshots
  # or perform operations that can only be done without snapshots
  if [ $n2 -eq 1 ]; then

    _litp create_snapshot
    plan_successful
    _litp create_snapshot -n soak
    plan_successful

  else
  
    file_op_count=$((file_op_count+1))

    # On first iteration add remaining KS FS not already modeled - software (TORF-111665)
    if [ $file_op_count -eq 1 ]; then
      _litp create -t file-system -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/software -o type="ext4" mount_point="/software" size="50G" snap_size="5" backup_snap_size="10" snap_external="false"
    fi

    # Create LVM FS - on both MS and MN 
    if [ $file_op_count -lt 20 ]; then
      _litp create -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg1/file_systems/SOAK_VG1_FS$file_op_count -t file-system -o type=ext4 mount_point=/soak_mp_VG1_FS$file_op_count size=20M snap_size=10
      _litp create -t file-system -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/soak_fs$file_op_count -o type="ext4" mount_point=/data1_soak$file_op_count size="20M" snap_size="5" snap_external="false"
    fi

    # Increase size of MS FS
    if [ $file_op_count -gt 2 ] && [ $file_op_count -lt 21 ] ; then
      _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/soak_fs$(($file_op_count-1)) -o size=40M 
    fi

    # Increase the root MN for first 40 iterations with no snapshot
    # Increase the size of a SFS FS for first 40 iterations with no snapshot
    # Increase the size of the VxVM FS for the first 40 iterations with no snapshot
    # Increase the size of the VxVM disks for the first 40 iterations with no snapshot (TORF-107261)
    # Increase the size of a MS KS FS for first 40 iterations with no snapshot (TORF-111665)
    if [ $file_op_count -lt 40 ]; then
      lvm_new_size=$(($lvm_initial_size + $file_op_count*4))
      sfs_new_size=$(($sfs_initial_size + $file_op_count*4))
      vxvm_new_size=$(($vxvm_initial_size + $file_op_count*4))
      vxvm_new_disk_size=$(($vxvm_disk_initial_size + $file_op_count*160))
      ks_varlog_size=$(($ks_varlog_initial_size + $file_op_count))
      _litp update -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg1/file_systems/root -o size="$lvm_new_size"M
      _litp update -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl1/file_systems/managed2 -o size="$sfs_new_size"M
      _litp update -p /infrastructure/storage/storage_profiles/profile_v1/volume_groups/vg_vmvx/file_systems/VXVM_FS_1 -o size="$vxvm_new_size"M 
      _litp update -p /infrastructure/systems/sys2/disks/disk1 -o size="$vxvm_new_disk_size"M
      _litp update -p /infrastructure/systems/sys3/disks/disk1 -o size="$vxvm_new_disk_size"M
      _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/varlog -o size="$ks_varlog_size"G 
    fi

    # Increase size of LVM disks for first 20 iterations with no snapshot (TORF-106941)
    if [ $file_op_count -lt 20 ]; then
      ms_lvm_disk=$(($ms_lvm_disk_initial_size + $file_op_count*4))
      mn_lvm_disk0=$(($mn_lvm_disk0_initial_size + $file_op_count*4))
      mn_lvm_disk1=$(($mn_lvm_disk1_initial_size + $file_op_count*4))
      _litp update -p /infrastructure/systems/sys1/disks/d1 -o size="$ms_lvm_disk"M
      _litp update -p /infrastructure/systems/sys2/disks/boot0 -o size="$mn_lvm_disk0"M
      _litp update -p /infrastructure/systems/sys2/disks/boot1 -o size="$mn_lvm_disk1"M
      _litp update -p /infrastructure/systems/sys3/disks/boot0 -o size="$mn_lvm_disk0"M
      _litp update -p /infrastructure/systems/sys3/disks/boot1 -o size="$mn_lvm_disk1"M
    fi

    # Change snap_size, snap_external and backup_snap_size (TORF-113332)- every other plan
    if [ $n4 -eq 0 ]; then
      _litp update -p /infrastructure/storage/storage_profiles/profile_v4/volume_groups/vg_vmvx/file_systems/VXVM_FS_4 -o snap_size=0 backup_snap_size=0
      _litp update -p /infrastructure/storage/storage_profiles/profile_v3/volume_groups/vg_vmvx/file_systems/VXVM_FS_3 -o snap_size=3 backup_snap_size=3
      _litp update -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg1/file_systems/root -o snap_size=0 backup_snap_size=0
      _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/soak_fs1 -o snap_size=0 backup_snap_size=0
      _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/var -o snap_size=0 backup_snap_size=0

      _litp update -p /infrastructure/storage/storage_profiles/profile_v1/volume_groups/vg_vmvx/file_systems/VXVM_FS_1 -o snap_external=true
      _litp update -p /infrastructure/storage/storage_profiles/profile_v2/volume_groups/vg_vmvx/file_systems/VXVM_FS_2 -o snap_external=true
      _litp update -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg1/file_systems/SOAK_VG1_FS1 -o snap_external=true
      _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/fs2 -o snap_external=true
      _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/var -o snap_external=true
    elif [ $n4 -eq 2 ]; then
      _litp update -p /infrastructure/storage/storage_profiles/profile_v4/volume_groups/vg_vmvx/file_systems/VXVM_FS_4 -o snap_size=100 backup_snap_size=50
      _litp update -p /infrastructure/storage/storage_profiles/profile_v3/volume_groups/vg_vmvx/file_systems/VXVM_FS_3 -o snap_size=100 backup_snap_size=50
      _litp update -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg1/file_systems/root -o snap_size=100 backup_snap_size=50
      _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/soak_fs1 -o snap_size=100 backup_snap_size=50
      _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/var -o snap_size=100 backup_snap_size=50

      _litp update -p /infrastructure/storage/storage_profiles/profile_v1/volume_groups/vg_vmvx/file_systems/VXVM_FS_1 -o snap_external=false
      _litp update -p /infrastructure/storage/storage_profiles/profile_v2/volume_groups/vg_vmvx/file_systems/VXVM_FS_2 -o snap_external=false
      _litp update -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg1/file_systems/SOAK_VG1_FS1 -o snap_external=false
      _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/fs2 -o snap_external=false
      _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/var -o snap_external=false
    fi

  fi

  # TORF-160948
  # Remove pxe_boot_only param and add eth0 to bond0
  # First iteration only
  if [ $c -eq 1 ]; then
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/if0 -o master=bond0 -d pxe_boot_only
  fi

  # CHANGES to bond0
  # Changes mgmt ips 2 plans in 4
  # Changes bond properties 2 plans in 4
  # Changes bridge params 2 plans in 4 (TORF-130325)
  if [ $n4 -eq 1 ]; then
    # update ipv4 on mgmt network n2
    _litp update -p /deployments/d1/clusters/c1/nodes/n2/network_interfaces/b0 -o ipaddress=${ipaddress1} 
    # update ipv4 on data network n2
    _litp update -p /deployments/d1/clusters/c1/nodes/n2/network_interfaces/if1 -o ipaddress=${node2_data_ipaddress1} 
    # update ipv6 on mgmt network n1
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/b0 -o ipv6address=${b0_ip6address1}
    # change ipv4allowed_clients to include new address
    _litp update -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl1/file_systems/managed2/exports/ex1 -o  ipv4allowed_clients=${sfs_fs2_ipv4allowed_clients1}
    _litp update -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl1/file_systems/managed1/exports/ex1 -o  ipv4allowed_clients=${sfs_fs1_ipv4allowed_clients1}
    # Update bridge params
    # Including hash_elasticity and ipv6_autoconf (159091)
    _litp update -p /ms/network_interfaces/br0 -o multicast_snooping=0 hash_elasticity=10 -d multicast_querier multicast_router hash_max ipv6_autoconf
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/br_834 -o hash_elasticity=10 multicast_snooping=0 -d multicast_querier multicast_router hash_max ipv6_autoconf
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/brtraffic1 -o multicast_snooping=1 multicast_querier=1 multicast_router=2 hash_max=2048

    # Update ETHTOOL_OPTS TORF-182186 and TORF-196696
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/if6 -o rx_ring_buffer=453 tx_ring_buffer=4078 txqueuelen=1250

  elif [ $n4 -eq 2 ]; then
    # update properties on bond0
    _litp update -p /deployments/d1/clusters/c1/nodes/n2/network_interfaces/b0 -o miimon=200 mode=6 

  elif [ $n4 -eq 3 ]; then
    # update ipv4 on mgmt network
    _litp update -p /deployments/d1/clusters/c1/nodes/n2/network_interfaces/b0 -o ipaddress=${ipaddress2} 
    # update ipv4 on data network
    _litp update -p /deployments/d1/clusters/c1/nodes/n2/network_interfaces/if1 -o ipaddress=${node2_data_ipaddress2} 
    # update ipv6 on mgmt network
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/b0 -o ipv6address=${b0_ip6address2}
    # change ipv4allowed_clients - remove new address
    _litp update -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl1/file_systems/managed2/exports/ex1 -o     ipv4allowed_clients=${sfs_fs2_ipv4allowed_clients2}
    _litp update -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl1/file_systems/managed1/exports/ex1 -o     ipv4allowed_clients=${sfs_fs1_ipv4allowed_clients2} 
    # Update bridge params
    # Including hash_elasticity and ipv6_autoconf (159091)
    _litp update -p /ms/network_interfaces/br0 -o multicast_snooping=1 multicast_querier=1 multicast_router=2 hash_max=2048 hash_elasticity=5 ipv6_autoconf=false
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/br_834 -o multicast_snooping=1 multicast_querier=1 multicast_router=2 hash_max=2048 hash_elasticity=5 ipv6_autoconf=false
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/brtraffic1 -o multicast_snooping=0 -d multicast_querier multicast_router hash_max

    # Remove ETHTOOL_OPTS TORF-182186
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/if6 -d rx_ring_buffer tx_ring_buffer
  elif [ $n4 -eq 0 ]; then
    # update properties on bond0
    _litp update -p /deployments/d1/clusters/c1/nodes/n2/network_interfaces/b0 -o miimon=100 mode=1

    # Add ETHTOOL_OPTS TORF-182186 and update TORF-196696
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/if6 -o rx_ring_buffer=2039 tx_ring_buffer=2039 txqueuelen=1000
  fi


   # Make config changes every other plan
  if [ $n2 -eq 1 ]; then

    # Change ntp service on node1 (TORF-166156)
    _litp update -p /software/items/ntp3/servers/server2 -o server=ntp30
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n1/items/ntp3 -s /software/items/ntp3
    _litp remove -p /deployments/d1/clusters/c1/nodes/n1/items/ntp 

    # Update vlan ipv4 and ipv6
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/bond0_836 -o ipaddress=${b0_v836_ip4address1} ipv6address=${b0_v836_ip6address1}

    # Add SFS managed mount to node2 
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/file_systems/managed2 -s /infrastructure/storage/nfs_mounts/managed2

    # Update unmanaged mounts (LITPCDS-5284)
    # Remove SFS unmanaged mount from node2 
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/file_systems/unmanaged1 
    # Remove NFS unmanaged mount to node2
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/file_systems/nfs2 

    # Install packages on node2
    # The following lines will cause a litp error after the first iteration
    # it does not stop the test running.
    # I have left it in as testing repeated errors might be interesting.
    _litp create -t package -p /software/items/remote-access -o name=telnet
    _litp create -t package -p /software/items/storage-udisks -o name=udisks
    _litp create -t package -p /software/items/browser-firefox -o name=firefox
    _litp create -t package -p /software/items/ant -o name=ant
    _litp create -t package -p /software/items/crash -o name=crash
    _litp create -t package -p /software/items/emacs -o name=emacs
    _litp create -t package -p /software/items/finger -o name=finger
    _litp create -t package -p /software/items/wireshark -o name=wireshark

    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/items/telnet-client -s /software/items/remote-access
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/items/storage-udisks -s /software/items/storage-udisks
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/items/browser-firefox  -s /software/items/browser-firefox
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/items/ant -s /software/items/ant
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/items/crash -s /software/items/crash
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/items/emacs -s /software/items/emacs 
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/items/finger -s /software/items/finger
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/items/wireshark -s /software/items/wireshark
    _litp inherit -p /ms/items/wireshark -s /software/items/wireshark

    # Create and update alias
    _litp create -t alias-cluster-config -p /deployments/d1/clusters/c1/configs/alias_config 
    _litp create -t alias -p /deployments/d1/clusters/c1/configs/alias_config/aliases/alias1 -o alias_names="alias.1" address="10.44.86.30"
    _litp create -t alias -p /deployments/d1/clusters/c1/configs/alias_config/aliases/alias1_ipv6 -o alias_names="alias.1.ipv6" address="fdde:4d7e:d471:1:0:835:105:100"
    _litp update -p /deployments/d1/clusters/c1/configs/alias_config/aliases/alias2 -o address="10.44.86.105" 
    _litp update -p /deployments/d1/clusters/c1/configs/alias_config/aliases/alias2_ipv6 -o address="fdde:4d7e:d471:0001::0835:105:0201"


    _litp create -t alias -p /ms/configs/alias_config/aliases/alias1 -o alias_names="alias.1" address="10.44.86.30"
    _litp create -t alias -p /ms/configs/alias_config/aliases/alias1_ipv6 -o alias_names="alias.1.ipv6" address="fdde:4d7e:d471:1:0:835:105:100"
    _litp update -p /ms/configs/alias_config/aliases/alias2 -o address="10.44.86.105" 
    _litp update -p /ms/configs/alias_config/aliases/alias2_ipv6 -o address="fdde:4d7e:d471:0001::0835:105:0201"


    _litp create -t alias -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/alias3 -o alias_names="alias.3" address="10.44.86.30"
    _litp create -t alias -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/alias3_ipv6 -o alias_names="alias.3.ipv6" address="fdde:4d7e:d471:1:0:835:105:100"
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/alias4 -o address="10.44.86.105"
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/alias4_ipv6 -o address="fdde:4d7e:d471:0001::0835:105:0201"

    # Remove duplicate aliases TORF-146545
    _litp remove -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/master_node_alias_dup 
    _litp remove -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/master_node_alias_ipv6_dup 
    _litp remove -p /ms/configs/alias_config/aliases/ms_alias_dup_1 
 
    # Create/update sysparams
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_enm4 -o value="Ak1core.%e.pid%p.usr%u.sig%s.tim%t"
    _litp create -t sysparam -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_custom -o  key="fs.file-max" value="26289444"

    _litp update -p /deployments/d1/clusters/c1/nodes/n2/configs/sysctl/params/sysctl_enm4 -o value="Ak2core.%e.pid%p.usr%u.sig%s.tim%t"
    _litp create -t sysparam -p /deployments/d1/clusters/c1/nodes/n2/configs/sysctl/params/sysctl_custom -o  key="fs.file-max" value="26289446"

    _litp update -p /ms/configs/sysctl/params/sysctl_enm1 -o  value="Amscore.%e.pid%p.usr%u.sig%s.tim%t"
    _litp create -t sysparam -p  /ms/configs/sysctl/params/sysctl_custom -o  key="fs.file-max" value="26289448"

    # Create logrotate
    _litp create -t logrotate-rule -p /deployments/d1/clusters/c1/nodes/n1/configs/logrotate/rules/rabbit -o name="a_rabbitmq" path="/var/log/rabbitmq" size=10M rotate=50 copytruncate=true
    _litp create -t logrotate-rule -p /ms/configs/logrotate/rules/rabbit -o name="a_rabbitmq" path="/var/log/rabbitmq" size=10M rotate=50 copytruncate=true

    # Update logrotate
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/logrotate/rules/engine -o mail=ruth.evans@ammeon.com

    # Update VCS parameters
    _litp update -p /deployments/d1/clusters/c1/services/multiple_SG/ -o offline_timeout=$(($c+300)) online_timeout=$(($c+800))
    _litp update -p /deployments/d1/clusters/c1/services/multiple_SG/ha_configs/fmmed1_conf -o fault_on_monitor_timeouts=$c tolerance_limit=$c  clean_timeout=$(($c+240)) restart_limit=$c startup_retry_limit=$c status_interval=$(($c+60)) status_timeout=$(($c+60))
    _litp update -p /deployments/d1/clusters/c1/services/SG_cups -o offline_timeout=$(($c+300)) online_timeout=$(($c+800))
    _litp update -p /deployments/d1/clusters/c1/services/SG_cups/ha_configs/config -o  fault_on_monitor_timeouts=$c tolerance_limit=$c  clean_timeout=$(($c+60)) restart_limit=$c startup_retry_limit=$c status_interval=$(($c+60)) status_timeout=$(($c+60))

    # Add SG dependency_list (LITPCDS-11453)
    _litp update -p /deployments/d1/clusters/c1/services/multiple_SG -o dependency_list="SG_cups" 
    # Update SG dependency_list (LITPCDS-11453)
    _litp update -p /deployments/d1/clusters/c1/services/SG_httpd -o dependency_list="SG_cups"

    # Remove vcs-trigger items (TORF-107489)
    _litp remove -p /deployments/d1/clusters/c1/services/SG_cups/triggers/trig1 
    _litp remove -p /deployments/d1/clusters/c1/services/multiple_SG/triggers/trig1

    # Change yum_repository
    _litp update -p /software/items/yum_osHA_repo -o ms_url_path=/6/os/x86_64/HighAvailability -d base_url

    # Update multicast_snooping
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/br_834 -o multicast_snooping=1
    _litp update -p /deployments/d1/clusters/c1/nodes/n2/network_interfaces/br_834 -o multicast_snooping=1
    _litp update -p /ms/network_interfaces/br1 -o multicast_snooping=1

    # Change nfs-mount provider
    _litp update -p /infrastructure/storage/nfs_mounts/managed3 -o provider="virtserv1" 

    # add mount_points
    _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/fs3 -o mount_point="/data_dir3"
    _litp update -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg1/file_systems/fs2 -o mount_point="/data_dir3"

    # LITPCDS-10650 -  generate replacement Config Task
    _litp update -p /software/items/tc01_foobar1 -o name=tc01_foobar2  

    # TORF 171233 - update vcs_seed_threshold
    _litp update -p /deployments/d1/clusters/c1 -o vcs_seed_threshold=1
  else

    # Change ntp service on node1 (TORF-166156)
    _litp update -p /software/items/ntp3/servers/server2 -o server=10.44.86.105
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n1/items/ntp -s /software/items/ntp2
    _litp remove -p /deployments/d1/clusters/c1/nodes/n1/items/ntp3 

    # Update vlan ipv6
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/bond0_836 -o ipaddress=${b0_v836_ip4address2} ipv6address=${b0_v836_ip6address2}

    # Remove SFS managed mount on node2 
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/file_systems/managed2 

    # Update unmanaged mounts (LITPCDS-5284)
    # Add SFS unmanaged mount to node2 
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/file_systems/unmanaged1 -s /infrastructure/storage/nfs_mounts/unmanaged1
    # Add NFS unmanaged mount to node2
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/file_systems/nfs2 -s /infrastructure/storage/nfs_mounts/nfs2

    # Remove packages
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/items/telnet-client
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/items/storage-udisks
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/items/browser-firefox
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/items/ant
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/items/crash
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/items/emacs
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/items/finger
    _litp remove -p /software/items/wireshark

    # Remove and update alias
    _litp remove -p /deployments/d1/clusters/c1/configs/alias_config/aliases/alias1
    _litp remove -p /deployments/d1/clusters/c1/configs/alias_config/aliases/alias1_ipv6
    _litp update -p /deployments/d1/clusters/c1/configs/alias_config/aliases/alias2 -o address="10.44.86.106"
    _litp update -p /deployments/d1/clusters/c1/configs/alias_config/aliases/alias2_ipv6 -o address="fdde:4d7e:d471:0001::0835:105:0200"

    _litp remove -p /ms/configs/alias_config/aliases/alias1 
    _litp remove -p /ms/configs/alias_config/aliases/alias1_ipv6
    _litp update -p /ms/configs/alias_config/aliases/alias2 -o address="10.44.86.106"
    _litp update -p /ms/configs/alias_config/aliases/alias2_ipv6 -o address="fdde:4d7e:d471:0001::0835:105:0200"

    _litp remove -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/alias3 
    _litp remove -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/alias3_ipv6
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/alias4 -o address="10.44.86.106"
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/alias4_ipv6 -o address="fdde:4d7e:d471:0001::0835:105:0200"

    # Add duplicate aliases TORF-146545
    _litp create -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/master_node_alias_dup -t alias -o alias_names="ms-aliasdup,ms-alias" address="10.44.86.105"
    _litp create -p /deployments/d1/clusters/c1/nodes/n1/configs/alias_config/aliases/master_node_alias_ipv6_dup -t alias -o alias_names="ms-aliasipv6dup,ms-aliasipv6" address="fdde:4d7e:d471:0001::0835:105:0100"
    _litp create -t alias -p /ms/configs/alias_config/aliases/ms_alias_dup_1 -o alias_names=msaliasdup1,msalias1 address="10.44.86.11"

    # Remove/update sysparams:
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_enm4 -o value="Bk1core.%e.pid%p.usr%u.sig%s.tim%t"
    _litp remove -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_custom

    _litp update -p /deployments/d1/clusters/c1/nodes/n2/configs/sysctl/params/sysctl_enm4 -o value="Bk2core.%e.pid%p.usr%u.sig%s.tim%t"
    _litp remove -p /deployments/d1/clusters/c1/nodes/n2/configs/sysctl/params/sysctl_custom

    _litp update -p  /ms/configs/sysctl/params/sysctl_enm1  -o  value="Bmscore.%e.pid%p.usr%u.sig%s.tim%t"
    _litp remove -p  /ms/configs/sysctl/params/sysctl_custom 

    # Remove logrotate
    _litp remove -p /deployments/d1/clusters/c1/nodes/n1/configs/logrotate/rules/rabbit
    _litp remove -p /ms/configs/logrotate/rules/rabbit

    # Update logrotate
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/logrotate/rules/engine -d mail

    # Update VCS parameters LITPCDS-6800 and LITPCDS-5172
    _litp update -p /deployments/d1/clusters/c1/services/SG_cups -d offline_timeout online_timeout
    _litp update -p /deployments/d1/clusters/c1/services/SG_cups/ha_configs/config -d fault_on_monitor_timeouts tolerance_limit   clean_timeout restart_limit startup_retry_limit status_interval status_timeout

    # Change yum_repository
    _litp update -p /software/items/yum_osHA_repo -o base_url="http://ms1105/6/os/x86_64/HighAvailability" -d ms_url_path

    # Remove SG dependency_list (LITPCDS-11453)
    _litp update -p /deployments/d1/clusters/c1/services/multiple_SG -d dependency_list
    # Update SG dependency_list (LITPCDS-11453)
    _litp update -p /deployments/d1/clusters/c1/services/SG_httpd -o dependency_list="SG_cups,SG_luci"

    # create vcs-trigger items (TORF-107489)
    _litp create -t vcs-trigger -p /deployments/d1/clusters/c1/services/SG_cups/triggers/trig1 -o trigger_type=nofailover
    _litp create -t vcs-trigger -p /deployments/d1/clusters/c1/services/multiple_SG/triggers/trig1 -o trigger_type=nofailover

    # Update multicast_snooping
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/br_834 -o multicast_snooping=0
    _litp update -p /deployments/d1/clusters/c1/nodes/n2/network_interfaces/br_834 -o multicast_snooping=0
    _litp update -p /ms/network_interfaces/br1 -o multicast_snooping=0

    # Change nfs-mount provider
    _litp update -p /infrastructure/storage/nfs_mounts/managed3 -o provider="virtserv2" 

    # remove mount-points
    _litp update -p /infrastructure/storage/storage_profiles/spms/volume_groups/vg1/file_systems/fs3 -d mount_point
    _litp update -p /infrastructure/storage/storage_profiles/profile_1/volume_groups/vg1/file_systems/fs2 -d mount_point

    # LITPCDS-10650 -  generate replacement Config Task
    _litp update -p /software/items/tc01_foobar1 -o name=tc01_foobar1

    # TORF 171233 - update vcs_seed_threshold
    _litp update -p /deployments/d1/clusters/c1 -o vcs_seed_threshold=2
  fi


  # FIREWALLS
  if [ $n20 -eq 5 ]; then
    # add/update firewall cluster firewall
    _litp create -t firewall-rule -p /deployments/d1/clusters/c1/configs/fw_config/rules/fw_test -o name="200 test" dport="614" 
    _litp update -p /deployments/d1/clusters/c1/configs/fw_config/rules/fw_test_update -o dport="2614" provider=iptables

    # add/update firewall config for a node (node1):
    _litp create -t firewall-rule -p /deployments/d1/clusters/c1/nodes/n1/configs/fw_config/rules/fw_test -o name="300 test" dport="615" 
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/fw_config/rules/fw_test_update -o dport="2615" provider=iptables 

  # add/update firewall config for ms
    _litp create -t firewall-rule -p /ms/configs/fw_config/rules/fw_test -o name="400 test" dport="616"
    _litp update -p /ms/configs/fw_config/rules/fw_test_update -o dport="2616" provider=iptables

  elif [ $n20 -eq 15 ]; then
  # remove/update cluster firewalls
    _litp remove -p /deployments/d1/clusters/c1/configs/fw_config/rules/fw_test
    _litp update -p /deployments/d1/clusters/c1/configs/fw_config/rules/fw_test_update -o dport="1614" 
    _litp update -p /deployments/d1/clusters/c1/configs/fw_config/rules/fw_test_update -d provider 

  # remove/update firewall config for a node (node1):
    _litp remove -p /deployments/d1/clusters/c1/nodes/n1/configs/fw_config/rules/fw_test
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/fw_config/rules/fw_test_update -o dport="1615" 
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/fw_config/rules/fw_test_update -d provider

  # remove/update firewall config for ms
    _litp remove -p /ms/configs/fw_config/rules/fw_test 
    _litp update -p /ms/configs/fw_config/rules/fw_test_update -o dport="1616"
    _litp update -p /ms/configs/fw_config/rules/fw_test_update -d provider

  fi


  # Create new VIPs for first 20 iterations (LITPCDS-5173)
  if [ $c -le 20 ]; then
    # Add to FO SG
    _litp create -t vip   -p /deployments/d1/clusters/c1/services/SG_cups/ipaddresses/new4_t1_ip$c -o ipaddress=10.19.105.$(($c+120)) network_name=traffic1
    _litp create -t vip   -p /deployments/d1/clusters/c1/services/SG_cups/ipaddresses/new6_t1_ip$c -o ipaddress=fdde:4d7e:d471:19::105:$(($c+120))/64 network_name=traffic1
    _litp create -t vip   -p /deployments/d1/clusters/c1/services/SG_cups/ipaddresses/new_t2_ip$c -o ipaddress=10.20.105.$(($c+120)) network_name=traffic2

    # Add to PL SG
    _litp create -t vip   -p /deployments/d1/clusters/c1/services/SG_httpd/ipaddresses/new4_t1_ip$c -o ipaddress=10.19.105.$(($c+150)) network_name=traffic1
    _litp create -t vip   -p /deployments/d1/clusters/c1/services/SG_httpd/ipaddresses/new4_t2_ip$c -o ipaddress=10.19.105.$(($c+180)) network_name=traffic1
  fi


  # Update critical_service property LITPCDS-10167 + LITPCDS-10168
  # Make a change 3 in 6 plans
  if [ $n6 -eq 0 ]; then
    _litp update -p /deployments/d1/clusters/c1 -o critical_service="SG_cups"
  elif [ $n6 -eq 2 ]; then
    _litp update -p /deployments/d1/clusters/c1 -o critical_service=SG_luci
  elif [ $n6 -eq 4 ]; then
    _litp update -p /deployments/d1/clusters/c1 -d critical_service
  fi


  # Update cleanup command LITPCDS-6800 + LITPCDS-9571
  # Make a change 3 in 6 plans
  if [ $n6 -eq 0 ]; then
    _litp update -p /software/services/fmmed1/ -o cleanup_command="/sbin/service fmmed1 force-stop"
  elif [ $n6 -eq 2 ]; then
    _litp update -p /software/services/fmmed1/ -o cleanup_command="/sbin/service fmmed1 stop-undefine --stop-timeout=240"
  elif [ $n6 -eq 4 ]; then
    _litp update -p /software/services/fmmed1/ -o cleanup_command="/sbin/service fmmed1 force-stop-undefine"
  fi

  # Add vxvm PD
  if [ $c -lt 6 ]; then
    _litp create -p /infrastructure/storage/storage_profiles/profile_v1/volume_groups/vg_vmvx/physical_devices/hd_vxvm_soak$c -t physical-device -o device_name=hd_vxvm_soak$c
    _litp create -p /infrastructure/systems/sys2/disks/disksoak$c -t disk -o name=hd_vxvm_soak$c size=2G bootable=false uuid="${hd_vxvm_soak[$c]}"
    _litp create -p /infrastructure/systems/sys3/disks/disksoak$c -t disk -o name=hd_vxvm_soak$c size=2G bootable=false uuid="${hd_vxvm_soak[$c]}"
  fi


  if [ $n8 -eq 1 ]; then
    # Remove SG ricci (with vips) 
    # Add SG anseo (without vips)
    # Add SG VM 

    _litp remove -p /deployments/d1/clusters/c1/services/SG_ricci
    _litp remove -p /software/services/ricci
    _litp remove -p /software/items/ricci

    # Add SG anseo 
    _litp create -t vcs-clustered-service -p /deployments/d1/clusters/c1/services/SG_anseo -o active=2 standby=0 name=PAR_SG3 online_timeout=50 offline_timeout=110    node_list=n1,n2 
    _litp create -t service -p /software/services/anseo -o service_name="test-lsb-11"
    _litp inherit -p /deployments/d1/clusters/c1/services/SG_anseo/applications/anseo_service -s /software/services/anseo
    _litp create -t package -p /software/items/testpkg11 -o name=EXTR-lsbwrapper11
    _litp inherit -p /software/services/anseo/packages/pkg11 -s /software/items/testpkg11
    _litp create -t ha-service-config -p /deployments/d1/clusters/c1/services/SG_anseo/ha_configs/config -o clean_timeout=90 startup_retry_limit=10 

    # VM as a SG on MNs
    _litp create -t vm-service -p /software/services/fmmed2 -o service_name=fmmed2 image_name=fmmed cpus=2 ram=2048M internal_status_check=on cleanup_command="/sbin/service fmmed2 force-stop" 
    _litp create -t vcs-clustered-service -p /deployments/d1/clusters/c1/services/SG_VM -o active=2 standby=0 name=PL_SGVM online_timeout=300 offline_timeout=300 node_list=n1,n2
    _litp inherit -p /deployments/d1/clusters/c1/services/SG_VM/applications/fmmed2 -s /software/services/fmmed2
    _litp create -t ha-service-config -p /deployments/d1/clusters/c1/services/SG_VM/ha_configs/conf -o status_interval=30 status_timeout=30 restart_limit=5 startup_retry_limit=1 
    # ipv4 interface on private network
    _litp create -t vm-network-interface -p /software/services/fmmed2/vm_network_interfaces/net1 -o network_name=net1vm device_name=eth0 host_device=br_vip1 gateway=10.46.85.1
    # ipv6 interface on 834
    _litp create -t vm-network-interface -p /software/services/fmmed2/vm_network_interfaces/net2 -o network_name=ipv61 device_name=eth1 host_device=br_834 gateway6=${ipv6_834_gateway}
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM/applications/fmmed2/ -o hostnames=105vmpl1,105vmpl2
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM/applications/fmmed2/vm_network_interfaces/net1 -o ipaddresses="10.46.85.6,10.46.85.7"   ipv6addresses="fdde:4d7e:d471:1:105::106/64,fdde:4d7e:d471:1:105::107/64"    
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM/applications/fmmed2/vm_network_interfaces/net2 -o ipv6addresses="fdde:4d7e:d471:0000::0834:105:501/64,fdde:4d7e:d471:0000::0834:105:502/64"    

  elif [ $n8 -eq 2 ]; then

    # Add a new VCS clustered_service and deactivate an existing one TORF-128825
    _litp create -t vcs-clustered-service -p /deployments/d1/clusters/c1/services/SG_13new -o deactivates=SG_13 active=1 standby=0 name=PAR_SG13new online_timeout=50 offline_timeout=110 node_list=n2 
    _litp inherit -p /deployments/d1/clusters/c1/services/SG_13new/applications/SG_13 -s /software/services/SG_13new
    _litp create -t ha-service-config -p /deployments/d1/clusters/c1/services/SG_13new/ha_configs/config -o clean_timeout=90 startup_retry_limit=10 

  elif [ $n8 -eq 3 ]; then

    # Contract node lists (LITPCDS-5168 and LITPCDS-11750)
    # And change other properties
    _litp update -p /deployments/d1/clusters/c1/services/SG_anseo -o node_list=n1 active=1
    _litp update -p /deployments/d1/clusters/c1/services/SG_anseo/ha_configs/config -o clean_timeout=5000 startup_retry_limit=5 
    _litp update -p /deployments/d1/clusters/c1/services/SG_anseo -o offline_timeout=120

    _litp update -p /deployments/d1/clusters/c1/services/SG_VM -o node_list=n1 active=1
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM -o online_timeout=600 offline_timeout=600 
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM/ha_configs/conf -o status_interval=60 restart_limit=1 startup_retry_limit=5 
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM/applications/fmmed2/ -o hostnames=105vmpl1
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM/applications/fmmed2/vm_network_interfaces/net1 -o ipaddresses="10.46.85.6"   ipv6addresses="fdde:4d7e:d471:105::106/64"    
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM/applications/fmmed2/vm_network_interfaces/net2 -o ipv6addresses="fdde:4d7e:d471:0000::0834:105:501/64"    

    # Migrate SG to n2 TORF-124980 
    _litp update -p /deployments/d1/clusters/c1/services/SG_12 -o node_list=n2 

  elif [ $n8 -eq 4 ]; then

    _litp update -p /deployments/d1/clusters/c1/services/SG_13new -d deactivates

  elif [ $n8 -eq 5 ]; then

    # Expand node lists 
    _litp update -p /deployments/d1/clusters/c1/services/SG_anseo -o node_list=n1,n2 active=2

    _litp update -p /deployments/d1/clusters/c1/services/SG_VM -o node_list=n1,n2 active=2
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM/applications/fmmed2/ -o hostnames=105vmpl1,105vmpl2
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM/applications/fmmed2/vm_network_interfaces/net1 -o ipaddresses="10.46.85.6,10.46.85.7"   ipv6addresses="fdde:4d7e:d471:10:105::106/64,fdde:4d7e:d471:10:105::107/64" 
    _litp update -p /deployments/d1/clusters/c1/services/SG_VM/applications/fmmed2/vm_network_interfaces/net2 -o ipv6addresses="fdde:4d7e:d471:0000::0834:105:501/64,fdde:4d7e:d471:0000::0834:105:502/64"    
   
    # Migrate SG to n1 TORF-124980 
    _litp update -p /deployments/d1/clusters/c1/services/SG_12 -o node_list=n1

    # Add a new VCS clustered_service and deactivate an existing one TORF-128825
    _litp create -t vcs-clustered-service -p /deployments/d1/clusters/c1/services/SG_13 -o deactivates=SG_13new active=1 standby=0 name=PAR_SG13 online_timeout=50 offline_timeout=110 node_list=n1 
    _litp inherit -p /deployments/d1/clusters/c1/services/SG_13/applications/SG_13 -s /software/services/SG_13
    _litp create -t ha-service-config -p /deployments/d1/clusters/c1/services/SG_13/ha_configs/config -o clean_timeout=90 startup_retry_limit=10 

  elif [ $n8 -eq 7 ]; then
    # Remove SG anseo 
    # Remove SG VM 
    _litp remove -p /deployments/d1/clusters/c1/services/SG_anseo
    _litp remove -p /software/services/anseo
    _litp remove -p /software/items/testpkg11

    _litp remove -p /deployments/d1/clusters/c1/services/SG_VM
    _litp remove -p /software/services/fmmed2

    # ADD SG ricci
    _litp create -t service -p /software/services/ricci -o service_name=ricci

    _litp create -t vcs-clustered-service -p /deployments/d1/clusters/c1/services/SG_ricci -o active=2 standby=0 name=PAR_SG2 online_timeout=300 offline_timeout=60 node_list="n2,n1" dependency_list="SG_cups,SG_luci"

    _litp inherit -p /deployments/d1/clusters/c1/services/SG_ricci/applications/s1_ricci -s /software/services/ricci
    _litp create -t ha-service-config -p /deployments/d1/clusters/c1/services/SG_ricci/ha_configs/config -o status_interval=3600 status_timeout=10 restart_limit=50 startup_retry_limit=1 fault_on_monitor_timeouts=1 tolerance_limit=1 clean_timeout=7000

    _litp create -t package -p /software/items/ricci -o name=ricci release=87.el6 version=0.16.2
    _litp inherit -p /software/services/ricci/packages/pkg1 -s /software/items/ricci

    # Add IP Resources
    # 1 IPv4 VIP per Traffic2 Network, 1 IPv4 + 1 IPv6 VIP per Traffic1 Network
    vip_count=1
    ip_count=1
    for (( i=1; i<5; i++ )); do
      _litp create -t vip   -p /deployments/d1/clusters/c1/services/SG_ricci/ipaddresses/t1_ip$ip_count -o ipaddress="${traf1_vip[$vip_count]}" network_name=traffic1
      ip_count=$[$ip_count+1]
      _litp create -t vip   -p /deployments/d1/clusters/c1/services/SG_ricci/ipaddresses/t1_ip$ip_count -o ipaddress="${traf1_vip_ipv6[$vip_count]}" network_name=traffic1
      ip_count=$[$ip_count+1]
      _litp create -t vip   -p /deployments/d1/clusters/c1/services/SG_ricci/ipaddresses/t2_ip${i} -o ipaddress="${traf2_vip[$vip_count]}" network_name=traffic2
      vip_count=($vip_count+1)
      ip_count=$[$ip_count+1]
    done 
  
    # Update SG TORF-124980 
    _litp update -p /deployments/d1/clusters/c1/services/SG_12 -o online_timeout=100 offline_timeout=220

    # Remove deactivates param TORF-128825
    _litp update -p /deployments/d1/clusters/c1/services/SG_13 -d deactivates

  fi

  # Change bond from miimon to arp, update arp properties and change back to miimon (TORF-106978)
  if [ $n4 -eq 1 ]; then 
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/b0 -d miimon -o arp_interval="1200" arp_ip_target="10.44.86.105" arp_validate="active" arp_all_targets="any"
  elif [ $n4 -eq 2 ]; then
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/b0 -o arp_interval="5000" arp_ip_target="10.44.86.105,10.44.86.65" arp_validate="all" arp_all_targets="1" 
  elif [ $n4 -eq 3 ]; then
   # Set arp_interval to 0 - this disables arp monitoring
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/b0 -o arp_interval="0"
  else
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/network_interfaces/b0 -o miimon=100 -d arp_interval arp_ip_target arp_validate arp_all_targets
  fi

  # Add/remove MS VM1
  # update MS VM2 
  if [ $n3 -eq 1 ]; then

    # Remove MS VM1
    _litp remove -p /ms/services/msfmmed1

    # Update MS VM2 (LITPCDS-13197)
    _litp remove -p /ms/services/msfmmed2/vm_disks/vm_disk1 
    _litp remove -p /ms/services/msfmmed2/vm_network_interfaces/net5
    _litp remove -p /ms/services/msfmmed2/vm_network_interfaces/net4
    _litp remove -p /ms/services/msfmmed2/vm_aliases/node1 
    _litp remove -p /ms/services/msfmmed2/vm_aliases/node2
    _litp remove -p /ms/services/msfmmed2/vm_aliases/ms1_ipv6
    _litp remove -p /ms/services/msfmmed2/vm_yum_repos/repo1
    _litp remove -p /ms/services/msfmmed2/vm_packages/3pp-irish-hello
    _litp remove -p /ms/services/msfmmed2/vm_ssh_keys/support_key1

    _litp update -p /ms/services/msfmmed2 -o hostnames=newmsvm
    _litp update -p /ms/services/msfmmed2/vm_network_interfaces/net1 -o ipaddresses=${ms_vm2_net1_2}
    _litp update -p /ms/services/msfmmed2/vm_network_interfaces/net2 -o ipv6addresses=${ms_vm2_ipv6_834_2}

    # Update image (TORF-113124)
    _litp update -p /ms/services/msfmmed2 -o image_name=rhel_6


  elif [ $n3 -eq 2 ]; then

    # Add MS VM1 
    _litp create -t vm-service -p /ms/services/msfmmed1 -o service_name=msfmmed1 image_name=fmmed cpus=2 ram=512M internal_status_check=off
    _litp create -t vm-network-interface -p /ms/services/msfmmed1/vm_network_interfaces/net1 -o network_name=mgmt device_name=eth0 host_device=br0   ipaddresses=${ms_vm1_mgmt_1} ipv6addresses=${ms_vm1_ipv6_mgmt_1}
    # ipv4 only
    _litp create -t vm-network-interface -p /ms/services/msfmmed1/vm_network_interfaces/net2 -o network_name=net1vm device_name=eth1 host_device=brnet1vm ipaddresses=${ms_vm1_net1_1}
    # ipv6 only
    _litp create -t vm-network-interface -p /ms/services/msfmmed1/vm_network_interfaces/net3 -o network_name=834 device_name=eth2 host_device=br1     ipv6addresses=${ms_vm1_ipv6_834_1}
    # vm-alias
    _litp create -t vm-alias -p /ms/services/msfmmed1/vm_aliases/ms1 -o alias_names=ms1105 address=10.44.86.105
    # vm repo
    _litp create -t vm-yum-repo -p /ms/services/msfmmed1/vm_yum_repos/repo1 -o name=repo1 base_url="http://ms1105/REPO1"
    # vm package
    _litp create -t vm-package -p /ms/services/msfmmed1/vm_packages/3pp-irish-hello -o name=3PP-irish-hello 
    # custom script (TORF-180365)
    _litp create -t vm-custom-script -p /ms/services/msfmmed1/vm_custom_script/customscript -o custom_script_names="cscript_crontab.sh"

    # Update MS VM2 (LITPCDS-13197)
    _litp create -t vm-disk -p /ms/services/msfmmed2/vm_disks/vm_disk1 -o host_volume_group=vg1 host_file_system=fs1 mount_point=/vm_data_dir
    _litp create -t vm-network-interface -p /ms/services/msfmmed2/vm_network_interfaces/net4 -o network_name=net3vm device_name=eth3 host_device=brnet3vm ipaddresses=${ms_vm2_net3}
    _litp create -t vm-network-interface -p /ms/services/msfmmed2/vm_network_interfaces/net5 -o network_name=net4vm device_name=eth4 host_device=brnet4vm ipaddresses=${ms_vm2_net4}
    _litp create -t vm-alias -p /ms/services/msfmmed2/vm_aliases/node1 -o alias_names="node1" address=${VM_net1vm_ip[0]}
    _litp create -t vm-alias -p /ms/services/msfmmed2/vm_aliases/node2 -o alias_names="node2" address=${VM_net1vm_ip[1]}
    _litp create -t vm-alias -p /ms/services/msfmmed2/vm_aliases/ms1_ipv6 -o alias_names="ms1105.ipv6" address="fdde:4d7e:d471:0001::0835:105:0100"
    _litp create -t vm-yum-repo -p /ms/services/msfmmed2/vm_yum_repos/repo1 -o name=repo1 base_url="http://ms1105/REPO1"
    _litp create -t vm-package -p /ms/services/msfmmed2/vm_packages/3pp-irish-hello -o name=3PP-irish-hello 
    _litp create -t vm-ssh-key -p  /ms/services/msfmmed2/vm_ssh_keys/support_key1 -o ssh_key="ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAxHQW3vVqhTikufpmOc+4XuJcCVscL4eDi3ahLKuj61tdjfPN0+HF8fJh+4ckpOpttCoZwM1AaBwyZx1H4t1K78E9CBEPwb9ftd57h/eFD9CnPtRIIg1eVEqGNNvhh6tAobEFSAQ1AuBrO5ye+pPGEXlXSb5ZU9ZYYJg4wAhNFlVX6zWCq6BqvzTQ7h4YFK4Bk8ACFOMD10N7rQEo6TVIyzkKoW0/HV61o537YFRav0kw9ZFyqS9jjWtui08GR1yIyhXb2jOiw20B5BnyaG3CR+tBmK6+EXzLVdf2D+3Lpf6nV2X76O5jd4OG5XW0NOOaXbAcqCzPQ39fwwBzgag6Sw== root@Ms1105"


    _litp update -p /ms/services/msfmmed2 -d hostnames
    _litp update -p /ms/services/msfmmed2/vm_network_interfaces/net1 -o ipaddresses=${ms_vm2_net1_1}
    _litp update -p /ms/services/msfmmed2/vm_network_interfaces/net2 -o ipv6addresses=${ms_vm2_ipv6_834_1}

  else

     # Update image (TORF-113124)
    _litp update -p /ms/services/msfmmed2 -o image_name=rhel_7

    _litp update -p /ms/services/msfmmed2/vm_aliases/ms1_ipv6 -o address="fdde:4d7e:d471:0001::0835:105:0101"

    # Update custom script (TORF-180365)
    _litp update -p /ms/services/msfmmed1/vm_custom_script/customscript -o custom_script_names="cscript1_crontab.sh"

  fi

  # Update VM items
  # TORF-107476 - vm-ram-mounts - add, update and remove
  # TORF-113124 - update VM image
  # TORF-180365 - custom script
  # ipv6 vm-alias
  # ipv6 network interface
  if [ $n3 -eq 1 ]; then 
   _litp create -t vm-ram-mount -p /ms/services/msfmmed2/vm_ram_mounts/vm-ram-mount -o type=tmpfs mount_point="/mnt/data2" mount_options="size=512M,noexec,nodev,nosuid"
   _litp update -p /software/services/fmmed1/vm_ram_mounts/vm_ram-mount -o mount_point="/mnt/data_new"

   _litp update -p /software/services/fmmed1 -o image_name=rhel_6
   _litp update -p /software/services/fmmed1/vm_aliases/node2_ipv6 -o address=fdde:4d7e:d471:10:105::102
   _litp update -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_network_interfaces/net1 -o ipv6addresses="fdde:4d7e:d471:10:105::202/64"

   _litp update -p /software/services/fmmed1/vm_custom_script/customscript -o custom_script_names="cscript1_crontab.sh"
 
  elif [ $n3 -eq 2 ]; then
   _litp update -p  /ms/services/msfmmed2/vm_ram_mounts/vm-ram-mount -o mount_point="/mnt/data3"
   _litp remove -p /software/services/fmmed1/vm_ram_mounts/vm_ram-mount  
   _litp remove -p /software/services/fmmed1/vm_custom_script/customscript 

  else
   _litp remove -p /ms/services/msfmmed2/vm_ram_mounts/vm-ram-mount
   _litp create -t vm-ram-mount -p /software/services/fmmed1/vm_ram_mounts/vm_ram-mount -o type=ramfs mount_point="/mnt/data1" mount_options="noexec,nodev,nosuid"
 
   _litp update -p /software/services/fmmed1 -o image_name=rhel_7
   _litp update -p /software/services/fmmed1/vm_aliases/node2_ipv6 -o address=fdde:4d7e:d471:10:105::101
   _litp update -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_network_interfaces/net1 -o ipv6addresses="fdde:4d7e:d471:10:105::102/64"
   _litp create -t vm-custom-script -p /software/services/fmmed1/vm_custom_script/customscript -o custom_script_names="cscript_crontab.sh" network_name=net1vm
  fi


  # LITPCDS-12817 LITPCDS-13197 Add remove items from VM on MN
  if [ $n4 -eq 1 ]; then

    # remove from source
    _litp remove -p /software/services/fmmed1/vm_aliases/node1
    _litp remove -p /software/services/fmmed1/vm_aliases/node1_ipv6
    _litp remove -p /software/services/fmmed1/vm_network_interfaces/net2
    _litp remove -p /software/services/fmmed1/vm_yum_repos/os
    _litp remove -p /software/services/fmmed1/vm_yum_repos/updates
    _litp remove -p /software/services/fmmed1/vm_packages/rhel7_tree 
    _litp remove -p /software/services/fmmed1/vm_packages/rhel7_unzip 
    _litp remove -p /software/services/fmmed1/vm_ssh_keys/support_key1

  elif [ $n4 -eq 2 ]; then

    # recreate
    _litp create -t vm-alias -p /software/services/fmmed1/vm_aliases/node1 -o alias_names="node1" address=10.46.85.10
    _litp create -t vm-alias -p /software/services/fmmed1/vm_aliases/node1_ipv6 -o alias_names="node1ipv6" address=fdde:4d7e:d471:10:105::100
    _litp create -t vm-network-interface -p /software/services/fmmed1/vm_network_interfaces/net2 -o network_name=ipv61 device_name=eth1 host_device=br_834 gateway6=fdde:4d7e:d471:0:0:834:0:1
    _litp update -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_network_interfaces/net2 -o ipv6addresses="fdde:4d7e:d471:0000::0834:105:401/64"
    _litp create -t vm-yum-repo -p /software/services/fmmed1/vm_yum_repos/os -o name=os base_url="http://Ms1105/6/os/x86_64"
    _litp create -t vm-yum-repo -p /software/services/fmmed1/vm_yum_repos/updates -o name=rhelPatches base_url="http://Ms1105/6/updates/x86_64/Packages"
    _litp create -t vm-package -p /software/services/fmmed1/vm_packages/rhel7_tree -o name=tree
    _litp create -t vm-package -p /software/services/fmmed1/vm_packages/rhel7_unzip -o name=unzip
    _litp create -t vm-ssh-key -p /software/services/fmmed1/vm_ssh_keys/support_key1 -o ssh_key="ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAxHQW3vVqhTikufpmOc+4XuJcCVscL4eDi3ahLKuj61tdjfPN0+HF8fJh+4ckpOpttCoZwM1AaBwyZx1H4t1K78E9CBEPwb9ftd57h/eFD9CnPtRIIg1eVEqGNNvhh6tAobEFSAQ1AuBrO5ye+pPGEXlXSb5ZU9ZYYJg4wAhNFlVX6zWCq6BqvzTQ7h4YFK4Bk8ACFOMD10N7rQEo6TVIyzkKoW0/HV61o537YFRav0kw9ZFyqS9jjWtui08GR1yIyhXb2jOiw20B5BnyaG3CR+tBmK6+EXzLVdf2D+3Lpf6nV2X76O5jd4OG5XW0NOOaXbAcqCzPQ39fwwBzgag6Sw== root@Ms1105"


  elif [ $n4 -eq 3 ]; then

    # remove from inherited item
    _litp remove -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_aliases/node1
    _litp remove -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_aliases/node1_ipv6
    _litp remove -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_network_interfaces/net2
    _litp remove -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_yum_repos/os
    _litp remove -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_yum_repos/updates
    _litp remove -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_packages/rhel7_tree 
    _litp remove -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_packages/rhel7_unzip 
    _litp remove -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_ssh_keys/support_key1

  else

    # reinherit
    _litp inherit -p  /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_network_interfaces/net2 -s /software/services/fmmed1/vm_network_interfaces/net2
    _litp update -p /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_network_interfaces/net2 -o ipv6addresses="fdde:4d7e:d471:0000::0834:105:401/64"

    _litp inherit -p  /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_aliases/node1 -s /software/services/fmmed1/vm_aliases/node1
    _litp inherit -p  /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_aliases/node1_ipv6 -s /software/services/fmmed1/vm_aliases/node1_ipv6
    _litp inherit -p  /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_yum_repos/os -s /software/services/fmmed1/vm_yum_repos/os
    _litp inherit -p  /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_yum_repos/updates -s /software/services/fmmed1/vm_yum_repos/updates
    _litp inherit -p  /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_packages/rhel7_tree -s /software/services/fmmed1/vm_packages/rhel7_tree 
    _litp inherit -p  /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_packages/rhel7_unzip -s /software/services/fmmed1/vm_packages/rhel7_unzip 
    _litp inherit -p  /deployments/d1/clusters/c1/services/multiple_SG/applications/fmmed1/vm_ssh_keys/support_key1 -s /software/services/fmmed1/vm_ssh_keys/support_key1

  fi

  # LITPCDS-10916 add SFS pools
  if [ $c -eq 5 ]; then
    _litp create -t sfs-pool -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl2 -o name="ST_Pool"
    _litp create -t sfs-filesystem -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl2/file_systems/managed1 -o path="/vx/ST105Pool2_managed1" size="40M" snap_size=200 cache_name=105cache1
    _litp create -t sfs-export -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl2/file_systems/managed1/exports/ex1 -o  ipv4allowed_clients=${sfs_fs_ipv4allowed_clients} options="rw,no_root_squash" 
    _litp create -t nfs-mount -p /infrastructure/storage/nfs_mounts/pool2managed1 -o export_path="/vx/ST105Pool2_managed1" provider="virtserv1" mount_point="/SFSPool2managed1" mount_options="soft" network_name=${sfs_network_name}
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n1/file_systems/pool2managed1 -s /infrastructure/storage/nfs_mounts/pool2managed1
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/file_systems/pool2managed1 -s /infrastructure/storage/nfs_mounts/pool2managed1

  elif [ $c -eq 10 ]; then
    _litp create -t sfs-pool -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl3 -o name="ST_Pool2"
    _litp create -t sfs-filesystem -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl3/file_systems/managed1 -o path="/vx/ST105Pool3_managed1" size="40M" snap_size=200 cache_name=105cache1
    _litp create -t sfs-export -p /infrastructure/storage/storage_providers/sfs_service_sp1/pools/pl3/file_systems/managed1/exports/ex1 -o  ipv4allowed_clients=${sfs_fs_ipv4allowed_clients} options="rw,no_root_squash" 
    _litp create -t nfs-mount -p /infrastructure/storage/nfs_mounts/pool3managed1 -o export_path="/vx/ST105Pool3_managed1" provider="virtserv1" mount_point="/SFSPool3managed1" mount_options="soft" network_name=${sfs_network_name}  
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n1/file_systems/pool3managed1 -s /infrastructure/storage/nfs_mounts/pool3managed1
    _litp inherit -p /deployments/d1/clusters/c1/nodes/n2/file_systems/pool3managed1 -s /infrastructure/storage/nfs_mounts/pool3managed1

  fi

  # LITPCDS-12973 create and remove network-hosts at runtime
  if [ $n2 -eq 1 ]; then
    _litp remove -p /deployments/d1/clusters/c1/network_hosts/nh8
    _litp remove -p /deployments/d1/clusters/c1/network_hosts/nh6
  else
    _litp create -t vcs-network-host -p /deployments/d1/clusters/c1/network_hosts/nh8 -o network_name=nfs ip=fdde:4d7e:d471:0002::0836:105:0301
    _litp create -t vcs-network-host -p /deployments/d1/clusters/c1/network_hosts/nh6 -o network_name=nfs ip=fdde:4d7e:d471:0002::0836:105:0201
  fi

  # TORF-107259 change default_nic_monitor 
  if [ $n10 -eq 1 ]; then
    _litp update -p /deployments/d1/clusters/c1 -o default_nic_monitor=mii
  elif [ $n10 -eq 2 ]; then
    _litp update -p /deployments/d1/clusters/c1 -o default_nic_monitor=netstat
  fi


  # If failplan flag is set then run a plan which will fail first every 5 plans
  if [ "$failplan_flag" = true ] && [ $n5 -eq 0 ]; then
   run_failplan   
   _litp show_plan
  fi

  _litp create_plan
  _litp show_plan
  _litp run_plan
  
  # Add sleep before testing add - TORF-171416
  sleep 60
  add_while_plan_is_running
  restore_while_plan_is_running

  plan_successful
  _litp show_plan

  _litp remove_plan

  # Remove snapshots
  if [ $n2 -eq 1 ]; then

    _litp remove_snapshot -n soak
    plan_successful

    _litp remove_snapshot
    plan_successful

  fi


  # change model and then restore
  # create/update sysparams

  _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_enm4 -o value="Ak1core.%e.pid%p.usr%u.sig%s.tim%t"
  _litp create -t sysparam -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_temp -o key="kernel.threads-max" value="4598222"

  _litp update -p /deployments/d1/clusters/c1/nodes/n2/configs/sysctl/params/sysctl_enm4 -o value="Ak2core.%e.pid%p.usr%u.sig%s.tim%t"
  _litp create -t sysparam -p /deployments/d1/clusters/c1/nodes/n2/configs/sysctl/params/sysctl_temp -o key="kernel.threads-max" value="4598222"

  _litp update -p /ms/configs/sysctl/params/sysctl_enm1 -o  value="Amscore.%e.pid%p.usr%u.sig%s.tim%t"
  _litp create -t sysparam -p  /ms/configs/sysctl/params/sysctl_temp -o key="kernel.threads-max" value="4598222"

  _litp restore_model


  # switch to maintenance mode and back again
  _litp update -p /litp/maintenance -o enabled=true

  add_while_plan_in_maintenance

  _litp update -p /litp/maintenance -o enabled=false

  # Once every 10 plans run short plan without locks (190067)
  if [ $n10 -eq 0 ]; then
    _litp update -p /ms/configs/sysctl/params/sysctl_enm1  -o  value=$c"Bmscore.%e.pid%p.usr%u.sig%s.tim%t"
    _litp update -p /deployments/d1/clusters/c1/nodes/n1/configs/sysctl/params/sysctl_enm4  -o  value=$c"Bmscore.%e.pid%p.usr%u.sig%s.tim%t"
    _litp create_plan --no-lock-tasks
    _litp show_plan
    _litp run_plan
    plan_successful
  fi


done 


