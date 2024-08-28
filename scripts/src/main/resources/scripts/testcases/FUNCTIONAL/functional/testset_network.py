#!/usr/bin/env python
"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     August 2016
@author:    Messers
@summary:   System Test for Checking E2E Network functionality
"""
from litp_generic_test import GenericTest, attr, CLIUtils, RHCmdUtils
import test_constants


class NetworkFunctional(GenericTest):
    """
    Description:
        Test to check end to end network functionality
    """
    def setUp(self):
        self.cli = CLIUtils()
        self.rhcmd = RHCmdUtils()
        super(NetworkFunctional, self).setUp()
        # Get paths to all nodes and the MS from the model
        self.model = self.get_model_names_and_urls()
        self.ms_node = self.get_management_node_filename()
        self.cmds = []
        self.test_passed = False

    def tearDown(self):
        """
        Runs after every test
        """
        self.log("info", "Beginning custom teardown/cleandown")
        if not self.test_passed:
            super(NetworkFunctional, self).tearDown()

    def update_multicast_props(self):
        """
        Description:
            Method to create a list of commands to update the multicast
            properties of all bridges in the deployment
        """
        # Find a list of paths to bridges under the MS and add it to list to
        # update
        bridge_paths = self.find(self.ms_node, "/ms", "bridge",
                                 assert_not_empty=False)
        # Find a list of paths to bridges under the nodes and add it to
        # the list to update
        for node in self.model["nodes"]:
            node_bridges = self.find(self.ms_node, node["url"], "bridge",
                                     assert_not_empty=False)
            # Add the path of every bridge to the list of paths
            for bridge in node_bridges:
                bridge_paths.append(bridge)

        path_number = 0
        # For each bridge in the deployment
        for path in bridge_paths:
            # Increase the path number
            path_number += 1
            # Create a hash_max value for this bridge
            hash_max = str(2 ** path_number)
            # If the path number is divisible by 2, update the multicast
            # props with the below values
            if path_number % 2 == 0:
                cmd = self.cli.get_update_cmd(path, "hash_max={0} "
                                                    "multicast_querier=1 "
                                                    "multicast_router=2"
                                              .format(hash_max))
                # Add update command to list of commands to run
                self.cmds.append(cmd)
            # If the path number is divisible by 3, update the multicast
            # props with the below values
            elif path_number % 3 == 0:
                cmd = self.cli.get_update_cmd(path, "hash_max={0} "
                                                    "multicast_querier=1 "
                                                    "multicast_router=0"
                                              .format(hash_max))
                # Add update command to list of commands to run
                self.cmds.append(cmd)
            # If the above conditions are not met, update the bridge with the
            # following multicast props
            else:
                cmd = self.cli.get_update_cmd(path, "hash_max={0} "
                                                    "multicast_querier=0 "
                                                    "multicast_router=1"
                                              .format(hash_max))
                # Add update command to list of commands to run
                self.cmds.append(cmd)

        # Enable multicast snooping on one of the bridges in the deployment
        cmd = self.cli.get_update_cmd(bridge_paths[-1], "multicast_snooping=1")
        # Add update command to list of commands to run
        self.cmds.append(cmd)

    def check_multicast_updates(self):
        """
        Description:
            Method to check that the update multicast properties have been
            applied correctly
        """

        # List of nodes to check
        nodes_to_check = []
        nodes_to_check.extend(self.model["nodes"])
        nodes_to_check.extend(self.model["ms"])

        # For each node
        for node in nodes_to_check:
            # Get the paths to bridges under the node
            bridges = self.find(self.ms_node, node["url"], "bridge",
                                assert_not_empty=False)
            # For each path
            for bridge in bridges:
                grep_items = []
                # Get the properties of the bridge in the model
                props = self.get_props_from_url(self.ms_node, bridge)
                # Path to the bridge config file
                config_file = "/etc/sysconfig/network-scripts/ifcfg-" +\
                              props["device_name"]

                # For each property
                for prop in props:
                    # List of properties to check
                    relevant_props = ["multicast_", "hash_max"]
                    if any(i in prop for i in relevant_props):
                        # Create string to grep for
                        grep_str = prop + "=" + props[prop]
                        # add grep string to list of strings to grep for
                        grep_items.append(grep_str)

                cmd = self.rhcmd.get_grep_file_cmd(config_file,
                                                   grep_items)

                self.log("info", "Looking for '{0}' in '{1}'".format(
                    grep_items, config_file))
                # Grep for properties string in config file
                self.run_command(node["name"], cmd, su_root=True,
                                 default_asserts=True)

    @attr('all', 'non-revert', 'functional', 'P1', 'functional_tc09')
    def test_09_network_runtime(self):
        """
        Description:
            Test to check end to end network functionality (test will be
            expanded to cover all networking functionality)
        Actions:
            1. Activate mulicast snooping for one bridge in the deployment and
               update the other multicast properties of all bridges in
               deployment
            2. Create and run plan
            3. Check if plan completed successfully
            4. Check for errors running the update commands
            5. Check that the multicast updates have been applied
        Results:
            The created plan runs successfully and there are no errors running
            any of the commands
        """
        # Allow teardown to detect if test has passed
        self.test_passed = False

        # Update multicast properties of all bridges in the deployment
        self.update_multicast_props()

        # Run list of update commands
        cmd_results = self.run_commands(self.ms_node, self.cmds,
                                        add_to_cleanup=False)
        # Create plan
        self.execute_cli_createplan_cmd(self.ms_node)

        # Show plan
        self.execute_cli_showplan_cmd(self.ms_node)

        # Run plan
        self.execute_cli_runplan_cmd(self.ms_node)

        # Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE)

        self.assertTrue(completed_successfully, "Plan did not run "
                                                "successfully")

        # Check for errors running list of update commands
        cmd_errors = self.get_errors(cmd_results)
        if cmd_errors:
            self.log("info", "There was an error running one or more update "
                             "commands")
            self.log("info", cmd_errors)
            self.assertFalse(cmd_errors, "There were errors from running the "
                                         "list of commands")
        # Check that the multicast updates have been applied
        self.check_multicast_updates()

        # Allow teardown to detect if test has passed
        self.test_passed = True
