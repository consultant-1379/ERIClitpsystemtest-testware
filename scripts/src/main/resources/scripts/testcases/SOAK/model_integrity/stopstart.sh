# UPDATE to use IP address range 4 your box
#!/bin/bash
set -x
litp create -p /software/items/fpack -t package-list -o name=fpack
litp create -p /software/items/fpack/packages/firefox -t package -o name=firefox
litp create -p /software/items/tpack -t package-list -o name=tpack
litp create -p /software/items/tpack/packages/telnet -t package -o name=telnet
litp create -p /infrastructure/networking/ip_ranges/r2 -t ip-range -o network_name=datanew start=10.46.90.146 end=10.46.90.160 subnet=10.46.90.0/21
litp create -p /infrastructure/networking/network_profiles/np2/networks/datanew -t network -o network_name=datanew interface=nic4
litp create -p /infrastructure/networking/network_profiles/np2/interfaces/nic4 -t interface -o interface_basename=eth4
litp create -p /infrastructure/systems/sys2/network_interfaces/nic_4 -t nic -o interface_name=eth4 macaddress='2C:59:E5:3D:B3:4A'
litp create -p /infrastructure/systems/sys3/network_interfaces/nic_4 -t nic -o interface_name=eth4 macaddress='2C:59:E5:3D:A3:92'
litp link -p /deployments/d1/clusters/c1/nodes/n1/ipaddresses/ip2 -t ip-range -o network_name=datanew address=10.46.90.146
litp link -p /deployments/d1/clusters/c1/nodes/n2/ipaddresses/ip2 -t ip-range -o network_name=datanew address=10.46.90.147
for (( c=1; c<=10000; c++ ))
do
  litp link -p /deployments/d1/clusters/c1/nodes/n1/items/fpack${c} -t package-list -o name=fpack
  litp update -p /deployments/d1/clusters/c1/nodes/n1/ipaddresses/ip2 -o address=10.46.90.146
  litp update -p /deployments/d1/clusters/c1/nodes/n2/ipaddresses/ip2 -o address=10.46.90.147
  litp create_plan
  echo "Plan for creating firefox and configuring eth4"
  litp show_plan
  # now check result of show_plan
  litp show_plan | grep "Install package \"firefox\""
  a=$?
  echo "Found install firefox on first plan ${a}"
  litp show_plan | grep "Configure interface \"eth4\""
  a=$?
  echo "Found configuring eth4 on first plan ${a}"
  litp run_plan
  litp create -p /software/items/e1pack${c} -t package-list -o name=e1pack${c}
  a=$?
  echo "Create when running output ${a}"
  sleep 1
  litp create -p /software/items/e2pack${c} -t package-list -o name=e2pack${c}
  b=$?
  echo "Create when running output ${b}"
  litp stop_plan
  # Depending on order plan is run, then it may or may not have installed 
  # firefox
  litp remove -p /deployments/d1/clusters/c1/nodes/n1/items/fpack${c}
  e=$?
  echo "Remove when stopping output ${e}"
  litp link -p /deployments/d1/clusters/c1/nodes/n1/items/tpack${c} -t package-list -o name=tpack
  d=$?
  echo "Create when stopping output ${d}"
  # Wait - as above plan will probably still be stoppping
  sleep 180
  litp show_plan | grep "Failed: 0"
  a=$?
  echo "Found Failed 0 on first plan ${a}"
  litp create_plan
  echo "Plan for modifying ip address"
  litp show_plan
  # now check result of show_plan
  litp show_plan | grep "Install package \"telnet\""
  a=$?
  echo "Notfound install telnet on second plan ${a}"
  litp show_plan | grep "Removing package \"firefox\""
  a=$?
  # Depending on plan order then firefox may not have been installed, on
  # first run, so therefore firefox IS valid to not be in this plan, as
  # may have removed it before it was configured
  echo "Notfound remove firefox on second plan ${a}"
  litp show_plan | grep "Configure interface \"eth4\""
  a=$?
  echo "Found configuring eth4 on second plan ${a}"
  litp remove_plan
  # Now repeat create and delete as should have failed when stopping, so add
  # now stopped
  litp remove -p /deployments/d1/clusters/c1/nodes/n1/items/fpack${c}
  e=$?
  echo "Remove when stopped output ${e}"
  litp link -p /deployments/d1/clusters/c1/nodes/n1/items/tpack${c} -t package-list -o name=tpack
  d=$?
  echo "Create when stopped output ${d}"
  litp create_plan
  echo "Plan for removing firefox, creating telnet and modifying ip address"
  litp show_plan
  # now check result of show_plan
  litp show_plan | grep "Install package \"telnet\""
  a=$?
  echo "Found install telnet on third plan ${a}"
  litp show_plan | grep "Remove package \"firefox\""
  a=$?
  echo "Notfound remove firefox on third plan ${a}"
  litp run_plan
  litp create -p /software/items/e3pack${c} -t package-list -o name=e3pack${c}
  a=$?
  echo "Create when running output ${a}"
  sleep 1
  litp create -p /software/items/e4pack${c} -t package-list -o name=e4pack${c}
  b=$?
  echo "Create when running output ${b}"
  sleep 360
  litp show_plan
  litp show_plan | grep "Failed: 0"
  a=$?
  echo "Found Failed 0 on third plan ${a}"
  litp remove -p /deployments/d1/clusters/c1/nodes/n1/items/tpack${c}
  e=$?
  echo "Remove when stopped output ${e}"
  litp update -p /deployments/d1/clusters/c1/nodes/n1/ipaddresses/ip2 -o address=10.46.90.148
  litp update -p /deployments/d1/clusters/c1/nodes/n2/ipaddresses/ip2 -o address=10.46.90.149
  litp create_plan
  echo "Plan for removing telnet and changing ip"
  litp show_plan
  # now check result of show_plan
  litp show_plan | grep "Remove package \"telnet\""
  a=$?
  echo "Found remove telnet on fourth plan ${a}"
  litp show_plan | grep "Configure interface \"eth4\""
  a=$?
  echo "Found configuring eth4 on fourth plan ${a}"
  litp run_plan
  litp create -p /software/items/e5pack${c} -t package-list -o name=e5pack${c}
  a=$?
  echo "Create when running output ${a}"
  sleep 1
  litp create -p /software/items/e6pack${c} -t package-list -o name=e6pack${c}
  b=$?
  echo "Create when running output ${b}"
  litp stop_plan
  litp show_plan
  # Wait - as above plan will probably still be stoppping
  sleep 180
  litp show_plan | grep "Failed: 0"
  a=$?
  echo "Found Failed 0 on fourth plan ${a}"
  litp create_plan
  echo "Plan for changing ip"
  litp show_plan
  # now check result of show_plan
  litp show_plan | grep "Configure interface \"eth4\""
  a=$?
  echo "Found configuring eth4 on fifth plan ${a}"
  litp run_plan
  litp create -p /software/items/e7pack${c} -t package-list -o name=e7pack${c}
  a=$?
  echo "Create when running output ${a}"
  sleep 360
  litp show_plan
  litp show_plan | grep "Failed: 0"
  a=$?
  echo "Found Failed 0 on fifth plan ${a}"
done

