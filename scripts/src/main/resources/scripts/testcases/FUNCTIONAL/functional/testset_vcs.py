#!/usr/bin/env python
'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Nov 2015
@author:    Messers
@summary:   System Test for Checking E2E VCS functionality
'''
from litp_generic_test import GenericTest, attr
from litp_cli_utils import CLIUtils
from redhat_cmd_utils import RHCmdUtils
from networking_utils import NetworkingUtils
import os
import test_constants


class VmFunctional(GenericTest):
    """
    Description:
        These tests are checking the litp mechanism for updating
        and configuring VM.
    """
    def setUp(self):
        self.cli = CLIUtils()
        self.rhcmd = RHCmdUtils()
        super(VmFunctional, self).setUp()
        self.ms_node = self.get_management_node_filename()
        # get one MN from each cluster
        self.targets = self.get_managed_node_filenames()
        if 'dot74' in self.targets:
            self.targets.remove('dot74')
        if 'dot76' in self.targets:
            self.targets.remove('dot76')
        if 'amosC3' in self.targets:
            self.targets.remove('amosC3')
        self.new_bridge_node = ""
        self.new_bridge_ip = "10.46.83.121"
        self.updated_vm_ip1 = "10.46.80.200"
        self.new_vm_ip = "10.46.83.37"
        self.ms_br2 = "10.46.80.2"
        self.ms_br3 = "10.46.83.2"
        self.updated_alias = "updated-alias"
        self.new_repo = "New_repo"
        self.ms_repo_dir = "newRepo_dir"
        self.pkg1 = 'gnome-bluetooth'
        self.parallel = '1'
        self.failover = '0'
        self.error_list = []
        self.cmds = []
        self.local_filepath = os.path.dirname(__file__) + "/CDB_XML_files/"
        self.test_passed = False

    def tearDown(self):
        """
        Runs after every test
        """
        self.log("info", "Beginning custom teardown/cleandown")
        if not self.test_passed:
            super(VmFunctional, self).tearDown()
        for item in self.error_list:
            print item

    def remove_items(self, remove_items):
        """
        Find items to remove from the model and save a property value
        for checking after plan
        """
        for item in remove_items:
            # Find all items of a paticular type
            item_path_list = self.find(self.ms_node, "/deployments",
                                       item['type'], assert_not_empty=False)

            for path in item_path_list:
                # Check if item is in remove items list
                if self.cli.get_path_name(path) == item['id']:
                    # Store value of property on item to be removed
                    item['val'] = self.execute_show_data_cmd(
                        self.ms_node, path, item['prop'])
                    # Create and store remove command
                    cmd = self.cli.get_remove_cmd(path)
                    self.cmds.append(cmd)
                    self.log('info', "added cmd to list >> {0}".format(cmd))
                    # mark item as been removed
                    item['action_taken'] = True
            if item['action_taken'] != True:
                # items been not found
                self.add_error_to_list(
                    'Item not found/removed >> {0}'.format(item))
        # return removed items dict with properties that can be checked
        return remove_items

    def check_items_are_removed(self, remove_items):
        """
        Checks that items of below tyes are removed
        Item = vcs-network-host: check IP is no longer in main.cf
        Item = vcs-clustered-service: check SG is not in "hastatus -sum" output
        Item = vcs-trigger: check trigger is no longer in main.cf
        """
        main_cf = test_constants.VCS_MAIN_CF_FILENAME
        self.log('info', 'remove_items list >> {0}'.format(remove_items))
        for item in remove_items:
            # this check only performing the action on items which were
            # successfully removed in the remove_items method and skipping
            # those that were not as they were already logged with an error
            if item['action_taken'] != True:
                continue

            # check vcs-network-hosts have been removed from main.cf file
            if item['type'] == "vcs-network-host":
                for node in self.targets:
                    # search by val( or IP in this case)
                    if self.search_string_in_file(main_cf, item['val'], node):
                        # if found add error message
                        self.add_error_to_list("String " + item['val'] +
                            " found in " + main_cf)
                        # store file where string found
                        self.store_file_on_ms(node, main_cf)

            # check vcs-clustered-service items removed from main.cf file
            elif item['type'] == "vcs-clustered-service":
                for node in self.targets:
                    # search by item id as this is used to create SG name
                    if self.search_string_in_file(main_cf, item['id'], node):
                        # if found add error message
                        self.add_error_to_list("String " + item['val'] +
                            " found in " + main_cf)
                        # store file where string found
                        self.store_file_on_ms(node, main_cf)

            elif item['type'] == "vcs-trigger":
                for node in self.targets:
                    # search by item id as this is used to create trigger name
                    if self.search_string_in_file(main_cf, item['id'], node):
                        # if found add error message
                        self.add_error_to_list("String " + item['val'] +
                            " found in " + main_cf)
                        # store file where string found
                        self.store_file_on_ms(node, main_cf)

            # unreconised item type been checked
            else:
                self.add_error_to_list(
                    'type not handled - more checks required >> ' +
                    '{0}'.format(item))

    def store_file_on_ms(self, node, filename):
        """
        Copys a file from a node and puts into /tmp on MS
        """
        store_file = "/tmp/CDB_" + node + "_" + filename.split('/')[-1]
        self.log('info', "Copy {0} from {1} on ms /tmp".format(filename, node))
        file_contents_ls = self.get_file_contents(node, filename, su_root=True)
        self.create_file_on_node(self.ms_node, store_file, file_contents_ls)

    def search_string_in_file(self, filename, search_string, node):
        """
        Confirm if string is found in a file on a node
        """
        # Create grep command
        cmd = self.rhcmd.get_grep_file_cmd(filename, search_string)
        # run command on node
        stdout, _, rc = self.run_command(node, cmd, su_root=True)
        self.log('info', "Found {0} in file {1} ".format(stdout, filename))
        # Check if string found message to failed list.
        if rc == 0:
            self.log('info', "String {0} found in {1} on node "
                "{2}".format(search_string, filename, node))
            return True
        else:
            self.log('info', "String {0} not found in file {1} "
                "on node {2}".format(search_string, filename, node))
            return False

    def find_update_property(self, url, ref, prop):
        """
        Find a url path and update item.
        """
        prop_url = sorted(self.find(self.ms_node, url, ref,
                                    assert_not_empty=False))
        cmd = self.cli.get_update_cmd(prop_url[0], prop)
        return cmd

    def find_add_item(self, url, ref, item_type, prop, id_name):
        """
        Find a url path and add item.
        """
        prop_url = self.find(self.ms_node, url, ref, assert_not_empty=False)

        cmd = self.cli.get_create_cmd(prop_url[0] + '/' + id_name,
                                      item_type, prop)
        return cmd

    def add_vm_with_xml(self):
        """
        Add a VM with XML snippets
        """
        # find correct cluster in deployments
        dep_services = self.find_url("/deployments", "vcs-cluster", "/c2")

        # copy files to MS
        self.copy_file_to(self.ms_node, self.local_filepath +
                          "/add_VM_dep.xml",
                          "/tmp/add_VM_dep.xml", root_copy=True,
                          add_to_cleanup=False)
        self.copy_file_to(self.ms_node, self.local_filepath +
                          "/add_VM_SW.xml",
                          "/tmp/add_VM_SW.xml", root_copy=True,
                          add_to_cleanup=False)
        # Load XML
        self.cmds.append(self.cli.get_xml_load_cmd("/software/",
                                                   "/tmp/add_VM_SW.xml",
                                                   args="--merge"))
        self.cmds.append(self.cli.get_xml_load_cmd(dep_services,
                                                   "/tmp/add_VM_dep.xml",
                                                   args="--merge"))

    def find_url(self, path, resource, id_str):
        """
        Finds a URL of a paticular type with string in URL
        """
        urls = self.find(self.ms_node, path,
                         resource, assert_not_empty=False)
        for item in urls:
            if id_str in item:
                return item

    def network_changes(self, vm_dep_url, vm_sw_url):
        """
        IP Update VM IP, use a different bridge,
        Add an extra interface
        Update a bridge IP
        """
        updated_mac = "0E:FF:AA"
        added_mac = "0E:FF:FF"
        # Dot 72
        update_prop = ("ipaddresses=" + self.updated_vm_ip1 +
                       " host_device=br6_444 network_name=net4vm" +
                       " mac_prefix=" + updated_mac + " -d gateway")
        create_prop = ("ipaddresses=" + self.new_vm_ip +
                       " network_name=net1vm device_name=eth4" +
                       " host_device=br5_911 gateway=10.46.83.1" +
                       " mac_prefix=" + added_mac)

        # IP Update VM IP, use a different bridge
        self.cmds.append(self.find_update_property(vm_dep_url,
                                                   "vm-network-interface",
                                                   update_prop))

        # Add a new vm-interface
        self.cmds.append(self.find_add_item(vm_sw_url,
                                            "collection-of-vm-network" +
                                            "-interface",
                                            "vm-network-interface",
                                            create_prop,
                                            "New_Net_id"))
        # Find the bridge to update
        nodes = self.find_url("/deployments", "node", "/n3")
        self.new_bridge_node = self.get_props_from_url(
            self.ms_node, nodes, "hostname", show_option="")
        print "Node to update bridge in is ", self.new_bridge_node
        bridge_url = self.find_url(nodes, "bridge", "/br5_911")
        print bridge_url
        self.cmds.append(self.find_update_property(bridge_url,
                                                   "bridge",
                                                   "ipaddress=" +
                                                   self.new_bridge_ip))
        return bridge_url

    def check_network_updates(self, vm_dep_url, updated_br):
        """
        Check network updated were completed successfully
        check all Mac prefix under url match model
        """
        updated_mac = "0E:FF:AA"
        added_mac = "0E:FF:FF"
        # Check the network update to eth0
        cmd_ifconfig = NetworkingUtils().get_ifconfig_cmd("eth0")
        cmd = self.rhcmd.get_grep_file_cmd(" ", self.updated_vm_ip1,
                                           file_access_cmd=cmd_ifconfig)
        self.check_vm(vm_dep_url,
                      "IP updated to " + self.updated_vm_ip1,
                      cmd,
                      "Expected IP " + self.updated_vm_ip1)
        # Check updated mac prefix
        cmd = self.rhcmd.get_grep_file_cmd(" ", updated_mac,
                                           file_access_cmd=cmd_ifconfig)
        self.check_vm(vm_dep_url,
                      "MAC updated to " + updated_mac, cmd,
                      "Expected MAC " + updated_mac)
        # Check the network addition of eth1
        cmd_ifconfig = NetworkingUtils().get_ifconfig_cmd("eth4")
        cmd = self.rhcmd.get_grep_file_cmd(" ", self.new_vm_ip,
                                           file_access_cmd=cmd_ifconfig)
        self.check_vm(vm_dep_url,
                      "Interface added to " + self.new_vm_ip, cmd,
                      "Expected IP " + self.new_vm_ip)

        # Check Added mac prefix
        cmd = self.rhcmd.get_grep_file_cmd(" ", added_mac,
                                           file_access_cmd=cmd_ifconfig)
        self.check_vm(vm_dep_url, "IP updated to " + added_mac, cmd,
                      "Expected IP " + added_mac)

        # Check the bridge was updated successfully
        device_name = self.get_props_from_url(self.ms_node, updated_br,
                                              "device_name", show_option="")

        cmd_ifconfig = NetworkingUtils().get_ifconfig_cmd(device_name)
        cmd = self.rhcmd.get_grep_file_cmd(" ", self.new_bridge_ip,
                                           file_access_cmd=cmd_ifconfig)

        print ("Confirm bridge on " + self.new_bridge_node +
               " contains " + self.new_bridge_ip)
        #self.check_vm(vm_dep_url, "MAC updated to " + added_mac, cmd,
        #              "Expected IP " + added_mac)
        _, _, rc = self.run_command(self.new_bridge_node, cmd,
                                    add_to_cleanup=False, su_timeout_secs=60)
        if rc != 0:
            self.add_error_to_list(self.new_bridge_node +
                " MN bridge IP " + self.new_bridge_ip + " not found")
        #self.assertTrue(rc == 0, "Bridge IP " + self.new_bridge_ip +
        #                " not found")
        # check all Mac prefix under url match model
        self.check_mac_prefixs(vm_dep_url)

    def check_mac_prefixs(self, vm_dep_url):
        """
        Function to check that all MacPrefix under url in
        references to network interface are correct on VM's
        """
        # Find all the network interfaces
        inf_list = self.find(self.ms_node, vm_dep_url,
                             "reference-to-vm-network-interface",
                             assert_not_empty=False)
        # loop through interfaces
        for inf_url in inf_list:
            mac_prefix = self.get_props_from_url(self.ms_node, inf_url,
                                                 "mac_prefix",
                                                 show_option="")
            # check if it has a MAC prefix
            if mac_prefix is not None:
                mac_prefix = mac_prefix.split(' ')
                dev_name = self.get_props_from_url(self.ms_node, inf_url,
                                                   "device_name",
                                                   show_option="").split(' ')
                print mac_prefix[0], dev_name[0]
                # Get ifconfig grep command
                cmd_ifconf = NetworkingUtils().get_ifconfig_cmd(dev_name[0])
                cmd = self.rhcmd.get_grep_file_cmd(" ", mac_prefix[0],
                                                   file_access_cmd=cmd_ifconf)
                self.check_vm(vm_dep_url,
                              " Check Mac Prefix " + mac_prefix[0],
                              cmd,
                              " Expected Mac Prefix " + mac_prefix[0])

    def update_vm_cpus(self, vm_url, updated_cpus):
        """
        # Update VM properties
        # Update number of CPU on a VM
        """
        # Update number of CPUs
        self.cmds.append(self.find_update_property(vm_url,
                                                   "vm-service",
                                                   "cpus=" +
                                                   updated_cpus))

    def check_update_vm_cpus(self, vm_url, updated_cpus):
        """
        Check that the CPU updated value is correct on VM
        """
        cmd = self.rhcmd.get_grep_file_cmd(self.rhcmd.cpu_info,
                                           "processor", "-c")

        # Check number of CPUs
        cpus = self.check_vm(vm_url,
                             "has " + updated_cpus + " cpus",
                             cmd,
                             "Expected a value to be returned ")
        if cpus[0] != updated_cpus:
            vm_name = self.get_props_from_url(self.ms_node, vm_url,
                                              "service_name",
                                              show_option="").split()
            self.add_error_to_list(vm_name[0] + " Expected: "
                                        + updated_cpus +
                                        " cpus Got: " + cpus[0])

    def update_vm_ram(self, vm_url, updated_ram):
        """
        # Update VM properties
        # Update amount or RAM on a VM
        """
        # Update RAM on a VM
        self.cmds.append(self.find_update_property(vm_url, "vm-service",
                                                   "ram=" +
                                                   str(updated_ram / 1000)
                                                   + "M"))

    def update_remove_add_vm_ram_mount(self):
        """
        1. Update a number of vm-ram-mount items
        2. Remove an existing vm-ram-mount item from the deployment
        3. Create a new vm-ram-mount item for a VM
        """
        find_urls = ["/deployments", "/ms"]

        # For ms and peer nodes:
        for url in find_urls:
            # 1. Update a number of vm-ram-mount items
            # Get a list of paths to existing vm-ram-mount items in the model
            vm_ram_mounts = self.find(self.ms_node, url, "vm-ram-mount",
                                      assert_not_empty=False)

            # For each path in the list:
            for path in vm_ram_mounts:
                # Get the properties for the vm-ram-mount
                props = self.get_props_from_url(self.ms_node, path)
                # If the vm-ram-mount item is of type ramfs, update it to be
                # tmpfs
                if props["type"] == "ramfs":
                    self.log("info", "vm-ram-mount '{0}' is type 'ramfs' - "
                                     "updating type to tmpfs".format(path))
                    # Get update command
                    cmd = self.cli.get_update_cmd(path, "type=tmpfs")
                    self.log("info", "Adding the following update command to "
                                     "list of commands to run")
                    self.log("info", cmd)
                    # Add command to the list of commands to be run
                    self.cmds.append(cmd)

                # If the vm-ram-mount item is of type tmpfs, update it to be
                # ramfs
                else:
                    self.log("info", "vm-ram-mount '{0}' is type 'tmpfs' - "
                                     "updating type to ramfs".format(path))
                    # Get update command
                    cmd = self.cli.get_update_cmd(path, "type=ramfs")
                    self.log("info", "Adding the following update command to "
                                     "list of commands to run")
                    self.log("info", cmd)
                    # Add command to the list of commands to be run
                    self.cmds.append(cmd)

            # 2. Remove an existing vm-ram-mount item from the deployment
            # If there is 3 or more vm-ram-mount items, remove one of them from
            # the model
            if len(vm_ram_mounts) > 2:
                remove_ram_mount = vm_ram_mounts[2]
                self.log("info", "vm-ram-mount '{0}' will be removed"
                         .format(remove_ram_mount))
                cmd = self.cli.get_remove_cmd(remove_ram_mount)
                self.log("info", "Adding the following remove command to list "
                                 "of commands to run")
                self.log("info", cmd)
                self.cmds.append(cmd)

            # Get list of vm-services under path
            vm_services = self.find(self.ms_node, url, "vm-service")
            # Create a list of vm-services that do not have a vm-ram-mount item
            for service in list(vm_services):
                service_path = service + "/"
                if (service_path in ram_path for ram_path in vm_ram_mounts):
                    self.log("info",
                             "Cannot create vm-ram-mount on vm-service '{0}' "
                             "as it already has one".format(service))
                    vm_services.remove(service)

            # 3. Create a new vm-ram-mount item for a VM
            # If there are any vm-services without a vm-ram-mount item, create
            #  a vm-ram-mount item on one of them
            if vm_services:
                # Take the first vm-service in the list
                vm_service = vm_services[0]
                # Get the path to vm-service that this vm-servics is inherited
                # from
                inherited_path = self.deref_inherited_path(self.ms_node,
                                                           vm_service)
                # Path to new vm-ram-mount
                path_to_add = inherited_path + "/vm_ram_mounts/stcdb_ram_mount"
                props_to_add = "type=ramfs mount_point=/stcdb " \
                               "mount_options=defaults"
                self.log("info", "Adding vm-ram-mount to vm-service {0}"
                         .format(vm_service))
                # Get create command for new vm-ram-mount
                cmd = self.cli.get_create_cmd(path_to_add, "vm-ram-mount",
                                              props_to_add)
                self.log("info", "Adding the following create command to the "
                                 "list of commands to run")
                self.log("info", cmd)
                # Add create command to list of command to run
                self.cmds.append(cmd)

    def check_update_vm_ram(self, vm_url, updated_ram):
        """
        Check that the RAM updated value is correct on VM
        """
        # Check VM RAM
        cmd = self.rhcmd.get_grep_file_cmd(self.rhcmd.mem_info, "MemTotal")
        ram_line = self.check_vm(vm_url,
                                 "Check memory",
                                 cmd,
                                 "Expected a value to be returned "
                                 + str(updated_ram))
        # Get memory value from string
        ram_str = ram_line[0].split()
        ram = int(ram_str[1])
        print ram
        # Confirm that returned ram value is within 10% of actual value
        if ((ram > updated_ram) |
                (ram < (updated_ram - (updated_ram / 10)))):
            vm_name = self.get_props_from_url(self.ms_node, vm_url,
                                              "service_name",
                                              show_option="").split()
            self.add_error_to_list(vm_name[0] + " Expected RAM of: "
                                        + str(updated_ram) +
                                        " Got: " + str(ram))

    def update_vm_image(self, vm_url):
        """
        # Update VM properties
        # Update image of a VM

        # Update all VMs using image 'image_with_ocf.qcow2' to use image
          'vm_test_image' so that 'image_with_ocf.qcow2' is
          unused and is removed from /var/lib/libvirt/images
        """
        prop = ("name=test_image source_uri=http://" + self.ms_br2 +
                "/images/STCDB_test_image.qcow2")
        # List of update image commands
        update_image_cmds = []

        # Find path to images in the model
        image_url = self.find(self.ms_node, "/", "collection-of-image-base",
                              assert_not_empty=False)
        # Path to new image item
        new_image_url = image_url[0] + '/new_image'

        # Add command to create new image item to the list of image commands
        update_image_cmds.append(self.cli.get_create_cmd(new_image_url,
                                                         "vm-image", prop))

        # Update image of a VM
        update_image_cmds.append(self.find_update_property(
            vm_url, "vm-service", "image_name=test_image"))

        # The vm-service will be updated if it uses any images in this list
        images_to_update = []
        update_image_name = ""
        # The old image file - this should no longer be present in
        # /var/lib/libvirt/images after test
        old_image_file = "image_with_ocf.qcow2"
        # The image file that the vm-services will use after test
        update_image_file = "vm_test_image.qcow2"

        # List of paths to vm-image items
        image_paths = self.find(self.ms_node, "/software", "vm-image")
        for path in image_paths:
            # Get properties of the image
            image_props = self.get_props_from_url(self.ms_node, path)

            # If the old image file name is in the source uri path, add the
            # image_name property to list of images to update
            if old_image_file in image_props["source_uri"]:
                self.log("info", "Adding '{0}' to the list of images that "
                                 "require update".format(image_props["name"]))
                images_to_update.append(image_props["name"])

            # Get the image_name for the image file to update to
            if update_image_file in image_props["source_uri"]:
                update_image_name = image_props["name"]

        self.assertTrue(images_to_update,
                        "There are no vm-image items using the image file "
                        "'{0}' that is required for this "
                        "test".format(old_image_file))

        self.assertTrue(update_image_name != "",
                        "There are no vm-image items using the image file "
                        "'{0}' that is required for this "
                        "test".format(update_image_file))

        self.log("info", "vm-services using the images in '{0}' will be "
                         "updated to use image_name='{1}'".format(
                            images_to_update, update_image_name))

        # list of VMs inherited on the nodes
        inherited_vm_paths = self.find(self.ms_node, "/deployments",
                                       "reference-to-vm-service")
        # list of vm-services to update
        vm_services_update = []
        for vm_path in inherited_vm_paths:
            # Get properties of the vm-service
            vm_props = self.get_props_from_url(self.ms_node, vm_path)

            # Add vm-service url to list to update if image_name is in list
            # of images to update
            if vm_props["image_name"] in images_to_update:
                self.log("info", "vm-service '{0}' will be updated to use "
                                 "image_name={1}".format(
                                    vm_props["service_name"],
                                    update_image_name))
                vm_services_update.append(vm_path)

        # For every vm-service in list, add update image_name to list
        # of commands
        for vm_service in vm_services_update:
            update_image_cmds.append(self.find_update_property(
                vm_service, "vm-service", "image_name={0}".format(
                    update_image_name)))

        # Run the update image commands
        cmd_results = self.run_commands(self.ms_node, update_image_cmds,
                                        add_to_cleanup=False)

        # Check for any errors running the update vm images commands
        if not self.is_std_out_empty(cmd_results):
            self.add_error_to_list("Std_outError running one or more "
                                   "litp commands")
        if self.get_errors(cmd_results):
            self.add_error_to_list("Error code running one or more "
                                   "litp commands")

    def check_update_vm_image(self, vm_url):
        """
        Create a command to check if updated image is used by
        checking if the file "Updated_Image" exists on VM in /tmp
        """
        cmd = self.rhcmd.get_grep_file_cmd("/tmp",
                                           "Updated_Image",
                                           file_access_cmd="/bin/ls")
        self.check_vm(vm_url,
                      "has updated Image ",
                      cmd,
                      "Expected image not present ")

    def check_remove_unused_images(self):
        """
        Check that the unused vm-image is removed from /var/lib/libvirt/images
        """
        # From update_vm_image method - expected not to be present in
        # /var/lib/libvirt/images after successful plan
        old_image_file = "image_with_ocf.qcow2"
        # Path to where the vm images are stored
        images_path = "/var/lib/libvirt/images"
        for node in self.targets:
            # List the images that are present
            present_images = self.list_dir_contents(node, images_path,
                                                    su_root=True)

            # If the unused image is present in any of the images, add error
            # message to list of errors
            for image in present_images:
                if old_image_file in image:
                    message = "Image '{0}' should have been deleted as it " \
                              "is unused".format(old_image_file)
                    self.log("info", message)
                    self.add_error_to_list(message)

    def update_vm_alias_baseURL(self, vm_url):
        """
        # Update VM properties
        # Update an alias of a VM
        # Update base URL of a VM repo
        """
        # find alias to update
        updated_alias_url = self.find_url(vm_url,
                                          "vm-alias",
                                          "helios")
        # Find repo to update
        updated_repo_url = self.find_url(vm_url,
                                         "vm-yum-repo",
                                         "os")
        # Update alias of a VM
        self.cmds.append(self.cli.get_update_cmd(updated_alias_url,
                                                 "alias_names=" +
                                                 self.updated_alias +
                                                 ",mars,helios,Ammeon-" +
                                                 "LITP-mars-VIP.ammeon.com"))
        # Update base URL of a repo
        self.cmds.append(self.cli.get_update_cmd(updated_repo_url,
                                                 "base_url=http://" +
                                                 self.updated_alias +
                                                 "/6/os/x86_64/Packages"))

    def check_update_vm_alias_baseURL(self, vm_dep_url):
        """
        Check alias was updated correctly
        """
        cmd = self.rhcmd.get_grep_file_cmd(test_constants.ETC_HOSTS,
                                           self.updated_alias)
        # Check Alias was added to VM
        self.check_vm(vm_dep_url,
                      "updated Alias " + self.updated_alias,
                      cmd,
                      "Expected Alias  " + self.updated_alias)

    def update_vm_hostname(self, vm_dep_url):
        """
        # Update VM properties
        # Update the hostname of a VM
        """
        service_url = self.find_url(vm_dep_url, "vm-service", "")
        service_name = self.get_props_from_url(self.ms_node, service_url,
                                          "service_name", show_option="")
        service_name = service_name.replace(' [*]', '')
        # find hostname to update
        if self.test_check_SG_type(vm_dep_url, self.failover):
            self.cmds.append(self.cli.get_update_cmd(
                service_url, "hostnames=newname-" + service_name))
        else:
            self.cmds.append(self.cli.get_update_cmd(
                service_url, ("hostnames=newname-1" + service_name +
                              ",newame-1" + service_name)))

    def check_vm_hostname(self, vm_dep_url):
        """
        Check if a hostname has been updated correctly
        """
        cmd = self.rhcmd.get_grep_file_cmd(test_constants.NODE_ATT_HOST,
                                           "newname-", file_access_cmd="")
        # Check Alias was added to VM
        self.check_vm(vm_dep_url, "updated hostname >>newname-<<",
                      cmd, " Expected hostname >>newname-<<")

    def check_pkt_ver_installed(self, vm_dep_url, pkg, ver):
        """
        Check if package is installed with correct version
        """
        cmd = self.rhcmd.get_yum_cmd("list " + pkg)
        yum_output = self.check_vm(vm_dep_url,
                                   "Check " + pkg + " version is " + ver,
                                   cmd,
                                   "Package " + pkg)

        pkg_intalled = False
        for i in xrange(len(yum_output) - 1):
            print yum_output[i]
            if "Installed" in yum_output[i]:
                pkg_intalled = True
                self.assertTrue(ver in yum_output[i + 1],
                                "Incorrect " + ver + "of" + pkg + " Found")
        if pkg_intalled is not True:
            vm_name = self.get_props_from_url(self.ms_node, vm_dep_url,
                                              "service_name",
                                              show_option="").split()
            self.add_error_to_list(vm_name[0] + " Package " + pkg +
                                        " not installed")

    def check_vm(self, vm_dep_url, msg, cmd, fail_msg):
        """
        Runs a command on a VM and checks return code = 0
        """
        vm_name = self.get_props_from_url(self.ms_node, vm_dep_url,
                                    "service_name", show_option="").split()

        print "Confirm VM " + vm_name[0] + " contains " + msg
        stdout, _, rc = self.run_command_via_node(self.ms_node,
                                                  vm_name[0],
                                                  cmd, "root",
                                                  "passw0rd")
        # Add message to failed list.
        if rc != 0:
            self.add_error_to_list(vm_name[0] + fail_msg + " not found")
        else:
            print "Found " + vm_name[0] + " contains " + msg
        return stdout

    def first_connect(self, vm_name):
        """
        Function to connect to each VM in order to setup RSA keys
        """
        # Run any command
        #cmd = self.rhcmd.get_grep_file_cmd("/tmp", "Setting RAS key",
        #                                   file_access_cmd="/bin/ls")

        self.log('info', "connect to vm {0}".format(vm_name))
        self.run_command_via_node(self.ms_node,
                                  vm_name,
                                  "df -h", "root",
                                  "passw0rd")

    def update_packages_repo(self, vm_sw_url):
        """
        Add a vm-alias NewMSAlias
        Add a new repo that uses NewMSAlias in it's base_url
        Add a vm-package from the new repo
        """
        new_alias = "NewMSAlias"
        # Add a vm-alias
        adr_prop = ('address=' + self.ms_br3 + ' alias_names=' + new_alias
                    + ',Ammeon-LITP-Tag-MS-VIP.ammeonvpn.com')
        self.cmds.append(self.find_add_item(vm_sw_url,
                                            "collection-of-vm-alias",
                                            "vm-alias",
                                            adr_prop,
                                            "New_Alias_id"))

        # Add repo base URL
        name_prop = ("name=" + self.new_repo + " base_url=http://" +
                     new_alias + "/" + self.ms_repo_dir)
        self.cmds.append(self.find_add_item(vm_sw_url,
                                            "collection-of-vm-yum-repo",
                                            "vm-yum-repo",
                                            name_prop,
                                            "New_repo_id"))

         # Add a package
        self.cmds.append(self.find_add_item(vm_sw_url,
                                            "collection-of-vm-package",
                                            "vm-package",
                                            "name=" + self.pkg1,
                                            "New_pkg_id"))

    def check_packages_repo(self, vm_dep_url):
        """
        # Check Alias was added to VM
        # Check Repo was added
        # Check A package was added
        """
        new_alias = "NewMSAlias"
        # Check Alias was added to VM
        cmd = self.rhcmd.get_grep_file_cmd(test_constants.ETC_HOSTS, new_alias)
        self.check_vm(vm_dep_url, "added Alias " + new_alias, cmd,
                      "Expected Alias " + new_alias)

        # Check repo was added
        cmd = self.rhcmd.get_grep_file_cmd(" ", self.new_repo,
                                           file_access_cmd="yum repolist")

        self.check_vm(vm_dep_url,
                      "added repo " + self.new_repo,
                      cmd,
                      "Repo " + self.new_repo)

        # Check A package was added
        cmd = self.rhcmd.get_grep_file_cmd(" ", "Installed",
                                           file_access_cmd="yum list "
                                           + self.pkg1)
        self.check_vm(vm_dep_url,
                      "added package " + self.pkg1,
                      cmd,
                      "Package " + self.pkg1)

    def store_vm_as_node(self, vm_url):
        """
        VM to be stored as a node so as it can be accessed
        """
        # Get the service name from each vm service model item
        # This will be used as node name in the connection data
        vm_name = self.get_props_from_url(self.ms_node, vm_url,
                                          "service_name", show_option="")
        vm_name = vm_name.split()

        # Get the IP of the VM
        vm_ip = self.get_vm_ip(vm_url)

        # Add name and IP to the node connection data
        self.add_vm_to_nodelist(vm_name[0], vm_ip[0], "root", "passw0rd")

        # Connect to the VM
        self.first_connect(vm_name[0])

    def get_vm_ip(self, vm_url):
        """
        Get VM IP address of all vm-network-interface in model
        """
        prop_url = self.find(self.ms_node, vm_url,
                             "reference-to-vm-network-interface",
                             assert_not_empty=False)
        for item in prop_url:
            network = self.get_props_from_url(self.ms_node, item,
                                              "network_name",
                                              show_option="").split()
            if network[0] == "net1vm":
                network_url = item
            if network[0] == "mgmt":
                network_url = item
        vm_ip = self.get_props_from_url(self.ms_node, network_url,
                                        "ipaddresses", show_option="")

        # Check if no property was returned for ipaddresses
        # This is the case for an IPv6 only VM
        if vm_ip is None:
            # Get the IPv6 addresses
            vm_ip = self.get_props_from_url(self.ms_node, network_url,
                                        "ipv6addresses", show_option="")

        ip_list = vm_ip.split(',')
        ip_list = ip_list[0].split(' ')
        return ip_list

    def update_vm_ssh_key(self, vm_sw_url):
        """
        VM to have a RSA key updated
        """
        ssh_key_prop = ('ssh_key="ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA' +
                        'wpI4la9paT3LYlDTZ5tpewMCXYA3WDO6Gl0Ml9iyvpgYW' +
                        'Y6z7jxfsbUQHFO9o9juNai5ENQoGNpEBrJojpdpZG9EDc' +
                        '5q5wdrZYiD2zBf0yY/zj1ftTBASrgMrnH37Ub2lKC1VHE' +
                        'XpHlz3MI7ClZgaxfiP8l1/EAMsxqfL2WOQJD2Lccyfypf' +
                        '9LTAhlwcGrU3/W/0GAsD6fsjMPsrTlPNc42y1vrBAdQZX' +
                        '+oeuYye+EMtHFveUrh0i3jvl6QI7e1flege9cKuKz0vM7' +
                        'HW1O6csbFly73AM5tFL7ZP2E5wSurIAeBBRj0eF5Oa5mM' +
                        'vG0pduxgZzhOMWjGkjCF9RpLhfz== updated@key"')

        # update ssh_key
        self.cmds.append(self.find_update_property(vm_sw_url,
                                                   "vm-ssh-key",
                                                   ssh_key_prop))
        """
        self.cmds.append(self.find_add_item(vm_sw_url,
                                            "collection-of-vm-ssh-key",
                                            "vm-ssh-key",
                                            ssh_key_prop,
                                            "key1"))
        """

    def create_vm_ssh_key(self, vm_sw_url):
        """
        VM to have a RSA key created
        """
        ssh_key_prop = ('ssh_key="ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA' +
                        'wpI4la9paT3LYlDTZ5tpewMCXYA3WDO6Gl0Ml9iyvpgYW' +
                        'Y6z7jxfsbUQHFO9o9juNai5ENQoGNpEBrJojpdpZG9EDc' +
                        '5q5wdrZYiD2zBf0yY/zj1ftTBASrgMrnH37Ub2lKC1VHE' +
                        'XpHlz3MI7ClZgaxfiP8l1/EAMsxqfL2WOQJD2Lccyfypf' +
                        '9LTAhlwcGrU3/W/0GAsD6fsjMPsrTlPNc42y1vrBAdQZX' +
                        '+oeuYye+EMtHFveUrh0i3jvl6QI7e1flege9cKuKz0vM7' +
                        'HW1O6csbFly73AM5tFL7ZP2E5wSurIAeBBRj0eF5Oa5mM' +
                        'vG0pduxgZzhOMWjGkjCF9RpLhFw== create@key"')

        # Create ssh_key
        self.cmds.append(self.find_add_item(vm_sw_url,
                                            "collection-of-vm-ssh-key",
                                            "vm-ssh-key",
                                            ssh_key_prop,
                                            "key1"))

    def check_vm_ssh_key(self, vm_dep_url):
        """
        Check VM RSA key has been added/updated correctly
        """
        ssh_key_url = self.find(self.ms_node, vm_dep_url,
                                "reference-to-vm-ssh-key",
                                assert_not_empty=False)
        for url in ssh_key_url:
            ssh_key = self.get_props_from_url(self.ms_node, url,
                                              'ssh_key',
                                              show_option="")
            ssh_key = ssh_key.replace(' [*]', '')
            cmd = self.rhcmd.get_grep_file_cmd('/root/.ssh/authorized_keys',
                                               ssh_key).replace('\"', '\'')

            self.check_vm(vm_dep_url,
                          "Updated SSH_KEY " + ssh_key,
                          cmd,
                          " Expected SSH_KEY " + ssh_key)

    def pingtest_vm_inf(self):
        """
        Test finds all vm-network-interface ip's in model
        and checks that these IP can be pinged from the MS
        """
        ip_list = []
        #self.is_ip_pingable(self.ms_node, "10.44.235.151")
        # Get a list of vm-network-interface in deployment
        vm_list = self.find(self.ms_node, "/deployments/",
                            "reference-to-vm-network-interface",
                            assert_not_empty=False)

        for link in vm_list:
            vm_ip = self.get_props_from_url(self.ms_node, link,
                                            "ipaddresses", show_option="")
            if vm_ip is None:
                continue
            ip_list += vm_ip.split(',')

        print "list of IP with duplicates: ", ip_list
        # remove inherited symbols
        ip_list = [ip.replace(' [*]', '') for ip in ip_list]
        # Remove Duplicates
        ip_list = list(set(ip_list))

        print "list of IP to test"
        print "ip_list=", ip_list
        for ips in ip_list:
            print "IP to Test", ips
            #if 'dhcp' != ips:
            if not self.is_ip_pingable(self.ms_node, ips):
                self.add_error_to_list("Could not ping " + ips +
                                            " from MS")

    @staticmethod
    def remove_unsed_vm(vm_list):
        """
        Removes services that distrupt the sorting of the VM list
        """
        add_to_end_list = []
        print "UnFiltered VM list = ", vm_list
        unused_vm = ['vmservice9',
                     'vmservice10',
                     'vmservice11',
                     'vmservice12',
                     'vmservice13',
                     'vmservice14',
                     'vmservice15',
                     'vmservice16',
                     'vmservice17',
                     'vmservice18',
                     'vmservice19',
                     'vmservice20',
                     'added_PL_VM',
                     'added_FO_VM'
                     ]
        for item in unused_vm:
            for vm_item in vm_list:
                if item in vm_item:
                    vm_list.remove(vm_item)
                    if item == 'vmservice10':
                        add_to_end_list.append(vm_item)
        print "Filtered VM list = ", vm_list
        return vm_list + add_to_end_list

    def update_vcs_parameters(self, vm_dep_url, vcs_prop):
        """
        Find VCS properties and uppdate
        """
        vm_dep_url = vm_dep_url.split('applications')[0]
        for item in vcs_prop:
            # Update image of a VM
            print "properties to update", vm_dep_url, item['prop'], item['val']
            self.cmds.append(self.find_update_property(
                vm_dep_url, item['type'], (item['prop'] + '=' + item['val'])))
        print self.cmds

    def check_vcs_parameters(self, vm_dep_url, vcs_prop):
        """
        Check VCS properties have been updated correctly
        """
        vm_dep_url = vm_dep_url.split('applications')[0]
        mn_names = self.get_mn_for_service_url(vm_dep_url)

        resource_id = self.get_resource_from_url(vm_dep_url)
        for res_app in vcs_prop:
            # CHECKING FOR VCS-TRIGGER
            if  res_app['type'] == 'vcs-trigger':
                cluster_id = vm_dep_url.split('/')[4]
                cs_id = vm_dep_url.split('/')[-1]
                sg_id = \
                self.vcs.generate_clustered_service_name(cs_id,
                                                     cluster_id)
                # CHECK VCS-TRIGGER SPECIFIED IN HAGRP PROPERTY
                cs_chk_cmd = \
                self.vcs.get_service_attribute_cmd(sg_id,
                                               'TriggersEnabled')
                stdout, stderr, ret_code = \
                self.run_command(mn_names[0],
                         cs_chk_cmd, su_root=True)
                self.assertEqual(0, ret_code)
                self.assertEqual([], stderr)
                # IF TRIGGER SPECIFIED IN LITP ENSURE IT HAS BEEN
                # CREATED IN VCS
                if res_app['val'] != '':
                    if res_app['val'] not in stdout[0]:
                        error_msg = (("Unexpected Value for {0} Expected {1} "
                                      "Found {2} url {3}").format(
                                      res_app['prop'], res_app['val'],
                                      stdout[0], vm_dep_url))
                        self.add_error_to_list(error_msg)
                # IF NO TRIGGER SPECIFIED IN LITP ENSURE NONE HAVE
                # BEEN CREATED IN VCS
                if res_app['val'] == '':
                    for item in ["NOFAILOVER"]:
                        if item in stdout[0]:
                            error_msg = \
                            (("Unexpected Value for {0} Expected \"{1}\" "
                              "Found {2} url {3}").format(
                              res_app['prop'], res_app['val'],
                              stdout[0], vm_dep_url))
                            self.add_error_to_list(error_msg)
                continue
            # skip dependancies check as these are checked in vcs sanity tests
            if  res_app['prop'] == 'initial_online_dependency_list':
                continue
            res_check_cmd = self.vcs.get_hares_resource_attr(resource_id,
                                                         res_app['res'])

            # checking cleanup command value vcs app
            stdout, stderr, ret_code = self.run_command(mn_names[0],
                         res_check_cmd, su_root=True)
            self.assertEqual(0, ret_code)
            self.assertEqual([], stderr)
            if res_app['type'] == 'vm-service' or res_app['type'] == 'service':
                if res_app['val'] not in stdout[0]:
                    error_msg = (("Unexpected Value for {0} Expected {1} "
                                 "Found {2} url {3}").format(
                                    res_app['prop'], res_app['val'],
                                    stdout[0], vm_dep_url))
                    self.add_error_to_list(error_msg)
            elif res_app['val'] != stdout[0]:
                error_msg = (("An unexpected Value for {0} Expected {1} "
                              "Found {2} url {3}").format(res_app['prop'],
                                                          res_app['val'],
                                                          stdout[0],
                                                          vm_dep_url))
                self.add_error_to_list(error_msg)

    def get_mn_for_service_url(self, vm_dep_url):
        """
        Return the MN a service is running on
        """
        node_names = []
        cluster_url = vm_dep_url.split('services')[0]
        node_urls = self.find(self.ms_node, cluster_url, 'node',
                              assert_not_empty=False)
        for item in node_urls:
            node_names.append(self.get_props_from_url(self.ms_node, item,
                                          "hostname", show_option=""))
        self.log('info', "Found Managed nodes {0}".format(node_names))
        return node_names

    def get_resource_from_url(self, prop_url):
        """
        Get a ResAPP from a URL
        """
        # DETERMINING THE TYPE OF SERVICE CONTAINTED WITHIN
        # CLUSTERED SERVICE
        # 1 - CHEKCING IF VM-SERVICE
        app_url = sorted(self.find(self.ms_node, prop_url, "vm-service",
                            assert_not_empty=False))
        # 2 - CHECKING IF SERVICE
        if app_url == []:
            app_url = sorted(self.find(self.ms_node, prop_url, "service",
                                assert_not_empty=False))
        # 3 - CHECKING IF LSB-RUNTIME
        if app_url == []:
            app_url = sorted(self.find(self.ms_node, prop_url, "lsb-runtime",
                                assert_not_empty=False))
        self.log('info', "prop_url = {0}".format(prop_url))
        app_ser_id = app_url[0].split("/")[-1]
        cluster_id = app_url[0].split("/")[4]
        ser_name = self.get_props_from_url(self.ms_node, prop_url,
                                     "name", show_option="").split()
        resource_id = self.vcs.generate_application_resource_name(
            ser_name[0], cluster_id, app_ser_id)
        self.log('info', "Resource to check is {0}".format(resource_id))
        return resource_id

    def test_check_SG_type(self, vm_dep_url, parallel_val):
        """
        Checks that a SG is PL or FL
        Parameters: parallel_val
            1 = Parallel
            0 = Failover
        """
        if parallel_val == '1':
            sg_type = "Parallel"
        else:
            sg_type = "Failover"

        print "Check if {0} is of type {1}".format(vm_dep_url, sg_type)
        # get values of SG
        cluster_url = vm_dep_url.split('services')[0]
        node_url_list = self.find(self.ms_node, cluster_url, "node")
        app_ser_id = vm_dep_url.split("/")[6]
        cluster_id = vm_dep_url.split("/")[4]

        cs_grp_name = self.vcs.generate_clustered_service_name(
                app_ser_id, cluster_id)
        # create command to check if SG is Parallel
        att_parallel = self.vcs.get_hagrp_value_cmd(cs_grp_name, "Parallel")

        # check if failover or parallel
        for node_url in node_url_list:
            node_to_exe = self.get_node_filename_from_url(self.ms_node,
                                                      node_url)
            stdout, stderr, rc = \
                self.run_command(node_to_exe, att_parallel, su_root=True)
            if (0 != rc) or ([] != stderr) or (parallel_val != stdout[0]):

                print ("{0} on node {1} expected type of {2}"
                             .format(cs_grp_name, node_to_exe, sg_type))
                #self.add_error_to_list(error_msg)
                return False
        return True

    def update_fo_sg_to_parallel(self, vm_dep_url):
        """
        Check if SG is FO and update to PL
        """
        xml_file = "/update_SG_STvm1_FO_to_PL.xml"
        xml_file_in_tmp = "/tmp" + xml_file

        # Check if SG is FO
        if self.test_check_SG_type(vm_dep_url, self.failover):
            service_url = vm_dep_url.split("services")[0] + "services"
            print service_url
            # copy files to MS
            #local_filepath = os.path.dirname(__file__)
            self.copy_file_to(self.ms_node,
                              self.local_filepath + xml_file,
                              xml_file_in_tmp,
                              root_copy=True,
                              add_to_cleanup=False)
            # get XML load command
            self.cmds.append(self.cli.get_xml_load_cmd(
                service_url, xml_file_in_tmp,
                args="--merge"))
        else:
            error_msg = ("{0} is not a FO group can't change to PL"
                         .format(vm_dep_url))
            self.add_error_to_list(error_msg)

    def check_sg_is_parallel(self, vm_dep_url):
        """
        Check if a SG is parallel
        """
        if self.test_check_SG_type(vm_dep_url, self.parallel):
            return True
        else:
            error_msg = ("{0} Was expected to be a PL SG"
                             .format(vm_dep_url))
            self.add_error_to_list(error_msg)
            return False

    def add_error_to_list(self, new_msg):
        """
            Prints error message
            updates error list
        """
        print "Error message -->> " + new_msg
        self.error_list.append(new_msg)

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

    def extend_pl_1_node_to_pl_2_node(self):
        """
        Extend vm11 from one node Paralled to a 2 node parallel service
        """
        self.copy_and_merge_xml("CDB_fun02_extend_vm11_2node_pl.xml",
                            "/deployments/",
                            "collection-of-clustered-service",
                            "c2")

    def check_SG_online_node_count(self, cluster_id, service_id, active_count):
        """
            Checks that a SG has expected number of nodes online
        """
        cs_grp_name = self.vcs.generate_clustered_service_name(
                service_id, cluster_id)
        # get hagrep command
        hagrp_cmd = self.vcs.get_hagrp_value_cmd(
            cs_grp_name, "State -clus " + cluster_id)
        # create grep command to count ONLINE systems
        cmd = self.rhcmd.get_grep_file_cmd(" ", 'ONLINE', "-c", hagrp_cmd)

        # Find cluster to run command on
        clusters_urls = self.find(self.ms_node, "/deployments",
                                  "vcs-cluster")
        for cluster_url in clusters_urls:
            if cluster_id in cluster_url:
                # get node to run command on
                node_url_list = self.find(self.ms_node, cluster_url, "node")
                # Run command on a node and check output
                for node_url in node_url_list:
                    node_to_exe = self.get_node_filename_from_url(
                        self.ms_node, node_url)
                    stdout, stderr, rc = \
                        self.run_command(node_to_exe, cmd, su_root=True)
                    if ((0 != rc) or ([] != stderr) or
                        (active_count != stdout[0])):
                        error_msg = (
                            "{0} on node {1} expected an active count of {2}"
                            .format(cs_grp_name, node_to_exe, active_count))
                        self.add_error_to_list(error_msg)
                        return False
                    return True

    def check_update_vm_mounts(self, vm_url):
        """
        Check that the expected mounts are present on VM 10
        """
        expected_mounts = ["cluster2c_fun02_new",
                           "cluster2b_fun02",
                           "cluster2a"]
        for item in expected_mounts:
            cmd = self.rhcmd.get_grep_file_cmd("/bin/mount ",
                                               item, "-c", " ")
            # Check number of CPUs
            self.check_vm(vm_url, " has mount " + item,
                          cmd, " Expected mount " + item)

    def update_critical_service(self, cluster, service):
        """
            Updates the critical service of a cluster
        """
        clusters_url = self.find(self.ms_node, "/deployments", "vcs-cluster")
        for item in clusters_url:
            if cluster in item:
                self.cmds.append(self.cli.get_update_cmd(
                    item, "critical_service=" + service))

    def contract_sg(self, service_to_contract):
        """
        method to contract a service group from a multiple node Parallel SG
        to a one node Parallel SG.
        Search for SG - ensure it is a parallel SG
        Update properties node_list, active, standby
        If SG is a vm-service
            update application property hostnames for 1 node
            update any interfaces for 1 node
        """
        service_url = ""
        # Find SG url to contract
        sg_url_list = self.find(self.ms_node, "/deployments/",
                            "vcs-clustered-service")
        for sg_url in sg_url_list:
            if service_to_contract in sg_url:
                service_url = sg_url
        self.assertFalse(service_url == "",
                         'SG {0} to contract not found'.format(
                                 service_to_contract))

        # Assert that it is a Parallel SG
        sg_dict = self.get_props_from_url(self.ms_node, service_url)
        self.assertTrue(int(sg_dict['active']) > 1)

        # update SG properties node_list, active, standby for a 1 node SG
        update_props = "active=1 standby=0 node_list={0}".format(
                sg_dict["node_list"].split(',')[1])
        self.cmds.append(self.cli.get_update_cmd(service_url, update_props))

        # Check if a VM SG
        vm_app_url = self.find(self.ms_node, service_url, "vm-service",
                               assert_not_empty=False)
        if vm_app_url == []:
            # non vm-service return
            return
        else:
            # It's a VM SG
            # find hostnames and remove updates so only one left
            vm_app_dict = self.get_props_from_url(self.ms_node, vm_app_url[0])
            if "hostnames" in vm_app_dict:
                update_props = "hostnames={0}".format(
                        vm_app_dict["hostnames"].split(',')[0])
                self.cmds.append(self.cli.get_update_cmd(vm_app_url[0],
                                                         update_props))

            # Find any VM network interfaces & update any IP for 1 node
            inf_url_list = self.find(self.ms_node, vm_app_url[0],
                            "vm-network-interface", assert_not_empty=False)
            # update any interfaces IP for 1 node
            for inf_url in inf_url_list:
                update_props = ""
                inf_dict = self.get_props_from_url(self.ms_node, inf_url)
                if 'ipv6addresses' in inf_dict:
                    update_props = '{0} ipv6addresses={1}'.format(
                            update_props,
                            inf_dict['ipv6addresses'].split(',')[0])
                if 'ipaddresses' in inf_dict:
                    update_props = '{0} ipaddresses={1}'.format(
                            update_props,
                            inf_dict['ipaddresses'].split(',')[1])
                self.cmds.append(self.cli.get_update_cmd(inf_url,
                                                         update_props))

    def remove_and_update_vm_inf(self, vm_service, path="/deployments/"):
        """
        method to test removal of vm network interfaces as part of story 12817
        Remove second last vm-network-interface from VM SG
        Update device_name of last interface to new device name been removed.
        method expects two or more interfaces on vm-service
        """
        vm_url = ""
        # Find SG url to update
        sg_url_list = self.find(self.ms_node, path, "vm-service")
        for sg_url in sg_url_list:
            if vm_service in sg_url:
                vm_url = sg_url
        self.assertFalse(vm_url == "",
                         'Expect VM SG {0} not found'.format(vm_service))

        # Find all VM network interfaces & check they are more than 2
        inf_url_list = self.find(self.ms_node, vm_url,
                            "vm-network-interface", assert_not_empty=False)
        inf_count = len(inf_url_list)
        self.assertTrue(inf_count >= 2)

        # find and sort all interface devices
        device_name_dict = {}
        for inf_url in inf_url_list:
            inf_dict = self.get_props_from_url(self.ms_node, inf_url)
            device_name_dict.update({inf_dict['device_name'][-1:]: inf_url})
        sort_device_list = sorted(device_name_dict)

        # update last vm-network-interface with required device_name
        self.cmds.append(self.cli.get_update_cmd(
                device_name_dict[sort_device_list[inf_count - 1]],
                'device_name=eth{0}'.format(sort_device_list[inf_count - 2])))

        # Remove second last vm-network-interface
        self.cmds.append(self.cli.get_remove_cmd(
                device_name_dict[sort_device_list[inf_count - 2]]))

    def remove_vm_alias(self, vm_service, path="/deployments/"):
        """
        Remove an vm-alias from a VM SG
        """
        vm_url = ""
        # Find SG url to update
        sg_url_list = self.find(self.ms_node, path,
                            "vm-service")
        for sg_url in sg_url_list:
            if vm_service in sg_url:
                vm_url = sg_url
        self.assertFalse(vm_url == "",
                         'Expect VM SG {0} not found'.format(vm_service))
        # Find any VM alias
        vm_alias_list = self.find(self.ms_node, vm_url,
                            "vm-alias", assert_not_empty=False)
        self.cmds.append(self.cli.get_remove_cmd(vm_alias_list[0]))

    def update_and_check_sg_props(self, update_set=False):
        """
        Updates properties if "update_set" is equal to True
        Checks properties if "update_set" is equal to False
        """

        # dictionary contains:
        #   type: is an item type which can be search for
        #   prop: is a litp property to be updated
        #   res:  is a vcs property to be checked
        #   val:  is the value we are upding property too
        vm3_props = [
            {'type':'vcs-clustered-service', 'prop':'online_timeout',
              'res': 'OnlineTimeout', 'val':'901'},
            {'type':'vcs-clustered-service', 'prop':'offline_timeout',
             'res': 'OfflineTimeout', 'val':'61'},
            {'type':'ha-service-config', 'prop':'clean_timeout',
             'res': 'CleanTimeout', 'val':'61'}]
        vm4_props = [
             {'type':'vcs-clustered-service', 'prop':'online_timeout',
              'res': 'OnlineTimeout', 'val':'902'},
            {'type':'vcs-clustered-service', 'prop':'offline_timeout',
             'res': 'OfflineTimeout', 'val':'62'},
            {'type':'ha-service-config', 'prop':'clean_timeout',
             'res': 'CleanTimeout', 'val':'52'},
            {'type':'ha-service-config', 'prop':'tolerance_limit',
             'res': 'ToleranceLimit', 'val':'2'},
            {'type':'ha-service-config',
             'prop':'fault_on_monitor_timeouts',
             'res': 'FaultOnMonitorTimeouts', 'val':'2'},
            {'type':'vm-service', 'prop':'cleanup_command',
             'res': 'ArgListValues',
             'val':'"/sbin/service vm4 stop-undefine --stop-timeout=3"'}]
        apache_props = [
            {'type':'vcs-clustered-service', 'prop':'online_timeout',
             'res': 'OnlineTimeout', 'val':'93'},
            {'type':'vcs-clustered-service', 'prop':'offline_timeout',
             'res': 'OfflineTimeout', 'val':'103'},
            {'type':'ha-service-config', 'prop':'clean_timeout',
             'res': 'CleanTimeout', 'val':'53'},
            {'type':'ha-service-config', 'prop':'tolerance_limit',
             'res': 'ToleranceLimit', 'val':'3'},
            {'type':'ha-service-config',
             'prop':'fault_on_monitor_timeouts',
             'res': 'FaultOnMonitorTimeouts', 'val':'3'},
            {'type':'service', 'prop':'cleanup_command',
             'res': 'ArgListValues',
             'val':'/opt/ericsson/clean_apache1.sh'},
            {'type':'vcs-clustered-service',
             'prop':'initial_online_dependency_list',
             'res': '', 'val':'anseo,ricci'}]
        cupan_tae_props = [
            {'type':'vcs-clustered-service', 'prop':'online_timeout',
              'res': 'OnlineTimeout', 'val':'901'},
            {'type':'vcs-clustered-service', 'prop':'offline_timeout',
             'res': 'OfflineTimeout', 'val':'61'},
            {'type':'vcs-clustered-service',
             'prop':'initial_online_dependency_list',
             'res': '', 'val':'ricci'}]
        flying_doves_props = [
            {'type':'vcs-clustered-service',
             'prop':'initial_online_dependency_list',
             'res': '', 'val':''}]
        anseo_props = [
            {'type':'service', 'prop':'cleanup_command',
             'res': 'ArgListValues', 'val':'/opt/ericsson/sin_e.sh'},
            {'type':'vcs-clustered-service',
             'prop':'initial_online_dependency_list',
             'res': '', 'val':'ricci'}]
        # Change items in a SG on cluster 3
        postfix_props = [
            {'type':'vcs-clustered-service', 'prop':'online_timeout',
              'res': 'OnlineTimeout', 'val':'91'},
            {'type':'ha-service-config', 'prop':'clean_timeout',
             'res': 'CleanTimeout', 'val':'51'},
            {'type':'ha-service-config', 'prop':'tolerance_limit',
             'res': 'ToleranceLimit', 'val':'3'}]

        # place properties into a list
        list_sg_props = [["SG_STvm3", vm3_props],
                         ["SG_STvm4", vm4_props],
                         ["cupan_tae", cupan_tae_props],
                         ["flying_doves", flying_doves_props],
                         ["anseo", anseo_props],
                         ["apache", apache_props],
                         ["postfix", postfix_props]
                         ]
        # Get a list of services
        sg_list = self.find(self.ms_node, "/deployments/",
                            "vcs-clustered-service", assert_not_empty=False)

        for service_url in sg_list:
            for sg_props in list_sg_props:
                if sg_props[0] in service_url:
                    if update_set:
                        self.update_vcs_parameters(service_url, sg_props[1])
                    else:
                        self.check_vcs_parameters(service_url, sg_props[1])

    def update_and_check_numthreads(self, cluster, num_threads_val,
                                    update_set=False):
        """
        Updates property for NumThreads if "update_set" is equal to True
        Checks property for NumThreads if "update_set" is equal to False
        """
        check_thread_cmd = " /opt/VRTS/bin/hatype -display Application " \
                           "-attribute NumThreads"
        clusters_urls = self.find(self.ms_node, "/deployments", "vcs-cluster")

        for clusters_url in clusters_urls:
            if cluster in clusters_url:
                if update_set == True:
                    # Add command to update property to cmd list
                    self.cmds.append(self.cli.get_update_cmd(
                        clusters_url,
                            "app_agent_num_threads=" + num_threads_val))
                    print self.cmds
                else:
                    # Create grep command to check value
                    checkforstr = "NumThreads.*" + num_threads_val
                    grep_cmd = self.rhcmd.get_grep_file_cmd(
                            " ", checkforstr, file_access_cmd=check_thread_cmd,
                            grep_args='-E')
                    # Find nodes on cluster
                    mn_names = self.get_mn_for_service_url(clusters_url)
                    # Run grep command on one node and check reslts
                    _, stderr, stdrc = self.run_command(
                            mn_names[0], grep_cmd, su_root=True)
                    if stderr != [] or stdrc != 0:
                        self.add_error_to_list(
                                "Expected value {0} for app_agent_num_threads "
                                "not found".format(num_threads_val))

    def replace_dep_list_with_initial_online_dep_list(self):
        """
        Description:
            Get a cluster service's dependency_lists and update them to
            use initial_online_dependency_list with same values.
        Actions:
            1. Find the cluster whos dependency_list you want to replace.
            2. Get the values in dependency_list property and store them.
            3. Remove the dependency_list property for each service.
            4. Add initial_online_dependency_list property to each service and
               give it the values found previously from dependency_list.
        """
        # Get path to deployment clusters
        cluster_paths = \
            self.find(self.ms_node,
                      "/deployments",
                      "vcs-cluster")
        clusters_found = len(cluster_paths)
        self.assertTrue(clusters_found > 1,
                        "Only one cluster was found on system: {0}"
                        .format(cluster_paths))
        # Get path to the vcs cluster services in cluster C2 which has
        # dependency_list set
        cluster_services_paths = \
            self.find(self.ms_node,
                      cluster_paths[1],
                      "vcs-clustered-service")
        # Loop through each cluster service path found
        for path in cluster_services_paths:
            self.log("info", "Checking for any cluster_dependency "
                             "property on service : {0}".format(path))
            # Get the property "dependency_list" values from service and
            # store values in list for future use
            dependency_list_values = \
                self.get_props_from_url(self.ms_node,
                                        path,
                                        filter_prop="dependency_list")
            # If a service is found with no dependency_list
            if not dependency_list_values:
                self.log("info", "No dependency_list found for {0} , "
                                 "trying next service".format(path))
            else:
                # Remove dependency_list property from service
                self.execute_cli_update_cmd(self.ms_node,
                                            path,
                                            props="dependency_list",
                                            action_del=True)
                # Update the service to add initial_online_dependency_list
                # property with values from previously removed dependency_list
                self.execute_cli_update_cmd(
                    self.ms_node,
                    path,
                    props="initial_online_dependency_list={0}"
                        .format(dependency_list_values))

    def create_new_vcs_triggers(self):
        """
        Description:
            Creates a vcs-trigger below all the discovered
            vcs-cluster-service's which don't already have one.
        """
        vcs_srvs_list = \
        self.find(self.ms_node, "/deployments/",
                  "vcs-clustered-service", assert_not_empty=False)
        # CHECK EACH TRIGGER FOUND IN THE DEPLOYMENT
        for vcs_srvs in vcs_srvs_list:
            # ASCERTAIN WHETHER THE SG ALREADY HAS A TRIGGER OBJECT
            vcs_triggers = \
            self.find(self.ms_node, vcs_srvs,
                      "vcs-trigger", assert_not_empty=False)
            runtimes = \
            self.find(self.ms_node, vcs_srvs,
                  "lsb-runtime", assert_not_empty=False)
            # IF NOT THEN CREATE A TRIGGER
            if vcs_triggers == [] and runtimes == []:
                obj_prop = \
                self.get_props_from_url(self.ms_node, vcs_srvs, "standby")
                if obj_prop == '1':
                    url = "{0}/triggers/cdb_trigger".format(vcs_srvs)
                    props = "trigger_type=nofailover"
                    self.log('info',
                         "Creating vcs-trigger under SG {0}".format(vcs_srvs))
                    cmd = self.cli.get_create_cmd(url, 'vcs-trigger', props)
                    self.cmds.append(cmd)

    def check_vcs_triggers(self):
        """
        Description:
            Function to check the vcs trigger applied to a
            vcs-clustered-service.
        """
        # Get a list of services
        sg_list = self.find(self.ms_node, "/deployments/",
                            "vcs-clustered-service", assert_not_empty=False)
        for sg_item in sg_list:
            prop = ""
            val = ""
            trigger_list = self.find(self.ms_node, sg_item,
                            "vcs-trigger", assert_not_empty=False)
            if trigger_list != []:
                prop = \
                self.get_props_from_url(self.ms_node, trigger_list[0],
                                        filter_prop="trigger_type")

            # FUTURE PROOFING CODE - EXTRA IF STATEMENTS EXPECTED
            # WHEN NEW TRIGGER TYPES CAN BE SPECIFIED IN LITP
            if prop == 'nofailover':
                val = "NOFAILOVER"
            item_props = [
            {'type':'vcs-trigger', 'prop': prop,
             'res': 'TriggersEnabled', 'val': val}]
            self.check_vcs_parameters(sg_item, item_props)

    @attr('all', 'non-revert', 'functional', 'P1', 'functional_tc02')
    def test_02_vcs_runtime(self):
        """
        Description:
            Test multiple updates to VCS
            A snapshot is created at the beginning of this test so that the
            system can be restored back to that point
        Actions:
            Remove deployment snapshot and create a new snapshot so system
            can be restored to this point
            Update VCS properties for a SG (non VM)
            Create vcs-trigger object below SG's
            Update hostnames of a VM * 2
            Update VCS properties for a VM SG * 2
            Update cpu count on a VM
            Update SSH key on a VM * 2
            Increase the amount of RAM used on a VM
            Update, remove & add tmpfs and ramfs to VMs
            Update the alias been used by a VM
            Update SG's by contracting them (VM and non VM)
            On a VM add a related Alias, yum-repo, package
            Update a interface (IP, network, bridge, Gateway) on a VM
            Add a new interface to a VM
            Update a bridge on a MN
            Update a package repo on a VM
            Reconfigure a FO SG to be a PL SG
            Remove items from deployment
                vcs-network-hosts
                vcs-cluster-services (service and vm-service)
                vcs-trigger
            Update initial_online_dependency_list
            ---- this is checked in vcs system sanity tests
            Import a package into a repo to update a package that is on a VM
            Add a FO VM SG & PL VM SG with XML
            Extend vm11 from a 1 node Paralled to a 2 node parallel vm-service
            update the criticial_service
            update the VCS NumThreads property
            Update the VM image been used by a VM
            Create and run a plan.

            Check all updates
            Performing a ping to ensure that VM networks are up

            Print any errors found during test.
        """
        # Allow teardown to detect if test has passed
        self.test_passed = False

        sw_vm_url = []
        updated_cpus = "8"
        updated_ram = 4000000
        pkg2_ver = "2.0-1"
        pkg2 = "test_service"
        pkg2_rpm = "/tmp/test_service-2.0-1.noarch.rpm"
        import_repo = test_constants.OS_UPDATES_PATH
        #test_constants.LITP_DEFAULT_OS_PROFILE_PATH

        # Assign a number for each VM updated task
        # This represents the index of dep_vm_url list which is used
        # to determine which VM to perform a check / update
        vm_hostname1 = 1
        vm_hostname2 = 3
        vm_pkg_repo = 0
        vm_net = 1
        vm_alias_baseurl = 2
        vm_image = 3
        vm_ram = 4
        vm_ssh_key_1 = 4
        vm_cpu = 1
        vm_ssh_key_2 = 0
        vm_fo_to_paralled = 0
        vm_mounts = 9

        # dictionary contains
        #   type: is an item type which can be search for
        #   prop: is a litp property that can be stored for checking
        #   id:   is item_id of item to be removed
        #   val:  is used to store the value of 'prop'
        #   action_taken: Used to indicate a remove cmd has been created.
        remove_items_dict = [
            {'type':'vcs-clustered-service', 'prop':'name', 'id':'lucky_luci',
             'val':'', "action_taken":False},
            {'type':'vcs-clustered-service', 'prop':'name', 'id':'SG_STvm9',
             'val':'', "action_taken":False},
            {'type':'vcs-network-host', 'prop':'ip', 'id': 'traf1_nh_test',
             'val':'', "action_taken":False},
            {'type':'vcs-network-host', 'prop':'ip', 'id': 'traf1_nh_test1',
             'val':'', "action_taken":False},
            {'type':'vcs-network-host', 'prop':'ip', 'id': 'traf2_nh_test',
             'val':'', "action_taken":False},
            {'type':'vcs-network-host', 'prop':'ip', 'id': 'traf2_nh_test1',
             'val':'', "action_taken":False},
            {'type':'vcs-network-host', 'prop':'ip', 'id': 'net1vm_nh_test',
             'val':'', "action_taken":False},
            {'type':'vcs-network-host', 'prop':'ip', 'id': 'net2vm_nh_test',
             'val':'', "action_taken":False},
            {'type':'vcs-network-host', 'prop':'ip', 'id': 'net3vm_nh_test',
             'val':'', "action_taken":False},
            {'type':'vcs-network-host', 'prop':'ip', 'id': 'net4vm_nh_test',
             'val':'', "action_taken":False},
            {'type':'vcs-trigger', 'prop':'trigger_type',
             'id':'SG_STvm1_trigger', 'val':'', "action_taken":False},
            {'type':'vcs-trigger', 'prop':'trigger_type',
             'id':'doves_trigger', 'val':'', "action_taken":False},
             ]

        """
        Get list of VM URL
        """
        # Check if snapshot is present
        snapshot = self.find(self.ms_node, "/", "snapshot-base",
                             assert_not_empty=False)
        if snapshot:
            # If there is a deployment snapshot present, remove snapshot
            self.log("info", "Removing the deployment snapshot")
            self.execute_and_wait_removesnapshot(self.ms_node)

        # Create new snapshot
        self.log("info", "Creating a new deployment snapshot so that the "
                         "system can be restored to this point")
        self.execute_and_wait_createsnapshot(self.ms_node,
                                             remove_snapshot=False)

        # Get a list of sorted VM URL
        vm_list = self.find(self.ms_node, "/deployments/",
                            "reference-to-vm-service", assert_not_empty=False)

        # Sort the list
        dep_vm_url = sorted(vm_list)

        # Remove VM that upset sorting of list
        dep_vm_url = self.remove_unsed_vm(dep_vm_url)

        # Get the source item for each inherited vm-service item
        for item in dep_vm_url:
            sw_vm_url.append(self.deref_inherited_path(self.ms_node, item))
        self.log('info', "List of parent vm-service items {0}"
                                                   .format(sw_vm_url))

        # CREATE A VCS TRIGGER ITEM BELOW VM AND NON VM
        # SG'S RESIDING IN THE DEPLOYMENT
        self.create_new_vcs_triggers()

        # Make updates to VM's
        self.update_vm_hostname(dep_vm_url[vm_hostname1])
        self.update_vm_hostname(dep_vm_url[vm_hostname2])
        self.update_vm_cpus(sw_vm_url[vm_cpu], updated_cpus)
        self.update_vm_ssh_key(sw_vm_url[vm_ssh_key_1])
        self.create_vm_ssh_key(sw_vm_url[vm_ssh_key_2])
        self.update_vm_ram(sw_vm_url[vm_ram], updated_ram)
        self.update_remove_add_vm_ram_mount()
        self.update_vm_alias_baseURL(sw_vm_url[vm_alias_baseurl])
        self.contract_sg("contractme")
        self.contract_sg("SG_STvm8")
        updated_br = self.network_changes(dep_vm_url[vm_net],
                                          sw_vm_url[vm_net])
        self.update_packages_repo(sw_vm_url[vm_pkg_repo])
        self.update_fo_sg_to_parallel(dep_vm_url[vm_fo_to_paralled])
        # remove items from the model
        remove_items_dict = self.remove_items(remove_items_dict)
        # -1 from vm_mounts as a VM9 is removed
        vm_mounts = vm_mounts - 1

        # Expand a PL SG using XML
        self.copy_and_merge_xml("expand_PL_SG.xml", "/deployments",
                                "collection-of-clustered-service", "c1")
        # Update mounts on VM10
        self.copy_and_merge_xml("vm10_update_mounts.xml", "/software",
                                "vm-service", "vmservice10")
        # Extend SG_STvm11 from one node Paralled to a 2 node parallel service
        self.copy_and_merge_xml("CDB_fun02_extend_vm11_2node_pl.xml",
                            "/deployments/", "collection-of-clustered-service",
                            "c2")

        self.update_critical_service("c1", "flying_doves")
        self.update_and_check_numthreads("c2", "18", update_set=True)
        # Update a Package in repo
        self.execute_cli_import_cmd(self.ms_node, pkg2_rpm, import_repo)
        # Add FO and PL VM with XML
        self.add_vm_with_xml()

        self.update_and_check_sg_props(update_set=True)
        # Comment in below 2 lines once a VM is added onto the MS
        # self.remove_vm_alias('ms_vm-serviceX', "/ms")
        # self.remove_and_update_vm_infs('ms_vm-serviceX', "/ms')
        self.remove_and_update_vm_inf('SG_STvm6')
        self.remove_vm_alias('SG_STvm6')
        self.remove_and_update_vm_inf('vmservice7', '/software')
        self.remove_vm_alias('vmservice8', '/software')

        # Run Commands and create and run plan
        cmd_results = self.run_commands(self.ms_node, self.cmds,
                                        add_to_cleanup=False)
        print cmd_results
        if not self.is_std_out_empty(cmd_results):
            self.add_error_to_list("Std_outError running one or more " +
                                        "litp commands")
        if self.get_errors(cmd_results) != []:
            self.add_error_to_list("Error code running one or more " +
                                        "litp commands")

        # Update VMs to use different vm-images
        self.update_vm_image(sw_vm_url[vm_image])

        # Call method to replace C2's services depdendency_lists property with
        # initial_online_dependency_list property
        self.replace_dep_list_with_initial_online_dep_list()

        # CREATE PLAN
        self.execute_cli_createplan_cmd(self.ms_node)

        # SHOW PLAN
        self.execute_cli_showplan_cmd(self.ms_node)

        # RUN PLAN
        self.execute_cli_runplan_cmd(self.ms_node)
        # Check if plan completed successfully
        completed_successfully = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=60)
        self.assertTrue(completed_successfully, "Plan was not successful")

        self.log('info', "plan was successful. start the configuration checks")

        # Store the vm info as node connection data so it can be accessed
        self.log('info',
                   "vm url list : {0}".format(dep_vm_url))
        self.log('info',
                   "store the vm info from each vm_url as a vm node")
        for vm_url in dep_vm_url:
            # temp exculsion of IPV6 only VM from connection until fw updates
            if "SG_STvm7" not in vm_url:
                self.store_vm_as_node(vm_url)

        # List all defined vm nodes
        self.log('info', "all defined vm nodes : {0}"
                                .format(self.get_vm_node_filenames()))

        # Check updates were successful
        # Check VM Hostname Update
        self.log('info',
                   "check update of hostname {0}".format(vm_hostname1))
        self.check_vm_hostname(dep_vm_url[vm_hostname1])
        self.log('info',
                   "check update of hostname {0}".format(vm_hostname2))
        self.check_vm_hostname(dep_vm_url[vm_hostname2])

        # Check Update of SG from FO to PL
        self.log('info',
               "check update of VM {0} from FO to PL"
                                  .format(vm_fo_to_paralled))
        self.check_sg_is_parallel(dep_vm_url[vm_fo_to_paralled])

        # Check VM Network Updates
        self.log('info', "check vm network updates")
        self.check_network_updates(dep_vm_url[vm_net], updated_br)

        # Check VM Package and Repo updates
        self.log('info', "check vm package and repo updates")
        self.check_packages_repo(dep_vm_url[vm_pkg_repo])

        # Check VM CPU updates
        self.log('info', "check vm cpu updates")
        self.check_update_vm_cpus(dep_vm_url[vm_cpu], updated_cpus)

        # Check VM RAM updates
        self.log('info', "check vm ram updates")
        self.check_update_vm_ram(dep_vm_url[vm_ram], updated_ram)

        # Check VM image updates
        self.log('info', "check vm image updates")
        self.check_update_vm_image(dep_vm_url[vm_image])

        # Check unused VM images are removed from /var/lib/libvirt/images
        self.log("info", "Check that unused VM images are removed")
        self.check_remove_unused_images()

        # Check VM alias updates
        self.log('info', "check vm alias updates")
        self.check_update_vm_alias_baseURL(dep_vm_url[vm_alias_baseurl])

        # Check version of package installed on vm
        self.log('info', "check version of package installed on vm")
        self.check_pkt_ver_installed(dep_vm_url[vm_pkg_repo], pkg2, pkg2_ver)

        # Check vm ssh keys updates
        self.log('info', "check vm ssh keys updates")
        self.check_vm_ssh_key(dep_vm_url[vm_ssh_key_1])
        self.check_vm_ssh_key(dep_vm_url[vm_ssh_key_2])

        # Check vm mount updates
        self.log('info', "check vm mount updates")
        self.check_update_vm_mounts(dep_vm_url[vm_mounts])

        # Check expanded SGs
        self.log('info', "check expanded SGs")
        # Check anseo is now a 2 node PL service group
        self.check_SG_online_node_count("c1", "anseo", "2")
        # Check SG_STvm11 is now a 2 node parallel service
        self.check_SG_online_node_count("c2", "SG_STvm11", "2")

        # Check removed items are removed
        self.log('info', "check removed items are removed")
        self.check_items_are_removed(remove_items_dict)

        # Check SG property updates
        self.log('info', "check SG property updates")
        self.update_and_check_sg_props()

        # CHECK VCS TRIGGER DEPLOYMENT
        self.log('info', "check vcs trigger runtime additions.")
        self.check_vcs_triggers()

        # Check update for number of vcs threads
        self.log('info', "check update of number of vcs threads")
        self.update_and_check_numthreads("c2", "18")

        # Perform a ping of each VM NIC
        self.log('info',
                   "perform a ping on each vm network interface in the model")
        self.pingtest_vm_inf()

        for item in self.error_list:
            print item
        self.assertTrue(self.error_list == [],
                        "### Checks failed ##### \n"
                        + str(self.error_list))
        print "Success"

        # Allow teardown to detect if test has passed
        self.test_passed = True
