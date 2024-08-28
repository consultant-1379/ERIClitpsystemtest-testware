# UPDATE to use IP address range for your box
#!/bin/bash
set -x
litp create -p /infrastructure/networking/ip_ranges/r2 -t ip-range -o network_name=datanew start=10.46.90.146 end=10.46.90.160 subnet=10.46.90.0/21
litp create -p /infrastructure/networking/network_profiles/np2/networks/datanew -t network -o network_name=datanew interface=nic4
litp create -p /infrastructure/networking/network_profiles/np2/interfaces/nic4 -t interface -o interface_basename=eth4
litp create -p /infrastructure/systems/sys2/network_interfaces/nic_4 -t nic -o interface_name=eth4 macaddress='98:4B:E1:69:30:42'
litp create -p /infrastructure/systems/sys3/network_interfaces/nic_4 -t nic -o interface_name=eth4 macaddress='98:4B:E1:69:30:CA'
litp link -p /deployments/d1/clusters/c1/nodes/n1/ipaddresses/ip2 -t ip-range -o network_name=datanew address=10.46.90.150
litp link -p /deployments/d1/clusters/c1/nodes/n2/ipaddresses/ip2 -t ip-range -o network_name=datanew address=10.46.90.151
