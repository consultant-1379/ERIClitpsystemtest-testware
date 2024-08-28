'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     March 2014
@author:    Amanda McGuinness
@summary:   System test to check
            Check can deploy extension which has own validator
            Check rejects invalid new items
            Check accepts valid new items
            Check can deploy new plugin which uses new extension
            Check can create and run plan using new item, and expected
            config task is created and file produced
            Uses the RPM generated from ERIClitpexampleextapi, and
            ERIClitpexampleplug located in ST/litp_2_0/PLUGIN
'''

from litp_generic_test import GenericTest, attr
from litp_cli_utils import CLIUtils
import test_constants
import time
import os
from redhat_cmd_utils import RHCmdUtils


class Plugins(GenericTest):
    """
        ST tests to test plugins created as per the plugin SDK guide
    """
    def setUp(self):
        """
        Description:
            Runs before every single test
        Actions:
            1. Calls the super class setup method
            2. Set up variables used in the tests
        Results:
            The super class prints out diagnostics and variables
            common to all tests that are available
        """
        super(Plugins, self).setUp()
        self.cli = CLIUtils()
        self.test_node = self.get_management_node_filename()

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Actions:
            1. Calls the super class teardown method
        """
        super(Plugins, self).tearDown()

    def _install_plugin(self, plugins, rpms):
        """
        Description:
            Utility function to install plugins
        Actions:
            1. Copies RPMS onto box
            2. Creates repo
            3. Cleans yum repo
            4. Installs plugin and extension
        Parameters:
            plugins - list of plugins/extensions to install
            rpms - rpm names in file to install
        Results:
            The plugins are installed and litp service restarted
        """
        local_path = os.path.dirname(repr(__file__)).strip('\'') + \
            "/plugin_rpms"
        for rpmname in rpms:
            retval = self.copy_file_to(self.test_node,
               "{0}/{1}.rpm".format(local_path, rpmname),
               test_constants.LITP_PKG_REPO_DIR, True)
            self.assertTrue(retval, "Failed to copy plugin rpm")
        rhutils = RHCmdUtils()
        cmd = rhutils.get_createrepo_cmd(
              directory=test_constants.LITP_PKG_REPO_DIR,
              args='--update')
        stdout, stderr, returnc = self.run_command(self.test_node, cmd,
            su_root=True)
        self.assertEqual(0, returnc)
        self.assertEqual([], stderr)
        self.assertTrue(self.is_text_in_list("complete", stdout),
                   "Missing complete in standard output")
        self.assertTrue(self.is_text_in_list(
            "Cleaning up Everything", stdout),
                   "Missing cleaning up in standard output")

        pluginlist = []
        for plugin in plugins:
            pluginlist.append(plugin)
        cmd = RHCmdUtils.get_yum_install_cmd(pluginlist)
        stdout, stderr, returnc = self.run_command(self.test_node, cmd,
            su_root=True)
        self.assertEqual(0, returnc)
        self.assertEqual([], stderr)
        # We want to know if either:
        # 1. Starting litp daemon is in stdout and OK
        # or 2. Nothing to do is in stdout
        # So we set found to False, and initialise to true if one of these
        # is found, and then assert True at end
        found = False
        if self.is_text_in_list(
            "Starting litp daemon", stdout):
            if self.is_text_in_list("OK", stdout):
                found = True
        if self.is_text_in_list(
            "Nothing to do", stdout):
            # For case when rpm already installed, i.e. re-running test
            found = True
        self.assertTrue(found,
                   "Missing restart litp in standard output")

    def _link_pl_on_nodes(self, nodes, linkname, props):
        """
        Description:
            This function adds a package-list to all nodes
        Parameters:
            nodes - list of nodes
            linkname - name of link
            props - properties to use on link
        """
        for node in nodes:
            linkpath = "{0}/items/{1}".format(node, linkname)
            self.execute_cli_link_cmd(self.test_node,
                linkpath, "package-list", props)

    @attr('all', 'non-revert', 'plugins', 'P2', 'plugins_tc01')
    def test_01_invalid_extension_items(self):

        """
        Description:
            This test verifies that validation prevents invalid example-items,
            where example-item is created by the example extension
        Actions:
            1. Creates example-item missing mandatory parameter name
            2. Creates example-item with invalid regular expression
            3. Creates example-item which doesn't match custom validator
               rubbish
        Results:
            The example-items are all rejected
        """
        rpms = []
        plugins = []
        plugin = "ERIClitpexampleextapi_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140407171744.noarch".format(plugin))
        plugin = "ERIClitpexampleplug_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140506123755.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        props = ""
        _, stderr, _ = self.execute_cli_create_cmd(self.test_node,
                 '/software/items/i1',
                 'example-item',
                 props,
                 expect_positive=False)
        self.assertTrue(self.is_text_in_list(
                  'with name "name"', stderr),
                  "Wrong errors reported in standard error")

        # Reenable debug logging
        self.turn_on_litp_debug(self.test_node)

        # Now test invalid size - not match regex
        props = "name=hello size=10b"
        _, stderr, _ = self.execute_cli_create_cmd(self.test_node,
                 '/software/items/i2',
                 'example-item',
                 props,
                 expect_positive=False)
        self.assertTrue(self.is_text_in_list(
                   'ValidationError in property: "size"', stderr),
                   "Wrong errors reported in standard error")

        # Now test invalid rubbish which has custom validator
        props = "name=hello size=10B rubbish=12345678901"
        _, stderr, _ = self.execute_cli_create_cmd(self.test_node,
                 '/software/items/i3',
                 'example-item',
                 props,
                 expect_positive=False)
        self.assertTrue(self.is_text_in_list(
            'ValidationError in property: "rubbish"', stderr),
                   "Wrong errors reported in standard error")

    @attr('all', 'non-revert', 'plugins', 'P2', 'plugins_tc02')
    def test_02_valid_example_extension_items(self):

        """
        Description:
            This test verifies that validation allows example-items, where
            example-items have been created by the extension
        Actions:
            1. Creates example-item with valid parameters
        Results:
            The example-items are all accepted
        """
        rpms = []
        plugins = []
        plugin = "ERIClitpexampleextapi_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140407171744.noarch".format(plugin))
        plugin = "ERIClitpexampleplug_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140506123755.noarch".format(plugin))
        self._install_plugin(plugins, rpms)

        # Reenable debug logging
        self.turn_on_litp_debug(self.test_node)

        # Automates 2.0 PLUG_TC1_P1 part c
        props = "name=test02 size=1B rubbish=test02"
        self.execute_cli_create_cmd(self.test_node,
                 '/software/items/test02',
                 'example-item',
                 props)

    @attr('all', 'non-revert', 'plugins', 'P2')
    def obsolete_03_p_valid_example_item_and_plan(self):

        """
        Temporarily Obsoleted
        Description:
            This test tests that config plugin using custom extension can
            be run
        Actions:
            1. Creates example-item with valid parameters
            2. Creates and run plan
            3. Checks file created called /etc/exampleplug_<name>_<size>_<rub>
                  on managed node
        Results:
            Filename created on managed nodes
        """
        rpms = []
        plugins = []
        plugin = "ERIClitpexampleextapi_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140407171744.noarch".format(plugin))
        plugin = "ERIClitpexampleplug_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140506123755.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        # Automates 2.0 PLUG_TC1_P1 part c
        props = "name=test03 size=10B rubbish=rub03"
        self.execute_cli_create_cmd(self.test_node,
                 '/software/items/test03',
                 'example-item',
                 props)

        # Now create it on each managed node
        nodes = self.find(self.test_node, "/deployments",
           "node")
        props2 = "name=test03"
        for node in nodes:
            linkpath = "{0}/items/t3".format(node)
            self.execute_cli_link_cmd(self.test_node,
                linkpath, "example-item", props2)

        # Now create plan
        self.execute_cli_createplan_cmd(self.test_node)

        try:
            # Now run plan
            self.execute_cli_runplan_cmd(self.test_node)
            timeout_mins = 3
            completed_successfully = self.wait_for_plan_state(self.test_node,
                 test_constants.PLAN_COMPLETE, timeout_mins)
            self.assertTrue(completed_successfully, "Wait for plan failed")

            # Now check file is there
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                    node)
                filename = "/etc/exampleplug_test03_10B_rub03.txt"
                self.assertTrue(self.remote_path_exists(mn_filename, filename),
                     "No file {0}".format(filename))
        finally:
            # Clear up /etc files produced by test
            nodes = self.find(self.test_node, "/deployments",
               "node")
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                                                              node)
                filename = "/etc/exampleplug_test03_10B_rub03.txt"
                self.remove_item(mn_filename, filename, su_root=True)

    @attr('all', 'non-revert', 'plugins', 'P2')
    def obsolete_04_p_valid_example_callback(self):

        """
        Temporarily Obsoleted

        Description:
            This test tests that callback plugin using core extension can
            be run
        Actions:
            1. Creates package-list with name EXCALL04 (as plugin
                   only acts on packages with name that contains EXCALL)
            2. Creates and run plans
            3. Checks file created called
                  /etc/examplecall_<hostname>_<packagelistname>
                  on ms
            4. For LITPCDS-3330, check that file created contains details
               of success of rpc command on node and failed on rubbish. As the
               plugin will run the MCO status command on the node we added
               package-list to plus a node called "rubbish", and will output
               the dictionary returned to the file it creates
        Results:
            The filename is created on MS
        """
        # Automates 2.0 PLUG_TC1_P1 part b
        rpms = []
        plugins = []
        plugin = "ERIClitpexamplecall_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140508125832.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        props = "name=EXCALL04"
        self.execute_cli_create_cmd(self.test_node,
                 '/software/items/test04',
                 'package-list',
                 props)

        # Now create it on each managed node
        nodes = self.find(self.test_node, "/deployments",
           "node")
        props2 = "name=EXCALL04"
        for node in nodes:
            linkpath = "{0}/items/t4".format(node)
            self.execute_cli_link_cmd(self.test_node,
                linkpath, "package-list", props2)

        # Now create plan
        self.execute_cli_createplan_cmd(self.test_node)

        try:
            # Now run plan
            self.execute_cli_runplan_cmd(self.test_node)
            timeout_mins = 3
            completed_successfully = self.wait_for_plan_state(self.test_node,
                 test_constants.PLAN_COMPLETE, timeout_mins)
            self.assertTrue(completed_successfully, "Wait for plan failed")

            # Now check file is there on MS
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
                hostname = self.get_node_att(mn_filename, 'hostname')
                filename = "/etc/examplecall_{0}_EXCALL04.txt".format(hostname)
                self.assertTrue(self.remote_path_exists(self.test_node,
                         filename), "No file {0}".format(filename))

                # Check contents of file created by the plugin. The file
                # contains the MCO RPC command output as follows:
                # errors is error returned from rpc command on success node
                # data is data returned from rpc command on success node
                # 2 errors is error returned from rpc command on invalid node
                # 2 data is data returned from rpc command on invalid node
                expected_strs = [
                         "errors:",
                         "data: {'status': 'running'}",
                         "2 errors: No answer from rubbish",
                         "2 data: {}",
                ]
                fileoutput = self.get_file_contents(self.test_node,
                        filename)
                for line in expected_strs:
                    self.assertTrue(self.is_text_in_list(line, fileoutput),
                        "Did not find {0} in {1}".format(line,
                                                         fileoutput))

        finally:
            # Clear up /etc files produced by test
            nodes = self.find(self.test_node, "/deployments",
               "node")
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                                                              node)
                hostname = self.get_node_att(mn_filename, 'hostname')
                msfilename = "/etc/examplecall_{0}_EXCALL04.txt".\
                                      format(hostname)
                self.remove_item(self.test_node, msfilename, su_root=True)

    @attr('all', 'non-revert', 'plugins', 'P2')
    def obsolete_05_p_valid_core_config(self):

        """
        Temporarily Obsoleted

        Description:
            This test tests that config plugin using core extension can
            be run
        Actions:
            1. Creates package-list with valid parameters
            2. Creates and run plan
            3. Checks file created called /etc/amanda_<sp>_<hostname>
                  and /etc/amandasp_<sp>_<hostname> on managed node
        Results:
            Filename created on managed nodes
        """
        # Automates 2.0 PLUG_TC1_P1 part a
        rpms = []
        plugins = []
        plugin = "ERIClitpamanda_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140306121138.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        props = "name=AMANDAtest05"
        self.execute_cli_create_cmd(self.test_node,
                 '/software/items/test05',
                 'package-list',
                 props)

        # Now create it on each managed node
        nodes = self.find(self.test_node, "/deployments",
           "node")
        for node in nodes:
            linkpath = "{0}/items/t5".format(node)
            self.execute_cli_link_cmd(self.test_node,
                linkpath, "package-list", props)

        # Now create plan
        self.execute_cli_createplan_cmd(self.test_node)

        try:
            # Now run plan
            self.execute_cli_runplan_cmd(self.test_node)
            timeout_mins = 3
            completed_successfully = self.wait_for_plan_state(self.test_node,
                 test_constants.PLAN_COMPLETE, timeout_mins)
            self.assertTrue(completed_successfully, "Wait for plan failed")

            # Now check file is there, two per storage-profile
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
                hostname = self.get_node_att(mn_filename, 'hostname')
                sps = self.find(self.test_node, node,
                      "storage-profile")
                for sp1 in sps:
                    cmd = self.cli.get_show_data_value_cmd(sp1,
                       "storage_profile_name")
                    stdout, stderr, returnc = self.run_command(self.test_node,
                        cmd)
                    self.assertEquals(0, returnc)
                    self.assertEqual([], stderr)
                    self.assertNotEqual([], stdout)
                    spname = stdout[0]
                    filename = "/etc/amanda_{0}_{1}.txt".format(spname,
                                            hostname)
                    self.assertTrue(self.remote_path_exists(mn_filename,
                            filename), "No file {0}".format(filename))

                    filename = "/etc/amandasp_{0}_{1}.txt".format(spname,
                                       hostname)
                    self.assertTrue(self.remote_path_exists(mn_filename,
                            filename), "No file {0}".format(filename))
        finally:
            # Clear up /etc files produced by test
            nodes = self.find(self.test_node, "/deployments",
               "node")
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                                                              node)
                hostname = self.get_node_att(mn_filename, 'hostname')
                sps = self.find(self.test_node, node,
                                "storage-profile")
                for sp1 in sps:
                    cmd = self.cli.get_show_data_value_cmd(sp1,
                            "storage_profile_name")
                    stdout, _, _ = self.run_command(self.test_node,
                            cmd)
                    self.assertNotEqual([], stdout)
                    spname = stdout[0]
                    filename = "/etc/amanda*_{0}_{1}.txt".format(spname,
                                                   hostname)
                    self.remove_item(mn_filename, filename, su_root=True)

    @attr('all', 'non-revert', 'plugins', 'P2')
    def obsolete_06_p_ordered_tasks(self):
        """
        Temporarily Obsoleted

        Description:
            This test tests that can use multiple ordered task plugins
            on same items as an unordered item and all tasks ran as
            expected. See PLUG_TC2_P1 on litp_2_1 plugin tests.
        Actions:
            1. Creates package-list with valid parameters
            2. Creates and run plan
            3. Checks following files are created in this order:
               /etc/example_ord1_call1_<hostname>_UNORDTEST on MS
               /etc/example_ord1_conf2_<hostname>_UNORDTEST on MN
               /etc/example_ord1_call2_<hostname>_UNORDTEST on MS
               /etc/example_ord1_conf1_<hostname>_UNORDTEST on MN
            4. Checks following files are created in this order:
               /etc/example_ord2_call2_<hostname>_UNORDTEST on MS
               /etc/example_ord2_call1_<hostname>_UNORDTEST on MS
               /etc/example_ord2_conf2_<hostname>_UNORDTEST on MN
               /etc/example_ord2_conf1_<hostname>_UNORDTEST on MN
            5. Checks following files are created in any order:
               /etc/example_unord1_call1_<hostname>_UNORDTEST on MS
               /etc/example_unord1_conf1_<hostname>_UNORDTEST on MN
        Results:
            Filename created on managed nodes and MS
            Tasks in plan in correct order
        """
        # Automates 2.1 PLUG_TC2_P1
        rpms = []
        plugins = []
        plugin = "ERIClitpextunord_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140320205559.noarch".format(plugin))
        plugin = "ERIClitpextorderedone_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140320205909.noarch".format(plugin))
        plugin = "ERIClitpextorderedtwo_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140320210048.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        # Name will fire both the unordered and ordered plugins
        props = "name=UNORDTEST"
        self.execute_cli_create_cmd(self.test_node,
                 '/software/items/test06',
                 'package-list',
                 props)

        # Now create it on each managed node
        nodes = self.find(self.test_node, "/deployments",
           "node")
        self._link_pl_on_nodes(nodes, "t6", props)

        # Now create plan
        self.execute_cli_createplan_cmd(self.test_node)

        # Do a show plan and check tasks are in correct order
        stdout, _, _ = self.execute_cli_showplan_cmd(self.test_node)

        for node in nodes:
            mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
            hostname = self.get_node_att(mn_filename, 'hostname')

            # Check order for ord1 ordered task list
            prefix = "Install file /etc/example_ord1_"
            # TESTUPDATE: If a managed node has a long nodename then the
            # task description is too long to fit on a single line. So instead
            # of the stdout containing a line starting with prefix, it will
            # just start with the filename
            # Therefore if prefix does not appear in the stdout the task
            # descriptions have been fixed, so only search for lines that
            # that start with the filename
            if not self.is_text_in_list(prefix, stdout):
                prefix = "/etc/example_ord1_"
            self.assertTrue(stdout.index("{0}call1_{1}_UNORDTEST".\
                       format(prefix, hostname)) <
                   stdout.index("{0}conf2_{1}_UNORDTEST".\
                       format(prefix, hostname)),
                   "Ord1 Call1 not before Ord1 Conf2")
            self.assertTrue(stdout.index("{0}conf2_{1}_UNORDTEST".\
                       format(prefix, hostname)) <
                   stdout.index("{0}call2_{1}_UNORDTEST".\
                       format(prefix, hostname)),
                   "Ord1 Conf2 not before Ord1 Call2")
            self.assertTrue(stdout.index("{0}call2_{1}_UNORDTEST".\
                       format(prefix, hostname)) <
                   stdout.index("{0}conf1_{1}_UNORDTEST".\
                       format(prefix, hostname)),
                   "Ord1 Call2 not before Ord1 Conf1")

            # Check order for ord2 ordered task list
            prefix = "Install file /etc/example_ord2_"
            # TESTUPDATE: If a managed node has a long nodename then the
            # task description is too long to fit on a single line. So instead
            # of the stdout containing a line starting with prefix, it will
            # just start with the filename
            # Therefore if prefix does not appear in the stdout the task
            # descriptions have been fixed, so only search for lines that
            # that start with the filename
            if not self.is_text_in_list(prefix, stdout):
                prefix = "/etc/example_ord2_"
            self.assertTrue(stdout.index("{0}call2_{1}_UNORDTEST".\
                       format(prefix, hostname)) <
                   stdout.index("{0}call1_{1}_UNORDTEST".\
                       format(prefix, hostname)),
                   "Ord2 Call2 not before Ord2 Call1_{0}".format(hostname))
            self.assertTrue(stdout.index("{0}call1_{1}_UNORDTEST".\
                       format(prefix, hostname)) <
                   stdout.index("{0}conf2_{1}_UNORDTEST".\
                       format(prefix, hostname)),
                   "Ord2 Call1 not before Ord2 Conf2")
            self.assertTrue(stdout.index("{0}conf2_{1}_UNORDTEST".\
                       format(prefix, hostname)) <
                   stdout.index("{0}conf1_{1}_UNORDTEST".\
                       format(prefix, hostname)),
                   "Ord2 Conf2 not before Ord2 Conf1")

            # Check unordered tasks are there
            self.assertTrue(self.is_text_in_list(
                     "unord1_call1_{0}".format(hostname),
                      stdout))
            self.assertTrue(self.is_text_in_list(
                     "unord1_conf1_{0}".format(hostname),
                      stdout))

        try:
            # Now run plan
            self.execute_cli_runplan_cmd(self.test_node)
            timeout_mins = 20

            # Now wait for state
            completed_successfully = self.wait_for_plan_state(self.test_node,
                test_constants.PLAN_COMPLETE, timeout_mins)

            # Do show plan to see what state its in, just to go into log
            self.execute_cli_showplan_cmd(self.test_node)

            self.assertTrue(completed_successfully, "Wait for plan failed")

            # Now check files are there
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
                hostname = self.get_node_att(mn_filename, 'hostname')

                # Files created by pluginA (extorderedone)
                filename = "/etc/example_ord1_call1_{0}_UNORDTEST".\
                     format(hostname)
                self.assertTrue(self.remote_path_exists(self.test_node,
                     filename), "No file {0}".format(filename))

                filename = "/etc/example_ord1_call2_{0}_UNORDTEST".\
                     format(hostname)
                self.assertTrue(self.remote_path_exists(self.test_node,
                     filename), "No file {0}".format(filename))

                filename = "/etc/example_ord1_conf1_{0}_UNORDTEST".\
                     format(hostname)
                self.assertTrue(self.remote_path_exists(mn_filename, filename),
                    "No file {0}".format(filename))

                filename = "/etc/example_ord1_conf2_{0}_UNORDTEST".\
                    format(hostname)
                self.assertTrue(self.remote_path_exists(mn_filename, filename),
                    "No file {0}".format(filename))

                # Files created by plugin B (extorderedtwo)
                filename = "/etc/example_ord2_call1_{0}_UNORDTEST".\
                    format(hostname)
                self.assertTrue(self.remote_path_exists(self.test_node,
                    filename), "No file {0}".format(filename))

                filename = "/etc/example_ord2_call2_{0}_UNORDTEST".\
                    format(hostname)
                self.assertTrue(self.remote_path_exists(self.test_node,
                    filename), "No file {0}".format(filename))

                filename = "/etc/example_ord2_conf1_{0}_UNORDTEST".\
                    format(hostname)
                self.assertTrue(self.remote_path_exists(mn_filename, filename),
                    "No file {0}".format(filename))

                filename = "/etc/example_ord2_conf2_{0}_UNORDTEST".\
                    format(hostname)
                self.assertTrue(self.remote_path_exists(mn_filename, filename),
                    "No file {0}".format(filename))

                # Files created by plugin C (extunord)
                filename = "/etc/example_unord1_call1_{0}_UNORDTEST".\
                    format(hostname)
                self.assertTrue(self.remote_path_exists(self.test_node,
                    filename), "No file {0}".format(filename))

                filename = "/etc/example_unord1_conf1_{0}_UNORDTEST".\
                    format(hostname)
                self.assertTrue(self.remote_path_exists(mn_filename, filename),
                    "No file {0}".format(filename))
        finally:
            # Clear up /etc files produced by test
            nodes = self.find(self.test_node, "/deployments",
               "node")
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                    node)
                hostname = self.get_node_att(mn_filename, 'hostname')
                msfilename = "/etc/example_ord*_call*_{0}_UNORDTEST".\
                    format(hostname)
                self.remove_item(self.test_node, msfilename, su_root=True)

                filename = "/etc/example_ord*_conf*_{0}_UNORDTEST".\
                    format(hostname)
                self.remove_item(mn_filename, filename, su_root=True)

                filename = "/etc/example_unord1_conf1_{0}_UNORDTEST".\
                    format(hostname)
                self.remove_item(mn_filename, filename, su_root=True)

                filename = "/etc/example_unord1_call1_{0}_UNORDTEST".\
                    format(hostname)
                self.remove_item(self.test_node, filename, su_root=True)

    @attr('all', 'non-revert', 'plugins', 'P2')
    def obsolete_07_p_restart_ordered_tasks(self):
        """
        Temporarily Obsoleted

        Description:
            This test tests that if restart litp in middle of ordered
            task run that will run correct commands after restart
            See PLUG_TC3_P1 on litp_2_1 plugin tests.
        Actions:
            1. Creates package-list with valid parameters
            2. Creates plan and show plan
            3. Plan should contain commands for files:
               /etc/exlongord1_call1_<hostname>_LONG07 on MS
               /etc/exlongord1_call2_<hostname>_LONG07 on MS
               /etc/exlongord1_call3_<hostname>_LONG07 on MS
            4. Wait for plan to be in state 1 running, 1 success, 1 initial
            5. Restart litp service
            6. Check state of item is still initial
            7. Create plan and check has all tasks in
        Results:
            Filename created on MS
            Tasks in plan in correct order
        """
        # Automates 2.1 PLUG_TC3_P1
        rpms = []
        plugins = []
        plugin = "ERIClitpexlongordered_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140321122159.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        # Name will fire both the unordered and ordered plugins
        props = "name=LONG07"
        self.execute_cli_create_cmd(self.test_node,
                 '/software/items/test07',
                 'package-list',
                 props)
        # Now create it on each managed node
        nodes = self.find(self.test_node, "/deployments",
           "node")
        self._link_pl_on_nodes(nodes, "t7", props)

        # Now create plan
        self.execute_cli_createplan_cmd(self.test_node)

        # Do a show plan and check tasks are in correct order
        stdout, _, _ = self.execute_cli_showplan_cmd(self.test_node)
        for node in nodes:
            mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
            hostname = self.get_node_att(mn_filename, 'hostname')

            # Check order for ord1 ordered task list
            # TESTUPDATE: If a managed node has a long nodename then the
            # task description is too long to fit on a single line. So instead
            # of the stdout containing a line starting with prefix, it will
            # just start with the filename
            # Therefore if prefix does not appear in the stdout the task
            # descriptions have been fixed, so only search for lines that
            # that start with the filename
            prefix = "Install file /etc/exlongord1_"
            if not self.is_text_in_list(prefix, stdout):
                prefix = "/etc/example_ord1_"
            dprefix = "Install delay file /etc/exlongord1_"
            if not self.is_text_in_list(dprefix, stdout):
                dprefix = "/etc/exlongord1_"
            self.assertTrue(stdout.index("{0}call1_{1}_LONG07".\
                       format(prefix, hostname)) <
                   stdout.index("{0}call2_{1}_LONG07".\
                       format(dprefix, hostname)),
                   "Ord1 Call1 not before Ord1 Call2")
            self.assertTrue(stdout.index("{0}call2_{1}_LONG07".\
                       format(dprefix, hostname)) <
                   stdout.index("{0}call3_{1}_LONG07".\
                       format(prefix, hostname)),
                   "Ord1 Call2 not before Ord1 Call3")
            self.assertTrue(stdout.index("{0}call3_{1}_LONG07".\
                       format(prefix, hostname)) <
                   stdout.index("status crond for {0}".\
                       format(hostname)),
                   "Ord1 Call3 not before crond status")

        # Now run plan
        self.execute_cli_runplan_cmd(self.test_node)
        timeout_mins = 20
        # Now wait until we have 1 running and 1 success
        docheck = True
        numchecks = 0
        while docheck:
            cmd = self.cli.get_show_plan_status_cmd()
            stdout, stderr, returnc = self.run_command(self.test_node,
                cmd)
            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)
            sdict = self.cli.load_plan_state_to_dict(stdout)
            if int(sdict['Success:']) == 1 and int(sdict['Running:']) == 1:
                docheck = False
            else:
                numchecks = numchecks + 1
                self.assertNotEquals(10, numchecks)
                time.sleep(10)

        # Now restart litp service
        cmd = RHCmdUtils.get_service_restart_cmd('litpd')
        stdout, stderr, returnc = self.run_command(self.test_node,
            cmd, su_root=True)
        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)
        self.assertFalse(self.is_text_in_list("FAIL", stdout),
             "Failed to restart service")

        # Now re-create plan
        self.execute_cli_createplan_cmd(self.test_node)

        # Do a show plan and check tasks are in correct order
        stdout, _, _ = self.execute_cli_showplan_cmd(self.test_node)
        for node in nodes:
            mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
            hostname = self.get_node_att(mn_filename, 'hostname')

            # Check order for ord1 ordered task list has 2 and 3 tasks in
            self.assertTrue(stdout.index("{0}call2_{1}_LONG07".\
                       format(dprefix, hostname)) <
                   stdout.index("{0}call3_{1}_LONG07".\
                       format(prefix, hostname)),
                   "Ord1 Call2 not before Ord1 Call3")

            self.assertTrue(stdout.index("{0}call3_{1}_LONG07".\
                       format(prefix, hostname)) <
                   stdout.index("status crond for {0}".\
                       format(hostname)),
                   "Ord1 Call3 not before crond status")

        try:
            # Now run plan
            self.execute_cli_runplan_cmd(self.test_node)
            timeout_mins = 20

            completed_successfully = self.wait_for_plan_state(self.test_node,
                 test_constants.PLAN_COMPLETE, timeout_mins)
            self.assertTrue(completed_successfully, "Wait for plan failed")

            # Now check files are there
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
                hostname = self.get_node_att(mn_filename, 'hostname')
                # Files created by pluginD
                filename = "/etc/exlongord1_call1_{0}_LONG07".format(hostname)
                self.assertTrue(self.remote_path_exists(self.test_node,
                       filename), "No file {0}".format(filename))

                filename = "/etc/exlongord1_call2_{0}_LONG07".format(hostname)
                self.assertTrue(self.remote_path_exists(self.test_node,
                       filename), "No file {0}".format(filename))

                filename = "/etc/exlongord1_call3_{0}_LONG07".format(hostname)
                self.assertTrue(self.remote_path_exists(self.test_node,
                       filename), "No file {0}".format(filename))
        finally:
            # Clear up /etc files produced by test
            nodes = self.find(self.test_node, "/deployments",
               "node")
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                                                              node)
                hostname = self.get_node_att(mn_filename, 'hostname')
                filename = "/etc/exlongord1_call1_{0}_LONG07".format(hostname)
                self.remove_item(self.test_node, filename, su_root=True)

                filename = "/etc/exlongord1_call2_{0}_LONG07".format(hostname)
                self.remove_item(self.test_node, filename, su_root=True)

                filename = "/etc/exlongord1_call3_{0}_LONG07".format(hostname)
                self.remove_item(self.test_node, filename, su_root=True)

    @attr('all', 'non-revert', 'plugins', 'P2')
    def obsolete_08_p_valid_network_view(self):

        """
        Temporarily Obsoleted

        Description:
            This test tests that network view can be got
        Actions:
            1. Creates package-list NET08 with valid parameters
            2. Creates and run plan
            3. Checks file created called
                  /etc/examplenet_<if>_<ip>_<mac>_NET08 on managed node
        Results:
            Filename created on managed nodes
        """
        # Automates 2.0 PLUG_TC1_P1 part a
        rpms = []
        plugins = []
        plugin = "ERIClitpstplugtc4_NetView_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140410191748.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        props = "name=NET08"
        self.execute_cli_create_cmd(self.test_node,
                 '/software/items/test08',
                 'package-list',
                 props)
        # Now create it on each managed node
        nodes = self.find(self.test_node, "/deployments",
           "node")
        self._link_pl_on_nodes(nodes, "t8", props)

        # Now create plan
        self.execute_cli_createplan_cmd(self.test_node)

        try:
            # Now run plan
            self.execute_cli_runplan_cmd(self.test_node)
            timeout_mins = 3
            completed_successfully = self.wait_for_plan_state(self.test_node,
                 test_constants.PLAN_COMPLETE, timeout_mins)
            self.assertTrue(completed_successfully, "Wait for plan failed")

            # Now check file is there and got all data
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
                # Check that its created an examplenet file
                filename = "/etc/examplenet_*_NET08.txt"
                self.assertTrue(self.remote_path_exists(mn_filename, filename),
                         "No {0} found".format(filename))

                # Check that no examplenet files exist with None in the name
                filename = "/etc/examplenet_*None*_NET08.txt"
                self.assertFalse(self.remote_path_exists(mn_filename,
                         filename), "{0} found".format(filename))
        finally:
            # Clear up /etc files produced by test
            nodes = self.find(self.test_node, "/deployments",
               "node")
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                                                              node)
                filename = "/etc/examplenet_*_NET08.txt"
                self.remove_item(mn_filename, filename, su_root=True)

    @attr('all', 'non-revert', 'plugins', 'P2')
    def obsolete_09_n_fail_remote_tasks(self):
        """
        Temporarily Obsoleted

        Description:
            This test tests that if have a plugin that contains amongst others
            a RemoteTask, that if the RemoteTask fails when plan is run then no
            other tasks are run. If you then re-creat the plan it will decide
            to re-do the remote task.
        Actions:
            1. Creates package-list with valid parameters
            2. Creates plan and show plan
            3. Plan should include restart rubbish service
            4. Wait for plan to stop
            5. Plan should fail, as no rubbish service
            6. Create plan and check has all tasks in
        Results:
            Plan should fail on restart of rubbish service
        """
        rpms = []
        plugins = []
        plugin = "ERIClitpexlongordered_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140321122159.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        # Name will fire both the unordered and ordered plugins
        props = "name=FAILLONG09"
        self.execute_cli_create_cmd(self.test_node,
                 '/software/items/test09',
                 'package-list',
                 props)
        # Now create it on each managed node
        nodes = self.find(self.test_node, "/deployments",
           "node")
        self._link_pl_on_nodes(nodes, "t9", props)

        # Now create plan
        self.execute_cli_createplan_cmd(self.test_node)

        try:
            # Do a show plan and check restart rubbish task is there
            stdout, _, _ = self.execute_cli_showplan_cmd(self.test_node)
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
                hostname = self.get_node_att(mn_filename, 'hostname')

                # Check restart rubbish is in plan
                # NB order of tasks generated by plugin is covered by test 07
                # key importance for this test is that we have restart rubbish
                # service
                self.assertTrue(self.is_text_in_list(
                   "restart rubbish for {0}".format(hostname),
                    stdout),
                   "Restart rubbish service missing for {0}".format(hostname))

            # Now run plan
            self.execute_cli_runplan_cmd(self.test_node)
            timeout_mins = 20
            self.wait_for_plan_state(self.test_node,
                 test_constants.PLAN_COMPLETE, timeout_mins)

            cmd = self.cli.get_show_plan_status_cmd()
            stdout, stderr, returnc = self.run_command(self.test_node,
                cmd)
            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)
            sdict = self.cli.load_plan_state_to_dict(stdout)
            self.assertEquals(3, int(sdict['Success:']))
            self.assertEquals(1, int(sdict['Failed:']))

            # Now re-create plan
            self.execute_cli_createplan_cmd(self.test_node)

            # Do a show plan and check have restart task for both nodes
            stdout, _, _ = self.execute_cli_showplan_cmd(self.test_node)
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
                hostname = self.get_node_att(mn_filename, 'hostname')

                self.assertTrue(self.is_text_in_list(
                   "restart rubbish for {0}".\
                       format(hostname), stdout),
                   "No start rubbish task")

        finally:
            # Clear up /etc files produced by test
            nodes = self.find(self.test_node, "/deployments",
               "node")
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                                                              node)
                hostname = self.get_node_att(mn_filename, 'hostname')
                filename = "/etc/exlongord1_call1_{0}_FAILLONG09".\
                    format(hostname)
                self.remove_item(self.test_node, filename, su_root=True)

                filename = "/etc/exlongord1_call2_{0}_FAILLONG09".\
                    format(hostname)
                self.remove_item(self.test_node, filename, su_root=True)

                filename = "/etc/exlongord1_call3_{0}_FAILLONG09".\
                    format(hostname)
                self.remove_item(self.test_node, filename, su_root=True)

    @attr('all', 'non-revert', 'plugins', 'P2')
    def obsolete_10_p_fail_rectify_remote_tasks(self):
        """
        Temporarily Obsoleted

        Description:
            This test tests that if have a failed remote task that further
            tasks don't run, and if rectify problem and re-run plan that
            task is run
        Actions:
            1. Creates package-list with valid parameters
            2. Creates plan and show plan
            3. Plan should contain commands for restart rubbish service
            4. Wait for plan to stop
            5. Plan should fail on remove task
            6. Create rubbish service
            7. Create plan and check has all tasks in
        Results:
            Plan should fail on first attempt, but succeed on second
        """
        rpms = []
        plugins = []
        plugin = "ERIClitpexlongordered_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140321122159.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        # Name will fire both the unordered and ordered plugins
        props = "name=FAILLONG10"
        self.execute_cli_create_cmd(self.test_node,
                 '/software/items/test10',
                 'package-list',
                 props)
        # Now create it on each managed node
        nodes = self.find(self.test_node, "/deployments",
           "node")
        self._link_pl_on_nodes(nodes, "t9", props)

        # Now create plan
        self.execute_cli_createplan_cmd(self.test_node)

        try:
            # Do a show plan and check restart rubbish task is there
            stdout, _, _ = self.execute_cli_showplan_cmd(self.test_node)
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
                hostname = self.get_node_att(mn_filename, 'hostname')

                # Check restart rubbish is in plan
                # NB order of tasks generated by plugin is covered by test 07
                # key importance for this test is that we have restart rubbish
                # service
                self.assertTrue(self.is_text_in_list(
                   "restart rubbish for {0}".format(hostname),
                   stdout),
                   "Restart rubbish service missing for {0}".format(hostname))

            # Now run plan
            self.execute_cli_runplan_cmd(self.test_node)
            timeout_mins = 20
            self.wait_for_plan_state(self.test_node,
                 test_constants.PLAN_COMPLETE, timeout_mins)

            cmd = self.cli.get_show_plan_status_cmd()
            stdout, stderr, returnc = self.run_command(self.test_node,
                cmd)
            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)
            sdict = self.cli.load_plan_state_to_dict(stdout)
            # Plan will only have our ordered task in so 4th task will be
            # the remote task
            self.assertEquals(3, int(sdict['Success:']))
            self.assertEquals(1, int(sdict['Failed:']))

            # Now re-create plan
            self.execute_cli_createplan_cmd(self.test_node)

            # Now put rubbish service on node1 and node2
            local_path = os.path.dirname(repr(__file__)).strip('\'')
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
                self.assertTrue(self.copy_file_to(mn_filename,
                    "{0}/rubbish".format(local_path),
                    "/etc/init.d", True), "Failed to copy rubbish service")
                cmd = 'chmod 777 /etc/init.d/rubbish'
                _, _, returnc = self.run_command(mn_filename, cmd,
                    su_root=True)
                self.assertEqual(0, returnc)

            # Do a show plan and check have restart task for both nodes
            stdout, _, _ = self.execute_cli_showplan_cmd(self.test_node)
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                     node)
                hostname = self.get_node_att(mn_filename, 'hostname')

                self.assertTrue(self.is_text_in_list(
                   "restart rubbish for {0}".\
                       format(hostname), stdout),
                   "No restart rubbish task")

            # Now run plan
            self.execute_cli_runplan_cmd(self.test_node)
            timeout_mins = 20
            completed_successfully = self.wait_for_plan_state(self.test_node,
                 test_constants.PLAN_COMPLETE, timeout_mins)
            self.assertTrue(completed_successfully, "Failed to run plan")

        finally:
            # Clear up /etc files produced by test
            nodes = self.find(self.test_node, "/deployments",
               "node")
            for node in nodes:
                mn_filename = self.get_node_filename_from_url(self.test_node,
                                                              node)
                hostname = self.get_node_att(mn_filename, 'hostname')
                filename = "/etc/exlongord1_call1_{0}_FAILLONG10".\
                    format(hostname)
                self.remove_item(self.test_node, filename, su_root=True)

                filename = "/etc/exlongord1_call2_{0}_FAILLONG10".\
                    format(hostname)
                self.remove_item(self.test_node, filename, su_root=True)

                filename = "/etc/exlongord1_call3_{0}_FAILLONG10".\
                    format(hostname)
                self.remove_item(self.test_node, filename, su_root=True)

    @attr('all', 'non-revert', 'plugins', 'P2')
    def obsolete_11_p_updatable_items(self):

        """
        Temporarily Obsoleted

        Description:
            This test uses a plugin that has a custom extension which has
            a property called updatable in its item example-item. Each time
            the plugin creates a file its value is updated, and this test
            verifies the value is updated
        Actions:
            1. Creates example-item with valid parameters
            2. Creates and run plan
            3. Checks 2 files per node are created on the MS
                  /etc/exampleplug_<name>_<size>_<rub>.txt.<updatable>
                  /etc/exampleplug_<name>_<size>_<rub>.txt.<updatable>1
               Each time file is created a 1 is appended to end of
               updatable
            4. Check value of updatable has been updated by plugin
        Results:
            Filename created on managed nodes
        """
        rpms = []
        plugins = []
        plugin = "ERIClitpexampleextapi_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140407171744.noarch".format(plugin))
        plugin = "ERIClitpexampleplug_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140506123755.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        # Automates 2.0 PLUG_TC1_P1 part c
        props = "name=testcall11 size=10B rubbish=rub03 updatable=1"
        soft_item_collect = self.find(self.test_node, "/software",
                                      "software-item", False)
        self.execute_cli_create_cmd(self.test_node,
                 '{0}/test11'.format(soft_item_collect[0]),
                 'example-item',
                 props)

        # Now create it on each managed node
        nodes = self.find(self.test_node, "/deployments",
           "node")
        props2 = "name=testcall11"
        for node in nodes:
            linkpath = "{0}/items/t11".format(node)
            self.execute_cli_link_cmd(self.test_node,
                linkpath, "example-item", props2)

        # Now create plan
        self.execute_cli_createplan_cmd(self.test_node)

        try:
            # Now run plan
            self.execute_cli_runplan_cmd(self.test_node)
            timeout_mins = 3
            completed_successfully = self.wait_for_plan_state(self.test_node,
                 test_constants.PLAN_COMPLETE, timeout_mins)
            self.assertTrue(completed_successfully, "Wait for plan failed")

            # Now check file is there
            exp_updatable = "1"
            prefix = "/etc/exampleplug_testcall11_10B_rub03.txt"
            for node in nodes:
                # Two files per node, 1st file
                filename = "{0}.{1}".format(prefix, exp_updatable)
                self.assertTrue(self.remote_path_exists(self.test_node,
                                                          filename),
                     "No file {0}".format(filename))
                # updatable updated, new file
                exp_updatable = "{0}1".format(exp_updatable)
                filename = "{0}.{1}".format(prefix, exp_updatable)
                self.assertTrue(self.remote_path_exists(self.test_node,
                                                          filename),
                     "No file {0}".format(filename))
                # Update updatable again
                exp_updatable = "{0}1".format(exp_updatable)

            # Now check that updatable has been incremented
            self.assertEqual(exp_updatable,
                       self.execute_show_data_cmd(
                       self.test_node,
                       '{0}/test11'.format(soft_item_collect[0]),
                       "updatable"))

        finally:
            # Clear up /etc files produced by test
            exp_updatable = "1"
            prefix = "/etc/exampleplug_testcall11_10B_rub03.txt"
            for node in nodes:
                filename = "{0}.{1}".format(prefix, exp_updatable)
                self.remove_item(self.test_node, filename, su_root=True)
                exp_updatable = "{0}1".format(exp_updatable)
                filename = "{0}.{1}".format(prefix, exp_updatable)
                self.remove_item(self.test_node, filename, su_root=True)
                exp_updatable = "{0}1".format(exp_updatable)

    @attr('all', 'non-revert', 'plugins', 'P2')
    def obsolete_12_n_invalid_readonly_items(self):

        """
        Temporarily Obsoleted

        Description:
            This test uses the example-items extension which has properties
            that cannot be updated by the REST API. This verifies that those
            values cannot be updated, and that an export/import of object
            stays the same.
        Actions:
            1. Creates example-item with readonly and constant parameter
            2. Updates example-item's readonly parameter by CLI
            3. Updates example-item's constant parameter by CLI
            4. Prove can export and then import successfully, and value
               is kept
        Results:
            The example-items updates are all rejected
        """
        rpms = []
        plugins = []
        plugin = "ERIClitpexampleextapi_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140407171744.noarch".format(plugin))
        plugin = "ERIClitpexampleplug_CXP1234567"
        plugins.append(plugin)
        rpms.append(
           "{0}-1.0.1-SNAPSHOT20140506123755.noarch".format(plugin))
        self._install_plugin(plugins, rpms)
        props = "name=i12a readonly=roset constant=coset"
        soft_item_collect = self.find(self.test_node, "/software",
                                      "software-item", False)
        self.execute_cli_create_cmd(self.test_node,
                 '{0}/i12'.format(soft_item_collect[0]),
                 'example-item',
                 props)
        # Now prove cannot update
        newprops = "readonly=roset2"
        _, stderr, _ = self.execute_cli_update_cmd(self.test_node,
                 '{0}/i12'.format(soft_item_collect[0]),
                 newprops,
                 expect_positive=False)
        self.assertTrue(self.is_text_in_list(
                  "Unable to modify readonly property: readonly", stderr),
                  "Wrong errors reported in standard error")

        # Now test with constant parameter
        newprops = "constant=coset2"
        _, stderr, _ = self.execute_cli_update_cmd(self.test_node,
                 '{0}/i12'.format(soft_item_collect[0]),
                 newprops,
                 expect_positive=False)
        self.assertTrue(self.is_text_in_list(
                  "Unable to modify readonly property: constant", stderr),
                  "Wrong errors reported in standard error")

        # Check not updated
        self.assertEqual("coset",
                         self.execute_show_data_cmd(self.test_node,
                       '{0}/i12'.format(soft_item_collect[0]),
                       "constant"))
        self.assertEqual("roset",
                         self.execute_show_data_cmd(self.test_node,
                        '{0}/i12'.format(soft_item_collect[0]),
                       "readonly"))
        self.execute_cli_export_cmd(self.test_node,
                                   '{0}/i12'.format(soft_item_collect[0]),
                                    "/tmp/i12.xml")
        self.execute_cli_remove_cmd(self.test_node,
                                 '{0}/i12'.format(soft_item_collect[0]))
        self.execute_cli_load_cmd(self.test_node,
                                    soft_item_collect[0],
                                    "/tmp/i12.xml")
        # Check has values originally set
        self.assertEqual("coset",
            self.execute_show_data_cmd(self.test_node,
                      '{0}/i12'.format(soft_item_collect[0]),
                       "constant"))
        self.assertEqual("roset",
                       self.execute_show_data_cmd(self.test_node,
                      '{0}/i12'.format(soft_item_collect[0]),
                       "readonly"))
