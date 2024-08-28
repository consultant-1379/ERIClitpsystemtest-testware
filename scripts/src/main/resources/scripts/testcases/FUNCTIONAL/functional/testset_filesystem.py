#!/usr/bin/env python
'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     July 2015
@Last_Update: Jun 2016
@author:    Messers
@summary:   System Test Suite for LITP Storage Functionality
'''
import time
import sys
import socket
import exceptions
from litp_generic_test import GenericTest, attr
from litp_cli_utils import CLIUtils
from networking_utils import NetworkingUtils
from redhat_cmd_utils import RHCmdUtils
import os
import test_constants
import xml.etree.ElementTree as ET


class FsFunctional(GenericTest):
    """
    Description:
        These tests are checking the litp mechanism for updating
        and configuring VM.
    """
    def setUp(self):
        self.cli = CLIUtils()
        self.net = NetworkingUtils()
        self.rhcmd = RHCmdUtils()
        super(FsFunctional, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.error_list = []
        self.cmds = []
        self.local_filepath = os.path.dirname(__file__) + "/CDB_XML_files/"
        self.nfs_mount_paths = []
        self.model = self.get_model_names_and_urls()
        self.va_ip = "10.44.235.29"

    def tearDown(self):
        """
        Runs after every test
        """
        self.log_failures()
        self.log('info', "Run mco ping for network diagnostic help")
        self.run_mco_command(self.ms_node, "mco ping")
        self.log('info', "Run restore_model at teardown in case of any issues")
        self.execute_cli_restoremodel_cmd(self.ms_node)

    def find_fs(self, child, tree, xml_file):
        """
            loop through XML to find filesystems and then update
        """
        for item in child:
            if "file-system" in str(item.tag):
                # update a filesystem
                self.update_fs(child, tree, xml_file)
                return
            else:
                self.find_fs(item, tree, xml_file)

    def update_fs(self, root, tree, xml_file):
        """
        Updates a FS by increasing it's size by 1G or 4M
        """
        for child in root:
            if ((child.find('type').text == "ext4" or
                 child.find('type').text == "vxfs") and
                ("root" not in str(child.attrib)) and
                ("No_snap" not in str(child.attrib)) and
                ("vm_images" not in str(child.attrib))):
                self.log('info',
                         "tag {0} -- attribute {1}".format(child.tag,
                                                           child.attrib))
                size = child.find('size').text
                if size[-1] == "M":
                    new_size = str(int(size[:-1]) + 4) + size[-1]
                elif size[-1] == "G":
                    new_size = str(int(size[:-1]) + 1) + size[-1]
                else:
                    error_msg = ("Unexpected size unit for FS " +
                    str(child.attrib))
                    self.error_list.append(error_msg)
                    return
                self.log('info', "Old file size  >> {0} << "
                       "New file size = >> {1} <<".format(size, new_size))
                child.find('size').text = new_size
                tree.write(xml_file)

    def add_error_to_list(self, new_msg):
        """
            Prints error message
            updates error list
        """
        self.log('info', "Error message -->> " + new_msg)
        self.error_list.append("Error message -->> " + new_msg)

    def log_failures(self):
        """
            Prints a list of recorded errors if they are any
        """
        if self.error_list != []:
            self.log('info', " ##### FAILURES #####")
            for item in self.error_list:
                self.log('info', item)
            self.assertTrue(self.error_list == [], "### Failures found ##### ")

    def rm_snapshot(self):
        """
        Runs remove_snapshot command for all snapshots
        and waits for plan to complete successfully
        """
        snapshot_list = self.find(self.ms_node, "/snapshots", "snapshot-base",
                             assert_not_empty=False)
        if snapshot_list == []:
            self.add_error_to_list("No snapshots found for removal")
            return
        # Remove all existing snapshots
        for snap in snapshot_list:
            # Create argument for named snapshots
            snap_id = snap.split("/")[-1]
            if snap_id != "snapshot":
                argument = "-n " + snap_id
            else:
                argument = ""
            # run remove_snapshot commands
            self.execute_cli_removesnapshot_cmd(
                            self.ms_node, args=argument, expect_positive=True)
            # Check if plan completed successfully
            completed_successfully = self.wait_for_plan_state(
                self.ms_node, test_constants.PLAN_COMPLETE, timeout_mins=10)
            self.assertTrue(completed_successfully,
                            "Remove snapshot plan was not successful")

    def cre_snapshot(self):
        """
        Runs create_snapshot and waits for plan to complete
        """
        self.execute_cli_createsnapshot_cmd(
                                    self.ms_node, expect_positive=True)
        # Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, timeout_mins=10)
        self.assertTrue(completed_successfully,
                        "Create snapshot plan was not successful")

    def update_fs_size_using_XML(self, item_type):
        """
            Export infrastructure to XML file X
            In XML File increase all XML file sizes
            Load XML file.
        """
        count = 1
        export_url_list = self.find(self.ms_node, "/", item_type,
                             assert_not_empty=False)
        for export_url in export_url_list:
            xml_export = '/tmp/CDB_fun_03_' + item_type + str(count) + '.xml'
            xml_load = xml_export + "_loaded"

            self.log("info", "############################################"
                             "This is an xml file containing the model info"
                             "under /infrastructure/storage"
                             "############################################")

            # open file for writing to
            _, stderr, stdrc = self.execute_cli_export_cmd(
                self.ms_node, export_url, xml_export)
            self.assertEqual(stderr, [], "stderr Export CLI command fails")
            self.assertEqual(stdrc, 0, "stdrc Export CLI command fails")

            file_contents = self.get_file_contents(
                self.ms_node, xml_export)

            file1 = open(xml_load, 'w+')
            for item in file_contents:
                file1.write(item + "\n")
            while file1.closed == False:
                file1.close()
                self.log('info',
                         "Close handle to file {0}".format(xml_load))
            #sleep(10)
            tree = ET.parse(xml_load)
            root = tree.getroot()
            for child in root:
                self.find_fs(child, tree, xml_load)

            # Copy new XML file to node and load
            self.copy_file_to(self.ms_node, xml_load,
                              xml_load, root_copy=True,
                              add_to_cleanup=False)
            self.assertEqual(stderr, [], "stderr get file contents fails")
            self.assertEqual(stdrc, 0, "stdrc get file contents fails")

            self.cmds.append(self.cli.get_xml_load_cmd(
                export_url.split(item_type, 1)[0], xml_load, args="--merge"))

            # Cleanup local system
            os.remove(xml_load)
            count = count + 1

    def copy_and_merge_xml(self, xml_file, search_url, item_type, item_id):
        """
        Copies an Existing XML file onto MS.
        Finds a URL location
        merges XML at one spot above location
        """
        xml_file_in_tmp = "/tmp/" + xml_file
        # copy XML files to MS
        if not self.copy_file_to(self.ms_node,
                          self.local_filepath + xml_file,
                          xml_file_in_tmp,
                          root_copy=True,
                          add_to_cleanup=False):
            self.add_error_to_list("Error unable to copy file {0} to MS"
                               .format(xml_file))
            return False
        item_urls = self.find(self.ms_node, search_url, item_type)
        for item_url in item_urls:
            if item_id in item_url:
                # get XML load command
                self.cmds.append(self.cli.get_xml_load_cmd(
                        item_url, xml_file_in_tmp,
                        args="--merge"))
                return True
        self.add_error_to_list("Error unable to copy_and_merge_xml "
                               "xml file {0} for item type {1} "
                               "containing {2} in the URL"
                               .format(xml_file, item_type, item_id))
        return False

    def vgA_extend_LVM_and_FS_add_disks(self, sys_a, sys_b, vg_to_extend):
        """
         VG A - Extend existing LVM volume group,FS and add extra disks
        """
        self.copy_and_merge_xml("CDB_fun03_add_LVM_disks_A.xml",
                            "/infrastructure",
                            "blade",
                            sys_a)

        self.copy_and_merge_xml("CDB_fun03_add_LVM_disks_B.xml",
                            "/infrastructure",
                            "blade",
                            sys_b)

        self.copy_and_merge_xml("CDB_fun03_add_LVM_PD.xml",
                                "/infrastructure",
                                "collection-of-volume-group",
                                vg_to_extend)

    def vgB_extend_VxVM_and_FS_add_disks(self, sys_a, sys_b, vg_to_extend):
        """
        VG B (VxVM VG) - Extend size of existing VxVM FS and existing
            VxVm disks , also adding a new VxVm disk
        """
        # Add a new VxVm disk to the volume group and increase the
        # size of an existing VxFs and VxVm disk
        self.log("info", "Adding in new VxVm disks")
        self.copy_and_merge_xml("CDB_fun03_add_VxVM_disks.xml",
                                "/infrastructure",
                                "blade",
                                sys_a)

        # This time the size of VxVm disk "fun03_vxvm_2" will be increased
        self.copy_and_merge_xml("CDB_fun03_add_VxVM_disks.xml",
                                "/infrastructure",
                                "blade",
                                sys_b)

        self.copy_and_merge_xml("CDB_fun03_add_VxVM_PD.xml",
                                "/infrastructure",
                                "collection-of-volume-group",
                                vg_to_extend)

        self.log("info", "Increasing the size of existing VxVm disks")
        self.copy_and_merge_xml("CDB_fun03_increase_VxVM_Disk.xml",
                                "/infrastructure",
                                "blade",
                                sys_a)
        self.copy_and_merge_xml("CDB_fun03_increase_VxVM_Disk.xml",
                                "/infrastructure",
                                "blade",
                                sys_b)

    def vgC_add_LVM_VG_FS_across_2_disks(self, sys_a, sys_b, profile2add_vg):
        """
        VG C - Add VG and LVM FS across 2 disks
        """
        self.copy_and_merge_xml("CDB_fun03_add_LVM_disks_C.xml",
                            "/infrastructure",
                            "blade",
                            sys_a)

        self.copy_and_merge_xml("CDB_fun03_add_LVM_disks_D.xml",
                            "/infrastructure",
                            "blade",
                            sys_b)

        self.copy_and_merge_xml("CDB_fun03_add_lvm_vg_2PD_fs.xml",
                            "/infrastructure",
                            "collection-of-volume-group",
                            profile2add_vg)

    def add_sfs_nfs_items_for_each_cluster(self, cluster_name):
        """
        Description:
            Method to add sfs and nfs items required for test
        Args:
            cluster_name (string) = the name of the cluster taken from the
                                    cluster path
        Returns:
            path_to_new_nfs_mount (string) = path to the nfs mount under
            /infrastructure in the model
        """

        is_va_flag = self.is_va()

        if is_va_flag == True:
            sfs_clientaddr_ip = "10.44.235.106"
            nfs_clientaddr_ip = "10.44.86.75"
            nas_network_name = "net898"
            subnet = "10.44.235.0/24"
            if cluster_name == "c1":
                sfs_clientaddr_ip = "10.44.235.104"
                nfs_clientaddr_ip = "10.44.86.73"
        else:
            sfs_clientaddr_ip = "10.44.86.225"
            nfs_clientaddr_ip = "10.44.86.75"
            nas_network_name = "net837"
            subnet = "10.44.86.192/26"
            if cluster_name == "c1":
                sfs_clientaddr_ip = "10.44.86.73"
                nfs_clientaddr_ip = "10.44.86.73"
                nas_network_name = "mgmt"
                subnet = "10.44.86.64/26"

        # Properties of managed SFS filesystem to be created
        sfs_fs_props = "path='/vx/ST_CDB_mgmt_sfs_{0}' size=50M " \
                       "cache_name=72cache snap_size=50".format(cluster_name)

        # Properties for new managed SFS export
        new_sfs_export_props = "ipv4allowed_clients={0} " \
                               "options='rw,no_root_squash'".format(subnet)

        # Find the path to the first sfs-service item in the model
        sfs_service_path = (self.find(self.ms_node, "/infrastructure",
                                      "sfs-service"))[0]

        self.log("info", "Filesystem will be added to sfs-service "
                         "'{0}'".format(sfs_service_path))

        # List of paths to collections of SFS filesystems
        sfs_fs_paths = self.find(self.ms_node, sfs_service_path,
                                 "collection-of-sfs-filesystem")

        # If there if a collection of sfs filesystems underneath the
        # sfs-service
        if sfs_fs_paths:
            # Path to managed SFS FS to be created
            path_to_add = sfs_fs_paths[0] + "/st_cdb_fs_{0}"\
                .format(cluster_name)

        # Add create command for the new managed SFS FS to list of commands
        self.add_create_command_to_list(path_to_add, "sfs-filesystem",
                                        sfs_fs_props)

        # Path to new managed sfs export
        new_sfs_export_path = path_to_add + "/exports/stcdb_exp_{0}"\
            .format(cluster_name)

        # Add the create command for the new sfs export to the list of commands
        self.add_create_command_to_list(new_sfs_export_path, "sfs-export",
                                        new_sfs_export_props)

        # Get the path to the virtual service
        virt_serv_path = (self.find(self.ms_node, sfs_service_path,
                                    "sfs-virtual-server"))[0]

        # Get the properties of the virtual service
        virt_serv_props = self.get_props_from_url(self.ms_node, virt_serv_path)

        # Name of virtual service
        virt_serv = virt_serv_props["name"]

        self.log("info", "sfs-virtual-server name : '{0}'".format(virt_serv))

        # Properties for the new nfs mount
        nfs_mount_props = "provider={0} network_name={1} " \
                          "mount_options=soft,intr,clientaddr={2} " \
                          "export_path=/vx/ST_CDB_mgmt_sfs_{3} " \
                          "mount_point=/STCDB_mgmt_sfs_fs_{3}"\
            .format(virt_serv,
                    nas_network_name,
                    sfs_clientaddr_ip,
                    cluster_name)

        # Path to new nfs mount
        path_to_new_nfs_mount = "/infrastructure/storage/nfs_mounts/" \
                                "STCDB_sfs_mount_{0}".format(cluster_name)

        self.nfs_mount_paths.append(path_to_new_nfs_mount)

        # Add the create command for the new nfs mount to the list of commands
        self.add_create_command_to_list(path_to_new_nfs_mount, "nfs-mount",
                                        nfs_mount_props)

        # Add unmanaged NFS share
        path_to_new_nfs_mount = "/infrastructure/storage/nfs_mounts/" \
                                "STCDB_nfs_mount_{0}".format(cluster_name)

        self.nfs_mount_paths.append(path_to_new_nfs_mount)

        # Properties of NFS Share
        nfs_mount_props = "provider=nfs1 network_name=mgmt " \
                          "mount_options=soft,intr,clientaddr={0} " \
                          "export_path=/home/admin/ST/" \
                          "nfs_share_dir_72/ST_CDB_nfs_{1} " \
                          "mount_point=/STCDB_mgmt_nfs_{1}"\
            .format(nfs_clientaddr_ip, cluster_name)

        # Add the create command for the new nfs mount to the list of commands
        self.add_create_command_to_list(path_to_new_nfs_mount, "nfs-mount",
                                        nfs_mount_props)

    def add_create_command_to_list(self, path, item_type, props):
        """
        Description:
            Method to add create commands to a list of commands to run
        Args:
            path (str): string of path in model
            type (str): item type in the model
            props (str): the properties that are being added
        """

        # Get the create command
        cmd = self.cli.get_create_cmd(path, item_type, props)

        # Add the create command to the list of commands to be run
        self.log("info", "Adding command '{0}' to list of commands to"
                         "run".format(cmd))
        self.cmds.append(cmd)

    def add_managed_SFS_FS_and_unmanaged_NFS(self):
        """
        1. Add a managed SFS filesystem to one node in cluster 'c1' and to one
          node in  cluster 'c2'
        2. Add an unmanaged NFS filesystem to one node in cluster 'c1' and to
          one node in cluster 'c2'
        """
        # For each cluster
        for cluster in self.model["clusters"]:
            # If there is two or more nodes in the cluster:
            if len(cluster["nodes"]) > 1:
                # Name of the cluster in the model
                cluster_name = cluster["url"].split("/")[-1]
                # Create the SFS and NFS items under /infrastructure required
                # for the test
                self.add_sfs_nfs_items_for_each_cluster(cluster_name)
                # Get the URL of the first node in the cluster
                node_path = cluster["nodes"][0]["url"]

                self.inherit_nfs_mount_on_node(node_path, cluster_name)

    def inherit_nfs_mount_on_node(self, node_path, cluster_name):
        """
        Description:
            Method to inherit the new nfs mounts under a given node path
        Args:
            node_path (str) = The URL of the node you want to inherit the nfs
                              mount on
            cluster_name (str) = The name of the cluster where the mount will
                                 be inherited
        Returns:
            inherit_paths (list) = list of urls where the mounts are to be
                                   inherited to
        """
        inherit_paths = []
        # For each new NFS mount path created
        for path in self.nfs_mount_paths:

            # Inherit the new nfs mount on the first node in the list
            inherit_path = node_path + "/file_systems/" \
                           + path.split("/")[-1]
            if cluster_name in path.split("/")[-1]:
                inherit_paths.append(inherit_path)
                # Get the inherit command for the new nfs mount
                cmd = self.cli.get_inherit_cmd(inherit_path, path)

                # Add the inherit command to the list of commands to be run
                self.log("info", "Adding command '{0}' to list of commands"
                                 " to run".format(cmd))
                self.cmds.append(cmd)
        return inherit_paths

    def increase_SFS_and_NFS_FS_size(self):
        """
        Increase SFS FS sizes and NFS FS sizes
        """
        self.copy_and_merge_xml("CDB_fun03_increase_SFS_FS.xml",
                                "/infrastructure",
                                "sfs-service",
                                "sfs_service_sp1")

    def find_and_update_ip(self, initial_ip, updated_ip):
        """
        Finds an IP in the model and update.
        Returns the host name of the node updated.
        """
        hostname = "unknown_host"
        # Check current status of the IP to be updated
        if not self.is_ip_pingable(self.ms_node, initial_ip):
            self.add_error_to_list("Could not ping " + initial_ip + " from MS")
        # Exit if IP that we are updating to is already in use
        self.assertFalse(self.is_ip_pingable(self.ms_node, updated_ip),
            "Exit as IP {0} we are updating to is in use".format(updated_ip))

        # Get MN and MS url
        node_urls = self.find(self.ms_node, "/", 'node',
                              assert_not_empty=False)
        node_urls.append("/ms")

        # Find IP to change in litp model
        ip_url = self.find_ipv4_in_model(self.ms_node, initial_ip)
        if ip_url == None:
            self.add_error_to_list("Could not find {0} in model"
                .format(initial_ip))
        else:
            self.execute_cli_update_cmd(self.ms_node, ip_url,
                props='ipaddress=' + updated_ip, expect_positive=True)
            # Find hostname of node where IP is to change
            for node_url in node_urls:
                if node_url in ip_url:
                    hostname = self.get_props_from_url(
                        self.ms_node, node_url, "hostname", show_option="")

        # Do an if config on node to be updated
        self.run_command(hostname, self.net.get_ifconfig_cmd())

        return hostname

    def find_and_update_ipv6(self, initial_ip, updated_ip):
        """
        Finds an IPv6 address in the model and updates.
        Returns the host name of the node updated.
        """
        hostname = "unknown_host"
        # Check current status of the IP to be updated
        if not self.is_ip_pingable(self.ms_node, initial_ip,
                                   timeout_secs=10, ipv4=False):
            self.add_error_to_list("Could not ping " + initial_ip + " from MS")
        # Exit if IP that we are updating to is already in use
        self.assertFalse(self.is_ip_pingable(self.ms_node, updated_ip,
                                             timeout_secs=10, ipv4=False),
            "Exit as IP {0} we are updating to is in use".format(updated_ip))

        # Get MN and MS url
        node_urls = self.find(self.ms_node, "/", 'node',
                              assert_not_empty=False)
        node_urls.append("/ms")

        # Find IP to change in litp model
        ip_url = self.find_ipv6_in_model(self.ms_node, initial_ip)
        if ip_url == None:
            self.add_error_to_list("Could not find {0} in model"
                .format(initial_ip))
        else:
            self.execute_cli_update_cmd(self.ms_node, ip_url,
                props='ipv6address=' + updated_ip, expect_positive=True)
            # Find hostname of node where IP is to change
            for node_url in node_urls:
                if node_url in ip_url:
                    hostname = self.get_props_from_url(
                        self.ms_node, node_url, "hostname", show_option="")

        # Do an if config on node to be updated
        self.run_command(hostname, self.net.get_ifconfig_cmd())

        return hostname

    def reboot_node(self, node):
        """ Reboot a node and wait for it to come up. """
        cmd = "/sbin/reboot"
        out, err, ret_code = self.run_command(node, cmd, su_root=True)
        self.assertTrue(self.is_text_in_list("The system is going down", out))

        self.assertEqual([], err)
        self.assertEqual(0, ret_code)

        self.assertTrue(self._node_rebooted(node))
        time.sleep(5)

    def _node_rebooted(self, node):
        """
            Verify that a node  has rebooted.
        """
        node_restarted = False
        max_duration = 1800
        elapsed_sec = 0
        # uptime before reboot
        up_time_br = self._up_time(node)
        while elapsed_sec < max_duration:
            # if True:
            try:
                # uptime after reboot
                up_time_ar = self._up_time(node)
                self.log("info", "{0} is up for {1} seconds"
                         .format(node, str(up_time_ar)))

                if up_time_ar < up_time_br:
                    self.log("info", "{0} has been rebooted"
                             .format(node))
                    node_restarted = True
                    break
            except (socket.error, exceptions.AssertionError):
                self.log("info", "{0} is not up at the moment"
                         .format(node))
            except:
                self.log("error", "Reboot check. Unexpected Exception: {0}"
                         .format(sys.exc_info()[0]))
                self.disconnect_all_nodes()

            time.sleep(10)
            elapsed_sec += 10

        if not node_restarted:
            self.log("error", "{0} not rebooted in last {1} seconds."
                     .format(node, str(max_duration)))
        return node_restarted

    def _up_time(self, node):
        """
            Return uptime of node
        """
        cmd = self.rhcmd.get_cat_cmd('/proc/uptime')
        out, err, ret_code = self.run_command(node, cmd, su_root=True)
        self.assertEqual(0, ret_code)
        self.assertEqual([], err)
        self.assertNotEqual([], out)
        uptime_seconds = float(out[0].split()[0])
        return uptime_seconds

    def _litp_up(self):
        """
            Verify that the MS has a working litp instance
        """
        litp_up = False
        max_duration = 300
        elapsed_sec = 0

        while elapsed_sec < max_duration:
            try:
                out, _, ret_code = self.execute_cli_show_cmd(
                    self.ms_node, "/deployments"
                )

                self.assertEqual(0, ret_code)
                self.assertNotEqual([], out)

                if self.is_text_in_list("collection-of-deployment", out):
                    self.log("info", "Litp is up")
                    litp_up = True
                    break
                else:
                    self.log("info", "Litp is not up.")

            except (socket.error, exceptions.AssertionError):
                self.log("info", "Litp is not up after {0} seconds"
                         .format(elapsed_sec))
            except:
                self.log("error", "LITP up check. Unexpected Exception: {0}"
                         .format(sys.exc_info()[0]))
            time.sleep(10)
            elapsed_sec += 10

        if not litp_up:
            self.log("error", "Litp is not up in last {0} seconds."
                     .format(str(max_duration)))
        return litp_up

    def get_nfs_mount_with_clientaddr_mount_option(self, expected_ip):
        """
        Description:
            Cycle through the nodes and find the node with clientaddr in
            its mount_options.
            When the Clientaddr mount option is found then it is checked for
            the expected value.
            Each node that has clientaddr as its mount option is added to a
            list to be returned.
        Args:
            expected_ip(string): IP passed in from test that is expected in
                                 clientaddr mount options
        Return:
             target_nodes(list): a list of nodes that has clientaddr as a mount
                                 option.
        """
        # Get each peer nodes name and url
        model_info = self.get_model_names_and_urls()
        # Create target_node list that will be updated every time a node is
        # found with clientaddr mount option set.
        target_nodes = []
        self.log("info",
                 "Finding path to nfs mount with clientaddr in mount option")
        # Cycle through every peer node in model to find nfs mounts
        for node in model_info["nodes"]:
            # Set the node url to check for nfs mount
            node_url = node["url"]
            # Check if the current node url has any nfs mounts
            mount_paths = self.find(self.ms_node,
                                    node_url,
                                    "nfs-mount",
                                    assert_not_empty=False)
            # If no nfs mount was found for current node log a message and
            # continue to next node
            if not mount_paths:
                self.log("info", "Node {0} does not have "
                                 "an nfs-mount".format(node["name"]))
            # When an nfs mount is found
            else:
                # For each path to an nfs mount check its mount options
                for path in mount_paths:
                    # Get mount option for current nfs mount
                    mount_option = \
                        self.get_props_from_url(self.ms_node,
                                                path,
                                                filter_prop="mount_options")
                    # if mount option contains expected IP
                    if expected_ip in mount_option:
                        self.log("info", "Node found with clientaddr "
                                         "mount option is "
                                         ": ".format(node["name"]))
                        found_node = [node["name"]]
                        # Add the node with expected IP in it's mount options
                        # to a list.
                        target_nodes.extend(found_node)
        # Assert at least one node was found with the clientaddr mount option
        self.assertTrue(target_nodes,
                "Target node with clientaddr mount "
                "option was not found")

        self.log("info", "Finished checking nodes for nfs mounts with "
                         "clientaddr mount option, "
                         "nodes found were {0}".format(target_nodes))
        return target_nodes

    def check_mount_on_node_for_clientaddr_config(self,
                                                  expected_ip,
                                                  target_nodes
                                                  ):
        """
        Description:
            Run a mount command on the peer node with an nfs mount with
            clientaddr specifed in its mount options.
            Check output of mount command to ensure correct IP has been applied
            for the clientaddr.
        Args:
            target_nodes(list): a list of nodes passed in to run the mount
                                command on.
            expected_ip(string): the IP passed in will be the IP to grep for
                                 while running the mount command on the node.
        """
        # command to run mount and pipe the output into a text
        # file stored in /tmp
        for node in target_nodes:
            # Construct mount command with grep
            mount_clientaddr_grep = "mount | grep 'clientaddr={0}'"\
                .format(expected_ip)
            # Run the mount with grep command
            _, stderr, rc = self.run_command(node,
                                             mount_clientaddr_grep,
                                             su_root=True)
            # Check the command ran successfully
            self.assertTrue(rc == 0, "Grep for clienataddr with "
                                     "correct IP address "
                                     "did not return anything")
            self.assertTrue(stderr == [], "stderr was not empty : {0}"
                            .format(stderr))

    def is_va(self):
        """
        Description:
            Method to determine if NAS Server is VA
        Args:
            NONE
        Returns:
            is_va(Boolean): true if NAS is VA false otherwise
        """
        path = "/infrastructure/storage/storage_providers/sfs_service_sp1"
        nas_ip = self.execute_show_data_cmd(self.ms_node, path,
                                            "management_ipv4",
                                            assert_value=False)
        self.log("info", "NAS mgmt IP '{0}'"
                         .format(nas_ip))
        is_va_flag = True
        if nas_ip != self.va_ip:
            is_va_flag = False
        return is_va_flag

    def inherit_stcdb_mounts(self, cluster_name):
        """
        Description:
            Method to inherit previously created nfs mounts onto new nodes and
            update the clientaddr mount option so that it has the correct IP
        Args:
            cluster_name (str) = The name of the cluster in the URL you want to
                                 inherit the mount to
        """
        # Required IP addresses depending on which cluster is being updated
        # And which NAS server - SFS or VA

        path = "/infrastructure/storage/storage_providers/sfs_service_sp1"
        nas_ip = self.execute_show_data_cmd(self.ms_node, path,
                                          "management_ipv4",
                                          assert_value=False)
        self.log("info", "NAS mgmt IP '{0}'"
                         .format(nas_ip))

        if nas_ip == self.va_ip:
            clientaddr_ip = "10.44.86.76"
            sfs_clientaddr_ip = "10.44.235.107"
            if cluster_name == "c1":
                clientaddr_ip = "10.44.86.74"
                sfs_clientaddr_ip = "10.44.235.105"

        else:
            clientaddr_ip = "10.44.86.76"
            sfs_clientaddr_ip = "10.44.86.226"
            if cluster_name == "c1":
                clientaddr_ip = "10.44.86.74"
                sfs_clientaddr_ip = clientaddr_ip

        # Find all mounts in the model
        mounts = self.find(self.ms_node, "/infrastructure", "nfs-mount")
        for mount in mounts:
            # If 'STCDB' is in the URL add it to list of nfs mounts to inherit
            if "STCDB" in mount:
                self.nfs_mount_paths.append(mount)

        # For each cluster in the model
        for cluster in self.model["clusters"]:
            # If the name of the cluster that the mounts are to be inherited
            # is present in the cluster url
            if cluster_name in cluster["url"]:
                self.log("info", "Inheriting nfs mounts on cluster '{0}'"
                         .format(cluster_name))
                # Pick the second node in the cluster
                node_path = cluster["nodes"][1]["url"]
                self.log("info", "The nfs mounts will be inherited under "
                                 "'{0}'".format(node_path))
                # Inherit the nfs mounts added in test_03_storage
                inherit_paths = self.inherit_nfs_mount_on_node(node_path,
                                                               cluster_name)
                # Run the list of commands created
                self.run_commands(self.ms_node, self.cmds)
                # For each of the inherited paths
                for path in inherit_paths:
                    # Get the current mount_options
                    mount_opts = self.get_props_from_url(self.ms_node, path,
                                                         "mount_options")
                    # Create the new mount_options with the updated
                    # clientaddr ip
                    if "STCDB_sfs" in path:
                        new_mount_ops = mount_opts.split("=")[0] + "=" + \
                            sfs_clientaddr_ip
                    else:
                        new_mount_ops = mount_opts.split("=")[0] + "=" + \
                            clientaddr_ip
                    # Get the command to update the mount with the new mount
                    # options
                    cmd = self.cli.get_update_cmd(path, "mount_options={0}"
                                                  .format(new_mount_ops))
                    # Run update command
                    self.run_command(self.ms_node, cmd, default_asserts=True)

    def check_show_plan_for_task(self, expected_ip):
        """
        Description:
            Check the output of a show_plan command, check if specified
            task_desc appears in plan and how many times.
        Args:
            expected_ip(string): the IP expected in the clientaddr task
                                 descriptions
        Returns:
            tasks_found(int): Number of times the expected task was found in
                              plan
        """
        tasks_found = 0
        plan_output, _, _ = self.execute_cli_showplan_cmd(self.ms_node)
        task_desc = 'Update "clientaddr" option to "{0}"'.format(expected_ip)
        for tasks in plan_output:
            if task_desc == tasks:
                self.log("info", "Task found in plan")
                tasks_found += 1
        self.assertTrue(tasks_found, "Expected task/s were not "
                                          "found in plan")
        self.log("info", "expected task was found in plan {0} times"
                 .format(tasks_found))
        return tasks_found

    @attr('all', 'non-revert', 'functional', 'P1', 'functional_tc03')
    def test_03_storage(self):
        """
        Description:
            Extend FS, add disks, add managed SFS filesystem,
            add unmanaged NFS filesystem, remove & create snapshots
        Actions:
            Remove existing snapshots (expect at least one)
            Export infrastructure to XML file X
            In XML File increase all XML file sizes
            VG A - Extend existing LVM and FS + add extra disk
            VG B (VxVM VG) - Extend size of existing VxVM FS and existing
            VxVm disks , also adding a new VxVm disk
            VG C - Add VG and LVM FS across 2 disks
            Add managed SFS filesystem and unmanaged NFS filesystem to the
              first node in cluster 'c1' and 'c2'
            Increase an SFS FS size and NFS FS sizes
            Re-order each cluster's dependency list
            Create and Run Plan.
            Create deployment snapshot.
        Results:
            The created plan is successful and a snapshot is created
            successfully
        """

        # Dot72 variables
        sys_2 = "sys2"
        sys_3 = "sys3"
        sys_4 = "sys4"
        sys_5 = "sys5"
        # sys_6 = "sys6"
        lvm_vg1 = "profile_1"
        vxvm_vg = "profile_2"
        profile = "profile_vm"
        """
        # dot 66 variables
        sys_2 = "sys2"
        sys_3 = "sys3"
        sys_4 = "sys2"
        sys_5 = "sys3"
        #sys_6 = "sys2"
        lvm_vg1 = "profile_1"
        vxvm_vg = "vg_vxvm_0"
        profile = "profile_1"
        """
        # Remove snapshots as cannot change filesystem_tem size otherwise
        self.log("info", "Removing existing deployment snapshots")
        self.rm_snapshot()
        # update file_system sizes
        self.log("info", "Updating all FS sizes")
        self.update_fs_size_using_XML("storage")
        # VG A - Extend existing LVM and FS + add extra disk
        self.log("info", "Extending LVM VG by "
                         "adding disks and increasing FS size")
        self.vgA_extend_LVM_and_FS_add_disks(sys_2, sys_3, lvm_vg1)
        # VG B - Extend size of existing VxVM FS and existing
        # VxVm disks , also adding a new VxVm disk
        self.log("info", "Increasing VxVm VG by "
                         "adding VxVm disks and increasing VxFS size")
        self.vgB_extend_VxVM_and_FS_add_disks(sys_2, sys_3, vxvm_vg)
        # VG C - Add VG and LVM FS across 2 disks
        self.log("info", "Adding LVM FS to be shared across 2 disks")
        self.vgC_add_LVM_VG_FS_across_2_disks(sys_4, sys_5, profile)
        # Add a managed SFS filesystem and an unmanaged NFS filesystem to one
        # node in cluster 'c1' and 'c2'
        self.log("info", "Adding a managed SFS filesystem and an "
                         "unmanaged NFS filesystem to one node in "
                         "cluster 'c1' and to one node in "
                         "cluster 'c2'")
        self.add_managed_SFS_FS_and_unmanaged_NFS()
        # Increase SFS FileSystem Size and NFS share sizes
        self.log("info", "Increasing a SFS FS size and NFS FS sizes")
        self.increase_SFS_and_NFS_FS_size()

        # Run Commands and create and run plan
        cmd_results = self.run_commands(self.ms_node, self.cmds,
                                        add_to_cleanup=False)

        # # Re-order cluster depdendencies
        # self.change_cluster_dependency_list(self.ms_node)

        # CREATE PLAN
        self.execute_cli_createplan_cmd(self.ms_node)

        # SHOW PLAN
        self.execute_cli_showplan_cmd(self.ms_node)

        # RUN PLAN
        self.execute_cli_runplan_cmd(self.ms_node)

        # Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, timeout_mins=60)

        self.assertTrue(completed_successfully,
                        "Update plan was not successful")
        self.log('info', cmd_results)

        if not self.is_std_out_empty(cmd_results):
            self.add_error_to_list("Std_outError running one or more " +
                                        "litp commands")
        if self.get_errors(cmd_results) != []:
            self.add_error_to_list("Error code running one or more " +
                                        "litp commands")

        self.cre_snapshot()
        self.log_failures()

    @attr('all', 'non-revert', 'functional', 'P1', 'functional_tc04')
    def test_04_update_MN_ip_for_mgmt_and_other_ip(self):
        """
        Description:
            On cluster2 node 1, update 2 IPV4 addresses
             mgmt network and one other
        Actions:
            On the MN
            Find and update the IPv4 address that is been used by mgmt
            Find and update the IPv4 address on a second network
        Results:
            Created plan should contain a Reboot task
            Plan should run to success and updated IP are reachable
        """

        # update dot75 IP
        initial_mgmt_ip = "10.44.86.75"  # mgmt IP of MN
        initial_898_ip = "10.44.86.225"  # IP of inf on 898 vlan
        updated_mgmt_ip = "10.44.86.93"
        updated_898_ip = "10.44.86.201"
        found = False
        self.find_and_update_ip(initial_mgmt_ip, updated_mgmt_ip)
        # find and update 898 IP and record hostname of system it's on
        rebooted_hostname = self.find_and_update_ip(initial_898_ip,
                                                    updated_898_ip)
        # Inherit the sfs and nfs mounts added in test_03_storage to node2
        # in c2
        self.inherit_stcdb_mounts("c2")
        # CREATE PLAN
        self.execute_cli_createplan_cmd(self.ms_node)

        # SHOW PLAN
        self.execute_cli_showplan_cmd(self.ms_node)
        plan_output = self.get_plan_task_states(
            self.ms_node, test_constants.PLAN_TASKS_INITIAL)

        # Check there is a Reboot task for node been updated
        for item in plan_output:
            if ((rebooted_hostname in item['MESSAGE']) &
                    ("Reboot" in item['MESSAGE'])):
                self.log('info', "Debug: Reboot task found for {0}"
                         .format(rebooted_hostname))
                found = True
        self.assertTrue(found, "Could not find Reboot task for {0}"
                                   .format(rebooted_hostname))

        # RUN PLAN
        self.execute_cli_runplan_cmd(self.ms_node)
        # Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, timeout_mins=60)
        self.assertTrue(completed_successfully,
                        "Update plan was not successful")

        # Do an if config on updated node
        # self.run_command(rebooted_hostname, self.net.get_ifconfig_cmd())

        # Update host properties file with new IP
        self.update_node_in_connfile(
                self.get_node_att(rebooted_hostname, "hostname"),
                updated_mgmt_ip,
                self.get_node_att(rebooted_hostname, 'username'),
                self.get_node_att(rebooted_hostname, 'password'),
                self.get_node_att(rebooted_hostname, 'nodetype'))

        # Check updated IP can be reached
        if not self.is_ip_pingable(self.ms_node, updated_mgmt_ip):
            self.add_error_to_list("Could not ping updated IP " +
            updated_mgmt_ip)
        # Check updated IP can be reached
        if not self.is_ip_pingable(self.ms_node, updated_898_ip):
            self.add_error_to_list("Could not ping updated IP " +
            updated_898_ip)

    @attr('all', 'non-revert', 'functional', 'P1', 'functional_tc05')
    def test_05_update_MS_ips_for_mgmt_and_ip_for_SFS_mount(self):
        """
        Description:
            On the MS , Update the mgmt network IPv4 & IPv6 addresses and the
            IPv4 address used by the NAS mounts (SFS or VA).
        Actions:
            On the MS
            Find and update the IPv4 that is been used by mgmt
            Find and update a IPv4 that is been used by NAS
            Find and update a IPv6 that is been used by mgmt
        Results:
            Plan should run to success and updated IP are reachable
        """

        # update dot72 IP
        initial_mgmt_ip = "10.44.86.72"  # mgmt IP of MS
        initial_mgmt_ipv6 = "fdde:4d7e:d471:0001::835:72:72"
        updated_mgmt_ip = "10.44.86.94"
        updated_mgmt_ipv6 = "fdde:4d7e:d471:0001::835:72:a072"

        is_va_flag = self.is_va()

        if is_va_flag == True:
            initial_sfs_ip = "10.44.235.103"  # IP of inf used by VA on MS
            updated_sfs_ip = "10.44.235.180"
        else:
            initial_sfs_ip = "10.44.86.222"  # IP of inf used by OLD SFS on MS
            updated_sfs_ip = "10.44.86.227"

        hostname = self.find_and_update_ip(initial_mgmt_ip, updated_mgmt_ip)
        self.assertTrue(hostname == self.ms_node, "Hostname returned for " +
            "mgmt IP {0} does not match MS {1}".format(hostname, self.ms_node))
        # find and update sfs IP and record hostname of system it's on
        hostname = self.find_and_update_ip(initial_sfs_ip, updated_sfs_ip)
        self.assertTrue(hostname == self.ms_node, "Hostname returned for SFS" +
                        " IP {0} does not match MS".format(initial_sfs_ip))
        # Find and update ipv6 address
        self.find_and_update_ipv6(initial_mgmt_ipv6, updated_mgmt_ipv6)

        #CREATE PLAN
        self.execute_cli_createplan_cmd(self.ms_node)

        # SHOW PLAN
        self.execute_cli_showplan_cmd(self.ms_node)
        self.get_plan_task_states(
            self.ms_node, test_constants.PLAN_TASKS_INITIAL)

        # RUN PLAN
        self.execute_cli_runplan_cmd(self.ms_node)
        # Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, timeout_mins=60)
        self.assertTrue(completed_successfully,
                        "Update plan was not successful")

        # Do an if config on updated node
        self.run_command(hostname, self.net.get_ifconfig_cmd())

        # Check updated IP can be reached
        if not self.is_ip_pingable(self.ms_node, updated_mgmt_ip):
            self.add_error_to_list("Could not ping updated IP " +
            updated_mgmt_ip)
        # Check updated IP can be reached
        if not self.is_ip_pingable(self.ms_node, updated_sfs_ip):
            self.add_error_to_list("Could not ping updated IP " +
            updated_sfs_ip)
        # Check updated IPv6 can be reached
        if not self.is_ip_pingable(self.ms_node, updated_mgmt_ipv6,
                                   timeout_secs=10, ipv4=False):
            self.add_error_to_list("Could not ping updated IP " +
            updated_mgmt_ipv6)
        # Reboot node for SFS mounts to get remounted
        self.reboot_node(self.ms_node)
        # Confirm litpd is up and running
        self.assertTrue(self._litp_up())

    @attr('all', 'non-revert', 'functional', 'P1', 'functional_tc06')
    def test_06_update_nfs_ip_to_remount_shares_with_clientaddr(self):
        """
        Description:
            On the MN (N1) on cluster (C1) ,
            Update mgmt IPv4 and IPv6 addresses on the node.
                NFS shares are mounted via this network
                The node being updated has an applied share who's mount options
                include clientaddr. This will generate a task to update the
                clieantaddr mount option for the IPV4 address being updated.
            Inherit the sfs and nfs mounts added in test_03_storage to
            node 2 in c1
        Actions:
            On the MN
            1. Find and update the mgmt net IPv4 address.
            2. Find and update the mgmt net IPv6 address.
        Results:
            Created plan should contain a Reboot task
            Created plan should contain a "Remount" task
            Created plan should contain a "Update clientaddr" task
            Plan should run to success and updated IP are reachable
        """

        # update dot76 IP
        initial_mgmt_ip = "10.44.86.73"  # mgmt IP of MN
        updated_mgmt_ip = "10.44.86.97"
        initial_mgmt_ipv6 = "fdde:4d7e:d471:0001::835:72:73"
        updated_mgmt_ipv6 = "fdde:4d7e:d471:0001::835:72:a073"

        # find and update mgmt IP and record hostname of system it's on
        remount_hostname = self.find_and_update_ip(
            initial_mgmt_ip, updated_mgmt_ip)
        # Find and update ipv6 address
        self.find_and_update_ipv6(initial_mgmt_ipv6, updated_mgmt_ipv6)
        # Inherit the sfs and nfs mounts added in test_03_storage to
        # node 2 in c1
        self.inherit_stcdb_mounts("c1")
        # CREATE PLAN
        self.execute_cli_createplan_cmd(self.ms_node)

        # SHOW PLAN
        self.execute_cli_showplan_cmd(self.ms_node)
        plan_output = self.get_plan_task_states(
            self.ms_node, test_constants.PLAN_TASKS_INITIAL)

        # Checks show_plan output for number of tasks with clientaddr mount
        # option with expected updated IP value ,
        # This will return a variable that should match the number of nfs
        # mounts that will be updated .
        # This check is done after plan has completed
        expected_tasks_found = self.check_show_plan_for_task(updated_mgmt_ip)

        # Check there is a Reboot task for node been updated
        found = False
        for item in plan_output:
            if ((remount_hostname in item['MESSAGE']) &
                    ("Reboot" in item['MESSAGE'])):
                self.log('info', "Debug: Reboot task found for {0}"
                         .format(remount_hostname))
                found = True
        self.assertTrue(found, "Could not find Reboot task for {0}"
                                   .format(remount_hostname))
        # Check there is a Remount task for node been updated
        found = False
        for item in plan_output:
            if ((remount_hostname in item['MESSAGE']) &
                    ("Remount" in item['MESSAGE'])):
                self.log('info', "Debug: Remount task found for {0}"
                         .format(remount_hostname))
                found = True
        self.assertTrue(found, "Could not find Remount task for {0}"
                                   .format(remount_hostname))

        # RUN PLAN
        self.execute_cli_runplan_cmd(self.ms_node)
        # Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, timeout_mins=60)
        self.assertTrue(completed_successfully,
                        "Update plan was not successful")
        # Enable debug after reboot
        self.turn_on_litp_debug(self.ms_node)
        # Do an if config on updated node
        #self.run_command(remount_hostname, self.net.get_ifconfig_cmd())

        # Update host properties file with new IP
        self.update_node_in_connfile(
                self.get_node_att(remount_hostname, 'hostname'),
                updated_mgmt_ip,
                self.get_node_att(remount_hostname, 'username'),
                self.get_node_att(remount_hostname, 'password'),
                self.get_node_att(remount_hostname, 'nodetype'))

        # Check updated IP can be reached
        if not self.is_ip_pingable(self.ms_node, updated_mgmt_ip):
            self.add_error_to_list("Could not ping updated IP " +
            updated_mgmt_ip)
        # Check updated IPv6 can be reached
        if not self.is_ip_pingable(self.ms_node, updated_mgmt_ipv6,
                                   timeout_secs=10, ipv4=False):
            self.add_error_to_list("Could not ping updated IP " +
            updated_mgmt_ipv6)
        # Call method to check model for clientaddr mount option
        nodes_with_clientaddr = \
            self.get_nfs_mount_with_clientaddr_mount_option(updated_mgmt_ip)
        number_of_nodes_to_remount = len(nodes_with_clientaddr)
        # Call method to check if running mount on node returns expected
        # mount options
        self.check_mount_on_node_for_clientaddr_config(
            updated_mgmt_ip,
            nodes_with_clientaddr)
        # Assert that there is one task in plan per nfs mount with
        # clientaddr mount option
        self.assertTrue(expected_tasks_found == number_of_nodes_to_remount)

    @attr('all', 'non-revert', 'on_hold', 'P3', 'functional_tc07')
    def test_07_configure_sentinel_licence(self):
        """
        Configure Sentinel Licence
        Verify that the license has been imported using "lsmon" utility
        Verify that the license will be persisted
        Verify file permissions
        """
        licence_file = "CDB_FAT1023070_100.txt"
        licence_file_in_tmp = "/tmp/" + licence_file
        sentinel = "/opt/SentinelRMSSDK/"
        cmd_install = sentinel + "bin/lslic -F " + licence_file_in_tmp
        cmd_verify_license = sentinel + "bin/lsmon localhost"
        lservrc = sentinel + "licenses/lservrc"
        check_permissions = "ls -l " + lservrc

        # copy Licence files to MS
        self.assertTrue(self.copy_file_to(
            self.ms_node, self.local_filepath + licence_file,
            licence_file_in_tmp, root_copy=True, add_to_cleanup=False),
            "Error unable to copy file {0} to MS".format(licence_file))

        # run isntall command
        self.run_command(self.ms_node, cmd_install,
                            su_root=True, default_asserts=True)

        # Verify that the license has been imported using "lsmon" utility
        self.run_command(self.ms_node, cmd_verify_license,
                    su_root=True, default_asserts=True)

        # Verify ownership and permission
        file1 = self.get_file_contents(self.ms_node, licence_file_in_tmp)
        file2 = self.get_file_contents(self.ms_node, lservrc, su_root=True)
        print file1
        print file2
        self.assertEqual(file1, file2)

        # Verify file permissions
        stdout, _, _ = self.run_command(
                        self.ms_node, check_permissions,
                        su_root=True, default_asserts=True)
        #import pdb; pdb.set_trace()
        self.assertTrue("-rw-r-----" in stdout[0],
            "Incorrect permessions on {0}".format(lservrc))
