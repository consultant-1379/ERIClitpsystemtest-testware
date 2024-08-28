#!/usr/bin/env python

'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     February 2014
@author:    Vinnie
@summary:   System Test for System integirity - search for forbidden strings
@change:    Vinnie Added test_02 & test_03
'''

from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
import test_constants


class SearchForString(GenericTest):

    """
    Description:
        This test searches system for forbidden string
    """

    # Allow nose to output longer assertion error messages
    maxDiff = None

    def setUp(self):
        """Run before every test"""
        super(SearchForString, self).setUp()
        self.new_timeout = 600
        self.rhcmd = RHCmdUtils()
        self.list_of_unsearchable_dirs = ['proc', 'sys', 'home', 'opt']
        self.list_of_unsearchable_dirs_opt = ['SentinelRMSSDK']
        self.search_items = ['ammeon']
        self.search_selinux = 'SELinux'
        self.search_invalid = 'invalid'
        self.error_grep_returnc = 2
        self.expected_find_returnc = 0
        self.ms_node = self.get_management_node_filename()
        self.targets = self.get_managed_node_filenames()
        self.targets.append(self.ms_node)
        if 'dot76' in self.targets:
            self.targets.remove('dot76')
        if 'dot74' in self.targets:
            self.targets.remove('dot74')
        if 'amosC3' in self.targets:
            self.targets.remove('amosC3')

    def tearDown(self):
        """Run after every test"""
        super(SearchForString, self).tearDown()

    def find_string(self, find_args, target):
        """
         Search on target using find command with find_args

         Args:
           find_args   (str): arguments for find command
           target      (str): target machine name

         Returns:
           return args from run_command
        """
        find_cmd = RHCmdUtils().get_find_files_in_dir_cmd(
            find_args, self.search_items, " -il"
        )

        stdout, stderr, returnc = self.run_command(
            target, find_cmd, su_root=True, su_timeout_secs=self.new_timeout)

        return stdout, stderr, returnc

    @classmethod
    def remove_items_from_list(cls, list_to_remove, list_original):
        """
        Check list_original for any items that are in the list_to_remove
        list_original is returned minus anything in list_to_remove

         Args:
           list_to_remove   (list): list of strings to remove
           list_original    (list): list of strings to check

         Returns:
           None
        """

        for item in list_to_remove:
            if item in list_original:
                list_original.remove(item)

    def remove_expected_strings(self, list_ok, list_returned):
        """
        Check list_returned for any items that are in list_ok
        If the item is in list_ok it is removed from list_returned
        Also removes hardwired list of expected strings
          from list_returned

         Args:
           list_ok   (list): list of strings to remove
           list_returned    (list): list of strings to edit

         Returns:
           list_returned is returned minus any items in list_ok
              and other expected items
        """
        self.log('info', "### List of suspect lines too be filtered ###")
        for item in list_returned:
            self.log('info', item)

        list_returned = self.remove_strings(list_ok, list_returned)
        # remove hardwired list of expected strings
        list_returned = self.remove_wont_fix_strings(list_returned)
        return list_returned

    def remove_strings(self, list_ok, list_returned):
        """
        Check list_returned for any items that are in list_ok
        If the item is in list_ok they are removed from list_returned

         Args:
           list_ok   (list): list of strings to remove
           list_returned    (list): list of strings to edit

         Returns:
           list_returned is returned minus any items in list_ok
        """
        # Filter through lists
        for item_ok in list_ok:
            for item_ret in list(list_returned):
                if item_ok in item_ret:
                    self.log('info', "Remove this item from list: {0}"
                              .format(item_ret))
                    list_returned.remove(item_ret)
        return list_returned

    def remove_wont_fix_strings(self, list_returned):
        """
        Removes hardwired list of expected strings
        This function has been introduced to resolve issues where a bug
          has been raised and closed as won't fix

         Args:
           list_returned (list): list of strings to edit

         Returns:
           list_returned is returned minus any expected items
        """
        litpcds_4537 = ["ivateKeyPassphraseHandler.options.password = secret"]
        litpcds_3303 = ["litpmcoll",
                        "marionette",
                        "litprabbitadmin",
                        "middleware_admin_password = 'secret",
                        "plugin.rabbitmq.pool.1.password = invalid"]
        litpcds_2892 = ["/etc/rabbitmq/rabbitmq.config"]

        self.log('info',
        "### LITPCDS_4537 Won't Fix lines filtered out ###")
        list_returned = self.remove_strings(litpcds_4537, list_returned)

        self.log('info', "### LITPCDS_3303 Won't Fix lines filtered out ###")
        list_returned = self.remove_strings(litpcds_3303, list_returned)

        self.log('info', "### LITPCDS_2892 Story to be completed ###")
        list_returned = self.remove_strings(litpcds_2892, list_returned)

        return list_returned

    def print_suspect_msg(self, suspect_msg):
        """
        If list suspect_msg is not empty then each
         element is printed out and the test failed

         Args:
           suspect_msg (list): list of strings to print

         Returns:
           None
        """
        # If there are unexpected items still in list, print and assert Fail
        self.log('info', "### Print list of suspect lines ###")
        for items in suspect_msg:
            self.log('info', items)

        self.assertTrue(suspect_msg == [], "Issue found")

    def search_nodes(self, password_list, dir_list, grep_arg, search_slash):
        """
        Search files for items in password_list
        Loops over all machines
        Get list of directories under /
        Find and remove any un-searchable directories from list
        loop over nodes, directories and passwords and test each separately

         Args:
           password_list (list): List of items to be checked for in grep cmd
           dir_list (list): List of dirs to search through
           grep_arg : grep arguments
           search_slash : Boolean flag - if True then / is searched

         Returns:
           List of files which contain items in password_list
        """
        suspect_str = []
        # self.targets = ['ms1']
        # Loop over all machines
        for target in self.targets:
            if dir_list == []:
                # Get list of directories under /
                dir_list = self.list_dir_contents(target, '/ -1', True)

            for directory in dir_list:
                # search_for = self.search_items
                search_str = (
                    "/" +
                    directory +
                    " -type f ! -name *.rpm ! -name *.iso ! -name *.gz "
                    " ! -name *.json ! -name *.ko")
                suspect_str = suspect_str + \
                    self.check_folders(target, search_str,
                                       password_list, grep_arg)
            # Search root directory of node
            if search_slash:
                search_str = ("/ -maxdepth 0 -type f -perm -o=r ! -name *.iso"
                              " ! -name *.gz ! -name *.json ! -name *.ko")
                suspect_str = suspect_str + \
                    self.check_folders(target, search_str,
                                       password_list, grep_arg)

        return suspect_str

    def check_folders(self, target, search_str, password_list, grep_arg):
        """
        Function runs a command to find a list of suspect files
        Each of these suspect files is checked for suspect strings
        Suspect location and strings are recorded
        Function returns suspect location and string in a list

         Args:
           target : target machine to search
           search_str : The parameters to pass to the find cmd
                (including the path)
           password_list (list): List of items to be checked for in grep cmd
           grep_arg : grep arguments

         Returns:
           List of files which contain items in password_list
        """
        find_arg = " "
        suspects_list = []
        not_searchable_list = [r'Permission denied',
                               r'Invalid argument',
                               r'Input/output error',
                               r'No such',
                               r'Connection timed out',
                               r'No such device or address']
        # Runs a command to find a list of suspect files
        if 'i' in grep_arg:
            find_arg = '-i'
        find_cmd = RHCmdUtils().get_find_files_in_dir_cmd(
            search_str, password_list, grep_arg)
        stdout, stderr, ret_code = self.run_command(target, find_cmd,
                                                    su_root=True)
        self.assertNotEqual(None, stderr)
        self.assertNotEqual(2, ret_code)
        stdout = self.remove_strings(not_searchable_list, stdout)
        # In each suspect file search for the suspect string
        for filename in stdout:
            # Create grep command to filter files
            cmd = RHCmdUtils().get_grep_file_cmd(filename, password_list,
                                                 find_arg)
            # Run grep command to filter files
            grep_std_out, std_err, ret_code = self.run_command(target, cmd,
                                                               su_root=True)
            self.assertEqual([], std_err)
            self.assertNotEqual(2, ret_code)
            # Append list of suspect files
            for item in grep_std_out:
                suspects_list.append("%s %s\t Contains -->>%s"
                                     % (target, filename, item))
        return suspects_list

    def check_file_in_list(self, expected_file, expected_number, dir_listing):
        """
        Function checks target exists expected number of times in list
        Args:
           expected_file: file name to search for
           expected_number: expected number of entries in dir_listing
           dir_listing (list): list of files

         Returns:
           Empty list if expected number of files found in list
           String containing description of issue if unexpected number found -
             either too many or too few
        """
        found_counter = 0
        issues_found = []

        for ls_entry in dir_listing:
            # Filter through lists
            if expected_file in ls_entry:
                self.log('info', "Found descriptor with name: {0}"
                  .format(expected_file))
                found_counter = found_counter + 1

        if found_counter == expected_number:
            self.log('info',
               "Found expected number of descriptors with name: {0}"
            .format(expected_file))
        elif found_counter > expected_number:
            issues_found.append("Too many descriptors with name: {0}"
            .format(expected_file))
        else:
            issues_found.append("Too few descriptors with name: {0}"
            .format(expected_file))

        return issues_found

    @attr('all', 'non-revert', 'system_integrity', 'P1',
          'system_integrity_tc01')
    def test_01_search_for_critical_files(self):

        """
        Description:
          Search for core and crash files on all machines
        Actions:
           1. Loop over machines
               2. Loop over critical file names
                   3. Search for critical file name
           4. Check no files found on any machine
         Result:
           No files with these names present on any machine
         """

        # store list of any files found
        files_found = []

        filenames_to_search_for = []
        filenames_to_search_for.append("/ -name core.*pid*")
        filenames_to_search_for.append("/ -name *crash.dump")

        # Get ALL machines
        targets = self.get_managed_node_filenames()
        targets.extend(self.get_management_node_filenames())

        # 1. Loop over all machines
        for target in targets:

            # 2. Loop over all strings
            for search_name in filenames_to_search_for:
                self.log('info', "Search for: {0}".format(search_name))

                # 3. search for string
                find_cmd = self.rhcmd.get_find_cmd(search_name)

                stdout, stderr, returnc = self.run_command(target, find_cmd,
                       su_root=True)

                # stop if there is an error
                if stderr != []:
                    self.log('info', "Stopping as find returned an error: {0}".
                    format(stderr))
                if self.expected_find_returnc != returnc:
                    self.log('info',
                    "Stopping as find returned an unexpected return code: {0}".
                    format(returnc))
                self.assertEqual(self.expected_find_returnc, returnc)
                self.assertEqual([], stderr)

                # if find result is not empty then add to files_found
                if stdout != []:
                    files_found.append(
                    "file found on machine {0}: {1}".
                    format(target, stdout))
                    self.log('info', "file found on machine {0}: {1}".
                    format(target, stdout))

                    # show details of files found
                    for crit_file_name in stdout:
                        self.log('info', "list filename: {0}".
                          format(crit_file_name))
                        list_cmd = "ls -l {0}".format(crit_file_name)
                        self.run_command(target, list_cmd, su_root=True,
                              default_asserts=True)

                        # if file is a rabbitmq file then cat its contents
                        if "rabbitmq" in crit_file_name:
                            self.log('info', "cat filename: {0}".
                              format(crit_file_name))
                            cat_cmd = self.rhcmd.get_cat_cmd(crit_file_name)
                            self.run_command(target, cat_cmd, su_root=True,
                                  default_asserts=True)

        # 4. Check no files found on any machine
        self.assertEqual([], files_found, "critical files found ")

    @attr('all', 'non-revert', 'system_integrity', 'P1',
          'system_integrity_tc02')
    def test_02_search_logs_for_critical_strings(self):

        """
        Description:
          Search for critical strings in /var/log/messages on all nodes
        Actions:
           1. Loop over all targets
               2. Loop over all critical strings
                   3. Search for string in messages file
           4. Check no hits on any machine
         Result:
           No critical strings in message files
         """

        # store list of any files found
        files_found = []

        # define strings
        strings_to_search_for = []
        strings_to_search_for.append("segfault")
        strings_to_search_for.append("execution expired")
        strings_to_search_for.append("error occurred while trying to spawn")
        strings_to_search_for.append("Cannot allocate memory")
        strings_to_search_for.append("Out of memory: Kill process")
        strings_to_search_for.append("invoked oom-killer")
        strings_to_search_for.append("running e2fsck is recommended")
        strings_to_search_for.append("syntax error")

        # Get ALL machines
        targets = self.get_managed_node_filenames()
        targets.extend(self.get_management_node_filenames())

        # 1. Loop over all machines
        for target in self.targets:

            # 2. Loop over all strings
            for search_string in strings_to_search_for:
                self.log('info', "Search for: {0}".format(search_string))

                # 3. search for string
                grep_cmd = self.rhcmd.get_grep_file_cmd(
                  test_constants.GEN_SYSTEM_LOG_PATH, search_string)

                stdout, stderr, returnc = self.run_command(target, grep_cmd)

                # stop if there is an error
                if stderr != []:
                    self.log('info', "Stopping as grep returned an error: {0}".
                    format(stderr))
                if self.error_grep_returnc == returnc:
                    self.log('info',
                    "Stopping as grep returned return code: {0}".
                    format(returnc))
                self.assertNotEqual(self.error_grep_returnc, returnc)
                self.assertEqual([], stderr)

                # if find result is not empty then add to files_found
                if stdout != []:
                    files_found.append(
                     "{0} found on machine {1}: {2}".
                     format(search_string, target, stdout))
                    self.log('info', "{0} found on machine {1}: {2}".
                     format(search_string, target, stdout))

        # 4. Check no suspect strings found on any machines
        self.assertEqual([], files_found, "critical strings found ")

    @attr('all', 'non-revert', 'system_integrity', 'P1',
          'system_integrity_tc03')
    def test_03_search_logs_for_selinux_invalid(self):

        """
        Description:
          Search for string "SELinux" and "invalid" in /var/log/messages
          on all nodes
        Actions:
           1. Get all nodes
           2. Loop over all targets
               3. Search for "SELinux" and "invalid" in messages files
           4. Check no hits on any machine
         Result:
           No "SElinux" "invalid" in message files
         """

        # store list of any files found
        files_found = []

        # 1. Get all nodes
        targets = self.get_managed_node_filenames()
        targets.extend(self.get_management_node_filenames())

        # 2. Loop over all machines
        for target in self.targets:

            # 3. search for string
            grep_cmd = self.rhcmd.get_grep_file_cmd(
                test_constants.GEN_SYSTEM_LOG_PATH, \
                [self.search_selinux])
            grep_cmd = grep_cmd + "| /bin/grep {0}".format('invalid')

            stdout, stderr, returnc = self.run_command(target, grep_cmd)

            # stop if there is an error
            self.assertNotEqual(self.error_grep_returnc, returnc)
            self.assertEqual([], stderr)

            # if find result is not empty then add to files_found
            if stdout != []:
                files_found.append(
                  "SELinux invalid found on machine {0}: {1}".
                   format(target, stdout))

        # 4. Check no SELinux invalid messages on any machines
        self.assertEqual([], files_found)

    @attr('all', 'non-revert', 'system_integrity', 'P3',
          'system_integrity_tc04')
    def test_04_system_intergity_search_for_ms1(self):
        """
        Description:
            Tests for any occurrence of "ms1" strings on all node.
        Actions:
            1.Group locations to be searched .
            2.Search node for system passwords.
            3.Remove any expected strings from list
        Result:
            No occurrences of "ms1" strings should remain on nodes.

        """
        suspect_str = []
        know_3pp_passwords = ['ms1']
        dir_list = ['opt']
        grep_arg = " -il"
        list_of_ok_phrases = ['Binary file (standard input)',
                              'No such file or directory',
                              '.bash_history',
                              'tmosms1',
                              'items1',
                              'bolums1',
                              'oms1',
                              'drms1',
                              'Gems1',
                              'engel@nms1',
                              'ca-bundle',
                              'ms1361',
                              'AUTHORS',
                              'Kxrmimms1',
                              'searchindex.js',
                              'isc-logo.eps',
                              'Streams1',
                              'liveHelp',
                              r'vg_ms1-lv_swap',
                              r'"sender":"ms1"',
                              r'permanentrepos.pp',
                              r'kickstart.pp',
                              r'&lt;hostname&gt',
                              r'network_plugin_plugin/index.txt',
                              r'network_plugin/network_plugin.py',
                              r'class litp::passenger($ms_hostname=',
                              r'dev_troubleshooting',
                              r'ssh-rsa',
                              r'nms/litp/share/docs/_sources'
                              '/item_types/ms.txt',
                              r'nms/litp/share/docs/item_types/ms.html',
                              r' /opt/ericsson/nms/litp'
                              '/etc/ssl/litp_server.cert',
                              r"if file_name.endswith('ms1.pp')",
                              r"replacing ms1.pp with the ms host name",
                              r"/litp/etc/ssl/litp_server.key",
                              r".pem",
                              r"/puppet/provider/ini_subsetting/ruby_spec.rb",
                              r'/mssql/pyodbc.py',
                              r'/mssql/base.py'
                              ]

        # Search node for system passwords
        suspect_str = suspect_str + self.search_nodes(know_3pp_passwords,
                                                      dir_list, grep_arg, True)
        # Find and remove any expected strings from list
        self.remove_expected_strings(list_of_ok_phrases, suspect_str)
        # Print result and assert Pass Fail
        self.print_suspect_msg(suspect_str)

    @attr('all', 'non-revert', 'system_integrity', 'P1',
          'system_integrity_tc05')
    def test_05_system_intergity_search_for_deprecat_n_msg(self):
        """
        Description:
            Tests for any occurrence of the strings
            deprecat in /var/log/messages
        Actions:
            1. grep locations for suspect strings
            2. check suspect strings against list of ok list_of_ok_phrases
        Results: No strings deprecat should exist in var/log/messages
        """
        list_of_ok_phrases = [r'net.ipv6.neigh.default.retrans_time',
                              r'vcs-trigger',
                              r'lsb-runtime',
                              'Property \'critical_service\'',
                              'Property \'repository\'',
                              'grep\' is using deprecated sysctl',
 r'is deprecated and will be ignored. This dependency was created in:']
        suspect_str = []
        grep_arg = " -il"
        dir_list = ['var/log/messages']
        search_for = ['deprecat']

        # Search node for system passwords
        suspect_str = suspect_str + self.search_nodes(search_for, dir_list,
                                                      grep_arg, False)

        # Find and remove any expected strings from list
        stdout = self.remove_expected_strings(
            list_of_ok_phrases, suspect_str)

        # If there are unexpected items still in list, print and assert Fail
        self.print_suspect_msg(stdout)

    @attr('all', 'non-revert', 'system_integrity', 'P3',
          'system_integrity_tc06')
    def test_06_check_litpd_service_file_descriptors(self):
        """
        Description:
            Checks the expected file descriptors are present
              in the list of litpd service file descriptors
            And that no unexpected descriptors are present
        Actions:
            1.Get pid of litpd service
            2.Get list of litpd service file descriptors
            3.Loop over names of expected files
               and check actual number of descriptors for that file
               matches expected number
            4.Check no unexpected descriptors are present
        Result:
            Expected file descriptors are present
        """

        # List of all expected descriptors
        all_expected_files = ["/var/log/litp/metrics.log",
                              "/var/log/litp/litpd_error.log",
                              "/var/log/litp/litpd_access.log",
                              "/dev/null",
                              "socket",
                              "/dev/urandom"]

        # Array of expected files and how many descriptors
        #      expected for that file
        # Only includes files we are certain will appear in the list
        #      a predictable number of times
        expected_files = [["/var/log/litp/metrics.log", 1],
               ["/var/log/litp/litpd_error.log", 1],
               ["/var/log/litp/litpd_access.log", 1],
               ["/dev/null", 3]]

        issues_found = []

        # 1. Get pid of litpd service
        stdout, _, _ =  \
               self.get_service_status_cmd(self.ms_node, "litpd")
        self.assertTrue(self.is_text_in_list('pid', stdout),
                            "Service status does not contain PID")
        pid_num = \
                self.get_service_pid_from_stdout(stdout, "litpd")

        # Get name of fd directory
        directory_name = "/proc/" + str(pid_num) + "/fd"
        self.log('info',
                "file descriptor directory: {0}".format(directory_name))

        # 2. List files
        list_cmd = "ls -ls " + directory_name
        dir_listing, _, _ = self.run_command(
            self.ms_node, list_cmd, su_root=True, default_asserts=True)

        self.log('info', "List of files: {0}".format(dir_listing))

        # 3. Loop over expected files
        #   and check there is the correct number of descriptors
        for i in range(len(expected_files)):
            issues = self.check_file_in_list(expected_files[i][0],
                                    expected_files[i][1],
                                    dir_listing)
            if issues != []:
                issues_found.append(issues)

        # Test no issues found
        self.assertEqual([], issues_found,
           "Incorrect number of file descriptors. {0}"
           .format(issues_found))

        self.log('info', "No unexpected File Descriptors have been found")

        # 4. Remove all expected files from list
        list_returned = self.remove_strings(all_expected_files, dir_listing)

        # Test for unexpected files
        # The only entry left should be total size
        self.assertEqual(['total 0'], list_returned,
           "Unexpected file descriptors found: {0}"
           .format(list_returned))

    @attr('all', 'non-revert', 'system_integrity', 'P3',
          'system_integrity_tc07')
    def test_07_check_litpd_number_threads(self):
        """
        Description:
            Checks the number of threads in 3 different ways -
             checks they are consistent
        Actions:
            1.Get pid of litpd service
            2.Check number of directories under /proc/<pid>/task
            3.Check number of threads listed in /proc/<pid>/status
            4.Check number of threads returned by ps
            5.Compare number of threads from different sources
        Result:
            Number of threads in different sources is consistent
        """

        # 1. Get pid of litpd service
        stdout, _, _ =  \
               self.get_service_status_cmd(self.ms_node, "litpd")
        self.assertTrue(self.is_text_in_list('pid', stdout),
                            "Service status does not contain PID")
        pid_num = \
                self.get_service_pid_from_stdout(stdout, "litpd")

        # Get name of task dir
        directory_name = "/proc/" + str(pid_num) + "/task"
        self.log('info',
                "task directory: {0}".format(directory_name))

        # 2. Get number of threads from number of directories
        #   under /proc/<pid>/task
        list_cmd = "ls " + directory_name + " | wc -l"
        stdout, _, _ = self.run_command(
            self.ms_node, list_cmd, su_root=True, default_asserts=True)

        num_threads_task = int(stdout[0])
        self.log('info', "Number of threads from task dir: {0}"
          .format(num_threads_task))

        # 3. Get number of threads from file /proc/<pid>/status
        status_cmd = "cat /proc/" + str(pid_num) + \
          "/status | grep Threads | cut -f 2 -d ':'"
        stdout, _, _ = self.run_command(
            self.ms_node, status_cmd, su_root=True, default_asserts=True)

        num_threads_status = int(stdout[0])
        self.log('info', "Number of threads from status file: {0}"
           .format(num_threads_status))

        # 4. Get number of threads from ps
        ps_cmd = "ps -T -p " + str(pid_num) + " | wc -l"
        stdout, _, _ = self.run_command(
            self.ms_node, ps_cmd, su_root=True, default_asserts=True)

        num_threads_ps = int(stdout[0]) - 1
        self.log('info',
           "Number of threads from ps: {0}".format(num_threads_ps))

        # 5. Compare values
        self.assertEqual(num_threads_task, num_threads_status,
          "Number of threads from different sources is different." \
          + "threads from task dir: {0}. threads from status file: {1}"
          .format(num_threads_task, num_threads_status))
        self.assertEqual(num_threads_task, num_threads_ps,
          "Number of threads from different sources is different." \
          + "threads from task dir: {0}. threads from ps: {1}"
          .format(num_threads_task, num_threads_ps))
