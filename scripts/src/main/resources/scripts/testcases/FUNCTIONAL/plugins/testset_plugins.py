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

    @attr('all', 'non-revert', 'plugins', 'P2', 'plugins_tc01')
    def obsolete_test_01_invalid_extension_items(self):

        """
        Temporarily Obsoleted

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
    def obsolete_test_02_valid_example_extension_items(self):

        """
        Temporarily Obsoleted
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
