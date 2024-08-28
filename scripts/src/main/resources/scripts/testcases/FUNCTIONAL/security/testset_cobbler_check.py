#!/usr/bin/env python
'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Nov 2014
@author:    Stefan
@summary:   System Test for Checking the output of
            "cobbler check"
            Agile: EPIC-xxxx, STORY-xxxx, Sub-task: STORY-xxxx
'''
from litp_generic_test import GenericTest, attr
from litp_generic_utils import GenericUtils


class CobblerChk(GenericTest):
    """
    Description:
        These tests are checking the risk items that
        "cobbler check" command returns.
    """
    def setUp(self):
        super(CobblerChk, self).setUp()
        self.cobbler_chk_cmd = '/usr/bin/cobbler check'

        self.expected_list = \
                      {
                      "1": "SELinux is enabled. Please review the following" \
                      " wiki page for details on ensuring cobbler works" \
                      " correctly in your SELinux environment:",
                      "2": "Unknown distribution type, cannot check for" \
                      " running service dhcpd",
                      "3": "Unknown distribution type, cannot check for" \
                      " running service cobblerd",
                      "4": "some network boot-loaders are missing from" \
                      " /var/lib/cobbler/loaders, you may run 'cobbler" \
                      " get-loaders' to download them, or, if you only want" \
                      " to handle x86/x86_64 netbooting, you may ensure" \
                      " that you have installed a *recent* version of the" \
                      " syslinux package installed and can ignore this" \
                      " message entirely.  Files in this directory, should" \
                      " you want to support all architectures, should" \
                      " include pxelinux.0, menu.c32, elilo.efi, and " \
                      "yaboot. The 'cobbler get-loaders' command is the" \
                      " easiest way to resolve these requirements.",
                      "5": "Apache (httpd) is not installed and/or in path",
                      "6": "since iptables may be running, ensure 69," \
                      " 80/443, and 25151 are unblocked",
                      "7": "debmirror package is not installed, it will be" \
                      " required to manage debian deployments and" \
                      " repositories",
                      "8": "ksvalidator was not found, install pykickstart",
                      "9": "fencing tools were not found, and are required" \
                      " to use the (optional) power management features." \
                      " install cman or fence-agents to use them"
                     }
        self.ms_node = self.get_management_node_filename()

    def tearDown(self):
        """
        Runs after every test
        """
        pass

    def _run_cmd(self, cmd, add_to_cleanup=True, su_root=False,
                 expect_positive=True):
        """
        Run a command asserting success or error (returns: stdout / stderr)
        """
        stdout, stderr, exit_code = self.run_command(
            self.ms_node, cmd, add_to_cleanup=add_to_cleanup, su_root=su_root)
        if expect_positive:
            self.assertNotEqual("", stdout)
            self.assertEqual([], stderr)
            self.assertEqual(0, exit_code)
            result = '\n'.join(stdout)
        else:
            self.assertEqual([], stdout)
            self.assertNotEqual("", stderr)
            self.assertNotEqual(0, exit_code)
            result = '\n'.join(stderr)
        return result

    def _get_risk_items(self):
        """
        Method to get the list returned by cobbler check
        """
        cobbler_check_string = self._run_cmd(self.cobbler_chk_cmd, \
                                             su_root=True)
        risk_items = cobbler_check_string.split('\n')
        risk_items_list = {}
        for item in risk_items:
            risk_id, _, risk_msg = item.partition(" : ")
            if risk_id.isdigit() == True:
                risk_items_list[risk_id] = risk_msg
        return risk_items_list

    @attr('all', 'non-revert', 'security', 'P3', 'security_tc01')
    def test_01_cobbler_chk(self):
        """
        Description:
            Positive test that checks cobbler check output
        Actions:
            1. Execute "cobbler check" on ms.
            2. Look for new messages that cobbler check might returned.
        Results:
            Cobbler check should return the expected items.
        """

        risk_items = self._get_risk_items()
        self.log('info', 'risk_items')
        self.log('info', risk_items)
        #self._assert_list_in(self.expected_list, risk_items)
        check_expected_not_in_actual = \
            GenericUtils.compare_lists(self.expected_list.values(), \
                                       risk_items.values(), True, False)

        self.assertEqual([], list(check_expected_not_in_actual), \
                         "Expected risk items not found in the" \
                         " output of cobbler check ...: '%s'" % \
                         str(check_expected_not_in_actual))

        check_actual_not_in_expected = \
            GenericUtils.compare_lists(self.expected_list.values(), \
                                       risk_items.values(), True, True)

        self.assertEqual([], list(check_actual_not_in_expected), \
                         "New risk items found in the output of" \
                         " cobbler check ...: '%s'" % \
                         str(check_actual_not_in_expected))

        self.log('info', 'Test passed, expected items were returned...')
