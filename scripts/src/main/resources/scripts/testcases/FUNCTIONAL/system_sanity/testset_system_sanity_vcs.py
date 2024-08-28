'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     May 2014
@author:    Vinnie McGuinness
@summary:   System test to check VCS setup correctly
            Assumptions:
                1 VCS cluster is present.
'''

from litp_generic_test import GenericTest, attr
from litp_cli_utils import CLIUtils
from vcs_utils import VCSUtils


class Vcs(GenericTest):
    """
        ST tests to check VCS cluster setup correctly
    """
    def setUp(self):
        """Run before every test"""
        super(Vcs, self).setUp()
        self.cli = CLIUtils()
        self.vcs_util = VCSUtils()
        self.mgmt_node = self.get_management_node_filename()
        self.targets = self.get_managed_node_filenames()
        self.targets.append(self.mgmt_node)
        self.count_res = 0
        self.pl_active = {}

    def tearDown(self):
        """run after each test"""
        super(Vcs, self).tearDown()

    def check_cmd_hastatus(self, node_test, node_names, fo_cs_list,
                           pl_cs_list, inf_list):
        """
        Run hastatus -sum command on node and check output is as expected
        Expected
            Nodes are found and are Running in SYSTEM STATE
            Nodes are found and have in service group under GROUP STATE
        """
        node_count = len(node_names)
        count_sys_running = 0
        cmd_hastatus = self.vcs_util.get_hastatus_sum_cmd()
        hastatus_list, stderr, rtcode = self.run_command(node_test,
                                                         cmd_hastatus,
                                                         su_root=True)
        self.assertNotEqual([], hastatus_list)
        self.assertEqual([], stderr)
        self.assertEqual(0, rtcode)

        # Nodes are found and are Running and Frozen is set to 0
        for item in hastatus_list:
            for node in node_names:
                if node in item:
                    if ("RUNNING" in item) & ("0" in item):
                        count_sys_running += 1
        # Check all VCS nodes are found
        self.assertTrue(count_sys_running == node_count,
                        (count_sys_running,
                         " RUNNING nodes found in SYSTEM STATE. Expected ",
                         node_count))
        self.findExpSG(hastatus_list, fo_cs_list, pl_cs_list, "Grp_CS")
        self.findExpInf(hastatus_list, inf_list, "Grp_NIC")

    def check_cmd_hagrp_state(self, node_test, inf_list, fo_cs_list,
                              pl_cs_list):
        """
        Run hagrp -state command on node and check output is as expected
        Expected
            Nodes are found
            Services are found
            interface are found
        """

        # Output from the hagrp -state command
        cmd = self.vcs_util.get_hagrp_state_cmd()
        hagrp_list, stderr, rtcode = self.run_command(node_test, cmd,
                                                      su_root=True)

        self.assertNotEqual([], hagrp_list)
        self.assertEqual([], stderr)
        self.assertEqual(0, rtcode)
        # for each node expect interface "Grp_NIC" ONLINE
        self.findExpSG(hagrp_list, fo_cs_list, pl_cs_list, "Grp_CS")
        self.findExpInf(hagrp_list, inf_list, "Grp_NIC")

    def findExpSG_Res_NIC(self, ret_list, fo_cs_list,
                          list_sg, res_str):
        """
        Check expected service group nic resources are present
        """
        for ser_grp in list_sg:
            online = 0

            if (ser_grp in fo_cs_list) or ((ser_grp + " ") in fo_cs_list):
                exp_num = 2 * 2  # if FO SG expect 4 resources
                #elif (ser_grp + " ") in fo_cs_list:
                #    exp_num = 2 * 2  # if FO SG expect 4 resources
            else:
                exp_num = int(self.pl_active[ser_grp]) * 2
            self.log('info', ("Expect to find {0} {1} ONLINE entry's "
                              "for SG {2}".format(exp_num, res_str, ser_grp)))

            for item in ret_list:
                if ((ser_grp in item) & (res_str in item) &
                        ("ONLINE" in item)):
                    self.log('info', "\tFound  {0}".format(item))
                    self.count_res += 1
                    online += 1
            if online == exp_num:
                self.log('info', "\tFound {0} for {1} ONLINE"
                         .format(online, res_str))
            else:
                self.assert_(False, "Expected {0} found {1} for {2} {3} ONLINE"
                             .format(exp_num, online, res_str, ser_grp))

    def findExpInf(self, ret_list, int_list, res_str):
        """
        Check all instances of nodes and interfaces stored in int_list
        are found in ret_list
        """
        self.log('info', "Check {0} are Present and ONLINE".format(res_str))
        count = 0
        length = len(int_list)
        while count < length:
            found = False
            node = int_list[count]
            count = count + 1
            inf = int_list[count]
            count = count + 1
            for item in ret_list:
                if ((node in item) & ((inf + " ") in item) &
                        (res_str in item) & ("ONLINE" in item)):
                    self.log('info', "\tFound {0}".format(item))
                    self.count_res += 1
                    found = True
            if found is False:
                self.assert_(False, "\nMissing interface {0} on node {1}"
                             .format(inf, node))

    def findExpSG(self, ret_list, fo_cs_list, pl_cs_list, res_str):
        """
        Check resources are present for each service group and are
        ONLINE or OFFLINE depending if there are FO or PL service groups
        """
        self.log('info', "Check {0} Res are Present and are ONLINE/OFFLINE"
                 .format(res_str))
        for ser_grp in fo_cs_list:
            offline = 0
            online = 0
            self.log('info', ("Find service group {0} and check status {1}"
                              .format(ser_grp, res_str)))
            for item in ret_list:
                if (ser_grp in item) & (res_str in item) & ("ONLINE" in item):
                    online += 1
                    self.log('info', "\tFound {0}".format(item))
                    self.count_res += 1
                if (ser_grp in item) & (res_str in item) & ("OFFLINE" in item):
                    offline += 1
                    self.log('info', "\tFound {0}".format(item))
                    self.count_res += 1
            self.log('info', "Check that {0} is a Fallover service group"
                     .format(ser_grp))
            self.assertTrue(online == 1,
                            "Unexpected {0} Num of nodes ONLINE for {1}"
                            .format(online, ser_grp))
            self.assertTrue(offline == 1,
                            "Unexpected {0} Num of nodes OFFLINE for{0}"
                            .format(offline, ser_grp))

        for ser_grp in pl_cs_list:
            offline = 0
            online = 0
            self.log('info', "Find service group {0} and check status"
                     .format(ser_grp))
            for item in ret_list:
                if (ser_grp in item) & (res_str in item) & ("ONLINE" in item):
                    online += 1
                    self.log('info', "\tFound {0}".format(item))
                    self.count_res += 1
                if (ser_grp in item) & (res_str in item) & ("OFFLINE" in item):
                    offline += 1
                    self.log('info', "\tFound {0}".format(item))
                    self.count_res += 1
            self.log('info', "Check that {0} is a parallel service group"
                     .format(ser_grp))
            self.assertTrue(online == int(self.pl_active[ser_grp]),
                            "Unexpected Num {0} of nodes ONLINE for {1}"
                            .format(online, ser_grp))
            self.assertTrue(offline == 0,
                            "Unexpected Num {0}of nodes OFFLINE for {1}"
                            .format(offline, ser_grp))

    def findExpFS(self, ret_list, fs_list, res_str):
        """
        Check all FS are present
        Assumption FS are VxVM and are part of FO system
        fs_list is an ordered list of services and fs
        """
        self.log('info', "Check {0} are Present and are ONLINE/OFFLINE"
                 .format(res_str))
        count = 0
        length = len(fs_list)
        while count < length:
            found_online = False
            found_offline = False
            service = fs_list[count]
            count = count + 1
            file_sys = fs_list[count]
            count = count + 1
            self.log('info', "\tLook for 2 {0} for SG {1} and FS {2} "
                    .format(res_str, service, file_sys))
            for item in ret_list:
                if ((service in item) & (file_sys in item) &
                        (res_str in item) & ("ONLINE" in item)):
                    self.log('info', "\tFound {0}".format(item))
                    self.count_res += 1
                    found_online = True
                elif ((service in item) & (file_sys in item) &
                      (res_str in item) & ("OFFLINE" in item)):
                    self.log('info', "\tFound {0}".format(item))
                    self.count_res += 1
                    found_offline = True
        if (found_online is False) | (found_offline is False):
            self.assert_(False, "\nMissing FS {0} on node {1}".format(
                file_sys, service))

    def get_vcs_clusters_url(self):
        """
        Search for cluster and return url in a list
        """
        # Assume one cluster. Find cluster URL
        clusters_url = self.find(self.mgmt_node, "/deployments", "vcs-cluster")
        self.assertTrue(clusters_url != [], "Did not find a VCS cluster")

        return clusters_url

    def get_vcs_nodes_url(self, cluster_url):
        """
        Search cluster for nodes and return url in a list
        """
        nodes_url = self.find(self.mgmt_node, cluster_url, "node")
        self.assertTrue(nodes_url != [], "Did not find a VCS nodes")
        self.log('info', "Found node url {0}".format(nodes_url))
        return nodes_url

    def get_vcs_cs_url(self, cluster_url):
        """
        Returns the list of Cluster Service URL from the model
        """
        vcs_cs_url = self.find(self.mgmt_node, cluster_url,
                               "vcs-clustered-service", assert_not_empty=False)

        self.log('info', "Service group URL found = {0} ".format(vcs_cs_url))
        return vcs_cs_url

    def get_cluster_service(self, cluster_url):
        """
        Find cluster service
        """
        # Find cluster URL
        fo_sg = []
        pl_sg = []
        vcs_cs_url = self.get_vcs_cs_url(cluster_url)
        for item in vcs_cs_url:
            standby_val = self.get_props_from_url(self.mgmt_node, item,
                                                  "standby", show_option="")
            if standby_val == '1':
                fo_sg = fo_sg + [item.split("/")[-1] + " "]
            elif standby_val == '0':
                new_pl_sg1 = item.split("/")[-1] + " "
                new_pl_sg2 = item.split("/")[-1] + "_"
                new_pl_sg3 = item.split("/")[-1]
                pl_sg = pl_sg + [new_pl_sg1]
                self.pl_active[new_pl_sg1] = self.get_props_from_url(
                    self.mgmt_node, item, "active", show_option="")
                self.pl_active[new_pl_sg2] = self.get_props_from_url(
                    self.mgmt_node, item, "active", show_option="")
                self.pl_active[new_pl_sg3] = self.get_props_from_url(
                    self.mgmt_node, item, "active", show_option="")
        self.log('info', "Fallover SG = {0}".format(fo_sg))
        self.log('info', "Parallel SG = {0}".format(pl_sg))
        return (fo_sg, pl_sg)

    def get_cluster_Res_App(self, cluster_url):
        """
        get_cluster_Res_App and sort them into FO and PL lists
        return lists of FO and Pl Res_App service groups
        """
        # Find cluster URL
        fo_sg = []
        pl_sg = []
        vcs_cs_url = self.get_vcs_cs_url(cluster_url)
        cluster_id = cluster_url.split("/")[-1]
        for item in vcs_cs_url:
            serv_name = self.get_props_from_url(
                            self.mgmt_node, item, "name", show_option="")
            # for lsb-runtime handling
            lsb_runtime_url = self.find(self.mgmt_node, item, "lsb-runtime",
                                         assert_not_empty=False)

            vm_services_url = self.find(self.mgmt_node, item, "vm-service",
                                        assert_not_empty=False)

            services_url = self.find(self.mgmt_node, item, "service",
                                     assert_not_empty=False)

            standby_val = self.get_props_from_url(self.mgmt_node, item,
                                                  "standby", show_option="")

            for service in services_url + vm_services_url + lsb_runtime_url:
                new_res = self.vcs.generate_application_resource_name(
                        serv_name, cluster_id, service.split("/")[-1])
                if standby_val == '1':
                    fo_sg.append(new_res)

                elif standby_val == '0':
                    pl_sg.append(new_res)
                    # Record number of active nodes for current PL service
                    self.pl_active[new_res] = self.get_props_from_url(
                        self.mgmt_node, item, "active", show_option="")

        self.log('info', "Fallover SG Res_App = {0}".format(fo_sg))
        self.log('info', "Parallel SG Res_App = {0}".format(pl_sg))
        return (fo_sg, pl_sg)

    def get_cluster_dep(self, cluster_url, hagrp_dep):
        """
        get a list of service dependency from the model
        """
        vcs_cs_url = self.get_vcs_cs_url(cluster_url)
        parent_child_list = []
        #children = []
        for item in vcs_cs_url:
            parent = [item.split("/")[-1]]
            dep_list = self.get_props_from_url(self.mgmt_node, item,
                                               "dependency_list",
                                               show_option="")
            if dep_list is not None:
                dependency = dep_list.split(",")
                for child in dependency:
                    found = False
                    for dep in hagrp_dep:
                        if ((parent[0] in dep) & (child in dep) &
                                ("online" in dep)):
                            found = True
                            dep_found = ("Found Parent {0} with child {1}"
                                         .format(parent[0], child))
                            self.log('info', dep_found)
                            parent_child_list.append(dep_found)
                    #if found != True:
                    self.assertTrue(found, ("Could not find dependency {0} {1}"
                                            .format(parent[0], child)))

        return parent_child_list

    def get_hostnames(self, nodes_url):
        """
        Get list of hostnames from URL list and return
        """
        self.log('info', "Get hostnames in {0}".format(nodes_url))
        node_hostnames = []
        for item in nodes_url:
            hostname = self.get_props_from_url(self.mgmt_node, item,
                                               "hostname", show_option="")
            node_hostnames = node_hostnames + [hostname]
        self.log('info', "Found the hostnames {0}".format(node_hostnames))
        return node_hostnames

    def get_net_interfaces(self, nodes_url):
        """
        Function gets a list of interfaces and the node there on
        """
        inf_list = []
        inf = ""
        for node_url in nodes_url:
            mn_hostnames = self.get_hostnames([node_url])
            inf_eth_url = self.find(self.mgmt_node, node_url, "eth",
                                    assert_not_empty=False)
            inf_vlan_url = self.find(self.mgmt_node, node_url, "vlan",
                                     assert_not_empty=False)
            inf_bond_url = self.find(self.mgmt_node, node_url, "bond",
                                     assert_not_empty=False)
            inf_bridge_url = self.find(self.mgmt_node, node_url, "bridge",
                                       assert_not_empty=False)

            inf_url = (inf_eth_url + inf_vlan_url + inf_bond_url +
                       inf_bridge_url)

            # Remove Interfaces that are not managed by VCS
            for url in inf_url:
                if_hb = self.get_props_from_url(self.mgmt_node, url,
                                                "network_name", show_option="")
                if_bond = self.get_props_from_url(self.mgmt_node, url,
                                                  "master", show_option="")
                if_bridge = self.get_props_from_url(self.mgmt_node, url,
                                                    "bridge", show_option="")
                self.log('info', if_hb)
                if if_hb is not None:
                    if ("heartbeat" in if_hb) | ("hb" in if_hb):
                        self.log('info', "Skip heartbeat network {0}"
                                 .format(if_hb))
                    elif if_bond is not None:
                        self.log('info', "Skip bond interface {0}"
                                 .format(if_hb))
                    else:
                        inf_list.append(mn_hostnames[0])
                        inf = self.get_props_from_url(self.mgmt_node, url,
                                                      "device_name",
                                                      show_option="")
                        inf = inf.replace(".", "_")
                        self.log('info', "Adding interface {0}".format(inf))
                        inf_list.append(inf)
                elif if_bond is not None:
                    self.log('info', "skip bond interface {0}".format(if_hb))
                elif if_bridge is not None:
                    self.log('info', "skip bridged inf {0}".format(if_hb))
                else:
                    inf_list.append(mn_hostnames[0])
                    inf = self.get_props_from_url(self.mgmt_node, url,
                                                  "device_name",
                                                  show_option="")
                    inf = inf.replace(".", "_")
                    self.log('info', "adding interface {0}".format(inf))
                    inf_list.append(inf)
        self.log('info', "List of interfaces found minus heartbeat "
                 "networks {0}".format(inf_list))
        return inf_list

    def edit_network(self, network, service_vips, count):
        """
        recursive function to add unique identifier to network_name of vip
        i.e. change net_traffic to net_traffic_1 or net_traffic_2
        """
        local_network = network + "_" + str(count)
        for item in service_vips:
            if local_network in item:
                count = count + 1
                return self.edit_network(network, service_vips, count)
        return local_network

    @classmethod
    def edit_nwk_pl(cls, in_vip_list, node_count):
        """
        recursive function to add unique identifier to network_name of vip
        i.e. change net_traffic to net_traffic_1 or net_traffic_2
        """
        out_vip_list = []
        done_list = []
        for item in in_vip_list:
            if item not in done_list:
                done_list.append(item)
                count = in_vip_list.count(item)
                act_count = count / node_count
                for inc in range(0, act_count):
                    vip = item + "_" + str(inc + 1)
                    out_vip_list.append(vip)
        return out_vip_list

    def get_vips(self, fo_cs_list, node_count, cluster_url):
        """
        Function to
            1. Return all vips on a cluster
            2. Return all SG with vips attached
        """
        vips = []
        cs_vip = []
        vcs_cs_url = self.get_vcs_cs_url(cluster_url)
        for service_url in vcs_cs_url:
            self.log('info', "Search URL  = {0}".format(service_url))
            vip_list_url = self.find(self.mgmt_node, service_url, "vip",
                                     assert_not_empty=False)
            if vip_list_url != []:
                service_vips = []
                sg_id = service_url.split("/")[-1]
                rt_id_url = self.find(self.mgmt_node, service_url,
                                      "lsb-runtime", assert_not_empty=False)
                if rt_id_url == []:
                    rt_id_url = self.find(self.mgmt_node, service_url,
                                          "reference-to-service",
                                          assert_not_empty=False)

                rt_id = rt_id_url[0].split("/")[-1]
                if sg_id in fo_cs_list:
                    reduced = 1
                else:
                    reduced = node_count
                cluster_id = cluster_url.split("/")[-1]
                if vip_list_url is not None:
                    network_list = []
                    for url in vip_list_url:
                        network_list = network_list + [self.get_props_from_url
                                                       (self.mgmt_node, url,
                                                        "network_name",
                                                        show_option="")]
                    pl_vips = self.edit_nwk_pl(network_list, reduced)
                    for items in pl_vips:
                        resource = ("Res_IP_" + cluster_id + "_" + sg_id + "_"
                                    + rt_id + "_" + items)
                        service_vips.append(resource)
                    vips = vips + service_vips
                    if vip_list_url != []:
                        cs_vip = cs_vip + [sg_id]
        return vips, cs_vip

    def get_res_dep(self, cluster_url):
        """
        Find service resources
        """
        ret_vip_res = []
        vcs_cs_url = self.get_vcs_cs_url(cluster_url)
        cluster_id = cluster_url.split("/")[-1]
        for ser_url in vcs_cs_url:
            vip_nwk = {}
            sg_id = ser_url.split("/")[-1]
            serv_name = self.get_props_from_url(
                            self.mgmt_node, ser_url, "name", show_option="")
            cs_name = self.vcs.generate_clustered_service_name(
                sg_id, cluster_id)
            # for lsb-runtime handling
            lsb_runtime_url = self.find(self.mgmt_node, ser_url, "lsb-runtime",
                                         assert_not_empty=False)

            vm_services_url = self.find(self.mgmt_node, ser_url, "vm-service",
                                        assert_not_empty=False)

            services_url = self.find(self.mgmt_node, ser_url, "service",
                                     assert_not_empty=False)

            active_val = self.get_props_from_url(self.mgmt_node, ser_url,
                                                  "active", show_option="")
            ha_config_url = self.find(self.mgmt_node, ser_url,
                            "ha-service-config",
                            assert_not_empty=False)
            for service in services_url + vm_services_url + lsb_runtime_url:
                app_id = service.split("/")[-1]
            app_res = self.vcs.generate_application_resource_name(
                        serv_name, cluster_id, app_id)
            # Look for FO service groups
            vip_urls = []
            vips = []
            self.pl_active[serv_name] = self.get_props_from_url(
                self.mgmt_node, ser_url, "active", show_option="")
            # Get all vips and store network_name
            vip_urls = self.find(self.mgmt_node, ser_url, "vip",
                                 assert_not_empty=False)
            # If there are multiple applications check ha_config items
            if len(ha_config_url) > 1:
                ret_vip_res = ret_vip_res + self.get_res_dep_ha_services(
                    ser_url, serv_name, cluster_id, vip_urls,
                    cs_name, ha_config_url)
            # single application serivce groups
            else:
                for vip_url in vip_urls:
                    network_name = self.get_props_from_url(
                        self.mgmt_node, vip_url, "network_name",
                        show_option="")
                    if network_name in vip_nwk:
                        vip_nwk[network_name] = vip_nwk[network_name] + 1
                    else:
                        vip_nwk[network_name] = 1
                    # get index value of network
                    index = vip_nwk[network_name] / int(active_val)
                    # if PL with multiple active ingore index 0
                    if index != 0:
                        new_vip = self.vcs.generate_ip_resource_name(
                            sg_id, cluster_id, app_id, network_name, index)
                        vips.append(new_vip)
                        res_nic_proxy = (
                            self.vcs.generate_nic_proxy_resource_name(
                                sg_id, cluster_id, network_name))
                        if [cs_name, app_res, new_vip] not in ret_vip_res:
                            ret_vip_res.append([cs_name, app_res, new_vip])
                            ret_vip_res.append([cs_name, new_vip,
                                               res_nic_proxy])
        return ret_vip_res

    def get_res_dep_ha_services(self, ser_url, serv_name, cluster_id,
                                vip_urls, cs_name, ha_config_url):
        """
        Get res and vip dependancies when there are multiple resources.
        """
        ret_res_dep = []
        ret_vip_res = []
        vip_nwk = {}
        vips = []
        sg_id = ser_url.split("/")[-1]
        for ha_config in ha_config_url:
            res_deps = self.get_props_from_url(self.mgmt_node, ha_config,
                                               "dependency_list",
                                               show_option="")
            service_id = self.get_props_from_url(self.mgmt_node, ha_config,
                                                 "service_id",
                                                 show_option="")
            active_val = self.get_props_from_url(self.mgmt_node, ser_url,
                                                  "active", show_option="")

            app_res = self.vcs.generate_application_resource_name(
                serv_name, cluster_id, service_id)
            if res_deps is not None:
                # store resource dependancies
                res_deps = res_deps.split(',')
                for dep_res in res_deps:
                    app_dep_res = self.vcs.generate_application_resource_name(
                        serv_name, cluster_id, dep_res)
                    ret_res_dep.append([cs_name, app_res, app_dep_res])
            else:
                # store vip resources for application
                index = 0
                vip_nwk = {}
                for vip_url in vip_urls:
                    network_name = self.get_props_from_url(self.mgmt_node,
                                                    vip_url,
                                                    "network_name",
                                                    show_option="")
                    if network_name in vip_nwk:
                        vip_nwk[network_name] = vip_nwk[network_name] + 1
                    else:
                        vip_nwk[network_name] = 1
                    # get index value of network
                    index = vip_nwk[network_name] / int(active_val)
                    # if PL with multiple active ingore index 0
                    if index != 0:
                        new_vip = (
                            self.vcs.generate_ip_resource_name_multi_srvs(
                            sg_id, cluster_id, network_name, index))
                        vips.append(new_vip)
                        res_nic_proxy = (
                            self.vcs.generate_nic_proxy_resource_name(
                                            sg_id, cluster_id, network_name))
                        if [cs_name, app_res, new_vip] not in ret_vip_res:
                            ret_vip_res.append([cs_name, app_res, new_vip])
                        if ([cs_name, new_vip, res_nic_proxy] not in
                            ret_vip_res):
                            ret_vip_res.append([cs_name, new_vip,
                                               res_nic_proxy])
        return ret_vip_res + ret_res_dep

    def get_vcs_fs(self, cluster_url):
        """
        find a list of reference-to-file-system in cluster
        """
        fs_list = []
        # Assume one cluster. Find cluster URL
        vcs_cs_url = self.get_vcs_cs_url(cluster_url)

        for item in vcs_cs_url:
            fs_url_list = self.find(self.mgmt_node, item,
                                    "reference-to-file-system",
                                    assert_not_empty=False)
            if fs_url_list != []:
                for fs_url in fs_url_list:
                    # add service group to ordered list
                    fs_list = fs_list + [item.split("/")[-1]]
                    # add filesystem to to ordered list
                    fs_list = fs_list + [fs_url.split("/")[-1]]
        return fs_list

    def check_dep(self, ret_list, service, res, parent, child):
        """
        Search for a single dependencies
        """
        found = False
        self.log('info', ("Check for SG {0} & Res {0} find Parent {0} & "
                          "Child {0}".format(service, res, parent, child)))
        for item in ret_list:
            if ((service in item) & (res in item) & (parent in item) &
                    (child in item)):
                self.log('info', "\tFound -> ".format(item))
                self.count_res += 1
                found = True
        if found is False:
            self.assert_(False, "Missing SG {0} & Res {1} with Parent {2} "
                         "& Child {3} ".format(service, res, parent, child))

    def check_hares_dep_fs(self, ret_list, fs_list):
        """
        Check all FS are present and have a Res_DG with parent Res_Mnt
        Check that all Res_Mnt have a parent Res_App
        Assumption FS are VxVM and are part of FO system
        fs_list is an ordered list of services and fs
        """
        self.log('info', "Check FS are Present and have dependancies")
        count = 0
        length = len(fs_list)
        while count < length:
            service = fs_list[count]
            count = count + 1
            file_sys = fs_list[count]
            count = count + 1

            self.check_dep(ret_list, service, file_sys, "Res_Mnt", "Res_DG")
            self.check_dep(ret_list, service, file_sys, "Res_App", "Res_Mnt")

    def check_hares_dep_vip(self, ret_list, service, res):
        """
        Check VIP is present and have a parent Res_IP with child Res_NIC_Proxy
        Check that vip has Parent Res_App and Res_IP child
        """
        self.check_dep(ret_list, service, res, "Res_IP", "Res_NIC_Proxy")
        self.check_dep(ret_list, service, res, "Res_App", "Res_IP")

    @attr('all', 'non-revert', 'system_sanity', 'P1', 'system_sanity_tc00')
    def test_00_call_check_vcs_cmd_hastatus_sum(self):
        """
        Description:
            Update config file with initial IP's as this is first TC
            On each node run "hastatus -sum" & check output
        Actions:
            1. Check system states are RUNNING and not Frozen
            2. Grp_CS (Cluster services Groups) are present and correct
            3. Grp_NIC (NIC groups) are present and correct
        Test created to do sanity check of system before
        ST automated test are run
        Result:System should be in the state expected.
        """

        for node in self.targets:
            if self.get_node_att(node, 'hostname') == 'dot73':
                self.update_node_in_connfile(
                        self.get_node_att(node, 'hostname'),
                        "10.44.86.73",
                        self.get_node_att(node, 'username'),
                        self.get_node_att(node, 'password'),
                        self.get_node_att(node, 'nodetype'))
            elif self.get_node_att(node, 'hostname') == 'dot75':
                self.update_node_in_connfile(
                        self.get_node_att(node, 'hostname'),
                        "10.44.86.75",
                        self.get_node_att(node, 'username'),
                        self.get_node_att(node, 'password'),
                        self.get_node_att(node, 'nodetype'))
            #elif self.get_node_att(node, 'hostname') == 'helios':
            #    self.update_node_in_connfile(
            #        self.get_node_att(node, 'hostname'),
            #        "10.44.86.71",
            #        self.get_node_att(node, 'username'),
            #        self.get_node_att(node, 'password'),
            #        "MS")

        self.test_01_check_vcs_cmd_hastatus_sum()

    @attr('all', 'non-revert', 'system_sanity', 'P1', 'system_sanity_tc01')
    def test_01_check_vcs_cmd_hastatus_sum(self):
        """
        Description:
            On each node run "hastatus -sum" & check output
        Actions:
            1. Check system states are RUNNING and not Frozen
            2. Grp_CS (Cluster services Groups) are present and correct
            3. Grp_NIC (NIC groups) are present and correct
        Result:System should be in the state expected.
        """
        clusters = self.get_vcs_clusters_url()
        for cluster_url in clusters:
            nodes_url = self.get_vcs_nodes_url(cluster_url)
            inf_list = self.get_net_interfaces(nodes_url)
            fo_cs_list, pl_cs_list = self.get_cluster_service(cluster_url)
            self.log('info', "PL active_list = {0}".format(self.pl_active))
            mn_hostnames = self.get_hostnames(nodes_url)
            # for node in nodes

            for node in nodes_url:
                node_filename = self.get_node_filename_from_url(self.mgmt_node,
                                                                node)
                self.check_cmd_hastatus(node_filename, mn_hostnames,
                                        fo_cs_list, pl_cs_list, inf_list)

    @attr('all', 'non-revert', 'system_sanity', 'P1', 'system_sanity_tc02')
    def test_02_check_vcs_cmd_hagrp_state(self):
        """
        Description:
            On each node run "hagrp -state" & check output
        Actions:
            1. Grp_CS (Cluster services Groups) are present and correct
            2. Grp_NIC (NIC groups) are present and correct
        Result:Cluster and NIC should be present and correct.
        """
        clusters = self.get_vcs_clusters_url()
        for cluster_url in clusters:
            nodes_url = self.get_vcs_nodes_url(cluster_url)
            inf_list = self.get_net_interfaces(nodes_url)
            fo_cs_list, pl_cs_list = self.get_cluster_service(cluster_url)

            # for node in nodes
            for node in nodes_url:
                node_filename = self.get_node_filename_from_url(self.mgmt_node,
                                                                node)
                self.check_cmd_hagrp_state(node_filename, inf_list, fo_cs_list,
                                           pl_cs_list)

    @attr('all', 'non-revert', 'system_sanity', 'P1', 'system_sanity_tc03')
    def test_03_check_vcs_cmd_gabconfig(self):
        """
        Description:
            On each node run "gabconfig -a" & check output
        Actions:
            1. run "gabconfig -a" on nodes
        Result:Number of Memberships match number of nodes in cluster
        """
        clusters = self.get_vcs_clusters_url()
        for cluster_url in clusters:
            count = 0
            nodes_url = self.get_vcs_nodes_url(cluster_url)
            node_count = len(nodes_url)
            for node in nodes_url:
                node_filename = self.get_node_filename_from_url(self.mgmt_node,
                                                                node)

                cmd_gabconfig = self.vcs_util.get_gabconfig_cmd()

                stdout, stderr, rtcode = self.run_command(node_filename,
                                                          cmd_gabconfig,
                                                          su_root=True)
                self.assertNotEqual([], stdout)
                self.assertEqual([], stderr)
                self.assertEqual(0, rtcode)

                for item in stdout:
                    if "membership" in item:
                        # Count characters in last word, match number of nodes
                        tmp = item.split()
                        count = len(tmp[(len(tmp) - 1)])

                # Assert that node contains the correct number of members
                self.assertTrue(count == node_count,
                                ("gabconfig expected ", node_count,
                                 " members, Found ", count))
                # Check all VCS nodes are found
                self.log('info', "gabconfig expected {0} members, Found {1}"
                         .format(node_count, count))

    @attr('all', 'non-revert', 'system_sanity', 'P1', 'system_sanity_tc04')
    def test_04_check_vcs_cmd_lltstat(self):
        """
        Description:
            On each node run "lltstat -n" & check output
        Actions:
            1. Node is found and there is an entry for each node in cluster
            2. All nodes are in an OPEN state
        Result:All nodes should be found and in open state for
        each node in cluster.
        """
        clusters = self.get_vcs_clusters_url()
        for cluster_url in clusters:
            self.log('info', "Find each Node in cluster in open state")
            nodes_url = self.get_vcs_nodes_url(cluster_url)
            node_count = len(nodes_url)

            # for node in nodes
            mn_hostnames = self.get_hostnames(nodes_url)
            cmd_hastatus = self.vcs_util.get_llt_stat_cmd('-n')
            for node in nodes_url:
                node_filename = self.get_node_filename_from_url(self.mgmt_node,
                                                                node)
                count = 0

                stdout, stderr, rtcode = self.run_command(node_filename,
                                                          cmd_hastatus,
                                                          su_root=True)
                self.assertNotEqual([], stdout)
                self.assertEqual([], stderr)
                self.assertEqual(0, rtcode)

                for item in stdout:
                    for node in mn_hostnames:
                        if node in item:
                            count += 1
                            self.assertTrue(("OPEN" in item),
                                            "State of lltstat is not OPEN")
                            self.log('info', "\tFound -> {0}".format(item))

                self.assertTrue(count == node_count,
                                (count, " OPEN nodes found. Expected ",
                                 node_count))

    @attr('all', 'non-revert', 'system_sanity', 'P1', 'system_sanity_tc05')
    def test_05_check_vcs_cmd_hares_state(self):
        """
        Description:
            On each node run "hares -state" & check output
        Actions:
            1. Res_App are Present and are ONLINE/OFFLINE
            2. Res_DG are Present and are ONLINE/OFFLINE
            3. Res_Mnt are Present and are ONLINE/OFFLINE
            4. Res_NIC_Proxy are Present and are ONLINE/OFFLINE
            5. Res_NIC are Present and are ONLINE
            6. Res_Phantom_NIC are Present and are ONLINE
            7. Res_IP Fallover VIPs are present
            8. Res_IP Parallel VIPs are present
        Result:Each nodes output should be present and online/offline.
        """
        clusters = self.get_vcs_clusters_url()
        for cluster_url in clusters:
            fo_cs_name_list, pl_cs_name_list = (self.get_cluster_Res_App
                                                (cluster_url))

            fs_list = self.get_vcs_fs(cluster_url)
            nodes_url = self.get_vcs_nodes_url(cluster_url)
            node_count = len(nodes_url)
            fo_cs_list, pl_cs_list = self.get_cluster_service(cluster_url)
            vips_list, vip_cs_list = self.get_vips(fo_cs_list, node_count,
                                                   cluster_url)
            res_list = self.get_res_dep(cluster_url)
            inf_list = self.get_net_interfaces(nodes_url)

            self.log('info', "fo_cs_name_list {0}".format(fo_cs_name_list))
            self.log('info', "pl_cs_name_list {0}".format(pl_cs_name_list))
            self.log('info', "vips_list {0}".format(vips_list))
            self.log('info', "vip_cs_list {0}".format(vip_cs_list))
            self.log('info', "fo_cs_list {0}".format(fo_cs_list))
            self.log('info', "pl_cs_list {0}".format(pl_cs_list))
            #self.log('info', "vip_res", vip_res))
            self.log('info', "res_list {0}".format(res_list))
            self.log('info', "inf_list {0}".format(inf_list))
            self.log('info', "self.pl_active {0}".format(self.pl_active))
            cmd = self.vcs_util.get_hares_state_cmd()
            # for node in nodes
            for node in nodes_url:
                self.count_res = 0
                node_filename = self.get_node_filename_from_url(self.mgmt_node,
                                                                node)
                # Output from the hares -state command
                hares_output, stderr, ret_cd = self.run_command(node_filename,
                                                                cmd,
                                                                su_root=True)
                self.assertEqual(0, ret_cd)
                self.assertEqual([], stderr)
                # Search for resources
                self.findExpSG(hares_output, fo_cs_name_list,
                               pl_cs_name_list, "Res_App")
                if fs_list != []:
                    self.findExpFS(hares_output, fs_list, "Res_DG")
                    self.findExpFS(hares_output, fs_list, "Res_Mnt")
                self.findExpSG_Res_NIC(hares_output, fo_cs_list,
                                       vip_cs_list, "Res_NIC_Proxy")
                self.findExpInf(hares_output, inf_list, "Res_NIC")
                self.findExpInf(hares_output, inf_list, "Res_Phantom_NIC")
                resource_list = []
                for res_item in res_list:
                    if ((res_item[1] not in resource_list) &
                        ("Res_IP_" in res_item[1])):
                        resource_list.append(res_item[1])
                    if ((res_item[2] not in resource_list) &
                        ("Res_IP_" in res_item[2])):
                        resource_list.append(res_item[2])
                self.log('info', "Find FO  Res_IP resources")
                for resource in resource_list:
                    for service_name in fo_cs_list:
                        service = service_name.replace(" ", "_")
                        if service in resource:
                            self.findExpSG(hares_output, [service], [],
                                           (resource + ' '))
                self.log('info', "Find PL Res_IP resources")
                for resource in resource_list:
                    for service_name in pl_cs_list:
                        service = service_name.replace(" ", "_")
                        if service in resource:
                            self.findExpSG(hares_output, [], [service],
                                           (resource + ' '))

                self.log('info', "Resource Expected = {0}"
                         .format(len(hares_output) - 1))
                self.log('info', "Resource Found = {0}"
                         .format(self.count_res))
                self.assertTrue(((len(hares_output) - 1) == self.count_res),
                                ("Expected %s but found %s " +
                                 " Resource") % (str(len(hares_output) - 1),
                                                 self.count_res))

    @attr('all', 'non-revert', 'system_sanity', 'P1', 'system_sanity_tc06')
    def test_06_check_vcs_cmd_hagrp_dep(self):
        """
        Description:
            On each node run "hagrp -dep" & check output
        Actions:
            1. For all groups check dependency
        Result:Dependencies should match the model.
        """
        clusters = self.get_vcs_clusters_url()
        for cluster_url in clusters:
            nodes_url = self.get_vcs_nodes_url(cluster_url)

            cmd = "/opt/VRTSvcs/bin/hagrp -dep"
            for node in nodes_url:
                node_filename = self.get_node_filename_from_url(self.mgmt_node,
                                                                node)
                # Output from the hares -dep command
                hagrp_dep, stderr, ret_cd = self.run_command(node_filename,
                                                             cmd, su_root=True)
                if "No Group dependencies" not in hagrp_dep[0]:
                    self.assertEqual(0, ret_cd)
                    self.assertEqual([], stderr)

                parent_child_list = self.get_cluster_dep(cluster_url,
                                                         hagrp_dep)

                self.run_command(node_filename, cmd, su_root=True)
                for item in parent_child_list:
                    self.log('info', item)

    @attr('all', 'non-revert', 'system_sanity', 'P1', 'system_sanity_tc07')
    def test_07_check_vcs_cmd_hares_dep(self):
        """
        Description:
            On each node run "hares -dep" & check output5
        Actions:
            1. For all FS Res check dependancies
            2. For all SG VIP Res check dependancies
        Result:Dependencies should match the model.
        """
        found = False
        clusters = self.get_vcs_clusters_url()
        for cluster_url in clusters:
            vip_res = self.get_res_dep(cluster_url)
            nodes_url = self.get_vcs_nodes_url(cluster_url)
            fs_list = self.get_vcs_fs(cluster_url)

            self.log('info', "vip_res = {0}".format(vip_res))
            cmd = "/opt/VRTSvcs/bin/hares -dep"
            for node in nodes_url:
                self.count_res = 0
                node_filename = self.get_node_filename_from_url(self.mgmt_node,
                                                                node)
                # Output from the hares -dep command
                hares_output, stderr, ret_cd = self.run_command(node_filename,
                                                                cmd,
                                                                su_root=True)
                if "No Resource dependencies" not in hares_output[0]:
                    self.assertEqual(0, ret_cd)
                    self.assertEqual([], stderr)
                    self.check_hares_dep_fs(hares_output, fs_list)
                    for model_dep in vip_res:
                        for cmd_dep in hares_output:
                            if ((model_dep[0] in cmd_dep) &
                                    (model_dep[1] in cmd_dep) &
                                    (model_dep[2] in cmd_dep)):
                                found_dep = cmd_dep
                                found = True
                        if found is True:
                            self.log('info', "Found dep -> {0}"
                                     .format(found_dep))
                            self.count_res = self.count_res + 1
                        self.assertTrue(found,
                                        "NOT FOUND -> Res_IP_ " +
                                        "with Res_NIC_Proxy "
                                        + str(model_dep))
                        found = False
                self.log('info', "Res Dependancy Expected {0}"
                         .format(len(hares_output) - 1))
                self.log('info', "Res Dependancy Found  {0}"
                         .format(self.count_res))
                self.assertTrue(((len(hares_output) - 1) == self.count_res),
                                "Expected {0} but found {1} Dependancies"
                                .format((len(hares_output) - 1),
                                self.count_res))
