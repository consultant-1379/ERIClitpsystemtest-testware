'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     May 2014
@author:    Vinnie McGuinness
@summary:   System test to check
            Checking NTP Service &
            Test that user can successfully install a new LITP rpm package
            on peer nodes from a newly created REPO (by import) after using the
            "import" command  to import it into LITP MS Yum Repositories
'''

from litp_generic_test import GenericTest, attr
from litp_cli_utils import CLIUtils
from redhat_cmd_utils import RHCmdUtils
import os
import re
import test_constants


class ImportPackages(GenericTest):
    """
        Description:
        These tests are checking the litp mechanism for updating
        and configuring DNS Clients.
        &
        ST tests to search any files in invalid locations
    """
    def setUp(self):
        """Run before every test"""
        super(ImportPackages, self).setUp()
        self.cli = CLIUtils()
        self.rhcmd = RHCmdUtils()
        self.dns_server_name = "ammeonvpn.com"
        self.nslookup_cmd = "/usr/bin/nslookup"
        self.ntp_pkg = 'ntp1'
        self.ntp_stat_cmd = "/usr/bin/ntpstat"
        self.ntp_alias = "ntp-alias-1"
        self.ms_node = self.get_management_node_filename()
        self.targets = self.get_managed_node_filenames()
        self.targets.append(self.ms_node)
        # set up required test item
        self.ntp_alias_ip = test_constants.NTP_SERVER_IP
        self.peer_paths = self.find(self.ms_node, "/deployments", "node", True)
        # Source of .rpm to use
        self.rpm_path = os.path.join(
            test_constants.LITP_DEFAULT_OS_PROFILE_PATH,
            "Packages", "gnome-bluetooth-2*x86_64*")

        self.ms_url_path = "newRepo_dir"
        self.rpm_repo_dir = (test_constants.PARENT_PKG_REPO_DIR +
                             self.ms_url_path)
        self.rpm_repo_name = "new_repo_name"
        self.rpm_source_path = "/tmp/gnomebluetooth.rpm"
        self.gnomebluetooth_pkg = 'gnome-bluetooth'

        # Get all software-items
        self.items_path = ("/software/items" + "/" + self.gnomebluetooth_pkg)
        # Group each node to its specific litp path
        self.node_path = dict(
            [(self.get_node_filename_from_url(self.ms_node, peer_path),
              peer_path) for peer_path in self.peer_paths])
        self.test_passed = False

    def tearDown(self):
        """
        Runs after every test
        """
        self.log("info", "Beginning custom teardown/cleandown")
        if not self.test_passed:
            super(ImportPackages, self).tearDown()

    def put_rpm_on_ms(self):
        """ Copy RPMs to the MS """
        return self.cp_file_on_node(
            self.ms_node,
            self.rpm_path,
            self.rpm_source_path, su_root=True, add_to_cleanup=False)

    def get_path_url(self, path, resource):
        """
        Description:
            Gets the url path
        Actions:
            1. Perform find command
            2. Return item
       Results:
           Returns the path url for the current environment
        """
        # 1 RUN FIND
        profile_path = self.find(self.ms_node, path, resource, False)

        # 2 RETURN ITEM
        return profile_path[0]

    def create_yum_repo(self, repo_path, repo_name, repo_id):
        """
        Find URL in model for yum repositorys
        Create and run CLI to add yum-repositorys to MS
        Create and run CLI to add yum-repositorys to node
        """

        sw_items = "/software/items"
        ms_items = self.find(self.ms_node, "/ms",
                             "ref-collection-of-software-item",
                             exact_match=True)

        sw_items_url = sw_items + repo_id
        ms_items_url = ms_items[0] + repo_id

        # Create the directory for the REPO on the MS
        self.create_dir_on_node(self.ms_node, self.rpm_repo_dir, su_root=True,
                                add_to_cleanup=False)

        # Create and run CLI to add yum-repositorys to MS
        props = ("name='" + repo_name + "' ms_url_path=/" + repo_path)
        self.execute_cli_create_cmd(
            self.ms_node, sw_items_url,
            "yum-repository", props, add_to_cleanup=False)

        #self.execute_cli_link_cmd(self.ms_node, ms_items_url,
        #                        "yum-repository", props, add_to_cleanup=False)
        self.execute_cli_inherit_cmd(self.ms_node, ms_items_url, sw_items_url,
                                     add_to_cleanup=False)

        # Create and run CLI to add yum-repositorys to node
        for node_url in self.peer_paths:
            node_sw_items_url = self.find(self.ms_node, node_url,
                                          "ref-collection-of-software-item",
                                          exact_match=True)
            items_id = node_sw_items_url[0] + repo_id
            #self.execute_cli_link_cmd(self.ms_node, items_id,
            #                    "yum-repository", props, add_to_cleanup=False)
            self.execute_cli_inherit_cmd(self.ms_node, items_id, sw_items_url,
                                         add_to_cleanup=False)

    def add_package(self, package, repo):
        """
        Create CLI to create a package to install from a Repo
        Create CLI for to inherit this package to nodes
        Run CLI to add Packages
        """
        # Create a Package & add to cmd list
        props = ('name=' + package + " repository=" + repo)

        self.execute_cli_create_cmd(self.ms_node, self.items_path,
                                    'package', props, add_to_cleanup=False)

        # Create CLI for to inherit this package to node
        for path in self.node_path.itervalues():
            props = 'name=' + package
            path = path + "/items/" + package

            #self.execute_cli_link_cmd(self.ms_node, path, 'package', props)
            self.execute_cli_inherit_cmd(self.ms_node, path, self.items_path,
                                         add_to_cleanup=False)

    def _get_dns_search_value(self, dns_url):
        """    _get_dns_search_value    """
        get_data_cmd = self.cli.get_show_data_value_cmd(dns_url, "search")

        stdout, _, _ = self.run_command(self.ms_node, get_data_cmd)
        if stdout:
            return stdout[0]
        else:
            return None

    def install_ntp_service(self):
        """
        Description:
            Positive test for checking the ntp-service.
        Actions:
            1. Create the ntp-service
            2. Create and set the ntp-server under ntp-service
            3. Create links for ms and peer nodes to ntp-service
        Results:
            The ntp-service should be up and running on ms and peer nodes.
        """
        # Get test environment info
        ntp_server = 'server0'
        items_path = self.get_path_url("/software", "software-item")
        ms_config_path = self.get_path_url("/ms", "node-config")
        ms_alias_config_path = ms_config_path + '/alias_config'
        ms_aliases_path = ms_alias_config_path + '/aliases'
        peer_alias_path = '/configs/alias_config/aliases/ntp-alias-1'
        #Define the node which already has alias-config in the CDB
        aliased_node = '/c1/nodes/n1'

        # Get peer node1/peer node2 litp paths present in litp tree
        peer_paths = self.find(self.ms_node, "/deployments", "node", True)
        node_path = dict([(self.get_node_filename_from_url(
            self.ms_node, peer_path), peer_path) for peer_path in peer_paths])
        peer_nodes = node_path.keys()

        self.assertNotEqual([], peer_nodes)

        # Create the ntp-service software-item package
        cmd_list = list()

        # Create the NTP Alias
        #props = "alias_names='{0}' address='{1}'".format(self.ntp_alias,
        #                                                 self.ntp_alias_ip)
        #cmd_list.append(self.cli.get_create_cmd(ms_aliases_path +
        #                                        '/' + self.ntp_alias,
        #                                        'alias', props))

        # Create the ntp server under ntp-service
        props = "server='{0}'".format(self.ntp_alias)
        cmd_list.append(self.cli.get_create_cmd(items_path + '/' +
                                                self.ntp_pkg + '/servers/' +
                                                ntp_server,
                                                'ntp-server', props))

        # Create the NTP Alias
        props = "alias_names='{0}' address='{1}'".format(self.ntp_alias,
                                                         self.ntp_alias_ip)
        cmd_list.append(self.cli.get_create_cmd(ms_aliases_path +
                                                '/' + self.ntp_alias,
                                                'alias', props))

        # Configure peer nodes with alias and ntp service
        for path in node_path.itervalues():

            if aliased_node not in path:
                # Create an alias config for each peer node
                cmd_list.append(self.cli.get_create_cmd(path +
                                '/configs/alias_config', 'alias-node-config'))

            # Create an alias for the NTP server for each peer node
            cmd_list.append(self.cli.get_create_cmd(path + peer_alias_path,
                                                'alias', props))
            # Inherit ntp service to peer nodes
            cmd_list.append(self.cli.get_inherit_cmd(path + '/items/' +
                                                     self.ntp_pkg,
                                                     items_path + '/' +
                                                     self.ntp_pkg))

        # Check that the commands can be entered without error
        cmd_results = self.run_commands(self.ms_node, cmd_list)
        self.assertEqual([], self.get_errors(cmd_results))
        self.assertTrue(self.is_std_out_empty(cmd_results),
                        "Error std_out is not empty.")

    def add_ntp_server(self):
        """
        Description:
            Function to add an additional server below the
            existing ntp-services.
        """
        # CREATE NEW NTP ALIAS FOR SECONDARY NTP SERVER
        self.add_secondary_ntp_aliases()
        services_paths = \
        self.find(self.ms_node, "/software", "ntp-service")

        for service in services_paths:
            url = service + "/servers/funct_ntp_test_addition"
            props = "server='ntp-alias-2'"
            self.execute_cli_create_cmd(self.ms_node, url, 'ntp-server',
                                        props, add_to_cleanup=False)

    def add_secondary_ntp_aliases(self):
        """
        Description:
            Adds a new alias object to the MS and each node for the
            secondary NTP server.
        """
        peer_node_suffix = "/configs/alias_config/aliases/ntp-alias-2"
        props = \
        "alias_names=\"ntp-alias-2\" address=\"{0}\"".format(
                                 test_constants.NTP_SERVER_IP_SECONDARY)

        # CREATE NEW NTP ALIAS FOR SECONDARY NTP SERVER ON THE NODES
        nodes = self.get_managed_node_filenames()
        for node in nodes:
            # GET URL OF NODE
            node_url = self.get_node_url_from_filename(self.ms_node, node)
            # Create an alias for the NTP server for the peer node
            alias_url = node_url + peer_node_suffix
            self.execute_cli_create_cmd(self.ms_node, alias_url,
                                        'alias', props, add_to_cleanup=False)

        # CREATE NEW NTP ALIAS FOR SECONDARY NTP SERVER ON MS
        ms_config_path = self.get_path_url("/ms", "node-config")
        ms_alias_config_path = \
        ms_config_path + '/alias_config/aliases/ntp-alias-2'
        self.execute_cli_create_cmd(self.ms_node, ms_alias_config_path,
                                    'alias', props,
                                    add_to_cleanup=False)

    def update_dns_client(self):
        """
        Description:
            Positive test for updating dns client on ms and peer nodes.
        Actions:
            1. Update the dns client by adding a new dns under search property
        Results:
            The dns client should be updated on ms and peer nodes.
        """
        cmd_list = list()

        # Get test environment info
        ms_dns_client_path = self.find(self.ms_node, "/ms",
                                       "dns-client", True)[0]
        self.log('info', 'ms_dns_client_path')
        self.log('info', ms_dns_client_path)
        # Get peer nodes litp paths present in litp tree
        peer_paths = self.find(self.ms_node, "/deployments", "node", True)
        node_dns_paths = self.find(self.ms_node, "/deployments",
                                   "dns-client", True)
        #node1_dns_client_path = node_dns_paths[0]
        #node2_dns_client_path = node_dns_paths[1]
        #node3_dns_client_path = node_dns_paths[2]
        #node4_dns_client_path = node_dns_paths[3]

        node_path = dict([(self.get_node_filename_from_url(
            self.ms_node, peer_path), peer_path) for peer_path in peer_paths])
        peer_nodes = node_path.keys()

        self.assertNotEqual([], peer_nodes)
        node_dns_paths.append(ms_dns_client_path)
        for item in node_dns_paths:
            node = self._get_dns_search_value(item)
            self.assertNotEqual(None, node)
            # UDATE THE DNS CLIENT ON NODE
            props = "search='{0},{1}'".format(self.dns_server_name, node)
            cmd_list.append(self.cli.get_update_cmd(item, props))

        # Check that the commands can be entered without error
        cmd_results = self.run_commands(self.ms_node, cmd_list)
        self.assertEqual([], self.get_errors(cmd_results))
        self.assertTrue(self.is_std_out_empty(cmd_results),
                        "Error std_out is not empty.")

    def add_dns_nameserver(self):
        """
        Description:
            Function to add extra nameserver below all dns clients.
        """
        # GET URL OF DNS OBJECT ON THE MS.
        ms_dns_client_path = self.find(self.ms_node, "/ms",
                                       "dns-client", True)[0]
        self.log('info',
                 'ms_dns_client_path: {0}'.format(ms_dns_client_path))

        # ADD NEW NAMESERVER BELOW THE DNS CLIENT ON THE MS.
        self.create_nameserver_below_dns_objs([ms_dns_client_path])

        # GET URLS OF DNS OBJECTS ON THE NODES.
        node_dns_paths = \
        self.find(self.ms_node, "/deployments",
                  "dns-client", True)

        for node_dns_path in node_dns_paths:
            self.log('info',
                     'node_dns_path: {0} \n'.format(node_dns_path))

        # ADD NEW NAMESERVER BELOW THE DNS CLIENT ON THE NODES.
        self.create_nameserver_below_dns_objs(node_dns_paths)

    def create_nameserver_below_dns_objs(self, node_dns_paths):
        """
        Description:
            Creates a new nameserver below each dns object
            supplied to the function.
        Args:
            node_dns_paths (list): Urls to the MS/node object
                                   below which the nameserver
                                   shall be created.
        """
        for dns_obj in node_dns_paths:
            number_of_children = \
            self.get_num_child_objs(dns_obj + "/nameservers",
                                    'nameserver')
            new_namesrvr_path = \
            dns_obj + "/nameservers/funct_test_08_namesrvr"
            position = number_of_children + 1
            props = \
            "ipaddress={0} position={1}".format(
                            test_constants.NTP_SERVER_IP_SECONDARY,
                            position)
            self.execute_cli_create_cmd(self.ms_node, new_namesrvr_path,
                                        'nameserver', props,
                                        add_to_cleanup=False)

    def get_num_child_objs(self, path, object_type):
        """
        Description:
            Ascertains the numbers of child objects
            below the specified path.
        Args:
            path (str):    Path to the object to be queried.
            object_type (str):     The object type to count.
        Returns:
            int. the number of child objects.
        """
        children = self.find(self.ms_node, path, object_type)
        return len(children)

    def check_dns_updates(self):
        """
        # Check that the new dns client nameserver was added
        # in /etc/resolv.conf
        """
        resolv_conf = "/etc/resolv.conf"
        cmd = RHCmdUtils().get_grep_file_cmd(
            resolv_conf, self.dns_server_name, '-i')

        # Run grep command
        grep_std_out, std_err, ret_code = self.run_command(self.ms_node, cmd,
                                                           su_root=True)
        self.assertNotEqual([], grep_std_out)
        self.assertEqual([], std_err)
        self.assertEqual(
            0, ret_code, "'{0}' not found in '{1}'on '{2}'".format(
                self.dns_server_name, resolv_conf, self.ms_node))

        for node in self.targets:
            cmd = RHCmdUtils().get_grep_file_cmd(resolv_conf,
                                                 self.dns_server_name,
                                                 '-i')
            # Run grep command
            grep_std_out, std_err, ret_code = self.run_command(node, cmd,
                                                               su_root=True)
            self.assertNotEqual([], grep_std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, ret_code, "'{0}' not found in '{1}'"
                             " on {2}".format(self.dns_server_name,
                                              resolv_conf, node))

    def check_dns_client(self):
        """
        Description:
            Test for checking that MS and Peer Nodes have the correct
            dns client setup.
        Actions:
            1. Run nslookup command on ms and peer nodes.
            2. Check the return code of the command.
        Results:
            The MS and Peer Nodes should have the dns clients
            correctly configured.
        """
        self.log('info', "Beginning DNS service checks.")
        # Get test environment info
        # Get peer node1/peer node2 litp paths present in litp tree
        dns_server_ip = "10.44.86.4"
        nslookup_host = "dns.ammeonvpn.com"
        peer_paths = self.find(self.ms_node, "/deployments", "node", True)
        node_path = dict([(self.get_node_filename_from_url(
            self.ms_node, peer_path), peer_path) for peer_path in peer_paths])
        peer_nodes = node_path.keys()

        self.assertNotEqual([], peer_nodes)

        # CHECK THE MS
        self.log('info', "Querying DNS status on MS via hostname.")
        std_out, std_err, rcode = self.run_command(self.ms_node,
                                                   self.nslookup_cmd + ' ' +
                                                   nslookup_host)
        self.assertNotEqual([], std_out)
        self.assertEqual([], std_err)
        self.assertEqual(0, rcode)
        # CHECK DNS IP IS RETURNED WHEN RUNNING "nslookup" AGAINST DNS SERVER
        self.log('info',
                 "Ensuring that DNS IP address reported in status was " \
                 "that specified.")
        self.assertTrue(
            self.is_text_in_list(str(dns_server_ip), std_out),
            "IP Address returned does not match the expected dns server ip.")
        self.log('info', "Check passed.")

        self.log('info', "Querying DNS status on MS via IP address.")
        std_out, std_err, rcode = self.run_command(self.ms_node,
                                                   self.nslookup_cmd + ' ' +
                                                   dns_server_ip)
        self.assertNotEqual([], std_out)
        self.assertEqual([], std_err)
        self.assertEqual(0, rcode)
        # CHECK DNS SERVER NAME IS RETURNED WHEN RUNNING "nslookup" AGAINST
        # DNS SERVER IP
        self.log('info',
                 "Ensuring that DNS hostname reported in status was " \
                 "that specified.")
        self.assertTrue(
            self.is_text_in_list(str(nslookup_host), std_out),
            "Server name returned does not match expected dns server name.")
        self.log('info', "Check passed.")

        self.log('info', "Executing DNS service checks on nodes.")
        for path in peer_paths:
            node = self.get_node_filename_from_url(self.ms_node, path)
            # CHECK DNS IP IS RETURNED WHEN RUNNING "nslookup"
            # AGAINST DNS SERVER
            self.log('info',
                     "Querying DNS status on {0} via hostname.".format(node))
            std_out, std_err, rcode = \
                self.run_command(node, self.nslookup_cmd + ' ' +
                                 nslookup_host)
            self.assertNotEqual([], std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, rcode)
            # CHECK DNS IP IS RETURNED WHEN RUNNING "nslookup"
            # AGAINST DNS SERVER
            self.log('info',
                     "Ensuring that DNS IP address reported in status was " \
                     "that specified.")
            self.assertTrue(
                self.is_text_in_list(str(dns_server_ip), std_out),
                "IP Address returned does not match expected dns server ip.")
            self.log('info', "Check passed.")

            # CHECK DNS SERVER IS RETURNED WHEN RUNNING "nslookup"
            # AGAINST DNS IP
            self.log('info',
                     "Ensuring that DNS hostname reported in status was " \
                     "that specified.")
            std_out, std_err, rcode = \
                self.run_command(node, self.nslookup_cmd + ' ' +
                                 dns_server_ip)
            self.assertNotEqual([], std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, rcode)
            # CHECK DNS SERVER NAME IS RETURNED WHEN RUNNING "nslookup"
            # AGAINST DNS SERVER IP
            self.assertTrue(
                self.is_text_in_list(str(self.dns_server_name), std_out),
                "Server name does not match expected dns server name.")
            self.log('info', "Check passed.")

    def check_ntp_service(self):
        """
        Description:
            Test for checking that MS and Peer Nodes are syncronized with the
            NTP Server.
        Actions:
            1. Run ntpstat command on ms and peer nodes.
            2. Check the return code of the command.
            3. Check that ntpstat server matches the ntp server defined
            4. Check that the sync is of a reasonable range
        Results:
            The NTP on MS and Peer Nodes should be syncronized with the
            NTP Servers defined by LITP CLI.
        """
        self.log('info', "Beginning NTP service checks.")
        sync_range_max = 1024
        sync_poll_max = 2048
        ms_path = "/ms"

        # Get test environment info
        # Get peer node1/peer node2 litp paths present in litp tree
        peer_paths = self.find(self.ms_node, "/deployments", "node", True)
        node_path = \
            dict([(self.get_node_filename_from_url(self.ms_node, peer_path),
                   peer_path) for peer_path in peer_paths])
        peer_nodes = node_path.keys()

        self.assertNotEqual([], peer_nodes)

        # CHECK THE MS
        self.log('info', "Executing NTP service checks on MS.")
        ntp_inherit = self.find(self.ms_node, ms_path,
                                "reference-to-ntp-service")[0]
        ntp_path = self.execute_show_data_cmd(self.ms_node,
                                              ntp_inherit,
                                              'inherited from')
        server_paths = self.find(self.ms_node,
                                 ntp_path,
                                 "ntp-server")
        self.log('info', "Gathering specified NTP servers on MS.")
        allowed_servers = []
        for server in server_paths:
            allowed_servers.append(self.execute_show_data_cmd(self.ms_node,
                                                              server,
                                                              "server"))
        # Get the IPs from /etc/hosts
        self.log('info',
                 "Gathering NTP servers IP addresses from /etc/hosts on MS.")
        allowed_servers_ips = []
        allowed_servers_ips.append("local")  # local is allowed ntp server
        for server in allowed_servers:
            stdout, stderr, rcode = self.run_command(
                self.ms_node, self.rhcmd.get_grep_file_cmd(
                    test_constants.ETC_HOSTS, server))
            self.assertEqual(0, rcode)
            self.assertEqual([], stderr)
            self.assertNotEqual([], stdout)
            server_ip = stdout[0].split()[0]
            allowed_servers_ips.append(server_ip)

        self.log('info', "Querying NTP status on MS.")
        std_out, std_err, rcode = self.run_command(self.ms_node,
                                                   self.ntp_stat_cmd)

        self.assertNotEqual([], std_out)
        self.assertEqual([], std_err)
        self.assertEqual(0, rcode)

        # Check that the NTP Server returned matches the one defined by
        # litp cli
        self.log('info',
                 "Ensuring that NTP server reported in status was " \
                 "that specified in LITP.")
        server_match = False
        for server_identifier in allowed_servers_ips:
            if self.is_text_in_list(server_identifier, std_out):
                server_match = True
                break
        self.assertTrue(server_match, "Running ntpstat on MS : IP does not "
                        "match the server defined in LITP CLI.")
        self.log('info',
                 "NTP server Check passed on MS. " \
                 "NTP server is as specified in LITP.")

        # Check that the sync is of a reasonable range
        self.log('info',
                 "Ensuring that NTP on MS is operating within " \
                 "acceptable range & poll tolerances.")
        sync_range = int(re.findall(r'\d+', std_out[1])[0])
        sync_poll = int(re.findall(r'\d+', std_out[2])[0])
        self.log('info', "MS NTP sync range: {0}".format(sync_range))
        self.log('info', "MS NTP sync poll: {0}".format(sync_poll))

        self.assertTrue(sync_range < sync_range_max,
                        "Sync range is not valid")
        self.assertTrue(sync_poll < sync_poll_max,
                        "Sync poll is not valid")
        self.log('info',
                 "NTP server Check passed. NTP server is operating " \
                 "within allowable range and polling time on MS.")

        # CHECK LITP NODES ARE IN SYNC WITH A SERVER ALLOWED BY THE LITP MODEL
        self.log('info', "Executing NTP service checks on nodes.")
        for path in peer_paths:
            node = self.get_node_filename_from_url(self.ms_node, path)
            self.log('info', "Querying NTP status on {0}.".format(node))
            std_out, std_err, rcode = \
                self.run_command(node, self.ntp_stat_cmd)

            self.assertNotEqual([], std_out)
            self.assertEqual([], std_err)
            self.assertEqual(0, rcode)

            # Check that the NTP Server returned matches the IP of a server
            # defined in the model
            self.log('info',
                     "Ensuring that NTP server reported in status " \
                     "matches an IP address gathered from the LITP model.")
            server_match = False
            for server_identifier in allowed_servers_ips:
                if self.is_text_in_list(str(server_identifier), std_out):
                    server_match = True
                    break
            self.assertTrue(server_match, "ntpstat does not match NTP "\
                                           "server IPs in the model.")
            self.log('info',
                 "NTP server Check passed on {0}. " \
                 "NTP server is as specified in LITP.".format(node))

            self.log('info',
                     "Ensuring that NTP on {0} is operating within " \
                     "acceptable range & poll tolerances.".format(node))
            sync_range = int(re.findall(r'\d+', std_out[1])[0])
            sync_poll = int(re.findall(r'\d+', std_out[2])[0])
            self.log('info',
                     "{0} NTP sync range: {1}".format(node, sync_range))
            self.log('info',
                     "{0} NTP sync poll: {1}".format(node, sync_poll))

            self.assertTrue(sync_range < sync_range_max,
                            "Sync range is not valid")
            self.assertTrue(sync_poll < sync_poll_max,
                            "Sync poll is not valid")
            self.log('info',
                     "NTP server Check passed. NTP server is operating " \
                     "within allowable range and " \
                     "polling time on {0}.".format(node))

    def check_pkt_installed(self, pkg, node):
        """
        Check if a package is installed on a node
        """
        cmd = self.rhcmd.get_grep_file_cmd(" ", "Installed",
                                           file_access_cmd="yum list "
                                           + pkg)
        _, _, rcode = self.run_command(node, cmd, su_root=True)
        # Add message to failed list.
        self.assertTrue(rcode == 0, pkg + " Pakage not found on " + node)

    def check_repo_setup(self, repo, node):
        """
        Check if a package is installed on a node
        """
        cmd = self.rhcmd.get_grep_file_cmd(" ", repo,
                                           file_access_cmd="yum repolist")
        _, _, rcode = self.run_command(node, cmd, su_root=True)
        # Add message to failed list.
        self.assertTrue(rcode == 0, repo + " Repo not found on " + node)

    @attr('all', 'non-revert', 'functional', 'P1', 'functional_tc01')
    def test_01_initial_ntp_dns_import_install_rpm(self):
        """
        Description:
            Test for checking the ntp-service.
            Test for updating dns client on ms and peer nodes.
            Test creation and function of a new repo.
            Assumes NTP is already configured on the MS
        Actions:
            1. Create the ntp-service
            2. Create and set the ntp-server under ntp-service
            3. Create links for ms and peer nodes to ntp-service
            4. Update the dns client by adding a new dns under search property
            5. Create a new yum REPO
            6. Copy an RPM into tmp dir
            7. Import .rpm into new repo
            8. Install package from new repo to nodes
            9. Re-order all clusters depdendency_list values (reverted)
            10. Run checks to confirm success.
        Results:
            The ntp-service should be up and running on ms and peer nodes.
            A package from a new repo should be installed on nodes
        """
        # Allow teardown to detect if test has passed
        self.test_passed = False

        install_package = False
        add_yum_repo = False
        rpm_repo_id = "/new_repo_id"
        # Configure NTP
        self.log('info', "Configure the NTP Service")
        self.install_ntp_service()

        # Configure DNS
        self.log('info', "Configure the DNS service")
        self.update_dns_client()

        # Create a new yum REPO
        self.log('info', "Create a new yum repo")
        self.create_yum_repo(self.ms_url_path, self.rpm_repo_name,
                             rpm_repo_id)

        # Copy an RPM into dir
        self.log('info', "Copy RPM onto the MS")
        self.put_rpm_on_ms()

        # Import .rpm into new repo
        self.log('info', "Import the RPM into the REPO")
        self.execute_cli_import_cmd(self.ms_node, self.rpm_source_path,
                                    self.rpm_repo_dir)

        # Install package from new repo to nodes
        self.log('info', "install the package on the managed nodes")
        self.add_package(self.gnomebluetooth_pkg, self.rpm_repo_name)
        # Run change_cluster_dependency_list method from imported Class
        #self.change_cluster_dependency_list(self.ms_node)

        #CREATE PLAN
        self.execute_cli_createplan_cmd(self.ms_node)
        # SHOW PLAN
        show_plan = self.execute_cli_showplan_cmd(self.ms_node)
        # RUN PLAN
        self.execute_cli_runplan_cmd(self.ms_node)
        # Check if plan completed successfully
        completed_successfully = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=50)
        self.assertTrue(completed_successfully, "Plan was not successful")

        self.check_dns_updates()
        # Check install package and add yum repositorys in plan
        for item in show_plan[0]:
            # self.log('info', item)
            if "Install package" in item:
                install_package = True
            if "Add yum repository" in item:
                add_yum_repo = True

        self.assertTrue(install_package, "package was not installed")
        self.assertTrue(add_yum_repo, "repo was not added in plan")

        for node in self.targets:
            if node != self.ms_node:  # Packages not installed on nodes
                self.check_pkt_installed(self.gnomebluetooth_pkg, node)
                self.check_repo_setup(self.rpm_repo_name, node)

        # Check package was installed on node
        cmd = self.rhcmd.check_pkg_installed([self.gnomebluetooth_pkg])
        for node in self.node_path:
            stdout, stderr, rcode = self.run_command(node, cmd)
            self.assertEqual(rcode, 0,
                             "package {0} was not installed on {1} peer node."
                             .format(self.gnomebluetooth_pkg, str(node)))
            self.assertEqual(stderr, [], "stderr is not empty")
            self.assertNotEqual(stdout, [], "stdout is not empty.")
            self.log('info', '{0} was installed on {1} peer node'
                     .format(self.gnomebluetooth_pkg, str(node)))

        # Allow teardown to detect if test has passed
        self.test_passed = True

    @attr('all', 'non-revert', 'functional', 'P1', 'functional_tc08')
    def test_08_create_new_ntp_server_and_dns_nameserver(self):
        """
        Description:
            Test for adding a new dns nameserver.
            Test for adding a new server to the NTP.

        Actions:
            1. Below the DNS client on the MS and the nodes
               create a new nameserver.
            2. Below all found ntp services create a
               new ntp server.
            3. Create a plan for deployment.
            4. Execute a show of the plan.
            5. Execute the plan.
        Results:
            The new DNS and NTP objects are deployed
            successfully.
        """
        # Allow teardown to detect if test has passed
        self.test_passed = False

        self.log('info', "#1 Below the DNS client on " \
                         "the MS and the nodes create " \
                         "a new nameserver.")
        self.add_dns_nameserver()

        self.log('info', "#2 Below all found ntp " \
                         "services create a new " \
                         "ntp server.")
        self.add_ntp_server()

        self.log('info', "#3 Issue the create_plan command.")
        self.execute_cli_createplan_cmd(self.ms_node)

        self.log('info', "#4 View the created plan.")
        self.execute_cli_showplan_cmd(self.ms_node)

        self.log('info',
                 "#5 Execute the plan, and wait for " \
                 "its successful completion.")
        self.execute_cli_runplan_cmd(self.ms_node)
        completed_successfully = self.wait_for_plan_state(
                                        self.ms_node,
                                        test_constants.PLAN_COMPLETE,
                                        timeout_mins=30)
        self.assertTrue(completed_successfully, "Plan was not successful")

        # Allow teardown to detect if test has passed
        self.test_passed = True

    @attr('all', 'non-revert', 'functional', 'P1', 'functional_tc99')
    def test_final_check_ntp(self):
        """
        Description:
            Test that MS and Peer Nodes are syncronized with the NTP Server.
        Actions:
            1. Run ntpstat command on ms and peer nodes.
            2. Check the return code of the command.
            3. Check that ntpstat server matches the ntp server defined
            4. Check that the sync is of a reasonable range
        Results:
            The NTP on MS and Peer Nodes should be syncronized with the
            NTP Servers defined by LITP CLI.
        """
        # Allow teardown to detect if test has passed
        self.test_passed = False

        self.check_ntp_service()

        # Allow teardown to detect if test has passed
        self.test_passed = True

    def obsolete_final_check_ntp_dns_client(self):
        """
        Description:
            Test that MS and Peer Nodes have the correct dns client setup
            Test that MS and Peer Nodes are syncronized with the NTP Server
            Temporarily obsoleted due to DNS Server issues (CIS-55528)
        Actions:
            1. Run nslookup command on ms and peer nodes.
            2. Check the return code of the command.
            3. Run ntpstat command on ms and peer nodes.
            4. Check the return code of the command.
            5. Check that ntpstat server matches the ntp server defined
            6. Check that the sync is of a reasonable range
        Results:
            The MS & Peer Nodes have the dns clients correctly configured.
            The NTP on MS and Peer Nodes should be syncronized with the
            NTP Servers defined by LITP CLI.
        """
        # Allow teardown to detect if test has passed
        self.test_passed = False

        self.check_dns_client()
        self.check_ntp_service()

        # Allow teardown to detect if test has passed
        self.test_passed = True
