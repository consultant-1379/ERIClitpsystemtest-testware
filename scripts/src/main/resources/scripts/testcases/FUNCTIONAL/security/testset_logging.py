'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     February 2014
@author:    Vinnie McGuinness
@summary:   System test to check
            Check system that log files are been stored in correct locations
'''

from litp_generic_test import GenericTest, attr
from litp_cli_utils import CLIUtils
from redhat_cmd_utils import RHCmdUtils


class LoggingChecks(GenericTest):
    """
        ST tests to search any files in invalid locations
    """
    def setUp(self):
        """Run before every test"""
        super(LoggingChecks, self).setUp()
        self.cli = CLIUtils()
        self.ms_node = self.get_management_node_filename()
        self.targets = self.get_managed_node_filenames()
        self.targets.append(self.ms_node)
        if 'dot74' in self.targets:
            self.targets.remove('dot74')
        if 'dot76' in self.targets:
            self.targets.remove('dot76')
        if 'amosC3' in self.targets:
            self.targets.remove('amosC3')

    def tearDown(self):
        """run after each test"""
        super(LoggingChecks, self).tearDown()

    def check_filename_in_folder(self, filepath, string, node):
        """
        Check for filenames in filepath containing
        Returns list of files
        """
        suspect_list = []
        if filepath == "/":
            cmd = RHCmdUtils().get_grep_file_cmd(filepath, string, '-i',
                           'ls -A --ignore=passenger* --ignore=.AutoInstall* '
                           '--ignore=.STCDB_autoinstall*')
        else:
            cmd = RHCmdUtils().get_grep_file_cmd(filepath, string, '-i',
                           'ls -AR --ignore=passenger* --ignore=.AutoInstall* '
                           '--ignore=.STCDB_autoinstall*')
        stdout, stderr, stdrc = self.run_command(node, cmd, su_root=True)
        for item in stdout:
            suspect_list.append("File found on %s in %s -->> %s"
                                        % (node, filepath, item))

        self.assertEqual(stderr, [], "stderr is not empty: {0}".format(stderr))
        self.assertNotEqual(stdrc, 2, "Error return code given")

        return suspect_list

    def remove_expected_strings(self, list_ok, list_returned):
        """
        Check list_returned for any items that are in the list_ok
        If the item is ok they are removed from the list_returned
        The list_returned is returned minus any OK items
        """
        #self.log('info', list_ok)
        #self.log('info', list_returned)
        for item_ok in list_ok:
            for item_ret in list(list_returned):
                if item_ok in item_ret:
                    self.log('info', item_ret)
                    list_returned.remove(item_ret)
        return list_returned

    def remove_wont_fix_strings(self, list_returned):
        """
        This function has been introduced to issues where a bug has been
        raised and closed as won't fix
        """
        # Filtering out both wont fix strings and
        # expected Red Hat files from install
        litpcds_9708 = ["vxconfigbackup.cmd.failog",
                        # Start of RedHat Files
                        'anaconda-ks.cfg',
                        'install.log',
                        'install.log.syslog',
                        'postinstall.rhel_copy.log',
                        'postinstall.security.log',
                        '.bash_logout',
                        'ks-post.log',
                        'ks-pre.log'
                        # End of Redhat files
                        ]

        print"\n\t\t### Filtered out due to bug LITPCDS_9708 ###"
        list_returned = self.remove_expected_strings(litpcds_9708,
                                                     list_returned)

        return list_returned

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc03')
    def test_03_ensure_no_litp_logs_in_root_and_tmp_dirs(self):
        """
        Description:
            Test /var/tmp', '/tmp', '/' and /root for *.log files
        Actions:
            Assert error if any unexpected .log files found
        Results:
            no unexpected .logs files found
        """
        # list of locations to check
        list_locations = ['/', '/tmp', '/var/tmp', '/root']
        self.log(
            "info",
            "checking for litp log files"
            " in {0}, {1}, {2} and {3}".format(
                list_locations[0],
                list_locations[1],
                list_locations[2],
                list_locations[3]))
        # list of files that can be in these locations
        list_of_ok_files = ['yum.log',
                            'run.log',
                            '.slmlog',
                            'diff_service.log',
                            'a_testset_logging',
                            'b_testset_logging'
                            ]
        suspect_list = []

        file_name_str = 'log'
        for node in self.targets:
            for item in list_locations:
                # Get list of files in a folder containing file_name_str
                suspect_list = suspect_list + self.check_filename_in_folder(
                    item, file_name_str, node)
                # self.log('info', suspect_list)
        #Find and remove any expected strings from list
        # self.log('info', suspect_list)
        suspect_list = self.remove_wont_fix_strings(suspect_list)
        print "\n\t\t#### Filtered out expected files ####"
        stdout = self.remove_expected_strings(list_of_ok_files, suspect_list)
        #Find and remove any expected strings from list
        self.log("info",
                 "#### Filtered out expected files #####")

        if stdout != []:
            print "\n\t\t#### Unexpected File(s) found ####"
            for filename in stdout:
                self.log('info', filename)
        else:
            print "\n\t\t#### No Suspect files found ####"
        # If list not empty test fails a log file has been found
        self.assertEqual([], stdout, ("Log file(s) -->>", stdout,
                                      " Unexpectedly found -->>",
                                      list_locations))

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc04')
    def test_04_no_system_critical_files_in_root_and_tmp_dirs(self):
        """
        Description:
            Checks / , /tmp , /var/tmp and /root for any system critical files
            remaining after an install
        Action:
            search / , /tmp , /var/tmp and /root for system critical files
            Filter out expected files
            Assert if any unexpected files found
        Results:
            no system critical files found in searched directories
        """
        file_list = []
        # list of locations to check
        list_locations = ['/', '/tmp', '/var/tmp', '/root']
        self.log(
            "info",
            "Directories to be checked for system critical files"
            "  {0}, {1}, {2} and {3}".format(
                list_locations[0],
                list_locations[1],
                list_locations[2],
                list_locations[3]))
        # list of files that can be in these locations
        list_of_ok_files = ['software',
                            'ks-script-',
                            'yum.log',
                            '.erlang.cookie',
                            '.ICE-unix',
                            'passenger',
                            'generation',
                            'puppet201',
                            'opt',
                            '.osuuid',
                            '.bashrc',
                            'proc',
                            'selinux',
                            'srv',
                            'storobs',
                            'usr',
                            'var',
                            '.autofsck',
                            'bin',
                            'boot',
                            'cgroup',
                            'cloaders',
                            'dev',
                            'etc',
                            'home',
                            'lib',
                            'lib64',
                            'lost+found',
                            'media',
                            'mnt',
                            'sys',
                            'cluster',
                            '/tmp:',
                            '/root:',
                            'rabbitmq_checker',
                            'vxvm_vol',
                            'gnomebluetooth.rpm',
                            'ms_share_',
                            '72_mg',
                            'test_service',
                            'vx.',
                            'vxvm.sh',
                            'add_VM_',
                            'lsb_pkg',
                            'helloapps',
                            'EXTR-lsbwrapper',
                            'test-lsb-',
                            'jump',
                            'SG_STvm1',
                            'expand_PL_SG.xml',
                            'vm10_update_mounts.xml',
                            '.slmlog',
                            '-hello-',
                            'lservsta',
                            'CDB_',
                            'mcollective_',
                            'enm_package_2.xml',
                            'ERICenm_CXP9027091',
                            'import_iso.sh',
                            'root_import_iso.exp',
                             '.bash_',
                            'anaconda-ks.cfg',
                            'ks-post.log',
                            'ks-pre.log',
                            '.tcshrc',
                            '.cshrc',
                            'install.log',
                            'postinstall.rhel_copy.log',
                            'postinstall.security.log',
                            '.ssh',
                            'cobbler.ks',
                            '.litprc',
                            '.viminfo',
                            '.rnd',
                            'known_hosts',
                            'diff_service.log',
                            'service_file.lock',
                            'ericsson',
                            '.pki',
                            'nssdb',
                            '.s.PGSQL.5432',
                            '.s.PGSQL.5432.lock',
                            'a_testset_',
                            'b_testset_'
                            ]
        for node in self.targets:
            for item in list_locations:
                # Print out which directory is currently being searched
                # for system critical files.
                self.log("info",
                         "checking for system critical "
                         "files in {0}".format(item))
                # Get list of files in a folder containing file_name_str
                if item == "/":
                    cmd = ('ls -A1 --ignore=passenger*--ignore=.AutoInstall* '
                           '--ignore=.STCDB_autoinstall --ignore=puppet201* '
                           ' --ignore=hsperfdata* --ignore=tmp --ignore=root '
                           + item)
                else:
                    cmd = ('ls -AR1 --ignore=passenger* --ignore=.AutoInstall*'
                           ' --ignore=.STCDB_autoinstall* --ignore=puppet201* '
                           '--ignore=hsperfdata* ' + item)
                stdout, stderr, stdrc = self.run_command(node,
                                                         cmd,
                                                         su_root=True)
                self.assertEqual(stderr, [],
                                 "stderr is not empty: {0}".format(stderr))
                self.assertNotEqual(stdrc, 1, "Error return code given")
                for files in stdout:
                    file_list.append("Unexpected file found on %s n %s -->> %s"
                                        % (node, item, files))

        #Find and remove any expected strings from list
        print "\n\t\t#### Filtered out expected files ####"
        stdout = self.remove_expected_strings(list_of_ok_files, file_list)

        if file_list != []:
            print "\n\t\t#### Unexpected File(s) found ####"
            for item in file_list:
                print item
        else:
            print "\n\t\t#### No Suspect files found ####"
        # If list not empty test fails a log file has been found

        self.assertEqual([], file_list, ("Log file(s) -->>", file_list,
                                      " Unexpectedly found in -->> ",
                                      list_locations))
