'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     October 2014
@author:    Vinnie McGuinness
@summary:   System test to check misc security issues,

'''

from litp_generic_test import GenericTest, attr
from litp_cli_utils import CLIUtils
from redhat_cmd_utils import RHCmdUtils
from litp_security_utils import SecurityUtils
import test_constants
from time import sleep
import os
import re


class SecurityChecks(GenericTest):
    """
        System tests to check possible security issues
    """

    def setUp(self):
        """Run before every test"""
        super(SecurityChecks, self).setUp()
        self.cli = CLIUtils()
        self.security = SecurityUtils()
        self.rhel = RHCmdUtils()
        self.ms_node = self.get_management_node_filename()
        self.targets = self.get_managed_node_filenames()
        self.targets.append(self.ms_node)
        if 'dot74' in self.targets:
            self.targets.remove('dot74')
        if 'dot76' in self.targets:
            self.targets.remove('dot76')
        if 'amosC3' in self.targets:
            self.targets.remove('amosC3')
        if 'ammsfs_01' in self.targets:
            self.targets.remove('ammsfs_01')
        if 'atsfsx82' in self.targets:
            self.targets.remove('atsfsx82')
        if 'dot66-node2' in self.targets:
            self.targets.remove('dot66-node2')
        self.local_filepath = os.path.dirname(__file__) + "/CDB_sec_files/"
        self.setup_cmds = []

    def tearDown(self):
        """run after each test"""
        super(SecurityChecks, self).tearDown()

    @staticmethod
    def remove_comments(in_list):
        """
        Remove any item in list that start with a "#" character
        """
        out_list = []
        for item in in_list:
            # check first character in item
            if item.strip()[0] == "#":
                print "Found comment to so ignore \t{0} ".format(item)
            else:
                print "Found entry so add to list {0} ".format(item)
                out_list.append(item)
        print "\n list of credentials to check {0} \t".format(out_list)
        return out_list

    @staticmethod
    def compare_lists(list1, list2):
        """
        Compare list1 against list2
        Print any differences
        return True if there are no differences
        """
        not_found_list = []
        match = True
        for item in list1:
            if item in list2:
                print "\tOK Found --> {0} ".format(item)
            else:
                not_found_item = "\tNot Found --> " + item
                not_found_list.append(not_found_item)
                print not_found_item
                match = False
        if not_found_list != []:
            print "\n\t*** Items not found ***"
            for item in not_found_list:
                print item
        return match

    @staticmethod
    def remove_strings(list_ok, list_returned):
        """
        Check list_returned for any items that are in the list_ok.
        If the item in list_ok they are removed from the list_returned.
        Any items which are the result of using "find" on a temporary file
        which no longer exists are also removed.
        The list_returned is returned minus any OK items.
        """
        # Define string which is used to identify the find command picking up
        # a temporary file which no longer exists
        find_error_output = ": No such file or directory"

        # Filter through lists
        for item_ok in list_ok:
            for item_ret in list(list_returned):
                if item_ok in item_ret or find_error_output in item_ret:
                    #self.log('info', item_ret)
                    list_returned.remove(item_ret)
        return list_returned

    @staticmethod
    def chk_and_remove_regex_matches(regex_list, list_returned):
        """
        Description:
            Function to check a list of files for matches from
            the regex list.
        Args:
            regex_list (list): A list of regex to check for
                               files that can be ignored.
            list_returned (list): All the files returned
                                  from the systems to be checked.
        Returns:
            list. A list of files from the system.
        """
        for regex in regex_list:
            for item_ret in list(list_returned):
                # WILL CHECK FOR ANY REGEX MATCHES
                if re.search(regex, item_ret):
                    list_returned.remove(item_ret)
        return list_returned

    @staticmethod
    def get_time_len(time):
        """
            function to take a real time and return a float value
        """
        time = time.replace('real\t', '')
        time = time.replace('m', '')
        time = time.replace('s', '')
        return float(time)

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc20')
    def test_20_check_authentication_credentials(self):
        """
        Description:
            Check authentication credentials criteria is consistent
        Actions:
            1.Check that PASS_MAX_DAYS is equal to 99999 in file
              /etc/login.defs on MS
            2.Check authentication credentials criteria is consistent
              for MS and LITP Nodes by comparing entry's in the file
              /etc/login.defs on MS and MN
        Results:
            1.Value matchs expected value in PASS_MAX_DAYS
            2.Authentication credentials criteria is consistent
        """
        filepath = "/etc/login.defs"

        ms_list = self.get_file_contents(self.ms_node, filepath, None, True)

        ms_cred = self.remove_comments(ms_list)

        found = False
        #Grep command to seach file and Grep PASS_MAX_DAYS,
        #assertion error if not present
        cmd = self.rhel.get_grep_file_cmd('/etc/login.defs', "PASS_MAX_DAYS")
        result, _, _ = self.run_command(self.ms_node, cmd,
                                        default_asserts=True)
        for item in result:
            if "99999" in item:
                found = True
                self.log("info",
                         "Expected value 99999 found in PASS_MAX_DAYS")

        self.assertTrue(found, "Error: Expected value 99999 not found in file")

        for node in self.targets:
            print "\nTesting node {0} ".format(node)
            mn_list = self.get_file_contents(node, filepath, None, True)
            mn_cred = self.remove_comments(mn_list)

            print "\nCompare credentials of nodes {0} & MS ".format(node)
            result = self.compare_lists(ms_cred, mn_cred)
            self.assertTrue(
                result, "{0} file does not match {1} ".format(node,
                                                              self.ms_node))
            print "\nCompare credentials of node MS & {0} ".format(node)
            result = self.compare_lists(mn_cred, ms_cred)
            self.assertTrue(
                result, "{0} file does not match {1} ".format(node,
                                                              self.ms_node))

    @attr('all', 'non-revert', 'security', 'P2', 'security_tc21')
    def test_21_check_litprc_permissions(self):
        """
        Description:
            When the .litprc file has incorrect permissions set, verify that
            litp only accepts the correct credentials when commands are entered
            SEC_TC17_P1
        Actions:
            1 Set incorrect permissions on .litprc
            2 running litp commands propts user for password
            3 Prompted for usename and password - Enter correct
            4 Prompted for usename and password - wrong password
            5 Prompted for usename and password - wrong name
            6 Run command with correct crenditionals in cmd
            7 test incorrect password entered in cmd
            8 test incorrect username entered in cmd
            9 Set correct permissions and run command
        Result:
            username & password is requested as expected
        """
        expected_err = "Authentication Failed. Provide Username and Password:"
        unauthorized_access = "Error 401: Unauthorized access"

        self.log('info', "*** 1 Set incorrect permissions on .litprc ***")
        cmd = "/bin/chmod 666 " + test_constants.AUTHTICATE_FILENAME
        stdout, stderr, ret_code = self.run_command(self.ms_node, cmd)
        self.assertEqual(stdout, [], "stdout should be outputted")
        self.assertEqual(stderr, [], "stderr should be outputted")
        self.assertEqual(0, ret_code, "Unexpected error code ")

        try:
            self.log('info',
             "*** 2 running litp commands propts user for password ***")
            cmd = self.cli.get_show_cmd('/')
            stdout, stderr, ret_code = self.run_command(self.ms_node, cmd)
            self.assertEqual(stdout, [], "No litp data should be outputted")
            self.assertTrue((expected_err in stderr),
                        ("unexpected error message", stderr))
            self.assertEqual(1, ret_code, "Unexpected error code ")

            self.log('info',
             "*** 3 Prompted for usename and password - Enter correct *** ")
            expects_cmds = list()
            expects_cmds.append(self.get_expects_dict("Username:",
             "litp-admin"))
            expects_cmds.append(self.get_expects_dict("Password:",
             "litp_admin"))
            cmd_to_run = self.cli.get_show_cmd('/')
            stdout, stderr, ret_code = self.run_expects_command(self.ms_node,
                                                            cmd_to_run,
                                                            expects_cmds)
            self.assertNotEqual(stdout, [], "No litp data should be outputted")
            self.assertEqual(stderr, [], ("unexpected error message"))
            self.assertEqual(0, ret_code, "Unexpected error code ")

            self.log('info',
             "*** 4 Prompted for usename and password - wrong password *** ")
            expects_cmds = list()
            expects_cmds.append(self.get_expects_dict("Username:",
             "litp-admin"))
            expects_cmds.append(self.get_expects_dict("Password:",
             "wrong"))
            cmd_to_run = self.cli.get_show_cmd('/')
            stdout, stderr, ret_code = self.run_expects_command(self.ms_node,
                                                            cmd_to_run,
                                                            expects_cmds)
            self.assertTrue((unauthorized_access in stdout),
                        ("unexpected error message", stdout))
            self.assertNotEqual(stdout, [], "unexpected error message")
            self.assertEqual(1, ret_code, "Unexpected Error code ")

            self.log('info',
             "*** 5 Prompted for usename and password - wrong name *** ")
            expects_cmds = list()
            expects_cmds.append(self.get_expects_dict("Username:",
              "wrong"))
            expects_cmds.append(self.get_expects_dict("Password:",
              "litp_admin"))
            cmd_to_run = self.cli.get_show_cmd('/')
            stdout, stderr, ret_code = self.run_expects_command(self.ms_node,
                                                            cmd_to_run,
                                                            expects_cmds)
            self.assertTrue((unauthorized_access in stdout),
                        ("unexpected error message", stdout))
            self.assertNotEqual(stdout, [], "unexpected error message")
            self.assertEqual(1, ret_code, "Unexpected error code ")

            self.log('info',
              "*** 6 Run command with correct crenditionals in cmd ***")
            cmd = self.cli.get_show_cmd('/')
            cmd = self.cli.add_creds_to_litp_cmd(cmd, "litp-admin",
              "litp_admin")
            stdout, stderr, ret_code = self.run_command(self.ms_node, cmd)
            self.assertNotEqual(stdout, [], "litp data should be outputted")
            self.assertEqual(stderr, [], "Unexpected error message")
            self.assertEqual(0, ret_code, "Unexpected error code ")

            self.log('info',
             "*** 7 test incorrect password entered in cmd ***")
            cmd = self.cli.get_show_cmd('/')
            cmd = self.cli.add_creds_to_litp_cmd(cmd, "litp-admin", "inc_pass")
            stdout, stderr, ret_code = self.run_command(self.ms_node, cmd)
            self.assertEqual(stdout, [], "litp data should be outputted")
            self.assertTrue((unauthorized_access in stderr),
                        ("unexpected error message", stderr))
            self.assertEqual(1, ret_code, "Unexpected error code ")

            self.log('info',
              "*** 8 test incorrect username entered in cmd ***")
            cmd = self.cli.get_show_cmd('/')
            cmd = self.cli.add_creds_to_litp_cmd(cmd, "no_user", "litp_admin")
            stdout, stderr, ret_code = self.run_command(self.ms_node, cmd)
            self.assertEqual(stdout, [], "litp data should be outputted")
            self.assertTrue((unauthorized_access in stderr),
                        ("unexpected error message", stderr))
            self.assertEqual(1, ret_code, "Unexpected error code ")

        finally:
            self.log('info',
             "*** 9 Set correct permissions and run command ***")
            cmd = "/bin/chmod 600 " + test_constants.AUTHTICATE_FILENAME
            stdout, stderr, ret_code = self.run_command(self.ms_node, cmd)
            cmd = self.cli.get_show_cmd('/')
            stdout, stderr, ret_code = self.run_command(self.ms_node, cmd)
            self.assertNotEqual(stdout, [], "litp data should be outputted")
            self.assertNotEqual(stdout, [], "unexpected error msg")
            self.assertEqual(0, ret_code, "Unexpected error code ")

    @attr('all', 'non-revert', 'security', 'P3', 'security_tc22')
    def test_22_performance_litpcrypt(self):
        """
        Description:
            SEC_TC22_P2
            Check performance of litpcrypt commands with X number of entries
        Actions:
            Add X number of entries using litpcypt.
            a) Can X + 1 entry be added -
                does it take longer to add than 1 second to enter?
            b) Can the X entry be deleted -
                does it take longer to delete than 1 second to enter?
        Result:
            time taken for first and last add/delete is less that 1 second
        """

        runs = 50
        num = 0
        start = 2
        cmdlist = list()
        # Add first cmd for litpcrypt add with time
        cmdlist.append("time " +
                       self.security.get_litpcrypt_set_cmd("crypt1",
                                                           "user1",
                                                           "pass1"))
        # Add first cmd for litpcrypt delete with time
        cmdlist.append("time " +
                       self.security.get_litpcrypt_delete_cmd("crypt1",
                                                              "user1"))
        # Add x nummber of cmds for litpcrypt add
        for num in range(start, runs):
            cmdlist.append(self.security.get_litpcrypt_set_cmd("crypt" +
                                                               str(num),
                                                               "user" +
                                                               str(num),
                                                               "pass" +
                                                               str(num)))
        # Add last cmd for litpcrypt add with time
        cmdlist.append("time " +
                       self.security.get_litpcrypt_set_cmd("crypt" +
                                                           str(num + 1),
                                                           "user" +
                                                           str(num + 1),
                                                           "pass" +
                                                           str(num + 1)))
        # Add last cmd for litpcrypt delete with time
        cmdlist.append("time " +
                       self.security.get_litpcrypt_delete_cmd("crypt" +
                                                              str(num),
                                                              "user" +
                                                              str(num)))
        # Add x nummber of cmds for litpcrypt delete
        for num in range(start, (runs - 1)):
            cmdlist.append(self.security.get_litpcrypt_delete_cmd("crypt" +
                                                                  str(num),
                                                                  "user" +
                                                                  str(num)))
        # Run commands
        stdout_dict = self.run_commands(self.ms_node, cmdlist)
        # Get times for first and last commands
        first_add = stdout_dict[self.ms_node][0]['stderr'][0]
        first_del = stdout_dict[self.ms_node][1]['stderr'][0]
        last_add = stdout_dict[self.ms_node][runs]['stderr'][0]
        last_del = stdout_dict[self.ms_node][runs + 1]['stderr'][0]
        print "first_add=", first_add
        print "first_del=", first_del
        print "last_add=", last_add
        print "last_del=", last_del
        # Check commands all run under 1 second
        self.assertFalse((self.get_time_len(first_add) > 1),
                         "Time for first_del too long - " + first_add)
        self.assertFalse((self.get_time_len(first_del) > 1),
                         "Time for first_del too long - " + first_del)
        self.assertFalse((self.get_time_len(last_add) > 1),
                         "Time for first_del too long - " + last_add)
        self.assertFalse((self.get_time_len(last_del) > 1),
                         "Time for first_del too long - " + last_del)

    @attr('all', 'non-revert', 'security', 'P2', 'security_tc23')
    def test_23_check_open_ports(self):
        """
        Description:
            SEC_TC23_P1    Check if ports are open on the System
        Actions:
            Check the open ports on MS and MNs to see if
            these are expected to be open
            Use : nmap -p 1-65535 <target>
        Result:
            No unexpected ports are open
        """
        string_ok = [r'>Starting Nmap',
                     r'>Nmap scan report for',
                     r'SERVICE',
                     r'>Host is up',
                     r'filtered ports',
                     r'>Nmap done:', ]

        #LITP does not use FTP so port 21 should never be added to ms filter
        ms_ok_ports = [r'>623/',
                       r'>67/',
                       r'>68/',
                       r'>69/',
                       r'>443/',
                       r'>80/',
                       r'>8139/',
                       r'>8140/',
                       r'>9999/',
                       r'>5672/',
                       r'>4369/',
                       r'>9100/',
                       r'>9101/',
                       r'>9102/',
                       r'>9103/',
                       r'>9104/',
                       r'>9105/',
                       r'>61613/',
                       r'>61614/',
                       r'>123/',
                       r'>22/',
                       r'>53/tcp',     # deployment
                       r'>111/tcp',    # deployment
                       r'>2049/tcp',   # deployment
                       r'>4001/tcp  closed newoak',     # deploymnnt
                       r'>4001/tcp  closed unknown', ]  # deployment

        #LITP does not use FTP so port 21 should never be added to mn filter
        mn_ok_ports = [r'>80/',
                       r'>8139/',
                       r'>8140/',
                       r'>9999/',
                       r'>5672/',
                       r'>4369/',
                       r'>9100/',
                       r'>9101/',
                       r'>9102/',
                       r'>9103/',
                       r'>9104/',
                       r'>9105/',
                       r'>61613/',
                       r'>61614/',
                       r'>123/',
                       r'>22/',
                       r'>53/tcp    closed domain',   # deploymnet
                       r'>111/tcp   open   rpcbind',  # deploymnet
                       r'>647/tcp   open   unknown',  # deploymnet
                       r'>67/',                       # deploymnet
                       r'>2049/tcp  closed nfs',      # deploymnet
                       r'>4001/tcp  closed unknown',  # deploymnet
                       r'>4001/tcp  closed newoak',   # deployment
                       r'>12987/tcp closed unknown', ]  # deploymnet

        suspect_ports = []
        ms_suspect_ports = []
        mn_suspect_ports = []

        for node in self.targets:
            # Get ip on node
            node_ip = self.get_node_att(node, 'ipv4')
            node_name = self.get_node_att(node, 'hostname')
            cmd = "/usr/bin/nmap -p 1-65535 " + node_ip
            stdout, _, ret_code = self.run_command_local(cmd)
            self.assertEqual(0, ret_code, (
                "Unexpected error code " + str(ret_code) +
                "\n\tIs nmap installed on node test is running from?"))
            print "node_name=", node_name

            for item in stdout:
                # remove empty lines from the list
                if len(item) > 0:
                    suspect_ports.append(node_name + ' open port ->' + item)

        print "suspect_ports=", suspect_ports
        suspect_ports = self.remove_strings(string_ok, suspect_ports)
        print "#### List of ports before filtering ####"
        print '\n'.join(suspect_ports)

        # Split MS ports an MN ports into seperate list
        for item in suspect_ports:
            if self.ms_node in item:
                ms_suspect_ports.append(item)
            else:
                mn_suspect_ports.append(item)

        # Filter MS list of suspect ports
        ms_suspect_ports = self.remove_strings(ms_ok_ports, ms_suspect_ports)
        # Filter MN list of suspect ports
        mn_suspect_ports = self.remove_strings(mn_ok_ports, mn_suspect_ports)

        print "\n#### Print MS suspect ports exist #### "
        print '\n'.join(ms_suspect_ports)
        print "\n#### Print MN suspect ports exist #### "
        print '\n'.join(mn_suspect_ports)
        # Assert if any items are not filtered out
        self.assertEqual(ms_suspect_ports, [], ("## Suspect MS ports ## ",
                                                 ms_suspect_ports))
        self.assertEqual(mn_suspect_ports, [], ("## Suspect MN ports ## ",
                                                 mn_suspect_ports))

    @attr('all', 'non-revert', 'security', 'P2', 'security_tc24')
    def test_24_search_for_files_size_zero(self):
        """
        Description:
            Checks nodes for files of size Zero
        Actions:
            use find to get all files sized zoro
            filter out known files of size zero
        Result:
            No unexpected files of size zero exist
        """
        postgresql_data_dir = test_constants.PSQL_9_6_DATA_DIR
        suspect_list = []
        rhel_files = [r'/etc/security/opasswd',
                      r'/etc/exports',
                      r'/etc/yum/pluginconf.d/versionlock.list',
                      r'/etc/.pwd.lock',
                      r'/etc/environment',
                      r'/etc/motd',
                      r'/etc/cron.deny',
                      r'/etc/crypttab',
                      r'targeted/contexts/netfilter_contexts',
                      r'modules/semanage.trans.LOCK',
                      r'modules/active/netfilter_contexts',
                      r'modules/semanage.read.LOCK',
                      r'/etc/gai.conf',
                      r'/.autofsck',
                      r'/var/lib/logrotate.status',
                      r'/var/lib/misc/postfix.aliasesdb-stamp',
                      r'/var/lib/rpm/.rpm.lock',
                      r'/var/lib/nfs/etab',
                      r'/var/lib/nfs/state',
                      r'/var/lib/nfs/xtab',
                      r'/var/lib/nfs/rmtab',
                      r'/var/lib/dhcpd/dhcpd.leases',
                      r'/var/lib/dhcpd/dhcpd6.leases',
                      r'/var/run/rpcbind.lock',
                      r'/var/run/cron.reboot',
                      r'/var/lock/subsys/crond',
                      r'/var/lock/subsys/messagebus',
                      r'/var/lock/subsys/blk-availability',
                      r'/var/lock/subsys/rpcbind',
                      r'/var/lock/subsys/libvirt-guests',
                      r'/var/lock/subsys/postfix',
                      r'/var/lock/subsys/atd',
                      r'/var/lock/subsys/sshd',
                      r'/var/lock/subsys/rhsmcertd',
                      r'/var/lock/subsys/netfs',
                      r'/var/lock/subsys/network',
                      r'/var/lock/subsys/ksmtuned',
                      r'/var/lock/subsys/local',
                      r'/var/lock/subsys/haldaemon',
                      r'/var/lock/subsys/lvm2-monitor',
                      r'/var/lock/subsys/rpc.statd',
                      r'/var/lock/subsys/auditd',
                      r'/var/lock/subsys/rsyslog',
                      r'/var/lock/kdump',
                      r'/var/log/tallylog',
                      r'/var/log/btmp',
                      r'/var/log/spooler',
                      r'/var/spool/at/.SEQ',
                      r'/var/spool/anacron/cron.monthly',
                      r'/var/spool/anacron/cron.daily',
                      r'/var/spool/anacron/cron.weekly',
                      r'/var/spool/mail/rpc',
                      r'/usr/share/rhn/__init__.py',
                      r'/usr/share/rhn/up2date_client/__init__.py',
                      r'/usr/share/groff/1.18.1.4/tmac/mm/se_locale',
                      r'/usr/share/groff/1.18.1.4/tmac/mm/locale',
                      r'share/doc/m2crypto-0.20.2/tests/__init__.py',
                      r'python/Products/GuardedFile/refresh.txt',
                      r'/usr/share/doc/hal-info-20090716/ChangeLog',
                      r'/usr/share/doc/dbus-python-0.83.0/TOD',
                      r'/usr/share/doc/cryptsetup-luks-1.2.0/TOD',
                      r'/usr/share/dracut/modules.d/95znet/55-ccw.rules',
                      r'/usr/share/dracut/modules.d/95znet/ccw_init',
                      r'/usr/share/X11/locale/iso8859-11/Compose',
                      r'/usr/share/X11/locale/microsoft-cp1255/Compose',
                      r'/usr/share/X11/locale/microsoft-cp1251/Compose',
                      r'/usr/share/X11/locale/am_ET.UTF-8/XI18N_OBJS',
                      r'/usr/share/X11/locale/am_ET.UTF-8/XLC_LOCALE',
                      r'/usr/share/X11/locale/microsoft-cp1256/Compose',
                      r'/usr/share/X11/locale/nokhchi-1/Compose',
                      r'/usr/share/X11/locale/fi_FI.UTF-8/XI18N_OBJS',
                      r'/usr/share/X11/locale/fi_FI.UTF-8/XLC_LOCALE',
                      r'/usr/share/X11/locale/iscii-dev/Compose',
                      r'/usr/share/X11/locale/isiri-3342/Compose',
                      r'/usr/share/X11/locale/C/Compose',
                      r'/usr/share/X11/locale/tatar-cyr/Compose',
                      r'/usr/share/X11/locale/th_TH/Compose',
                      r'/usr/share/X11/locale/el_GR.UTF-8/XI18N_OBJS',
                      r'/usr/share/X11/locale/el_GR.UTF-8/XLC_LOCALE',
                      r'/usr/share/X11/locale/tscii-0/Compose',
                      r'/usr/share/mime/icons',
                      r'share/rhsm/subscription_manager/__init__.py',
                      r'rhsm/subscription_manager/plugin/__init__.py',
                      r'/usr/share/rhsm/rhsm_debug/__init__.py',
                      r'/usr/share/rhsm/rct/__init__.py',
                      r'site-packages/sos/plugins/__init__.py',
                      r'te-packages/redhat_support_lib/web/__init__.py',
                      r'redhat_support_lib/__init__.py',
                      r'redhat_support_lib/utils/__init__.py',
                      r'redhat_support_lib/infrastructure/__init__.py',
                      r'redhat_support_lib/system/__init__.py',
                      r'redhat_support_lib/xml/__init__.py',
                      r'redhat_support_tool/__init__.py',
                      r'redhat_support_tool/vendors/__init__.py',
                      r'redhat_support_tool/tools/__init__.py',
                      r'redhat_support_tool/helpers/__init__.py',
                      r'virtconv/parsers/__init__.py',
                      r'/usr/lib/locale/locale-archive.tmpl',
                      r'/usr/lib64/python2.6/email/mime/__init__.py',
                      r'/usr/lib64/python2.6/sepolgen/__init__.py',
                      r'/usr/lib64/python2.6/rhsm/__init__.py',
                      r'/tmp/yum.log',
                      r'0000:05:00.0/host1/fw_dump',
                      r'/0000:05:00.0/host1/optrom',
                      r'/0000:05:00.0/host1/optrom_ctl',
                      r'/0000:05:00.0/host1/vpd',
                      r'/0000:05:00.0/host1/reset',
                      r'/0000:05:00.1/host2/fw_dump',
                      r'/0000:05:00.1/host2/optrom',
                      r'/0000:05:00.1/host2/optrom_ctl',
                      r'/0000:05:00.1/host2/vpd',
                      r'/0000:05:00.1/host2/reset',
                      r'/sys/firmware/acpi/tables/DSDT',
                      r'/sys/firmware/acpi/tables/FACS',
                      r'/sys/firmware/acpi/tables/FACP',
                      r'/sys/firmware/acpi/tables/SPCR',
                      r'/sys/firmware/acpi/tables/MCFG',
                      r'/sys/firmware/acpi/tables/HPET',
                      r'/sys/firmware/acpi/tables/FFFF1',
                      r'/sys/firmware/acpi/tables/SPMI',
                      r'/sys/firmware/acpi/tables/ERST',
                      r'/sys/firmware/acpi/tables/APIC',
                      r'/sys/firmware/acpi/tables/SRAT',
                      r'/sys/firmware/acpi/tables/FFFF2',
                      r'/sys/firmware/acpi/tables/BERT',
                      r'/sys/firmware/acpi/tables/HEST',
                      r'/sys/firmware/acpi/tables/DMAR',
                      r'/sys/firmware/acpi/tables/FFFF3',
                      r'/sys/firmware/acpi/tables/PCCT',
                      r'/sys/firmware/acpi/tables/SSDT1',
                      r'/sys/firmware/acpi/tables/SSDT2',
                      r'/sys/firmware/acpi/tables/SSDT3',
                      r'/sys/firmware/acpi/tables/SSDT4',
                      r'/sys/firmware/acpi/tables/SSDT5',
                      r'/sys/firmware/acpi/tables/SSDT6',
                      r'/sys/firmware/acpi/tables/SSDT7',
                      r'/sys/firmware/acpi/tables/SSDT8',
                      r'/sys/firmware/acpi/tables/SSDT9',
                      r'/sys/firmware/acpi/tables/SSDT10',
                      r'/usr/lib64/firefox/browser/chrome.manifest',
                      r'/usr/lib64/firefox/chrome.manifest']

        list_of_ok_files = [r'/var/VRTSvcs/',
                            r'/cachecookie',
                            r'/dev/odm/',
                            r'/cgroup/',
                            r'/opt/ericsson/nms/litp/lib/',
                            r'__init__.py',
                            r'/etc/cups/',
                            r'/var/lib/ricci',
                            r'/VRTS',
                            r'/sys/devices',
                            r'/var/lib/nfs/',
                            r'var/lock/subsys/',
                            r'etc/default/sfm_resolv.conf.lock',
                            r'/etc/vx/.uuid_sem_lock',
                            r'/etc/vx/.vxesd.cs.lock',
                            r'/tmp/puppet20',
                            r'/var/log/puppet/masterhttp.log ',
                            r'/var/log/rabbitmq/shutdown_err',
                            r'/var/log/rabbitmq/startup_err',
                            r'/var/log/httpd/ssl_request_log',
                            r'/var/log/httpd/ssl_access_log',
                            r'/var/lib/tftpboot/s390x/profile_list',
                            r'rabbit@helios/msg_store_transient/0.rdq',
                            r'rabbit@helios/msg_store_persistent/0.rdq',
                            r'/usr/share/doc/libfontenc-1.0.5/AUTHORS',
                            r'profile/certstore/keystore/KeyStore.lock',
                            r'.VRTSat/profile/certstore/CertStore.lock',
                            r'.VRTSat/profile/systruststore/CertStore.lock',
                            r'/var/run/saslauthd/mux.accept',
                            r'/var/tmp/vxconfigbackup.cmd.fai',
                            r'6Server/.gpgkeyschecked.yum',
                            r'/var/log/puppet/masterhttp.log',
                            r'/var/spool/mail/',
                            r'msg_store_transient/0.rdq',
                            r'msg_store_persistent/0.rdq',
                            r'/var/log/litp/litpd_error.log',
                            r'/var/lib/cobbler/lock',
                            r'gems/rake-10.1.1/lib/rake/ext/module.rb',
                            r'gems/rack-1.5.2/test/.bacon',
                            r'/dev/vx/.dmp/HBA',
                            r'/etc/puppet/namespaceauth.conf',
                            r'/etc/vx/.aascsi3',
                            r'/etc/vx/reconfig.d/vxvm_start_initrd',
                            r'/etc/vx/.vold_msg_buf_shm',
                            r'/etc/vx/jbod.info',
                            r'/usr/lib/python2.6/site-packages/',
                            r'/usr/share/doc/gstreamer-0.10.29/TOD',
                            r'/usr/share/doc/libfontenc-1.0.5/AUTHORS',
                            r'init.pp',
                            r'/var/log/httpd/access_log',
                            r'puppet/modules/mcollective/files/empty/.keep',
                            r'/var/lib/cobbler/kickstarts/sample_esx4.ks',
                            r'/usr/sbin/fence_virsh',
                            r'tmp/test-lsb-',
                            r'/var/spool/postfix/pid/unix.',
                            r'EXTRlitpliblogging_CXP9032141-',
                            r'/system72_mg/lost+found/.fsadm',
                            r'/cluster1_mg/lost+found/.fsadm',
                            r'/opt/SentinelRMSSDK/licenses/lservrc',
                            r'/system72_mg/lost+found/.fsadm',
                            r'/opt/SentinelRMSSDK/licenses/lservrc',
                            r'/opt/SentinelRMSSDK/licenses/lservrc',
                            r'/system72_mg/lost+found/.fsadm',
                            r'/var/spool/postfix/pid/unix.local',
                            r'/var/run/libvirt/network/nwfilter.leases',
                            r'/var/spool/postfix/pid/unix.cleanup',
                            r'/etc/ghostscript/',
                            r'/var/cache/litp/yum/',
                            r'/usr/share/doc/xorg-x11-xauth-1.0.2/',
                            r'/opt/SentinelRMSSDK/bin/lservrc',
                            r'last_run_report.yaml',
                            r'/var/adm/vx/reclaim_disklist',
                            r'/var/log/messages',
                            r'etc/.java/.systemPrefs',
                            r'jdk1.7.0',
                            r'/var/lib/puppet/state/state.yaml',
                            r'/var/lock/lvm/',
                            r'/tmp/service_file.lock',
                            r"/ericsson/3pp/jboss/standalone/" \
                            "deployments/README.txt",
                            r"/opt/ericsson/com.ericsson.oss." \
                            "services.nhm.kpi-calculation-flow-model/" \
                            "README.txt",
                            "/var/vx/vftrk/vcs",
                            "/var/vx/vftrk/vxfs",
                            "/var/vx/vftrk/vxvm",
                            "/var/vx/vftrk/dbed",
                            r"puppet/modules/inifile/spec/fixtures/tmp/.empty",
                            "/var/lib/pgsql/pgstartup.log",
                             postgresql_data_dir,
                            r'/var/lib/puppetdb/mq/localhost/KahaDB/lock',
                            r'/var/lib/puppetdb/mq/localhost/scheduler/lock',
                            r"/queues/XELP0FONH83JWO8D9CLW8H44/journal.jif",
                            r"/queues/EPR0PB9CI774LYHM86SEYKRLB/journal.jif",
                            r"/queues/25T2MMZ8O5OGMAFEK19H0O6WI/journal.jif",
                            r"/var/lib/puppetdb/mq/localhost/" \
                            "scheduler/db-1.log",
                            r"/var/log/puppetdb/puppetdb-daemon.log",
                            r"/usr/share/pki/ca-trust-legacy/" \
                                r"ca-bundle.legacy.disable.crt",
                            r"/usr/java/jre1.8.0_172-amd64/.java/" \
                                ".systemPrefs/.systemRootModFile",
                            r"/usr/java/jre1.8.0_172-amd64/.java/" \
                                ".systemPrefs/.system.lock",
                            r"/var/log/java_install.log",
                            r"/usr/java/jre1.8.0_172-amd64/lib/" \
                                "security/trusted.libraries",
                            r"/usr/java/jdk1.8.0_172/jre/lib/" \
                                "security/trusted.libraries"
                            ]
        # Known temporary files of size zero that will be matched
        # against a regex
        regex_ok_lists = \
        [
            r'/var/lib/puppet/client_data/catalog/.*json.',
            r'/lost\+found/\.fsadm',
            r'[/aA-zZ/]+.\.yaml[0-9]+'
        ]
        # create find command
        find_str = (r' / \( -path /proc -o -path /selinux \) ' +
                    r'-prune -o -type f ! -iname \"puppet*.lock\" ' \
                    r'-size 0 -exec ls {} \;')
        find_cmd = RHCmdUtils().get_find_cmd(find_str)
        self.setup_cmds.append(find_cmd)
        self.log('info', self.targets)
        # Do for each node in model
        for node in self.targets:
            stdout, stderr, ret_code = self.run_command(node, find_cmd,
                                                        su_root=True,
                                                        add_to_cleanup=False)
            self.assertEqual(stderr, [], "Error expected some file returned")
            self.assertEqual(stderr, [], "Error running command")
            self.assertEqual(ret_code, 0, "non zero return code")

            for item in stdout:
                suspect_list = suspect_list + [node + ' Contains -->> ' + item]
        self.log("info",
                 "\n\n\t##### List of size Zero Files "
                 "before Filtering #####\n")
        self.log("info", "'\n{0}'".format(suspect_list))

        suspect_list = self.remove_strings(rhel_files, suspect_list)
        suspect_list = self.remove_strings(list_of_ok_files, suspect_list)
        suspect_list = \
        self.chk_and_remove_regex_matches(regex_ok_lists, suspect_list)

        self.log("info", "\n\n\t##### List of size Zero Files #####\n")
        self.log("info", "\n{0}".format(suspect_list))
        self.assertEqual(suspect_list, [],
                         "Unexpected file(s) of size ZERO found")

    @attr('all', 'non-revert', 'security', 'P3', 'security_tc25')
    def test_25_test_old_password_timeout(self):
        """
        SEC_TC25_P1
        Test after password change. Change the password. Test it is
        not possible to run a command using the old password.
        (Test after 60 secs of password change.)
        Action:
            Create new user
            Set initial password & test after 60seconds
            Update password
            Test old password after 60 seconds.
            Test new password works
        Result:
            Cannot use old litp password after 60 seconds has expired
        """
        expects_cmds = list()
        password1 = "@dm1nS3rv3r"
        password2 = "p3erS3rv3r"
        newuser = "litp-st-user"
        password_timeout = 60
        unauthorized_access = "Error 401: Unauthorized access"

        print "Create new user: ", newuser
        cmd = "/usr/sbin/useradd " + newuser

        print "Set initial password to: ", password1
        _, _, ret_code = self.run_command(self.ms_node, cmd,
                                                    su_root=True)
        self.assertEqual(0, ret_code, "User not created ")
        cmd_to_run = "/usr/bin/passwd " + newuser
        expects_cmds.append(self.get_expects_dict("New password:",
                                                  password1))
        expects_cmds.append(self.get_expects_dict("Retype new password:",
                                                  password1))

        _, _, ret_code = self.run_expects_command(self.ms_node,
                                                            cmd_to_run,
                                                            expects_cmds,
                                                            su_root=True)
        self.assertEqual(0, ret_code, "Unexpected Error code on setting "
                         "initial password")

        print "Sleep for 60 seconds after initial password change"
        sleep(password_timeout)

        print "Test initial password works"
        cmd = self.cli.get_show_cmd('/')
        cmd = self.cli.add_creds_to_litp_cmd(cmd, newuser, password1)
        stdout, stderr, ret_code = self.run_command(self.ms_node, cmd,
                                                    newuser, password1)

        print "Update password to: ", password2
        expects_cmds = []
        cmd_to_run = "/usr/bin/passwd " + newuser
        expects_cmds.append(self.get_expects_dict("New password:", password2))
        expects_cmds.append(self.get_expects_dict("Retype new password:",
                                                  password2))
        _, _, ret_code = self.run_expects_command(self.ms_node,
                                                            cmd_to_run,
                                                            expects_cmds,
                                                            su_root=True)
        self.assertEqual(0, ret_code, "Unexpected Error code on updating "
                         "password for new user")

        #self.assertEqual(0, ret_code, "Unexpected error code ")
        print "Sleep for 60 seconds after second password change"
        sleep(password_timeout)

        print "Test Old password now fails"
        cmd = self.cli.get_show_cmd('/')
        cmd = self.cli.add_creds_to_litp_cmd(cmd, newuser, password1)
        stdout, stderr, ret_code = self.run_command(self.ms_node, cmd,
                                                            su_root=True)
        self.assertEqual(stdout[0], unauthorized_access,
                         "litp data shouldn't be outputted")
        self.assertEqual(stderr, [], "no expected error message")
        self.assertEqual(1, ret_code, "Unexpected Error code ")

        print "Confirm that updated password works"
        cmd = self.cli.get_show_cmd('/')
        cmd = self.cli.add_creds_to_litp_cmd(cmd, newuser, password2)
        stdout, stderr, ret_code = self.run_command(self.ms_node, cmd,
                                                            su_root=True)
        self.assertNotEqual(stdout[0], unauthorized_access,
                            "litp data should be outputted")
        self.assertEqual(stderr, [], "no expected error message")
        self.assertEqual(0, ret_code, "Unexpected error code ")
