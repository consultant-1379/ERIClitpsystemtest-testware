#!/bin/bash
#
# Sets up items needed for the deployment
#
# Usage:
#   ST_Deployment_18_pre_xml.sh <CLUSTER_SPEC_FILE>
#

if [ "$#" -lt 1 ]; then
    echo -e "Usage:\n  $0 <CLUSTER_SPEC_FILE>" >&2
    exit 1
fi

cluster_file="$1"
source "$cluster_file"

set -x


litp import /tmp/test_service_name-2.0-1.noarch.rpm 3pp
litp import /tmp/lsb_pkg/EXTR-lsbwrapper1-2.0.0.rpm 3pp
litp import /tmp/lsb_pkg/EXTR-lsbwrapper2-2.0.0.rpm 3pp
litp import /tmp/test_service-1.0-1.noarch.rpm 3pp

# Plugin Install
for (( i=0; i<${#rpms[@]}; i++)); do
    # import plugin
    litp import "/tmp/${rpms[$i]}" litp
    # install plugin
    expect /tmp/root_yum_install_pkg.exp "${ms_host_short}" "${rpms[$i]%%-*}"
done

# Import the ENM ISO 
expect /tmp/root_import_iso.exp "${ms_host}" "${enm_iso}"

# Set up passwords
litpcrypt set key-for-root root "${nodes_ilo_password}"
litpcrypt set key-for-sfs support "${sfs_password}"

# Switch on debug
litp update -p /litp/logging -o force_debug=true


# REPOS
declare -a repo=("pkgApps" "pckglist1" "pckglist2" "pckglist3")
for i in ${repo[@]}
do
 litp import /var/www/html/$i /var/www/html/$i 
done

# Create the md5 checksum file
/usr/bin/md5sum /var/www/html/images/vm_image_rhel7.qcow2 | cut -d ' ' -f 1 > /var/www/html/images/vm_image_rhel7.qcow2.md5

# Remove the ENM ISO after import
rm "${enm_iso}"

