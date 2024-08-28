#!/usr/bin/env python

'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     February 2014
@author:    Ruth
@summary:   System Test for Security - search for forbidden strings
@change:    Vinnie Added test_02 & test_03
'''

from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
from datetime import datetime


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
        self.connection_timeout_secs = 1200
        self.su_timeout_secs = 1200
        self.search_items = ['ammeon']
        # define the nodes which will be checked
        self.ms_node = self.get_management_node_filename()
        self.targets = self.get_managed_node_filenames()
        self.targets.append(self.ms_node)
        if 'dot76' in self.targets:
            self.targets.remove('dot76')
        if 'dot74' in self.targets:
            self.targets.remove('dot74')
        if 'amosC3' in self.targets:
            self.targets.remove('amosC3')
        if 'dot66-node1' in self.targets:
            self.targets.remove('dot66-node1')

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
        find_cmd = RHCmdUtils().get_find_files_in_dir_cmd(find_args,
                                                          self.search_items,
                                                          " -il")

        stdout, stderr, rc = self.run_command(target, find_cmd,
                 su_root=True,
                 su_timeout_secs=self.su_timeout_secs,
                 connection_timeout_secs=self.connection_timeout_secs)

        return stdout, stderr, rc

    def remove_items_from_list(self, list_to_remove, list_original):
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
                self.log('info', "Exclude this item from results:" + item)
                list_original.remove(item)

    def remove_expected_strings(self, list_ok, list_returned):
        """
        Check list_returned for any items that are in the list_ok
        If the item in list_ok they are removed from the list_returned
        The list_returned is returned minus any OK items
        """
        print"\n\t\t### List of suspect lines too be filtered ###"
        for item in list_returned:
            self.log('info', item)

        list_returned = self.remove_strings(list_ok, list_returned)
        list_returned = self.remove_wont_fix_strings(list_returned)
        return list_returned

    def remove_strings(self, list_ok, list_returned):
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
                    self.log('info', item_ret)
                    list_returned.remove(item_ret)
        return list_returned

    def remove_wont_fix_strings(self, list_returned):
        """
        This function has been introduced to issues where a bug has been
        raised and closed as won't fix
        """
        litpcds_4537 = ["ivateKeyPassphraseHandler.options.password = secret"]
        litpcds_3303 = ["litpmcoll",
                        "marionette",
                        "litprabbitadmin",
                        "middleware_admin_password = 'secret",
                        "plugin.rabbitmq.pool.1.password = invalid"]
        litpcds_2892 = ["/etc/rabbitmq/rabbitmq.config"]

        print"\n\t\t### LITPCDS_4537 Won't Fix lines filtered out ###"
        list_returned = self.remove_strings(litpcds_4537, list_returned)

        print"\n\t\t### LITPCDS_3303 Won't Fix lines filtered out ###"
        list_returned = self.remove_strings(litpcds_3303, list_returned)

        print"\n\t\t### LITPCDS_2892 Story to be completed ###"
        list_returned = self.remove_strings(litpcds_2892, list_returned)

        return list_returned

    def print_suspect_msg(self, suspect_msg):
        """
        Function receives a list of suspect messages
        Prints any suspect messages
        """
        # If there are unexpected items still in list, print and assert Fail
        print"\n\n\t\t### Print list of suspect lines ###"
        for items in suspect_msg:
            self.log('info', items)

        self.assertTrue(suspect_msg == [], "Issue found")

    def search_nodes(self, password_list, dir_list, grep_arg, search_slash):
        """
        Loops over all machines
        Get list of directories under /
        Find and remove any un-searchable directories from list
        loop over nodes, directories and passwords and test each seperatly
        """
        suspect_str = []
        # self.targets = ['ms1']
        # Loop over all machines
        for target in self.targets:
            if dir_list == []:
                # Get list of directories under /
                dir_list = self.list_dir_contents(target, '/ -1', True)

            for directory in dir_list:
                #search_for = self.search_items
                search_str = ("/" + directory +
                              " -type f ! -name *.rpm ! -name *.iso ! "
                              "-name *.gz ! -name *.json ! -name *.ko")
                suspect_str = suspect_str + self.check_folders(target,
                                                               search_str,
                                                               password_list,
                                                               grep_arg)
            # Search root directory of node
            if search_slash is True:
                search_str = ("/ -maxdepth 0 -type f -perm -o=r ! -name *.iso"
                              " ! -name *.gz ! -name *.json ! -name *.ko")
                suspect_str = suspect_str + self.check_folders(target,
                                                               search_str,
                                                               password_list,
                                                               grep_arg)

        return suspect_str

    def check_folders(self, target, search_str, password_list, grep_arg):
        """
        Function runs a command to find a list of suspect files
        Each of these suspect files is checked for suspect strings
        Suspect location and strings are recorded
        Function returns suspect location and string in a list
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
        find_cmd = RHCmdUtils().get_find_files_in_dir_cmd(search_str,
                                                          password_list,
                                                          grep_arg)
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

    def list_dirs(self, target, top_level_dir):
        """
        Returns list of directories under top_level_dir
        """
        success = True
        ls_command = 'ls -p ' + top_level_dir + ' | grep "/"'
        stdout, stderr, returnc = self.run_command(target,
                                                   ls_command,
                                                   su_root=True)

        if stderr != [] and returnc != 0:
            success = False

        self.assertTrue(success, "Error reported running command: {0}"
                        .format(stderr))

        return stdout

    def remove_files_with_ignore_string(self,
                                        file_list,
                                        target):
        """
        Use sed to replace the string to ignore
        and then re-search for the original string
        The file_list is returned without files which
        only contain the string that can be ignored
        """
        success = True
        # Loop through file names in list
        for test_file in list(file_list):

            # construct sed command
            sed_command = ("cat " + test_file +
                           " | /bin/sed 's/ammeonvpn/allowed/g' | "
                           "/bin/sed 's/Ammeon-LITP/allowed/g' | "
                           "/bin/sed 's/VIP.ammeon/allowed/g' | "
                           "/bin/sed 's/helios.ammeon.com/allowed/g' | "
                           "/bin/grep  -i ammeon")

            # run command
            stdout, err, ret_code = self.run_command(target, sed_command,
                                              su_root=True)

            # if grep result is empty then remove from list
            if stdout == []:
                self.log('info',
                         "Exclude this item from results:" + test_file)
                file_list.remove(test_file)

            if err != [] and ret_code != 0:
                success = False

            self.assertTrue(success, "Error reported running command: {0}"
                            .format(err))

        return file_list

    @staticmethod
    def is_find_error_in_stdout(stdout):
        """
        Description:
            Checks stdout for existance of an error caused by find accessing
            temporary files which no longer exist
        """
        find_error_output = ": No such file or directory"
        for line in stdout:
            if find_error_output in line:
                return True

        # Return false if not found
        return False

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc13')
    def test_13_search_system_passwords(self):
        """
        Description:
            Tests for any occurrence of the system_passwords strings
            on all node under /.
        Actions:
            system_passwords = ['@dm1nS3rv3r',
                                'litpc0b6lEr',
                                'litp_admin',
                                'p3erS3rv3r',
                                'Aut01nstall',
                                'shroot12',
                                'mm30n',]
        Result:
            No files with system_passwords can be found on any machine
        """
        grep_arg = " -l"
        suspect_str = []
        dir_list = []
        system_passwords = ['@dm1nS3rv3r',
                            'litpc0b6lEr',
                            'litp_admin',
                            'p3erS3rv3r',
                            'Aut01nstall',
                            'shroot12',
                            'mm30n',
                            #'master',
                            #'support'
                            ]

        list_of_ok_phrases = [r'default_node_litp_admin_pass --iscrypted',
                              r'default_node_litp_admin_pass: \"$1$',
                              r'default_node_litp_admin_pass: "$1$',
                              r'/root/.litprc',
                              r'/bin/grep',
                              r'/usr/bin/xargs /bin/grep  -l',
                              r'/home/litp-admin/.litprc',
                              r'Binary file (standard input)',
                              r'Invalid argument',
                              r'.AutoInstall_2.1',
                              r'autoinstall',
                              r'/opt/ericsson/nms/litp/lib/sanapi/test/',
                              r'No such file or directory']

        # Search node for system passwords
        suspect_str = suspect_str + self.search_nodes(system_passwords,
                                                      dir_list, grep_arg, True)
        # Find and remove any expected strings from list
        self.remove_expected_strings(list_of_ok_phrases, suspect_str)
        # Print result and assert Pass Fail
        self.print_suspect_msg(suspect_str)

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc14')
    def test_14_search_3pp_passwords(self):
        """
        Description:
            Test for any occurrence of 3pp passwords strings
            on all nodes under /.
        Actions:
            3pp_passwords = ['litpmcoll',
                              'marionette',
                              'litprabbitadmin']
        Result:
            No files with 3pp_passwords can be found on any machine
        """
        suspect_str = []
        grep_arg = " -l"
        know_3pp_passwords = ['litpmcoll',
                              'marionette',
                              'litprabbitadmin']
        dir_list = []
        list_of_ok_phrases = [r'default_node_litp_admin_pass',
                              r'/root/.litprc',
                              r'/bin/grep',
                              r'/usr/bin/xargs /bin/grep  -l',
                              r'/home/litp-admin/.litprc',
                              r'Binary file (standard input)',
                              r'Invalid argument',
                              r'marionette-collective.org',
                              r'Marionette',
                              r'mcollective_spec.rb',
                              r'>>marionette</p>',
                              r'litpmcollective',
                              r'No such file or directory']

        # Search node for system passwords
        suspect_str = suspect_str + self.search_nodes(know_3pp_passwords,
                                                      dir_list, grep_arg, True)
        # Find and remove any expected strings from list
        self.remove_expected_strings(list_of_ok_phrases, suspect_str)
        # Print result and assert Pass Fail
        self.print_suspect_msg(suspect_str)

    @attr('all', 'non-revert', 'security', 'P2', 'security_tc15')
    def test_15_search_additional_3PP_passwords_on_etc_home_root(self):
        """
        Description:
            Tests for any occurrence of 3PP passwords
            in '/etc','/home','/root' on all nodes
        Actions:
            Searches for these passwords:
                    passwords = ['support',
                                'master',
                                'secret',
                                'puppet',
                                'cobbler']
        Result:
            No files with 3PP passwords can be found on any machine
            in listed dirs
        """
        suspect_str = []
        dir_list = ['etc', 'home', 'root']
        grep_arg = " -l"
        know_3pp_passwords = ['support',
                              'master',
                              'secret',
                              'puppet',
                              'cobbler']

        list_of_ok_phrases = [r'master=bond0',
                              r'path    =',
                              r'>puppet:!!',
                              r'-->># ',  # Removes all comments
                              r'default_node_litp_admin_pass',
                              r'/root/.litprc',
                              r'/bin/grep',
                              r'/usr/bin/xargs /bin/grep  -l',
                              r'/home/litp-admin/.litprc',
                              r'Binary file (standard input)',
                              r'Invalid argument',
                              r'marionette-collective.org',
                              r'Marionette Collective',
                              r'mcollective_spec.rb',
                              r'>>marionette</p>',
                              'supported',
                              'supports',
                              'not support',
                              'that support',
                              'sound support',
                              'later  support',
                              'udev support',
                              'cobbler managed',
                              'cobbler registration',
                              'puppet registration',
                              'conf.cobbler',
                              'support everything',
                              'mastered',
                              'puppetmaster',
                              'supporting',
                              '_secrets',
                              '_master',
                              'masters',
                              'master device',
                              'VCSmaster',
                              '_listsupport',
                              'listsupport',
                              'Secret',
                              'Master',
                              'Secret',
                              'webmaster:',
                              'ostmaster',
                              'emaster',
                              'master-',
                              'tmaster',
                              'master.',
                              'master files',
                              r'system_u:object_',
                              r'$puppetd',
                              r'puppet agent',
                              r'through puppet',
                              r'/udp',
                              r'/tcp',
                              r"doesn't support",
                              r'support not',
                              r'support availa',
                              r'support every',
                              r'support IP',
                              r'support necessary',
                              r'support:  ',
                              r'support this',
                              r'support by',
                              r'not support ',
                              r'colour support ',
                              r'enable support',
                              r'support to',
                              r'# support ',
                              r'protocol support',
                              r'support on',
                              r'that support',
                              r"doesn't support",
                              r'support.',
                              r'puppet service',
                              r'puppet on',
                              r'puppetd',
                              r'puppetlabs ',
                              r'993 puppet ',
                              r'by puppet ',
                              r'puppet client',
                              r'puppet agent',
                              r': name=puppet',
                              r'_qmaster',
                              r'Qmaster',
                              r'master file',
                              r'master certificate',
                              r'VCSmaster',
                              r'webmaster',
                              r'puppet master',
                              r"master's",
                              r'the master',
                              r'ismaster',
                              r'master device',
                              r'master process',
                              r'to master',
                              r'text-master',
                              r'master>bond',
                              r'type master',
                              r'master server',
                              r'-secret-$DEVICE',
                              r'gpg_secret',
                              r'BINDPW',
                              r'bindpw',
                              r'secret with',
                              r'puppet-agent',
                              r'EXTRlitppuppet',
                              r'redhat-support',
                              r'http://',
                              r'PUPPET_SERVER',
                              r'>> /etc/hosts',
                              r'dmp_native_support',
                              r'COBBLER',
                              r'rm -r /etc/sysconfig/network-scripts/cobble',
                              r'mv /etc/sysconfig/network-scripts/cobbler/*',
                              r'>> /etc/sysconfig/network-scripts/cobbler/i',
                              r'>mv ',
                              r'>>+ mv ',
                              r'>>cp ',
                              r'>>mkdir ',
                              r'>>echo ',
                              r'/bin/echo ',
                              r'>>chmod ',
                              r'>>touch ',
                              r'rundir /',
                              r'logdir = /',
                              r'rm -f /etc/puppet/puppet.conf',
                              r'/root/anaconda-ks.cfg     Contains -->>pupp',
                              r'mcollective-puppet',
                              r'status -p $pidfile',
                              r'lockfile=',
                              r'logging support',
                              r'system log',
                              r'secrets.tdb',
                              r'dirs    /var/puppet',
                              r'puppet:x:52',
                              r'AutoInstall_2.1',
                              r'cobblerudp',
                              r'993 puppet',
                              r'PUPPET_LOG',
                              r'gcj_support',
                              r'puppet_pol',
                              r'check puppet',
                              r'puppet_phase',
                              r'puppet phase ',
                              r'mco puppet',
                              r'puppet_not',
                              r'puppet:!::',
                              r'service puppet',
                              r'puppet.service',
                              r'Directory',
                              r'AliasMatch',
                              r'Alias /cobbler',
                              r'log {',
                              r'cobblerd',
                              r'cobbler_web',
                              r'cobbler-completion',
                              r'cobbler_server',
                              r'cobbler import',
                              r'cobbler()',
                              r'from_cobbler',
                              r'[cobbler-',
                              r'/network.cobbler',
                              r'allocator_support',
                              r'support for',
                              r'lvm_support',
                              r'HAL support',
                              r'color support',
                              r'IPv6 support',
                              r'support@redhat.com',
                              r'support was',
                              r'support will',
                              r'#ident "$Source:',
                              r'vxdctl support',
                              r'scramdisk',
                              r'masterport',
                              r'master": {}',
                              r'LogicalVolume = master',
                              r'>>[master]',
                              r'puppetversion',
                              r'puppet_vardir',
                              r'concat_basedir',
                              r'classesfile',
                              r'cobbler-ext-nodes',
                              r'rundir =',
                              r'modulepath = ',
                              r'manifestdir =',
                              r'config_version',
                              r'>>dirs',
                              r'puppet_auto_setup',
                              r'puppet_certs',
                              r'puppetca_path',
                              r'puppet phase',
                              r'puppetqueue',
                              r'pidfile=',
                              r'puppetqd',
                              r'killproc',
                              r'[ -f /etc/',
                              r'create 0644',
                              r'# Created by LITP',
                              r'master_1103',
                              r"cat << 'EOF",
                              r'connect_cobbler',
                              r'tag in cobbler',
                              r'default_kickstart:',
                              r'template_dir:',
                              r'webdir:',
                              r'addn-hosts =',
                              r'cobbler_system',
                              r'cobbler --helpbash',
                              r'complete -F _cobbler',
                              r'cobbler = ""',
                              r'append -c ',
                              r'cobbler:Cobbler:',
                              r'puppet reload',
                              r'Saving to:',
                              r'+ mkdir',
                              r'+ cp',
                              "/root/cobbler.ks\t Contains -->>puppet",
                              "/root/anaconda-ks.cfg\t Contains -->>pupp",
                              r"cobbler-config.repo' saved [0/0]",
                              r"cobbler.ks' saved",
                              r'snippetsdir',
                              r'puppet_mco_timeout',
                              r'.AutoInstall_2.1',
                              r'autoinstall',
                              r'.pem',
                              r'/etc/sysconfig/ip',
                              r'master:',
                              r'/etc/libreport',
                              r'cobbler check']

        # Search node for system passwords
        suspect_str = suspect_str + self.search_nodes(
            know_3pp_passwords, dir_list, grep_arg, True)
        # Find and remove any expected strings from list
        self.remove_expected_strings(list_of_ok_phrases, suspect_str)
        # Print result and assert Pass Fail
        filename = datetime.now().strftime(
            "/tmp/test05_output%Y%m%d-%H%M%S.log")
        outputfile1 = open(filename, 'w+')
        for item in suspect_str:
            outputfile1.write("\n" + item)
        self.print_suspect_msg(suspect_str)

    def obsolete_test_16_search_dict_passwords_not_in_testrun(self):
        """
        Description:
            Tests for any occurrence of dictionary password strings
            on all nodes.
        Actions:
            To be run seperatelly over the weekend.
                    passwords = ['support',
                                'master',
                                'secret',
                                'puppet',
                                'cobbler']
        Result:
            No files with dictionary password can be found on any machine
            in listed dirs
        """
        suspect_str = []
        dir_list = []
        grep_arg = " -l"
        know_3pp_passwords = ['support',
                              'master',
                              'secret',
                              'puppet',
                              'cobbler']

        list_of_ok_phrases = [r'default_node_litp_admin_pass',
                              r'/root/.litprc',
                              r'/bin/grep',
                              r'/usr/bin/xargs /bin/grep  -l',
                              r'/home/litp-admin/.litprc',
                              r'Binary file (standard input)',
                              r'Invalid argument',
                              r'marionette-collective.org',
                              r'Marionette Collective',
                              r'mcollective_spec.rb',
                              r'>>marionette</p>',
                              'supported',
                              'supports',
                              'mastered',
                              'puppetmaster',
                              'supporting',
                              '_secrets',
                              '_master',
                              'masters',
                              '_listsupport',
                              'listsupport',
                              'Secret',
                              'Master',
                              'Secret',
                              'webmaster:',
                              'ostmaster',
                              'emaster',
                              'master-',
                              'tmaster',
                              'master.',
                              'mcollective-puppet',
                              r'cobbler system',
                              r'support-tool',
                              r'cobbler-config',
                              r'mkdir',
                              r'registration',
                              r'COBBLER',
                              r'PUPPET',
                              r'Generated by puppet ',
                              r'ifcfg-',
                              r'wget-',
                              r'support not',
                              r'support availa',
                              r'support every',
                              r'support IP',
                              r'support necessary',
                              r'support:  ',
                              r'support this',
                              r'support by',
                              r'not support ',
                              r'colour support ',
                              r'enable support',
                              r'support to',
                              r'# support ',
                              r'protocol support',
                              r'support on',
                              r'that support',
                              r"doesn't support",
                              r'support.',
                              r'puppet service',
                              r'puppet on',
                              r'puppetd',
                              r'puppetlabs ',
                              r'993 puppet ',
                              r'by puppet ',
                              r'puppet client',
                              r'puppet agent',
                              r': name=puppet',
                              r'_qmaster',
                              r'Qmaster',
                              r'master file',
                              r'master certificate',
                              r'VCSmaster',
                              r'webmaster',
                              r'puppet master',
                              r"master's",
                              r'the master',
                              r'ismaster',
                              r'master device',
                              r'master process',
                              r'to master',
                              r'text-master',
                              r'master>bond',
                              r'type master',
                              r'master server',
                              r'-secret-$DEVICE',
                              r'gpg_secret',
                              r'BINDPW',
                              r'bindpw',
                              r'secret with', ]

        # Search node for system passwords
        suspect_str = suspect_str + self.search_nodes(
            know_3pp_passwords, dir_list, grep_arg, True)
        # Find and remove any expected strings from list
        self.remove_expected_strings(list_of_ok_phrases, suspect_str)
        # Print result and assert Pass Fail
        filename = datetime.now().strftime(
            "/tmp/test05_output%Y%m%d-%H%M%S.log")
        outputfile1 = open(filename, 'w+')
        for item in suspect_str:
            outputfile1.write("\n" + item)
        self.print_suspect_msg(suspect_str)

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc17')
    def test_17_search_ks_files_4_passwds(self):
        """
        Description:
            Tests for any occurrence of cleartext passwords in kickstart files
        Actions:
            system_passwords in install dir of .iso
            system_passwords = ['@dm1nS3rv3r',     'litpc0b6lEr',
                                'litp_admin',      'p3erS3rv3r',
                                'Aut01nstall',     'shroot12',
                                'Amm30n',         'master',
                                'support', pass, pwd, pswd]
        Result:
            No files with system_passwords can be found in kickstart files
        """
        cmd_mount = ("mount /home/litp-admin/.*nstall*/"
                     "ERIClitp* /mnt -o loop")
        cmd_umount = "umount /mnt"
        dir_to_list = "/home/litp-admin/.*nstall*/"
        suspect_str = []
        dir_list = ['mnt/install/',
                    'var/lib/cobbler/kickstarts/']
        grep_arg = " -il"
        system_passwords = ['@dm1nS3rv3r',
                            'litpc0b6lEr',
                            'litp_admin',
                            'p3erS3rv3r',
                            'Aut01nstall',
                            'shroot12',
                            'Amm30n',
                            'master',
                            'support',
                            'pass',
                            'pwd',
                            'pswd',
                            ]

        list_of_ok_phrases = [r'Creating repo in $(pwd)',
                              r'PASS_MAX_DAYS',
                              r'PASS_MIN_LEN',
                              r'passwd for single',
                              r'minimum password len',
                              r'servicRoot password',
                              r'change password',
                              r'password expiration',
                              r'${LITP_ADMIN}',
                              r'PASSWD_FILE=/etc/passwd',
                              r'LITP_ADMIN=litp-admin',
                              r"PASSWD='$1$",
                              r'passalgo=sha512',
                              r'default_password_crypted',
                              r'passwd/root-',
                              r'passwd/make-',
                              r'Master Boot Record',
                              r'password_settings',
                              r'passed ',
                              r'#Root password',
                              r'$default_node_litp_admin_pass --iscrypted',
                              r'language support',
                              r'langsupport',
                              r'supported',
                              r'root account and password']

        dir_contents = self.list_dir_contents(self.ms_node,
                                            dir_to_list)
        self.log('info', "contents of dir: " + ','.join(dir_contents))

        stdout, stderr, rtcode = self.run_command(self.ms_node,
                                                  cmd_mount,
                                                  su_root=True)

        self.assertEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, rtcode)

        save_targets = self.targets
        self.targets = [self.ms_node]
        # Search node for system passwords
        suspect_str = suspect_str + self.search_nodes(system_passwords,
                                                      dir_list,
                                                      grep_arg, True)
        self.targets = save_targets
        stdout, stderr, rtcode = self.run_command(self.ms_node,
                                                  cmd_umount, su_root=True)
        # Find and remove any expected strings from list
        self.remove_expected_strings(list_of_ok_phrases, suspect_str)
        # Print result and assert Pass Fail
        self.print_suspect_msg(suspect_str)

    @attr('all', 'non-revert', 'security', 'P3', 'security_tc18')
    def test_18_search_for_ammeon_opt(self):

        """
        Description:
          Search for string "ammeon" on all nodes under /opt
        Actions:
        /opt is in its own test as all files under /opt/SentinelRMSSDK
               need to be excluded - they have spaces in the filenames
           Loop over all targets
             Get names of directories under /opt
             Find and remove any unsearchable directories from list
             Loop over searchable directories
               Search for ammeon
             Search for ammeon under / only
         Result:
           No files with "ammeon" present in /opt
         """

        # store list of any files found
        files_found = []
        # exclude some file types from the find
        find_args = " -type f -perm -o=r ! -name *.iso ! -name *.gz"
        top_level_find_args = (
            "/opt -maxdepth 1 -type f -perm -o=r ! -name *.iso ! -name *.gz")
        # exclude some dirs from the search
        list_of_unsearchable_dirs = ['SentinelRMSSDK/']

        # list of files which can be excluded from results
        # excluding sanapi test files - ' in names confuses grep
        exclude_files = [r"/opt/ericsson/nms/litp/lib/sanapi/test/data"]

        # Loop over all machines
        for target in self.targets:

            # Get list of directories under /opt
            dir_list = self.list_dirs(target, "/opt")

            # Find and remove any unsearchable directories from list
            self.remove_items_from_list(list_of_unsearchable_dirs, dir_list)

            # loop over searchable directories
            for dir_name in dir_list:

                # search for string
                complete_find_args = ("/opt/" + dir_name + find_args)
                stdout, stderr, returnc = self.find_string(complete_find_args,
                                                           target)

                # stop if there is an error
                self.assertEqual([], stderr)
                self.assertNotEqual(-1, returnc)

                # Remove expected files
                self.remove_strings(exclude_files, stdout)

                # remove any files which only contain ammeonvpn
                #  or Ammeon-LITP
                self.remove_files_with_ignore_string(stdout,
                                                     target)

                # if find result is not empty then add to files_found
                if stdout != []:
                    files_found.append(
                        "String 'Ammeon' found on machine {0} in files: ".
                        format(target))
                    files_found.append(stdout)

            # search in /opt itself
            stdout, stderr, returnc = self.find_string(
                top_level_find_args, target)

            # stop if there is an error
            self.assertEqual([], stderr)
            self.assertNotEqual(-1, returnc)

            # if find result is not empty then add to files_found
            if stdout != []:
                files_found.append(
                    "String 'Ammeon' found on machine {0} in files: ".
                    format(target))
                files_found.append(stdout)

        # Check no files found on any machine
        self.assertEqual([], files_found)

    @attr('all', 'non-revert', 'security', 'P3', 'security_tc19')
    def test_19_search_for_ammeon(self):
        """
        Description:
          Search for string "ammeon" on all nodes
        Actions:
           Loop over all targets
             Get names of directories under /
             Find and remove any unsearchable directories from list
             Loop over searchable directories
               Search for ammeon
             Search for ammeon under / only
         Result:
           No files with "ammeon" present on any machine
         """

        # store list of any files found
        files_found = []
        # list of files which can be excluded from results
        list_of_expected_files = ["/tmp/lsb_pkg/EXTR-lsbwrapper10-2.0.0.rpm",
             "/tmp/lsb_pkg/EXTR-lsbwrapper5-2.0.0.rpm",
             "/tmp/lsb_pkg/EXTR-lsbwrapper1-2.0.0.rpm",
             "/tmp/lsb_pkg/EXTR-lsbwrapper6-2.0.0.rpm",
             "/tmp/lsb_pkg/EXTR-lsbwrapper2-2.0.0.rpm",
             "/tmp/lsb_pkg/EXTR-lsbwrapper7-2.0.0.rpm",
             "/tmp/lsb_pkg/EXTR-lsbwrapper3-2.0.0.rpm",
             "/tmp/lsb_pkg/EXTR-lsbwrapper8-2.0.0.rpm",
             "/tmp/lsb_pkg/EXTR-lsbwrapper4-2.0.0.rpm",
             "/tmp/lsb_pkg/EXTR-lsbwrapper9-2.0.0.rpm",
             "/tmp/lsb_pkg/EXTR-lsbwrapper40-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper10-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper5-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper1-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper6-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper2-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper7-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper3-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper8-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper4-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper9-2.0.0.rpm",
             "/var/www/html/3pp/EXTR-lsbwrapper40-2.0.0.rpm",
             "/var/lib/rpm/Packages",
             "/var/lib/rpm/__db.001",
             "/var/lib/rpm/__db.002",
             "/var/lib/rpm/__db.003",
             "/var/lib/rpm/__db.004",
           "/var/lib/libvirt/instances/STvmserv4/test_image.qcow2",
           "/var/lib/libvirt/instances/STvmserv2/image_with_ocf.qcow2",
           "/var/lib/libvirt/instances/STvmserv5/image_with_ocf.qcow2",
           "/var/lib/libvirt/instances/FO-VM/image_with_ocf.qcow2",
           "/var/lib/libvirt/instances/STvmserv6/image_with_ocf.qcow2",
           "/var/lib/libvirt/instances/STvmserv1/user-data",
           "/var/lib/libvirt/instances/STvmserv1/user-data.live",
           "/var/lib/libvirt/instances/STvmserv1/image_with_ocf.qcow2",
           "/var/lib/libvirt/instances/STvmserv3/user-data",
           "/var/lib/libvirt/instances/STvmserv3/user-data.live",
           "/var/lib/libvirt/instances/STvmserv3/image_with_ocf.qcow2",
    "/var/lib/libvirt/instances/STvmserv3/vm_rhel_7_test_image-1-1.0.1.qcow2",
           "/var/lib/libvirt/instances/STvmserv11/image_with_ocf.qcow2",
           "/var/lib/libvirt/instances/PL-VM/image_with_ocf.qcow2",
           "/var/lib/libvirt/images/vm_rhel_7_test_image-1-1.0.1.qcow2",
           # enm image has some .150 info after manipulation to disable dhcp
           "/var/lib/libvirt/instances/STvmserv3/enm_rhel_7_base_image.qcow2",
           "/var/www/html/images/vm_rhel_7_test_image-1-1.0.1.qcow2",
             "/var/www/html/3pp/test_service-1.0-1.noarch.rpm",
             "/var/www/html/6.6/updates/x86_64/Packages/" \
             "test_service-2.0-1.noarch.rpm",
             "/var/www/html/6.6/os/x86_64/test_service-2.0-1.noarch.rpm",
             "/tmp/test_service-1.0-1.noarch.rpm",
             "/tmp/test_service-2.0-1.noarch.rpm",
             "/usr/lib64/firefox/libxul.so",
             "/tmp/test_service_name-2.0-1.noarch.rpm",
             "/var/www/html/3pp/test_service_name-2.0-1.noarch.rpm",
             "/var/lib/rpm/Name",
             "/var/lib/rpm/Dirnames",
             "/var/lib/rpm/Installtid",
             "/var/lib/libvirt/instances/FO-VM/vm_test_image.qcow2",
             "/var/lib/libvirt/instances/STvmserv11/vm_test_image.qcow2",
             "/var/lib/libvirt/instances/STvmserv4/STCDB_test_image.qcow2",
             "/var/lib/libvirt/instances/STvmserv1/vm_test_image.qcow2",
             "/var/lib/libvirt/instances/STvmserv2/vm_test_image.qcow2"]

        # exclude some file types and directories from the find
        # puppet lock files is excluded as it is transient
        #  - so wont be present for the second part of the test
        find_args = " -type f -perm -o=r ! -name *.iso "\
          "! -name *.gz ! -name agent_catalog_run.lock "\
          "! -name *enm_base_image.qcow2 ! -name *enm_jboss_1.0.42.qcow2 "\
          "! -name *vm_test_image-1-1.0.1.qcow2 "\
          "! -name *-hello-* "\
          "! -name *.sqlite-journal "\
          "! -name *yaml*.lock "\
          "! -name *.sqlite ! -name ctl ! -name fid "\
          "! -name db-*log "\
          " -not -path '/var/www/html/ENM*'" \
          " -and -not -path '/var/www/html/images/ENM*'"
        top_level_find_args = "/ -maxdepth 1 -type f -perm -o=r !"\
                              " -name *.iso ! -name *.gz"
        # exclude some dirs from the search
        # - these contain transient files
        list_of_unsearchable_dirs = ['proc/', 'sys/', 'opt/']

        # Loop over all machines
        for target in self.targets:

            # Get list of directories under /
            dir_list = self.list_dirs(target, "/")

            # Find and remove any unsearchable directories from list
            self.remove_items_from_list(
            list_of_unsearchable_dirs, dir_list)

            # loop over searchable directories
            for dir_name in dir_list:

                # search for string
                complete_find_args = ("/" + dir_name + find_args)
                stdout, stderr, returnc = self.find_string(complete_find_args,
                                                           target)

                # stop if there is an error
                self.assertEqual([], stderr)
                self.assertNotEqual(-1, returnc)

                # if find result is not empty, check for allowed exceptions
                if stdout != [] and not self.is_find_error_in_stdout(stdout):

                    # remove expected files
                    self.remove_items_from_list(
                     list_of_expected_files, stdout)

                    # remove any files which only contain ammeonvpn
                    # or Ammeon-LITP
                    self.remove_files_with_ignore_string(stdout,
                                                         target)

                    # if find result is still not empty, then add to
                    # files_found
                    if stdout != []:
                        files_found.append(
                          "String 'Ammeon' found on machine {0} in files: ".
                           format(target))
                        files_found.append(stdout)

            # search in / itself
            stdout, stderr, returnc = self.find_string(
                top_level_find_args, target)

            # stop if there is an error
            self.assertEqual([], stderr)
            self.assertNotEqual(-1, returnc)

            # if find result is not empty then add to files_found
            if stdout != [] and not self.is_find_error_in_stdout(stdout):
                files_found.append(
                  "String 'Ammeon' found on machine {0} in files: ".
                   format(target))
                files_found.append(stdout)

        # Check no files found on any machine
        self.assertEqual([], files_found)
