#!/usr/bin/env python

'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     February 2014
@author:    Stefan
@summary:   System Test for "InstallUninstallPkg"
            Agile: EPIC-xxxx, STORY-xxxx, Sub-task: STORY-xxxx
'''

from litp_generic_test import GenericTest
from litp_cli_utils import CLIUtils
from redhat_cmd_utils import RHCmdUtils
import test_constants


class InstallUninstallPkg(GenericTest):

    """
    Description:
        These tests are checking the litp  mechanism
        for installing/uninstalling rpm packages that
        are present in LITP Repositories.
    """

    def setUp(self):
        super(InstallUninstallPkg, self).setUp()

        self.firefox_pkg = 'firefox'
        self.telnet_pkg = 'telnet'
        self.finger_pkg = 'finger'
        self.pkg_list_1 = 'pkg_list_1'
        self.pkg_list_2 = 'pkg_list_2'

        self.ms_node = self.get_management_node_filename()
        self.targets = self.get_managed_node_filenames()
        self.targets.append(self.ms_node)
        self.redhat = RHCmdUtils()
        self.cli = CLIUtils()
        self.ms_path = "/ms"
        self.timeout_mins = 50

        # Get all software-items
        self.items_path = self.get_path_url("/software", "software-item")
        # Get peer node1/peer node2 litp path present in litp tree
        self.peer_paths = self.find(self.ms_node, "/deployments", "node", True)
        self.assertNotEqual(self.peer_paths,
                            [],
                            "No node collections found in LITP deployment")

        # Group each node to its specific litp path
        self.node_path = dict([(self.get_node_filename_from_url(self.ms_node,
                                                                peer_path),
                                peer_path) for peer_path in self.peer_paths])

        if '/deployments/d1/clusters/c1/nodes/n2' in self.peer_paths:
            self.peer_paths.remove('/deployments/d1/clusters/c1/nodes/n2')
        if '/deployments/d1/clusters/c2/nodes/n4' in self.peer_paths:
            self.peer_paths.remove('/deployments/d1/clusters/c2/nodes/n3')
        if '/deployments/d1/clusters/c2/nodes/n4' in self.peer_paths:
            self.peer_paths.remove('/deployments/d1/clusters/c2/nodes/n4')
        if '/deployments/d1/clusters/c3/nodes/n5' in self.peer_paths:
            self.peer_paths.remove('/deployments/d1/clusters/c3/nodes/n5')
        if '' in self.peer_paths:
            self.peer_paths.add('/ms')

# Get the peer nodes list
        self.peer_nodes = self.node_path.keys()
        self.assertNotEqual(self.peer_nodes,
                            [],
                            "No management nodes defined in connection data "
                            "files")

    def tearDown(self):
        """Runs for every test"""
        pass

    def get_a_node_url_from_each_cluster(self):
        """
        Search each cluster for node url and returns list of node URLs
        """
        node_urls = []
        # find A list of clusters
        clusters_url = self.find(self.ms_node, "/deployments", "vcs-cluster")
        self.assertTrue(clusters_url != [], "Did not find a VCS cluster")
        print "list of vcs cluster found", clusters_url
        for cluster in clusters_url:
            node_list = self.find(self.ms_node, cluster, "node")
            node_urls.append(node_list[0])
        print "print list of one node from each cluster ", node_urls
        return node_urls

    def get_path_url(self, path, resource):
        """
        Description:
            Gets the url path
        Actions:
            1. Perform find command
            2. Assert find command returns item
            3. Return item
       Results:
           Returns the path url for the current environment
        """
        # 1 RUN FIND
        profile_path = self.find(self.ms_node, path, resource, False)
        # 2 ASSERT FIND RETURNS ITEM
        self.assertNotEqual(profile_path,
                            [],
                            "Could not find path url : {0} in {1}."
                            .format(resource, path))

        # 3 RETURN ITEM
        return profile_path[0]

    def obsolete_01_install_pkg(self):
        """
        Test case obsoleted as this functionality is already
        tested in the Package KGB area in
        test_01_p_require_pkg_install_order_dflt_vrsn
        Description:
            This test will check if a package can be successfully
            installed on one peer node of each cluster.
        Actions:
            1. Create two packages in "/software/items" path called
            telnet and firefox.
            2. Create inherit items on one peer node of each cluster to
            the previously created software items.
            3. Create Plan.
            4. Run Plan.
            5. Check that telnet/firefox packages were installed on one
            peer node of each cluster nodes.
        Results:
            telnet and firefox and packages should be present on one
            peer node of each cluster.
        """
        node_list = self.peer_paths
        # Create the telnet package
        cmd_list = list()
        props = 'name=' + self.telnet_pkg
        cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                        self.telnet_pkg, 'package', props))

        # Create the firefox package
        props = 'name=' + self.firefox_pkg
        cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                        self.firefox_pkg, 'package', props))

        for path in node_list:
            # Inherit telnet package on this peer node
            cmd_list.append(self.cli.get_inherit_cmd(path + '/items/' + \
                            self.telnet_pkg, self.items_path + '/' + \
                            self.telnet_pkg))
            # Inherit firefox package on this peer node
            cmd_list.append(self.cli.get_inherit_cmd(path + '/items/' + \
                            self.firefox_pkg, self.items_path + '/' + \
                            self.firefox_pkg))

        # Run LITP CLI Commands
        cmd_results = self.run_commands(self.ms_node, cmd_list)
        self.assertEqual(self.get_errors(cmd_results), [],
                         "Error in commands")
        self.assertTrue(self.is_std_out_empty(cmd_results),
                        "Error std_out not empty")

        #CREATE PLAN
        self.execute_cli_createplan_cmd(self.ms_node)
        # SHOW PLAN
        self.execute_cli_showplan_cmd(self.ms_node)
        # RUN PLAN
        self.execute_cli_runplan_cmd(self.ms_node)
        # Check if plan completed successfully
        completed_successfully = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
        self.assertTrue(completed_successfully, "Plan was not successful")

    def obsolete_02_p_uninstall_pkg_specific_node(self):
        """
        Description:
            This scenario was allready covered by -
            test_03_p_uninstall_pkg_all_nodes
            This test will check if a package can be successfully
            uninstalled from on one peer node of each cluster where
            they were installed previously
        Actions:
            1. Remove the package item from all peer nodes.
            2. Create Plan.
            3. Run Plan.
        Results:
            The telnet package was successfully removed from on one
            peer node of each cluster where they were installed
            previously.
        """

        cmd_list = list()
        node_list = self.peer_paths

        # For each peer node remove the link to telnet package
        for path in node_list:
            cmd_list.append(self.cli.get_remove_cmd(path + '/items/' + \
                            self.telnet_pkg))
        # Run commands
        cmd_results = self.run_commands(self.ms_node, cmd_list)
        self.assertEqual(self.get_errors(cmd_results), [],
                         "Error in commands")
        self.assertTrue(self.is_std_out_empty(cmd_results),
                        "Error std_out not empty")

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
                                     self.timeout_mins)
        self.assertTrue(completed_successfully, "Plan was not successful")

    def obsolete_02_uninstall_pkg_all_nodes(self):
        """
        Test case obsoleted as this functionality is already
        tested in the Package KGB area in
        test_01_p_require_pkg_install_order_dflt_vrsn
        Description:
            This test will check if a package can be successfully
            uninstalled from on one peer node of each cluster.
        Actions:
            1. Remove the package items firefox and telnet from on one
            peer node of each cluster where they were installed previously.
            2. Remove the firefox and telnet packages from software items.
            3. Create Plan.
            4. Run Plan.
        Results:
            firefox/telnet packages should be successfully removed from
            on one peer node of each cluster where they were installed
            previously.
        """
        cmd_list = list()
        node_list = self.peer_paths
        for path in node_list:  # self.node_path.itervalues():
            # Remove the link to firefox package for this peer node
            cmd_list.append(self.cli.get_remove_cmd(path + '/items/' + \
                            self.firefox_pkg))
            cmd_list.append(self.cli.get_remove_cmd(path + '/items/' + \
                            self.telnet_pkg))

        # Remove the firefox software item
        cmd_list.append(self.cli.get_remove_cmd(self.items_path + '/' + \
                                                self.firefox_pkg))
        # Remove the telnet software item
        cmd_list.append(self.cli.get_remove_cmd(self.items_path + '/' + \
                                                self.telnet_pkg))

        # Run the litp plan
        cmd_results = self.run_commands(self.ms_node, cmd_list)
        self.assertEqual(self.get_errors(cmd_results), [],
                         "Error in commands")
        self.assertTrue(self.is_std_out_empty(cmd_results),
                        "Error std_out not empty")

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
                                     self.timeout_mins)
        self.assertTrue(completed_successfully, "Plan was not successful")

    def obsolete_03_create_pkg_list(self):
        """
        Test is now covered in Package KGB.

        Description:
            Creates the definition for a list of rpm packages.
            Inherit the previously created package list on one peer
            node from each cluster.
        Actions:
            1. Create the package-list definition.
            2. Inherit package-list on one peer node from each cluster.
            3. Create Plan.
            4. Run Plan
        Results:
            The rpms package list should be created successfully.
            All rpms present in the package list should be installed
            on one peer node from each cluster.
        """
        cmd_list = list()
        node_list = self.peer_paths

        # create package list
        props = 'name=' + self.pkg_list_1
        cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                        self.pkg_list_1, 'package-list', props))

        # create all the packages inside the package-list
        # create firefox package
        props = 'name=' + self.firefox_pkg
        cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                        self.pkg_list_1 + '/packages/' + self.firefox_pkg, \
                        'package', props))

        # create telnet package
        props = 'name=' + self.telnet_pkg
        cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                        self.pkg_list_1 + '/packages/' + self.telnet_pkg, \
                        'package', props))

        # create finger package
        props = 'name=' + self.finger_pkg
        cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                        self.pkg_list_1 + '/packages/' + self.finger_pkg, \
                        'package', props))

        # Create a link to package list for each peer node
        for path in node_list:
            cmd_list.append(self.cli.get_inherit_cmd(path + '/items/' + \
                            self.pkg_list_1, self.items_path + '/' + \
                            self.pkg_list_1))

        # Check you can create a plan without error
        cmd_results = self.run_commands(self.ms_node, cmd_list)
        self.assertEqual(self.get_errors(cmd_results),
                         [],
                         "Error in commands")
        self.assertTrue(self.is_std_out_empty(cmd_results),
                        "Error std_out not empty")

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
                                     self.timeout_mins)
        self.assertTrue(completed_successfully, "Plan was not successful")

    def obsolete_04_remove_pkg_from_list(self):
        """
        Test is now covered in Package KGB.

        Description:
            This test was obsoleted because it is an IT test and the message
            it expects returned will no longer be returned.
            This is due to new functionality form Story LITPCDS-12018.
        Actions:
            1. Remove firefox packages from the package list.
            2. Check MethodNotAllowedError is returned.
        Results:
            Removing inherited items should not be allowed.
        """
        # Remove a specific package from the package list
        cmd = self.cli.get_remove_cmd(self.items_path + '/' + \
                        self.pkg_list_1 + '/packages/' + self.firefox_pkg)
        stdout, stderr, rcode = self.run_command(self.ms_node, cmd)
        self.assertEqual(rcode, 1)
        self.assertEqual(stdout, [], "stdout is not empty")
        self.assertTrue(
            self.is_text_in_list("MethodNotAllowedError", stderr),
            "MethodNotAllowedError message is missing")
        self.log('info',
                 'Test Passed MethodNotAllowed Error was returned when '
                 'removing an installed package from package list...')

    def obsolete_05_add_pkg_to_node(self):
        """
        Test is now covered in Package KGB.

        Description:
            Checking that a new package can be added
            to an existing package list.
        Actions:
            1. Add a package rpm to package list.
            2. Create Plan.
            3. Run Plan.
            4. Check package "wireshark" was successfully installed on one
            peer node from each cluster.
        Results:
            The newly added rpm package was successfully added to
            package list and also installed on one peer node from each
            cluster..
        """
        pkg_1 = 'wireshark'
        cmd_list = list()

        # Add a new package to package list
        props = 'name=' + pkg_1
        cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                        self.pkg_list_1 + '/packages/' + pkg_1, 'package',
                        props))

        # Run the litp plan
        cmd_results = self.run_commands(self.ms_node, cmd_list)
        self.assertEqual(self.get_errors(cmd_results), [],
                         "Error in commands")
        self.assertTrue(self.is_std_out_empty(cmd_results),
                        "Error std_out not empty")

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
                                     self.timeout_mins)
        self.assertTrue(completed_successfully, "Plan was not successful")

        for node_url in self.peer_paths:
            node = self.get_props_from_url(self.ms_node, node_url,
                                              "hostname",
                                              show_option="")
            # Check that the new rpm package was installed on peer nodes
            cmd = self.redhat.check_pkg_installed([pkg_1])
            _, stderr, rcode = self.run_command(node, cmd)
            self.assertEqual(rcode,
                             0,
                             "package {0} was not installed. on managed "
                             "node 1.".format(pkg_1))
            self.assertEqual(stderr, [], "stderr is not empty")
            self.log('info',
                     '{0} was installed on {1} peer node'
                     .format(pkg_1, str(node)))

    def obsolete_06_remove_pkg_list(self):
        """
        Test is now covered in Package KGB.

        Description:
            Checking that a package list that was
            previously installed can be successfully removed.
        Actions:
            1. Run remove command against an existing package list.
            2. Create Plan.
            3. Run Plan.
        Results:
            The package list should be removed from software items.
        """
        cmd_list = list()
        node_list = node_list = self.peer_paths
        # Remove package list item from all peer nodes
        for path in node_list:
            cmd_list.append(self.cli.get_remove_cmd(path + '/items/' + \
                            self.pkg_list_1))

        # Remove the package list from software items
        cmd_list.append(self.cli.get_remove_cmd(self.items_path + '/' + \
                        self.pkg_list_1))

        # Run LITP CLI Commands
        cmd_results = self.run_commands(self.ms_node, cmd_list)
        self.assertEqual(self.get_errors(cmd_results), [],
                         "Error in commands")
        self.assertTrue(self.is_std_out_empty(cmd_results),
                        "Error std_out not empty")

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
                                     self.timeout_mins)
        self.assertTrue(completed_successfully, "Plan was not successful")

    def obsolete_07_remove_pkg_after_inherit(self):
        """
        Test is now covered in Package KGB.

        Description:
            Checking that litp plan is correctly
            evaluating the scenario when a new peer node is inheriting an
            existing package list and also at the same time one or more
            packages are removed from the package list.
            LITP should not install the removed package on the peer nodes.
        Actions:
            1. Create package list
            2. Add firefox.
            3. Add telnet.
            4. Remove telnet package from package list.
            5. Create Plan.
            6. Run Plan.
            7. Check that the removed rpm package was not installed.
        Results:
            LITP should not install the removed package on peer nodes that
            inherit the package-list.
        """
        try:
            cmd_list = list()
            node_list = self.peer_paths + ["/ms"]
            # create package list
            props = 'name=' + self.pkg_list_2
            cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                            self.pkg_list_2, 'package-list', props))

            # add firefox package
            props = 'name=' + self.firefox_pkg
            cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                            self.pkg_list_2 + '/packages/' + self.firefox_pkg,
                            'package', props))

            # add telnet package
            props = 'name=' + self.telnet_pkg
            cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                            self.pkg_list_2 + '/packages/' + self.telnet_pkg,
                            'package', props))

            # Inherit the package list on peer nodes
            for path in node_list:
                cmd_list.append(self.cli.get_inherit_cmd(path + '/items/' + \
                                self.pkg_list_2, self.items_path + '/' + \
                                self.pkg_list_2))

            # Remove a telnet from  package list
            cmd_list.append(self.cli.get_remove_cmd(self.items_path + '/' + \
                            self.pkg_list_2 + '/packages/' + self.telnet_pkg))

            # Run the litp plan
            cmd_results = self.run_commands(self.ms_node, cmd_list)
            self.assertEqual(self.get_errors(cmd_results), [],
                             "Error in commands")
            self.assertTrue(self.is_std_out_empty(cmd_results),
                            "Error std_out not empty")

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
                                         self.timeout_mins)
            self.assertTrue(completed_successfully, "Plan was not successful")

            # Check that "telnet" rpm package was not installed on peer nodes
            cmd = self.redhat.check_pkg_installed([self.telnet_pkg])
            for node in self.node_path.keys():
                stdout, stderr, rcode = self.run_command(node, cmd)
                self.assertNotEqual(rcode, 0, "package {0} was installed."
                                    .format(self.telnet_pkg))
                self.assertEqual(stderr, [], "stderr is not empty")
                self.assertEqual(stdout, [], "stdout is not empty.")
                self.log('info', '{0} package was not installed on {1} peer' \
                         ' node.'.format(self.telnet_pkg, str(node)))
        finally:
            cmd_list = list()
            #node_list = self.get_a_node_url_from_each_cluster()
            #Remove pkg_list_2 from peer nodes
            for path in node_list:
                cmd_list.append(self.cli.get_remove_cmd(path + '/items/' + \
                                self.pkg_list_2))
            # Remove pkg_list_2 from software items
            cmd_list.append(self.cli.get_remove_cmd(self.items_path + '/' + \
                            self.pkg_list_2))
            # Run LITP CLI Commands
            cmd_results = self.run_commands(self.ms_node, cmd_list)
            self.assertEqual(self.get_errors(cmd_results), [],
                             "Error in commands")
            self.assertTrue(self.is_std_out_empty(cmd_results),
                            "Error std_out not empty")
            #CREATE PLAN
            self.execute_cli_createplan_cmd(self.ms_node)
            # SHOW PLAN
            self.execute_cli_showplan_cmd(self.ms_node)
            # RUN PLAN
            self.execute_cli_runplan_cmd(self.ms_node)
            # Check if plan completed successfully
            completed_successfully = \
                self.wait_for_plan_state(self.ms_node,
                                         test_constants.PLAN_COMPLETE,
                                         self.timeout_mins)
            self.assertTrue(completed_successfully, "Plan was not successful")

    def obsolete_08_pkg_name_altered(self):
        """
        Test is now covered in Package KGB.

        Description:
            Check if LITP Model is not allowing the
            user to use a package with altered name
        Actions:
            1. Create a telnet package in "/software/items" path with
               name equal to telnet.
            2. Inherit telnet package on one peer node from each cluster.
            3. Create/Run LITP Plan.
            5. Check that the package was installed on one peer node
            from each cluster..
            6. Update telnet package and peer nodes package items name
            with
            a new value "firefox".
            7. Check you get a InvalidRequestError when updating the
            package name.
        Results:
            LITP Model should now allow the user to update a litp package.
        """
        cmd_list = list()
        node_list = self.peer_paths
        try:
            # Create the telnet package
            props = 'name=' + self.telnet_pkg
            cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                            self.telnet_pkg, 'package', props))

            # Create a link to telnet package for all peer nodes
            for path in node_list:
                cmd_list.append(self.cli.get_inherit_cmd(path + '/items/' + \
                                self.telnet_pkg, self.items_path + '/' + \
                                self.telnet_pkg))

            # Check you can create a plan without error
            cmd_results = self.run_commands(self.ms_node, cmd_list)
            self.assertEqual(self.get_errors(cmd_results), [],
                             "Error in commands")
            self.assertTrue(self.is_std_out_empty(cmd_results),
                            "Error std_out not empty")

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
                                         self.timeout_mins)
            self.assertTrue(completed_successfully, "Plan was not successful")

            for node in node_list:
                # Check that "telnet" rpm package was installed on peer nodes
                cmd = self.redhat.check_pkg_installed([self.telnet_pkg])
                _, stderr, rcode = self.run_command(node, cmd)
                self.assertNotEqual(rcode,
                                 0,
                                 "package {0} was not installed. on managed "
                                 "node 1.".format(self.telnet_pkg))
                self.assertNotEqual(stderr, [], "stderr is not empty")
                self.log('info',
                         '{0} was installed on {1} peer node'
                         .format(self.telnet_pkg, str(node)))

            cmd_list = list()
            # Update the name of telnet package
            props = 'name=' + self.firefox_pkg
            cmd_list.append(self.cli.get_update_cmd(self.items_path + '/' + \
                            self.telnet_pkg, props))

            for path in node_list:
                props = 'name=' + self.firefox_pkg
                # Update the link to telnet package for this peer node
                cmd_list.append(self.cli.get_update_cmd(path + '/items/' + \
                                self.telnet_pkg, props))

            # Run the update commands.
            cmd_results = self.run_commands(self.ms_node, cmd_list)
            errors = self.get_errors(cmd_results)
            for err in errors:
                self.assertTrue('InvalidRequestError in property: "name"' \
                             '    Unable to modify readonly property: ' \
                                  'name' in err['stderr'], \
                                 'No errors returned when updating the '
                                 'software item name...')

            self.assertTrue(self.is_std_out_empty(cmd_results),
                            "Error std_out not empty")

            self.log('info',
                     'Test Passed InvalidRequestError was returned when '
                     'updating litp package name...')
        finally:
            # Remove the telnet pkg
            cmd_list = list()
            # Remove the links to telnet package
            for path in node_list:
                cmd_list.append(self.cli.get_remove_cmd(path + '/items/' + \
                                self.telnet_pkg))
            cmd_list.append(self.cli.get_remove_cmd(self.items_path + '/' + \
                            self.telnet_pkg))
            # Run the commands
            cmd_results = self.run_commands(self.ms_node, cmd_list)
            self.assertEqual(self.get_errors(cmd_results), [],
                             "Error in commands")
            self.assertTrue(self.is_std_out_empty(cmd_results),
                            "Error std_out not empty")

            #CREATE PLAN
            self.execute_cli_createplan_cmd(self.ms_node)
            # SHOW PLAN
            self.execute_cli_showplan_cmd(self.ms_node)
            # RUN PLAN
            self.execute_cli_runplan_cmd(self.ms_node)
            # Check if plan completed successfully
            completed_successfully = \
                self.wait_for_plan_state(self.ms_node,
                                         test_constants.PLAN_COMPLETE,
                                         self.timeout_mins)
            self.assertTrue(completed_successfully, "Plan was not successful")

    def obsolete_09_multiple_references(self):
        """
        Test is now covered in Package KGB.

        Description:
            Check if LITP Model is throwing an error
            when user tries to install two packages that are refering
            to the same package.
        Actions:
            1. Create a package-list definition.
            2. Create a package inside the package list that refer to
            firefox.
            3. Create a second package inside the package list that
            also refer to firefox.
            4. Create a link to package-list for all peer nodes.
            5. Create LITP Plan.
            6. Check LITP Plan throws a Validation Error.
        Results:
            Create PLAN should throw a Validation Error: package defined
            multiple times.
        """
        try:
            cmd_list = list()
            pack1 = 'pack1'
            pack2 = 'pack2'
            node_list = self.peer_paths
            # create package list
            props = 'name=' + self.pkg_list_1
            cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                            self.pkg_list_1, 'package-list', props))

            # create all the packages inside the package-list
            # create pack1 refering to firefox package
            props = 'name=' + self.firefox_pkg
            cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                            self.pkg_list_1 + '/packages/' + pack1, \
                            'package', props))

            # create pack2 refering to firefox package
            props = 'name=' + self.firefox_pkg
            cmd_list.append(self.cli.get_create_cmd(self.items_path + '/' + \
                            self.pkg_list_1 + '/packages/' + pack2, \
                            'package', props))

            # Create a link to package list for each peer node
            for path in node_list:
                cmd_list.append(self.cli.get_inherit_cmd(path + '/items/' + \
                                self.pkg_list_1, self.items_path + '/' + \
                                self.pkg_list_1))

            # Run the commands
            cmd_results = self.run_commands(self.ms_node, cmd_list)
            self.assertEqual(self.get_errors(cmd_results), [],
                             "Error in commands")
            self.assertTrue(self.is_std_out_empty(cmd_results),
                            "Error std_out not empty")

            # Create the LITP Plan and check it throws a Validation Error
            _, stderr, _ = self.execute_cli_createplan_cmd(
                self.ms_node, expect_positive=False
            )
            # 4. Assert expected validation Error returned
            self.assertTrue(
                self.is_text_in_list("ValidationError", stderr),
                "ValidationError message is missing")
            self.assertTrue(
                self.is_text_in_list("Package \"{0}\" is already added"
                            .format(self.firefox_pkg), stderr),
                "ValidationError does not state package defined multiple "
                "times in error message")
            self.log('info',
                     'Test Passed Validation Error was returned when using'
                     ' two packages refering to the same real package'
                     '...LITPCDS-2747')
        finally:
            cmd_list = list()
            node_list = self.peer_paths
            # Remove the links to package list for each peer node
            for path in node_list:
                cmd_list.append(self.cli.get_remove_cmd(path + '/items/' + \
                                self.pkg_list_1))
            # Remove the package list from software items
            cmd_list.append(self.cli.get_remove_cmd(self.items_path + '/' + \
                            self.pkg_list_1))
            # Run the remove commands
            cmd_results = self.run_commands(self.ms_node, cmd_list)
            self.assertEqual(self.get_errors(cmd_results), [],
                             "Error in commands")
            self.assertTrue(self.is_std_out_empty(cmd_results),
                            "Error std_out not empty")
