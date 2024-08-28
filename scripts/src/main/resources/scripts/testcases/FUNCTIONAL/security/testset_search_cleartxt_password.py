"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     January 2014
@author:    Vinnie McGuinness
@summary:   System test to check,
            Check system    for cleartext passwords
            Check model     for cleartext passwords
            Check logs       for cleartext passwords
            Check json files for cleartext password
"""

from litp_generic_test import GenericTest, attr
from litp_cli_utils import CLIUtils
from redhat_cmd_utils import RHCmdUtils
import test_constants


class SecurityChecks(GenericTest):
    """
        System tests to check file system for possible
        cleartext passwords
    """

    def setUp(self):
        """Run before every test"""
        super(SecurityChecks, self).setUp()
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
        if 'ammsfs_01' in self.targets:
            self.targets.remove('ammsfs_01')
        if 'atsfsx82' in self.targets:
            self.targets.remove('atsfsx82')
        if 'rover2' in self.targets:
            self.targets.remove('rover2')
        self.setup_cmds = []
        self.results = []
        self.grep_pass = [r'pass\|pwd\|pswd']
        self.list_of_unsearchable_dirs = []
        self.list_of_exclude_dirs = ['var', 'usr', 'opt', 'etc', 'root']
        self.list_of_ok_phrases = ['Binary file (standard input) matches',
                            r'set_postgres_postgrespw',
                            r'-->>password = litp_admin',
                            r'/lib/modules/2.6.32-504.12.2.el6.x86_64'
                            r'ncrypt the password',
                            r'print >> sys.stderr',
                            r'getpass.getpass(',
                            r'/home/litp-admin/.litprc',
                            r'servicRoot password',
                            r'set password expiration to 30 days',
                            r'force change password at first login',
                            r'set minimum password len 9',
                            r'Additional Password Checks for <code',
                            r'password --encrypted $1$',
                            r'No such file or directory',
                            r'.Autoinstall_',
                            r'.AutoInstall_',
                            r'Pass-through',
                            r'sbin/grub-md5-crypt',
                            r'sbin/grub-crypt',
                            r'name="EcimPassword',
                            r'name="password"',
                            r'<description>',
                            r'ffffffff',
                            r'CONFIG_',
                            r'Passive',
                            r'PASSNO',
                            r'sestatus',
                            r'ntp/keys',
                            r'passphrases',
                            r'password-auth',
                            r'include',
                            r'password    required',
                            r'password    requisite',
                            r'password    sufficient',
                            r'Binary file (standard input) matches',
                            r'# Password',
                            r'orginal password crypted',
                            r'local opts="--username --password',
                            r'simple username+password mechanis',
                            r'system-config-rootpassword',
                            r'challengePassword',
                            r'PasswordAuthentication',
                            r'_password = secret',
                            r'password_crypted: "$1$',
                            r'#PermitEmptyPasswords no',
                            r'# the setting of "PermitRootLogin without',
                            r'_subscription_manager_common_opts=',
                            r'shell           514/tcp         cmd',
                            r'password-chg    586/udp',
                            r'password required       pam_deny.so',
                            r'-password   optional pam_gnome_keyring.so',
                            r'#crypto pw apassword  ',
                            r'Contains -->>[password]',
                            r'Contains -->>#crypto pw',
                            r'Contains -->>proxy_password ',
                            r'prompt=$(printf',
                            r'password   optional',
                            r'password   substack',
                            r'password protected" "$mount_point',
                            r'encrypted $1$',
                            r'Same thing without a password',
                            r'ODSJQf.4IJN7E',
                            r'xxj31ZMTZzkVA',
                            r'# LU_',
                            r'http_proxy/authentication_password',
                            r'HTTP proxy password',
                            r'str Password',
                            r'encrypt',
                            r'/bin/grep:',
                            r'local opts="--',
                            r'haattr -add RemoteGrou',
                            r'--environment --force --name --org',
                            r'checkpassword',
                            r'PasswordDatabase',
                            r'_passwords',
                            r'password=test',
                            r'nopassword',
                            r'#ssl_key_password',
                            r'litp_admin_pass: "$1$',
                            r'774/tcp',
                            r'first_pass',
                            r'ldap_search_passwd:',
                            r'object_r',
                            r'passed',
                            r'bypass',
                            r'Bypass',
                            r'passwd.db',
                            r'lPass',
                            r'Pass Phrase',
                            r'NOPASSWD',
                            r'hrase',
                            r'PassGo',
                            r'Pass-Thru',
                            r'Passthru',
                            r'SurfPass',
                            r'askpass',
                            r'llm-pass',
                            r'poppassd',
                            r'alias',
                            r'PASSED',
                            r'IPASS',
                            r'kpwd',
                            r'PASS_',
                            r'=$(pwd)',
                            r'bin/passwd ',
                            r'passenger',
                            r'passive',
                            r'etc/rpc',
                            r'nsswitch',
                            r'snmpd',
                            r'ltrace.',
                            r'namespace',
                            r'USEPASSWDQC=no',
                            r'PM-GPG-KEY',
                            r'ldap_search_passwd',
                            r'loop through the data structure we have been',
                            r'"password": "master"',
                            r'lanplus',
                            r'kernel',
                            r"key-for-root",
                            r"u'master', u'user_name': u'master'",
                            r'DEBUG: checking prop password_key',
                            r'Property type password_key added',
                            r'emc: long trespass command sent',
                            r'Passenger',
                            r'EXTRlitppassenger_',
                            r'DEBUG: checking prop password',
                            r'name "password_key',
                            r'key-for-sfs',
                            r'ricci user password is not set',
                            r'{pwd} -I lanplus',
                            r'Element password_key',
                            r'password_key: key-for-sfs',
                            r'loop through the data structure',
                            r'nfs_service password: master',
                            r'set password expiration to 30 days',
                            r'autoinstall',
                            r'Installing passwd-0.77-4',
                            r'force change password at first login',
                            r'set minimum password len 9',
                            r'Get root passwd for single user mode',
                            r'512',
                            r'Creating repo in $(pwd)',
                            r'.litprc',
                            r'.viminfo',
                            r'password_key=key-for-',
                            r'passed',
                            r'--password=$1$',
                            r'Binary file (standard input) matches',
                            r'cd `dirname $0`; pwd',
                            r'iscrypted',
                            r'md5pass=',
                            r'#Root password',
                            r'passenv',
                            r'ca-bundle',
                            r'ProxyPass',
                            r'Assigned',
                            r'passdown',
                            r'multipass',
                            r'PassAuth',
                            r'usepasswd=False',
                            r"didn't pass",
                            r'passing',
                            r'sys.stderr',
                            r'pass through',
                            r'SApswd',
                            r'LsnrPwd',
                            r'REG_INT',
                            r'savedir',
                            r'passwd-file',
                            r'passdb',
                            r'pass = yes',
                            r'/etc/passwd',
                            r'Passwd.tx',
                            r'passwd-like',
                            r'PasswdFile',
                            r'pass DAD',
                            r"$PWD",
                            r'passwdless',
                            r'passes',
                            r'passwd file',
                            r'hpwdt',
                            r'driver = passwd',
                            r'.bash_history',
                            r'gestionnaire',
                            r'ssh_host_rsa_key',
                            r'save-passwd="false',
                            r'optional      pam_pkcs11.so',
                            r'.auth.password = password',
                            r'--unset --username --pass',
                            r'password_in = password_in',
                            r'XYZ12345',
                            r'encap:175',
                            r'/etc/pki/tls/certs/localhost.crt',
                            r'/etc/lvm',
                            r'/sys/devices/',
                            r'__mount___',
                            r'ssh_host_dsa_key',
                            r'test-lsb',
                            r'/etc/pki/tls/private/localhost.key',
                            r'/etc/pki/dovecot/',
                            r'prop_value=',
                            r'/tmp/root_import_iso.exp',
                            r'_password.rb',
                            r'/tmp/.erlang.cookie',
                            r'Passing shared_disks argument',
                            r'/etc/puppetdb/conf.d/database.ini',  # TORF135656
                            r'ENCRYPTED PASSWORD',
                            r'puppetdb_psdatabase_password',
                            r'/etc/libreport',
                            r'fsck_pass',  # TORF-173856
                            r'pass => "2"'  # TORF-173856
                            ]

    def tearDown(self):
        """run after each test"""
        super(SecurityChecks, self).tearDown()

    def remove_expected_strings(self, list_ok, list_returned):
        """
        Check list_returned for any items that are in the list_ok
        If the item in list_ok they are removed from the list_returned
        The list_returned is returned minus any OK items
        """
        print"\n\t\t### List of suspect lines too be filtered ###"
        for item in list_returned:
            self.log('info', item)

        print"\n\t\t### Filtered out ok lines ###"
        list_returned = self.remove_strings(list_ok, list_returned)
        list_returned = self.remove_wont_fix_strings(list_returned)
        return list_returned

    @classmethod
    def remove_strings(cls, list_ok, list_returned):
        """
        Check list_returned for any items that are in the list_ok
        If the item in list_ok they are removed from the list_returned
        The list_returned is returned minus any OK items
        """
        for item_ok in list_ok:
            for item_ret in list(list_returned):
                if item_ok in item_ret:
                    print item_ok, "<<-- used to filtered out-->> ", item_ret
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
        Asserts Fail if there are any suspect messages
        """
        # If there are unexpected items still in list, print and assert Fail
        print"\n\n\t\t### Print list of suspect lines ###"
        for item in suspect_msg:
            print item
        self.assertEqual([], suspect_msg)
        print"\n\n"

    def filter_suspects(self, suspect_list, list_of_ok_phrases):
        """
        Find and remove any expected strings from list
        """
        stdout = self.remove_expected_strings(
            list_of_ok_phrases, suspect_list)
        return stdout

    def check_folders(self, find_cmd):
        """
            Finds all nodes and calls a search on a specific folder
        """
        suspect_lines = []
        node_list = self.targets
        # Perform search on all nodes
        for node in node_list:

            suspect_lines.append(self.check_node_folders(node, find_cmd))
        return suspect_lines

    def check_node_folders(self, node, find_cmd):
        """
        Function runs a command to find a list of locations with suspect string
        Each of these locations is checked for suspect strings
        Suspect location and strings are recorded
        Filter suspects against list of ok phrases
        Function asserts fail if suspect strings remain
        All nodes are checked
        """
        sentence = []
        list_pass_file_and_line = []
        max_words = 7
        max_string_len = 70
        search_for = self.grep_pass
        filename_list = []
        not_searchable_list = [r"Permission denied",
                               r"Invalid argument",
                               r"Input/output error",
                               r"No such ",
                               r"Connection timed out",
                               r"No such device or address",
                               r'/lib/modules/2.6.32-504.12.2.el6.x86_64'
                               ]

        # Run find command to search for suspect locations
        stdout, stderr, ret_code = self.run_command(
                                            node, find_cmd, su_root=True)
        self.assertEqual([], stderr)
        self.assertNotEqual(2, ret_code)

        filename_list = self.remove_strings(not_searchable_list, stdout)

        # In each suspect file search for suspect string
        for filename in filename_list:
            # Create grep command to filter files
            cmd = RHCmdUtils().get_grep_file_cmd(
                filename, search_for, '-i')

            # Run grep command
            grep_std_out, std_err, ret_code = self.run_command(
                                        node, cmd, su_root=True)
            self.assertNotEqual(0, std_err)
            self.assertNotEqual(2, ret_code)

            for item in grep_std_out:
                # If line has more than max_words or is over max_string_len
                # it is considered a sentence and removed from search but
                # will be stored and printed out later.
                if ((len(item.split()) > max_words) or
                                    (len(item) > max_string_len)):
                    sentence.append("%s %s\tContains -->>%s"
                                    % (node, filename, item))
                else:
                    list_pass_file_and_line.append("%s %s\tContains -->>%s"
                                            % (node, filename, item))

        if sentence != []:
            print"\n\n\t\t### Print list of ignored sentences ###"
            for item in sentence:
                print item

        return list_pass_file_and_line

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

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc05')
    def test_05_search_password_on_model(self):
        """
        Description:
            Tests litp Model for cleartext password
        Actions:
            1. Find all locations on model
            2. grep locations for suspect strings 'pass|pwd|pswd'
            3. check suspect strings against list of ok list_of_ok_phrases
        Results:
            no passwords found in json files
        """

        suspect_urls = []
        suspects_list = []
        suspects_items = self.grep_pass

        show_cmd = self.cli.get_show_cmd('/', '-r')
        grep_cmd = RHCmdUtils().get_grep_file_cmd(show_cmd, self.grep_pass,
                                                  '-i', file_access_cmd="")
        suspects_list, stderr, ret_code = self.run_command(
            self.ms_node, grep_cmd, su_root=True, add_to_cleanup=False)
        self.assertEqual(ret_code, 0, "non zero return code")
        self.assertEqual(stderr, [], "stderr is not empty: {0}".format(stderr))
        print "suspect_list=", suspects_list
        # Find and remove any expected strings from list
        suspects_list = self.remove_expected_strings(self.list_of_ok_phrases,
                                                            suspects_list)

        if suspects_list != []:
            print "Suspect lines found test model item by item"
            # Find all locations on model and searched individually.
            show_cmd = self.cli.get_show_cmd('/', '-lr')
            stdout, stderr, ret_code = self.run_command(
                self.ms_node, show_cmd, add_to_cleanup=False)
            self.assertEqual(ret_code, 0, "non zero return code")
            self.assertEqual(stderr, [],
                             "stderr is not empty: {0}".format(stderr))
            self.assertNotEqual(stdout, [], "Expected a list of locations")

            # For each location on model do a litp show of what it contains
            for url_line in stdout:
                show_cmd = self.cli.get_show_cmd(url_line)
                stdout1, stderr, ret_code = self.run_command(
                    self.ms_node, show_cmd, add_to_cleanup=False)
                self.assertEqual(stderr, [],
                                 "stderr is not empty: {0}".format(stderr))
                self.assertEqual(ret_code, 0, "non zero return code")

                # Check if any suspect string is found in output
                for greps in suspects_items:
                    for line_txt in stdout1:
                        if greps.lower() in line_txt.lower():
                            suspect_urls = suspect_urls + [url_line +
                                                           " " + line_txt]

            # Find and remove any expected strings from list
            suspects_list = self.remove_expected_strings(
                self.list_of_ok_phrases, suspect_urls)

        # If there are unexpected items still in list, print and assert Fail
        self.print_suspect_msg(suspects_list)

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc06')
    def test_06_search_password_in_var_logs_msg(self):
        """
        Description:
            Test /var/log/messages for cleartext password
        Actions:
            1. grep locations for suspect strings 'pass|pwd|pswd'
            2. check suspect strings against list of ok list_of_ok_phrases
        Results:
            no passwords found in /var/log/messages
        """

        log_location_n_str = []

        for node in self.targets:
            # grep file and add any suspect strings to list
            grep_cmd = RHCmdUtils().get_grep_file_cmd(
                test_constants.GEN_SYSTEM_LOG_PATH, self.grep_pass, '-i')
            stdout, stderr, ret_code = self.run_command(node, grep_cmd,
                                        su_root=True, add_to_cleanup=False)

            # Ensure return code is one of 0 or 1
            expected_rc = (ret_code == 0 or ret_code == 1)
            self.assertTrue(expected_rc,
                        "Return code of {0} indicates error".format(ret_code))

            # Validate empty stderr
            self.assertEqual(stderr, [],
                             "stderr is not empty: {0}".format(stderr))
            for item in stdout:
                log_location_n_str = (log_location_n_str + [node + ' ' +
                                        test_constants.GEN_SYSTEM_LOG_PATH +
                                       '\tContains -->>' + item])

        # Find and remove any expected strings from list
        stdout = self.remove_expected_strings(
            self.list_of_ok_phrases, log_location_n_str)

        # If there are unexpected items still in list, print and assert Fail
        self.print_suspect_msg(stdout)

    def obsolete_07_search_password_in_json(self):
        """
        Description:
            Obsoleted Sept 16 when puppetdb was introduced TORF-107213
            Test /var/lib/litp/ for cleartext password
        Actions:
            1. grep locations for suspect strings
            2. check suspect strings against list of ok list_of_ok_phrases
            Search for strings 'pass|pwd|pswd'
        Results:
            no passwords found in json files
        """

        json_location_n_str = []
        json_files = ['.json', 'LAST']
        json_file_list = []

        # Find list of file to check
        dir_list = self.list_dir_contents(self.ms_node,
                                        test_constants.LITP_LIB_MODEL_PATH)

        for item in dir_list:
            for item1 in json_files:
                if item1 in item:
                    json_file_list.append(item)

        # For each file check for suspect strings
        for filename in json_file_list:
            file_to_check = test_constants.LITP_LIB_MODEL_PATH + filename
            grep_cmd = RHCmdUtils().get_grep_file_cmd(
                file_to_check, self.grep_pass, '-i')

            grep_std_out, grep_std_err, ret_code = self.run_command(
                self.ms_node, grep_cmd, add_to_cleanup=False)
            self.assertNotEqual(ret_code, 2, "non zero return code")
            self.assertEqual(grep_std_err, [],
                             "stderr is not empty: {0}".format(grep_std_err))
            for suspect_str in grep_std_out:
                json_location_n_str = (json_location_n_str +
                                       [file_to_check +
                                        '\tContains -->>' + suspect_str])

        #Find and remove any expected strings from list
        stdout = self.remove_expected_strings(
            self.list_of_ok_phrases, json_location_n_str)

        #If there are unexpected items still in list, print and assert Fail
        self.print_suspect_msg(stdout)

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc08')
    def test_08_search_root_for_cleartxt_password(self):
        """
        Description:
            Tests nodes for cleartext password in dir
             /root
        Actions:
            1. do a find on /root to find suspect files
            2. grep suspect files for suspect strings 'pass|pwd|pswd'
            3. check suspect strings against list of ok list_of_ok_phrases
        Results:
            no passwords found /root
        """
        search_for = self.grep_pass
        list_pass_file_and_line = []

            # Find files containing suspect strings
        find_cmd = RHCmdUtils().get_find_files_in_dir_cmd(
                ("/root ! -name *.iso ! -name *.gz ! -name .viminfo "
                "! -name .bash_history"), search_for, " -il")
        self.setup_cmds.append(find_cmd)

        self.log('info', self.targets)
        # Do for each node in model
        for node in self.targets:
            stdout, stderr, ret_code = self.run_command(
                                            node, find_cmd, su_root=True,
                                            add_to_cleanup=False)
            # Update to run_command function required
            # stderr sometimes contains data that should be in stdout
            # Workaround implemented
            # self.assertEqual(stderr, [],
            #                "stderr is not empty: {0}".format(stderr))
            if stdout == []:
                if stderr != []:
                    stdout = stderr
            self.log('info', stdout)
            self.assertEqual(ret_code, 0, "non zero return code")

            # use cat suspect files and store suspect strings in list
            for filename in stdout:
                # Create grep command to filter files
                cmd = RHCmdUtils().get_grep_file_cmd(
                    filename, self.grep_pass, '-i' ' ')
                grep_std_out, std_err, ret_code = self.run_command(
                    node, cmd, su_root=True, add_to_cleanup=False)
                #import pdb; pdb.set_trace()
                self.assertEqual(std_err, [],
                                 "stderr is not empty: {0}".format(std_err))
                self.assertEqual(ret_code, 0, "non zero return code")
                self.assertNotEqual(grep_std_out, [],
                                    "Expected a list of suspect lines lines")
                # Add file name and supect string to list
                for item in grep_std_out:
                    list_pass_file_and_line = list_pass_file_and_line + [
                        node + ' File ' + filename + '\tContains -->>' + item]

        # Find and remove any expected strings from list
        stdout = self.remove_expected_strings(
            self.list_of_ok_phrases, list_pass_file_and_line)

        self.print_suspect_msg(stdout)

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc09')
    def test_09_search_etc_for_cleartxt_password(self):
        """
        Description:
            Tests nodes for cleartext password in dir
            /etc
        Action:
            1. do a find in dir(s) above to find suspect files
            2. grep suspect files for suspect strings 'pass|pwd|pswd'
            3. check suspect strings against list of ok list_of_ok_phrases
        Results:
            no passwords found in /etc
        """
        find_cmd = []
        suspect_lines = []
        search_for = self.grep_pass

        # Find files containing suspect strings
        find_cmd = RHCmdUtils().get_find_files_in_dir_cmd(
                ("/etc -type f ! -name *.iso ! -name *.gz ! -name *.pem"),
                                            search_for, " -l -i")
        for node in self.targets:
            suspect_lines = suspect_lines + self.check_node_folders(
                                                            node, find_cmd)
        suspect_str = self.filter_suspects(suspect_lines,
                                                self.list_of_ok_phrases)
        # Run function to print suspect messages
        self.print_suspect_msg(suspect_str)

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc10')
    def test_10_search_dirs_for_cleartxt_password(self):
        """
        Description:
            Tests nodes for cleartext password in all dir
            excluding 'var', 'usr', 'opt', 'etc, 'root'
            These dirs are been checked else where
        Action:
            1. do a find in dir(s) to find suspect files
            2. grep suspect files for suspect strings 'pass|pwd|pswd'
            3. check suspect strings against list of ok list_of_ok_phrases
        Results:
            no passwords found in listed dirs
        """
        find_cmd = []
        suspect_lines = []
        search_for = self.grep_pass
        targets = []
        # 1. Get all nodes
        targets = self.targets
        #targets.append(self.get_management_node_filenames())

        for node in targets:
        # 3. Get list of directories under /
            dir_list = self.list_dir_contents(node, '/ -1', True)

            # 4. Find and remove any unsearchable directories from list
            self.remove_items_from_list(self.list_of_unsearchable_dirs,
                                                                    dir_list)
            self.remove_items_from_list(self.list_of_exclude_dirs, dir_list)

            print dir_list
            # Find files containing suspect strings
            for folders in dir_list:
                search_str = ("/" + folders +
                " -type f ! -name *.rpm ! -name *.iso ! -name *.gz " +
                "! -name *.ko ! -name *.so ! -name *.pem ")
                find_cmd = RHCmdUtils().get_find_files_in_dir_cmd(
                    search_str, search_for, " -l -i")

                suspect_lines = suspect_lines + self.check_node_folders(
                                                            node, find_cmd)
        suspect_str = self.filter_suspects(suspect_lines,
                                                self.list_of_ok_phrases)
        # Run function to print suspect messages
        self.print_suspect_msg(suspect_str)

    def obsolete_11_search_large_dirs_cleartxt_pwd_not_in_testrun(self):
        """
        Description:
            Test made obsolete as system adequedly covered in other
            test here.
            Tests nodes for cleartext password in dir
            'var', 'usr', 'opt'
            Test not to be added to ST testrun as will take too long to run.
            To be run seperatelly over the weekend.
        Action:
            1. do a find in dir(s) above to find suspect files
            2. grep suspect files for suspect strings 'pass|pwd|pswd'
            3. check suspect strings against list of ok list_of_ok_phrases
        Results:
            no passwords found in listed directorys
        """
        find_cmd = []
        suspect_lines = []
        search_for = self.grep_pass
        targets = []
        # 1. Get all nodes
        targets = self.targets
        #targets.append(self.get_management_node_filenames())

        for node in targets:
        # 3. Get list of directories under /
            dir_list = ['var', 'usr', 'opt']

            print dir_list
            # Find files containing suspect strings
            for folders in dir_list:
                search_str = ("/" + folders +
                " -type f ! -name *.rpm ! -name *.iso ! -name *.gz ")
                find_cmd = RHCmdUtils().get_find_files_in_dir_cmd(
                    search_str, search_for, " -l -i")

                suspect_lines = suspect_lines + self.check_node_folders(
                                                            node, find_cmd)

        suspect_str = self.filter_suspects(suspect_lines,
                                                    self.list_of_ok_phrases)
        # Run function to print suspect messages
        filename = "/tmp/test_11_output.log"
        outputfile1 = open(filename, 'w+')
        for item in suspect_str:
            outputfile1.write("\n" + item)
        self.print_suspect_msg(suspect_str)

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc12')
    def test_12_search_password_in_manifests(self):
        """
        Description:
            Tests nodes for cleartext password in the manifest dir
        Action:
            manifest dir:
            "/opt/ericsson/nms/litp/etc/puppet/manifests/plugins/"
            1. do a find in dir(s) above to find suspect files
            2. grep suspect files for suspect strings 'pass|pwd|pswd'
            3. check suspect strings against list of ok list_of_ok_phrases
        Results:
            no passwords found in manifest dir
        """
        find_cmd = []
        suspect_lines = []
        search_for = self.grep_pass
        # Find files containing suspect strings
        find_cmd = RHCmdUtils().get_find_files_in_dir_cmd(
                (test_constants.PUPPET_MANIFESTS_DIR +
                 " -type f ! -name *.iso ! -name *.gz "),
                                            search_for, " -l -i")
        #for node in self.ms_node:
        suspect_lines = suspect_lines + self.check_node_folders(
                                                    self.ms_node, find_cmd)
        suspect_str = self.filter_suspects(suspect_lines,
                                                self.list_of_ok_phrases)
        # Run function to print suspect messages
        self.print_suspect_msg(suspect_str)
