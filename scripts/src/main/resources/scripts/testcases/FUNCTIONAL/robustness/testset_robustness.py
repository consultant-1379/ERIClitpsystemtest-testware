#!/usr/bin/env python
'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     February 2016
@author:    Messers
@summary:   ST Test Suite to verify Robustness KPI TCs
'''

from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
from litp_cli_utils import CLIUtils
import test_constants
import time
import sys
import socket
import exceptions
import os


class ROBRUN(GenericTest):
    """
    Description:
        This set of tests is checking the robustness of the
        system when different services are restarted
    """
    def setUp(self):
        """
        Runs before every single test
        """

        super(ROBRUN, self).setUp()

        self.redhat = RHCmdUtils()
        self.ms_node = self.get_management_node_filename()
        self.cli_utils = CLIUtils()
        # Get list of available nodes
        self.targets = self.get_managed_node_filenames()
        # self.target will always be cluster 1 node 1
        # self.target = self.targets[0]
        # Get paths for available nodes
        self.peer_paths = self.find(self.ms_node,
          "/deployments/", "node", True)
        # self.target_url will get path of cluster 1 node 1
        # self.target_url = self.peer_paths[0]
        self.ms_path = "/ms"
        self.timeout_mins = 30
        self.litpd_stop_timeout_secs = 180

        self.model_info = self.get_model_names_and_urls()

        for cluster in self.model_info["clusters"]:
            if len(cluster["nodes"]) > 1:
                self.cluster_url = cluster["url"]
                self.peer_nodes = cluster["nodes"]

        self.target = self.peer_nodes[0]["name"]
        self.target_url = self.peer_nodes[0]["url"]
        self.postgres_service_name = test_constants.PSQL_SERVICE_NAME

        # Check litpd service status at the start of every test
        self.get_service_status(self.ms_node, "litpd", assert_running=False)
        # List of MS only services
        self.ms_only = ["litpd", "rabbitmq-server", self.postgres_service_name,
                        "puppetdb"]

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Actions:
            1. Perform Test Cleanup
            2. Call superclass teardown
        Results:
            Items used in the test are cleaned up and the
            super class  prints out end test diagnostics
        """
        super(ROBRUN, self).tearDown()

    def chk_individual_litp_running(self):
        """
        Function to check that only a single instance of the
        LITP service is running.
        """
        litp_file_name = test_constants.LITP_SERVICE_FILE_NAME
        grep_cmd = self.redhat.grep_path
        ps_cmd = self.redhat.get_ps_cmd("-ef")
        complete_cmd = \
        ps_cmd + " | {0} {1} | {0} -v grep".format(grep_cmd,
                                                   litp_file_name)
        # ASSERT THAT THERE IS ONLY A SINGLE INSTANCE OF LITP RUNNING
        stdout, _, _ = \
        self.run_command(self.ms_node, complete_cmd, su_root=True)
        length = len(stdout)
        self.assertTrue(length == 1,
                        "A single instance of LITP should be running, " \
                        "but {0} instances were found.".format(length))

    def _up_time(self, node):
        """
            Get uptime of node using cat on /proc/uptime
            Return up_time in seconds
        """
        cmd = self.redhat.get_cat_cmd('/proc/uptime')
        out, err, ret_code = self.run_command(node, cmd, su_root=True)
        self.assertEqual(0, ret_code)
        self.assertEqual([], err)
        self.assertNotEqual([], out)
        uptime_seconds = float(out[0].split()[0])
        return uptime_seconds

    def _litp_up(self):
        """
            Verify that the litpd service is running on the MS
        """
        litp_up = False
        max_duration = 300
        elapsed_sec = 0

        while elapsed_sec < max_duration:
            try:
                out, _, ret_code = self.execute_cli_show_cmd(
                    self.ms_node, "/deployments"
                )

                self.assertEqual(0, ret_code)
                self.assertNotEqual([], out)

                if self.is_text_in_list("collection-of-deployment", out):
                    self.log("info", "Litp is up")
                    litp_up = True
                    break
                else:
                    self.log("info", "Litp is not up.")

            except (socket.error, exceptions.AssertionError):
                self.log("info", "Litp is not up after {0} seconds"
                         .format(elapsed_sec))
            except:
                self.log("error", "LITP up check. Unexpected Exception: {0}"
                         .format(sys.exc_info()[0]))
            time.sleep(10)
            elapsed_sec += 10

        if not litp_up:
            self.log("error", "Litp is not up in last {0} seconds."
                     .format(str(max_duration)))
        return litp_up

    def _create_package(self,
                        package_name,
                        version=None,
                        release=None,
                        expected_state=True,
                        do_cleanup=True):
        """
        Description:
            Create test package
        Args:
            package_name (str): package name
            expected_state (bool): If True expect positive is True
                                   if False expect positive is False
        Actions:
            1. Get software items collection path
            2. Create test package
        Results:
            stdmsg, stderr
        """
        # 1. Get items path
        items = self.find(self.ms_node, "/software", "software-item", False)
        items_path = items[0]

        # 2. Create a package with cli
        package_url = items_path + "/" + package_name
        props = "name='{0}'".format(package_name)
        if version:
            props += " version={0}".format(version)
        if release:
            props += " release={0}".format(release)

        self.execute_cli_create_cmd(
            self.ms_node,
            package_url,
            "package",
            props,
            args="",
            expect_positive=expected_state,
            add_to_cleanup=do_cleanup)

        return package_url

    def _create_package_inheritance(self, node_url, package_name, package_url,
                                    do_cleanup=True):
        """
        Description:
            Create package inheritance on the test node.
        Args:
            node_url (str): node url
            package_name (str): package name
            package_url (str): package software url
        Actions:
            1. Create package inheritance using CLI.
        Results:
            Path in litp tree to the created package inheritance.
        """
        # 1. Inherit package with cli
        node_package_url = node_url + "/items/{0}".format(package_name)
        self.execute_cli_inherit_cmd(self.ms_node,
                                     node_package_url,
                                     package_url,
                                     add_to_cleanup=do_cleanup)
        return node_package_url

    def stop_puppet_if_service_enforced(self, service, ms_only):
        """
        Description:
            Stops puppet on the last unlock task if the service is enforced
            by puppet
        Args:
            service (str) = the service you want to stop
            ms_only = list of ms_only services
        """

        puppet_stop_node_list = []
        phase_num = 0
        task_num = 0
        # Execute show_plan
        std_out, _, _ = self.execute_cli_showplan_cmd(self.ms_node)

        # Parse plan output into dictionary
        plan_dict = self.cli.parse_plan_output(std_out)
        # Get the task description for the last unlock task in the plan
        for key_num in sorted(plan_dict.keys(), reverse=True):
            desc = "Unlock VCS on node"
            for task in sorted(plan_dict[key_num].keys(), reverse=True):
                if any(desc in taskd for taskd in
                       plan_dict[key_num][task]["DESC"]):
                    # The number of the phase that the task is in
                    phase_num = int(key_num)
                    # The number of the task within that phase
                    task_num = int(task)
                    break

            else:
                continue
            break
        self.assertFalse(phase_num == 0, "Unlock task phase has not been "
                                         "found")
        # String of unlock task description to wait for
        unlock_task_desc = (self.cli.get_task_desc(
            std_out, phase_num, task_num))[1]

        # Wait for the last unlock task in the plan
        self.wait_for_task_state(
            self.ms_node,
            unlock_task_desc,
            test_constants.PLAN_TASKS_RUNNING,
            seconds_increment=1, ignore_variables=False)

        # Add MS to list of nodes with puppet stopped
        puppet_stop_node_list.append(self.ms_node)
        self.log("info", "{0} is enforced by puppet. Stopping puppet "
                         "on node {1}".format(service, self.ms_node))
        # Stop puppet service on the MS
        self.stop_service(self.ms_node, "puppet")
        # Only stop puppet on peer nodes if service that is enforced is
        # present on peer nodes
        if service not in ms_only:
            for node in self.peer_nodes[0:2]:
                # Stop puppet service on the peer node if service is
                # enforced by puppet
                # Add peer node to list of nodes with puppet stopped
                puppet_stop_node_list.append(node["name"])
                self.log("info", "{0} is enforced by puppet. Stopping "
                                 "puppet on node {1}".format(service,
                                                             node["name"]))
                self.stop_service(node["name"], "puppet")

        # Return the list of nodes that have puppet stopped
        return puppet_stop_node_list

    def wait_for_service_group_start(self, node):
        """
        Description:
            Function to poll Service Groups until there are none in the state
            STARTING or PARTIAL
        Actions:
            1. Wait for cmd 'hastatus -sum' to have return code 0
            2. For each service group
            3. If any strings from wait_list are in the output of
               'hastatus -sum'
                a. Assert that the Service Group is not in state
                   'PARTIAL|FAULTED'
                b. Wait for SG to ONLINE
                c. Poll Service Groups again
            4. Continue if there is no SG in state PARTIAL or STARTING
        """
        cmd = "hastatus -sum"

        # Wait for cmd 'hastatus -sum' to have return code 0
        self.wait_for_cmd(node, cmd, 0, su_root=True)

        # List of strings that indicate that the SGs are still starting up and
        # must be waited for
        wait_list = ["STARTING", "PARTIAL", "RESOURCES NOT PROBED"]

        stdout = self.run_command(node, cmd, su_root=True)

        # 2. For each service group
        for line in stdout[0][6:]:
            group = line.split()[1]

            # If any strings from wait_list in line
            if any(item in line for item in wait_list):

                # a. Asserts that the Service Group is not in state
                # 'PARTIAL|FAULTED'
                self.assertFalse("FAULTED" in line,
                                 "Service group {0} in state FAULTED"
                                 .format(group))

                self.log("info", "SGs are still starting up")
                self.log("info", line)

                # b. Wait for SG to ONLINE
                time.sleep(5)

                # c. Poll Service Groups again
                self.wait_for_service_group_start(node)

        # 4. Continue if there are no strings from wait_list present
        self.log("info", "The cluster is back in working "
                         "state - continue")

    def _node_rebooted(self, node, up_time_pre_reboot):
        """
        Verify that a node  has rebooted.
        Takes the up_time before reboot occurred and
        compares it against the uptime after reboot.
        If uptime before reboot is greater than uptime after reboot
        then the node has been sucessfully rebooted.
        """
        node_restarted = False
        max_duration = 900
        elapsed_sec = 0
        while elapsed_sec < max_duration:
            # if True:
            try:
                # uptime after reboot
                up_time_after_boot = self._up_time(node)
                self.log("info", "{0} is up for {1} seconds"
                         .format(node, str(up_time_after_boot)))
                # Comparrisson of uptime pre reboot -vs- uptime post reboot
                if up_time_after_boot < up_time_pre_reboot:
                    self.log("info", "{0} has been rebooted"
                             .format(node))
                    node_restarted = True
                    break
            except (socket.error, exceptions.AssertionError):
                self.log("info", "{0} is not up at the moment"
                         .format(node))
            except:
                self.log("error", "Reboot check. Unexpected Exception: {0}"
                         .format(sys.exc_info()[0]))
                self.disconnect_all_nodes()

            time.sleep(10)
            elapsed_sec += 10
        if not node_restarted:
            self.log("error", "{0} not rebooted in last {1} seconds."
                     .format(node, str(max_duration)))
        return node_restarted

    def restart_service_on_task(self, task_desc, service_to_restart, node):
        """
        Check task is running
        Task_running will take the specified task and check it's state.
        Self.assertTrue will check the expected state was found or
        return an error message.
        If state was as expected the service specified is restarted by calling
        service restart.
        """
        # check if specified task is running based on task description
        # Return True if task is running
        task_running = self.wait_for_task_state(self.ms_node,
                                task_desc,
                                test_constants.PLAN_TASKS_RUNNING,
                                ignore_variables=False)
        # If task specified is in state running assert true
        self.assertTrue(task_running, "Task is not in state: 'Running'")
        # Restart the service
        restart_service = self.restart_service(node, service_to_restart,
                                               assert_success=False)

        # If return code is not equal to 0
        if restart_service[2] != 0:
            self.log("info", "Restart of service has failed")
            # Check status of the service
            self.get_service_status(node, service_to_restart,
                                    assert_running=False)
            # Grep the processes of the service
            process_grep = "/bin/ps -eaf | /bin/grep {0} | /bin/grep -v grep"\
                .format(service_to_restart)
            self.run_command(node, process_grep)
            self.assertTrue(restart_service[2] == 0,
                            "Service failed to restart")

    def kill_service_httpd_and_recover(self, task_desc, node):
        """
        Args:
            task_desc(str): Pass in the task description to trigger kill
            node(str): Pass in the node that the kill will be run on
        Description:
            Get the httpd service status.
            Ensure task description is in state running.
            1. kill http using -9 kill signal
            2. Get service status
                if the service is dead and subsystems locked
                    3. get child services of dead service
                    4. kill child services of dead service
                    5. start the service
                    6. get service status
                    7. ensure service is in running state
        """
        service = "httpd"
        # Get service status pre kill service , expects running
        service_status, _, _ = self.get_service_status(
                node, service, assert_running=True)
        # Log results of get service status
        self.log("info", "Service status: {0}".format(service_status))

        # Ensure that task specified is running
        task_running = self.wait_for_task_state(
            self.ms_node, task_desc, test_constants.PLAN_TASKS_RUNNING,
            ignore_variables=False)
        # If task specified is in state running assert true
        self.assertTrue(task_running, "Task is not in state: 'Running'")

        get_child_services_cmd = "/usr/sbin/lsof -i tcp:443"
        # Get httpd service status
        self.get_service_status(node,
                                service,
                                assert_running=True)
        # 1. Kill service with kill -9
        self.stop_service(node,
                          service,
                          kill_service=True,
                          kill_args="-9")
        # 2. Get service status , expect service is dead
        httpd_status_post, _, _ = \
            self.get_service_status(node,
                                    service,
                                    assert_running=False)

        if "httpd dead but pid file exists" in httpd_status_post:
            self.log("info", "Http dead, killing child services now")
            # 3. Get child services of dead service
            # List the child processes of httpd
            child_processes, _, _ = \
                self.run_command(self.ms_node,
                                 get_child_services_cmd,
                                 su_root=True)
            # Logic to isolate child PIDs
            child_pids = []
            filtered_list = []
            for entry in child_processes:
                for this_entry in entry.split(" "):
                    if this_entry != "":
                        filtered_list.append(this_entry)
                child_pids.append(filtered_list[1])
                filtered_list = []
            child_pids.pop(0)

            # 4. Kill child services of dead service
            # Begin killing the child processes of httpd
            for entry in child_pids:
                self.log("info", "killing child PIDs")
                self.run_command(self.ms_node,
                                 "/bin/kill " + entry,
                                 su_root=True)
            # Does an additional to see if any child processes remain
            child_processes_post_kill, _, _ = \
                self.run_command(self.ms_node,
                                 get_child_services_cmd,
                                 su_root=True)
            # Assert that no child processes remain
            self.assertEqual(child_processes_post_kill, [],
                             "Unexpected child processes "
                             "of httpd remain")

            # 5. Start the service
            self.start_service(node, service)

            # 6. Get service status
            # 7. Ensure service is running
            service_status, _, _ = \
                self.get_service_status(node,
                                        service,
                                        assert_running=True)

            self.log("info", "service is back in running state")
            return True
        else:
            return False

    def kill_service_on_config_task(self, task_desc, service, node,
                                    kill_arg='', timeout_mins=10):
        """
        Args:
            task_desc(str): Pass in the task description to trigger kill
            service on service(str): Pass in the service that will be killed
            node(str): Pass in the node that the kill will be run on
            kill_arg(str): Pass in either "" or "-9"
                         to select which version of kill you want used
        Description:
            Get the service status of service passed in.
            If valid kill_arg passed then
                Ensure task description is in state running
                kill  the service provided with the kill_ar provided
                get service status
                start the service that was killed
                get service status
                ensure service has started
        """
        # Get service status pre kill service , expects running
        service_status, _, _ = self.get_service_status(
                node, service, assert_running=True)
        # Log results of get service status
        self.log("info", "Service status: {0}".format(service_status))
        # if valid kill_arg is provided
        if kill_arg == '' or kill_arg == "-9":
            # Ensure that task specified is running
            task_running = self.wait_for_task_state(
                self.ms_node, task_desc, test_constants.PLAN_TASKS_RUNNING,
                ignore_variables=False, timeout_mins=timeout_mins)
            # If task specified is in state running assert true
            self.assertTrue(task_running, "Task is not in state: 'Running'")
            if service == "libvirtd" and kill_arg == "-9":
                service_libvirt_status, _, _ = \
                    self.get_service_status(
                        node,
                        service,
                        assert_running=True)
                self.log("info", "Service status: {0}"
                         .format(service_libvirt_status))
                self.log("info", "kill -9 of libvirt service occurring")
                # kill the libvirt service with -9 kill signal
                self.stop_service(node,
                                  service,
                                  kill_service=True,
                                  kill_args=kill_arg)
                self.log("info", "service has been killed")
                service_libvirt_status2, _, _ = \
                    self.get_service_status(
                        node,
                        service,
                        assert_running=False)
                self.log("info", "Service status: {0}"
                         .format(service_libvirt_status2))
                # Wait five seconds
                time.sleep(5)
                # Restart the libvirt service
                self.restart_service(node,
                                     service,
                                     assert_success=True)
                service_libvirt_status3, _, _ = \
                    self.get_service_status(
                        node,
                        service,
                        assert_running=True)
                self.log("info", "Service status: {0}"
                         .format(service_libvirt_status3))
            else:
                # Kill or kill -9 depending on kill_arg provided
                self.stop_service(node, service, kill_service=True,
                                  kill_args=kill_arg)
                # Log when kill occurs
                self.log("info", "Kill service occurred: {0}".format(service))

                # If the service being killed is litpd, wait for the expected
                # return code from 'service litpd status' to ensure that the
                # service is dead before trying to start the service
                if "litpd" in service:
                    kill = True
                    self.start_litpd_if_stopped(kill, kill_arg)
                else:
                    # Get service status after kill has occurred
                    service_status2, _, _ = self.get_service_status(
                        node, service, assert_running=False)
                    # Log service status after kill of service
                    self.log("info", "Service status: {0}".format(
                        service_status2))
                    time.sleep(10)
                    # Start the service
                    self.start_service(node, service)
                    # Get service status after service has been started
                    service_status3, _, _ = self.get_service_status(
                            node, service, assert_running=True)
                    self.log("info", "Service status: {0}".format(
                        service_status3))

                return True
        else:
            self.log("error", "Unexpected kill argument provided")
            return False

    def reboot_node(self, node):
        """
        Reboot a node
        This runs an /sbin/reboot command after
        taking the uptime of the node
        """
        cmd = "/sbin/reboot"

        up_time_pre = self._up_time(node)
        out, err, ret_code = self.run_command(node, cmd, su_root=True)
        self.assertTrue(self.is_text_in_list("The system is going down",
                                             out))
        self.assertEqual([], err)
        self.assertEqual(0, ret_code)
        self.assertTrue(self._node_rebooted(node, up_time_pre))

        time.sleep(5)

    def _run_kill_cmds(self, node, service):
        """
        Private method used to sequence the 'kill' and 'kill -9' commands for
        mcollective rebustness tests
        """

        # Kill mcollective
        self.stop_service(node, service, kill_service=True)
        # Restart mcollective after kill
        self.restart_service(node, service)
        # Kill -9 mcollective
        self.stop_service(node, service, kill_service=True,
                          kill_args="-9")
        # Restart mcollective after kill -9
        self.restart_service(node, service)

    def check_for_rabbitmq_crash_file(self):
        """
        Description:
            Method to check the contents of rabbitmq crash file after service
            is killed. The relevant contents are printed. And file creation
            time is noted
        """

        # Name of the expected crash dump file
        crash_file = "/var/ -name erl_crash.dump"
        # Create command to find file
        find_cmd = self.redhat.get_find_cmd(crash_file)

        self.log("info", "Checking for rabbitmq crash dump file "
                         "after the kill of rabbitmq service")
        # The find command is run on the MS
        stdout, _, _ = self.run_command(self.ms_node, find_cmd, su_root=True)

        # If the crash dump file is found
        if len(stdout) > 0:
            # String of complete path to the crash dump file
            file_path = stdout[0]
            self.log("info", "Rabbitmq crash dump file found")
            # List command that will output when the file is created
            self.list_dir_contents(self.ms_node, file_path, su_root=True)
            # Output the first 20 lines of the crash dump file
            self.log("info", "Outputting the first 20 lines of crash dump "
                             "file")
            head_cmd = "head -n 20 {0}".format(file_path)
            self.run_command(self.ms_node, head_cmd, su_root=True)

        else:
            self.log("info", "No rabbitmq crash dump file found")

    def reboot_on_specified_task(self, task_desc, node_to_reboot):
        """
        Check task is running before reboot
        Task_running will take the specified task and check it's state.
        Self.assertTrue will check the expected state was found or
        return an error message.
        If state was as expected the node is rebooted by calling
        reboot_node method.
        """
        # check if specified task is running based on task description
        # Return True if task is running
        task_running = self.wait_for_task_state(self.ms_node,
                                task_desc,
                                test_constants.PLAN_TASKS_RUNNING)
        # If task specified is in state running assert true
        self.assertTrue(task_running, "Task is not in state: 'Running'")
        # Reboot the managed node
        self.reboot_node(node_to_reboot)

    def set_up_callback_tasks(self):
        """
        Sets up the required plan with Callback Tasks for robustness tests
        """
        # List of package names to be installed

        package_names = {"EXTR-lsbwrapper40": "test-lsb-40",
                         "EXTR-lsbwrapper39": "test-lsb-39"}

        self.log("info", "Creating tasks to run during the test")

        # For each package in the list of packages
        for package_name in package_names:

            service_name = package_names[package_name]

            lsbwrapper_url = self._create_package(package_name)

            # Gets the name of the nodes from the URL for the node list
            node_list_name1 = (self.peer_nodes[0]["url"].split("/"))[-1]
            node_list_name2 = (self.peer_nodes[1]["url"].split("/"))[-1]

            self.execute_cli_create_cmd(
                self.ms_node,
                "{0}/services/{1}".format(self.cluster_url, package_name),
                "vcs-clustered-service",
                "active=2 standby=0 name=vcs{0} online_timeout=220"
                " node_list={1},{2}".format(package_name, node_list_name2,
                                            node_list_name1))

            self.execute_cli_create_cmd(
                self.ms_node,
                "{0}/services/{1}/ha_configs/conf1".format(self.cluster_url,
                                                           package_name),
                "ha-service-config",
                "status_interval=30 status_timeout=20 restart_limit=2 "
                "startup_retry_limit=2")

            self.execute_cli_create_cmd(
                self.ms_node,
                "/software/services/{0}".format(package_name), "service",
                "service_name={0}".format(service_name))

            self.execute_cli_inherit_cmd(
                self.ms_node,
                "/software/services/{0}/packages/pkg1".format(package_name),
                lsbwrapper_url)

            self.execute_cli_inherit_cmd(
                self.ms_node,
                "{0}/services/{1}/applications/{1}".format(self.cluster_url,
                                                           package_name),
                "/software/services/{0}".format(package_name))

        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

    def _stop_service_callback(self, service, killarg="", kill=False):
        """
        Description:
            Private method that carries out service stop during CallbackTasks.
        Args:
            service (str) = the service you want to stop
            kill (bool) = whether you want to use kill commands. False by
                          default
            killarg (string) = string to pass argument to kill command ""
                               or "-9"
        """

        # List of packages to install
        package_names = ["EXTR-lsbwrapper40", "EXTR-lsbwrapper39"]

        # List of services enforced by puppet - puppet must be stopped
        # before stopping/killing these services
        puppet_enforce = ["mcollective", "rabbitmq-server",
                          self.postgres_service_name, "puppetdb"]

        # List of nodes where puppet is stopped - needed to start puppet for
        # retry plan
        puppet_stop_node_list = []

        # String used for log messages below
        action = "stop"
        if kill:
            action = "kill"

        # Set up and run plan that contains CallbackTasks
        self.set_up_callback_tasks()

        # Stop puppet service on the MS and the peer nodes if service is
        # enforced by puppet
        if service in puppet_enforce:
            puppet_stop_node_list = self.stop_puppet_if_service_enforced(
                service, self.ms_only)

        # Wait for Callback task
        task_running = \
            self.wait_for_task_state(
                self.ms_node,
                'Create VCS service group "Grp_CS_c1_EXTR_lsbwrapper39"',
                test_constants.PLAN_TASKS_RUNNING,
                seconds_increment=1,
                ignore_variables=False)

        self.assertTrue(task_running,
                        "Task did not reach running state in specified time")

        # If service not vcs run stop service on the MS
        if "vcs" not in service:

            self.log("info", "Running {0} of service {1} on node '{2}'"
                     .format(action, service, self.ms_node))
            self.stop_service(self.ms_node, service, kill_service=kill,
                              kill_args=killarg)
            self.log("info", "Checking status of {0} service".format(service))
            self.get_service_status(self.ms_node, service,
                                    assert_running=False)
            # Puppet service status check included to add a very short delay
            self.log("info", "Checking status of puppet service")
            self.get_service_status(self.ms_node, "puppet",
                                    assert_running=False)
            if "rabbitmq-server" in service:
                # If rabbitmq-server was the service stopped/killed, check for
                # a crash dump file and output some details about the file
                # if it is present
                # Note the file creation time vs time the service was killed.
                # Not all the info printed will be pertinent for this test.
                self.check_for_rabbitmq_crash_file()

        # Stop service on peer nodes if it is not a ms only service
        if service not in self.ms_only:
            for node in self.peer_nodes[0:2]:
                self.log("info", "Running {0} of {1} service on node '{2}'"
                         .format(action, service, node["name"]))
                self.stop_service(node["name"], service, kill_service=kill,
                                  kill_args=killarg)
                # Check the status of services
                self.log("info", "Checking status of {0} service"
                         .format(service))
                self.get_service_status(node["name"], service,
                                        assert_running=False)
                self.log("info", "Checking status of puppet service")
                self.get_service_status(node["name"], "puppet",
                                        assert_running=False)

        # Wait for plan to complete
        plan_state = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_COMPLETE)

        # For VCS start service on the peer nodes again
        if "vcs" in service:
            self.log("info", "Plan finished. Starting service '{0}' "
                             "on peer nodes".format(service))
            for node in self.peer_nodes[0:2]:
                self.start_service(node["name"], service)

            # Wait added to allow service groups to start up fully
            self.wait_for_service_group_start(self.target)

        # Start services before running the retry plan
        for node in puppet_stop_node_list:
            self.log("info", "Starting puppet service on node '{0}' before"
                             " retry".format(node))
            self.start_service(node, "puppet")
            self.log("info", "Checking status of puppet service")
            self.get_service_status(node, "puppet")
            self.log("info", "Starting {0} service on node '{1}' before"
                             " retry".format(service, node))
            self.start_service(node, service)
            self.log("info",
                     "Checking status of {0} service".format(service))
            self.get_service_status(node, service)

        #If plan failed, retry and assert success
        if plan_state:
            self.log("info", "Initial plan passed, no need to retry")
        else:
            self.assertTrue(self._retry_callback_plan(package_names),
                            "Retry plan has failed")

    def _stop_litpd_callback(self, killarg="", kill=False):
        """
        Description:
            Private method that carries out litpd stop during CallbackTasks.
        Args:
            kill (bool) = whether you want to use kill commands. False by
                          default
            killarg (string) = string to pass argument to kill command ""
                               or "-9"
        """

        service = "litpd"

        # List of packages to install
        package_names = ["EXTR-lsbwrapper40", "EXTR-lsbwrapper39"]

        # String used for log messages below
        action = "stop"
        if kill:
            action = "kill"

        # Set up and run plan that contains CallbackTasks
        self.set_up_callback_tasks()

        # Wait for Callback task
        task_running = \
            self.wait_for_task_state(
                self.ms_node,
                'Create application resource '
                    '"Res_App_c1_vcsEXTR_lsbwrapper39_EXTR_lsbwrapper39"',
                test_constants.PLAN_TASKS_RUNNING,
                seconds_increment=1,
                ignore_variables=False)

        self.assertTrue(task_running,
                        "Task did not reach running state in specified time")

        # Get all started phases at time of stop litpd
        self.log('info',
                 'Get all started phases at time of {0} litpd'.format(action))
        started_phases_at_litpd_stop = \
                    self.get_tasks_by_state(self.ms_node, 'Running').keys() \
                    + self.get_tasks_by_state(self.ms_node, 'Success').keys()

        # Run stop service on the MS
        self.log("info", "Running {0} of service {1} on node '{2}'"
                 .format(action, service, self.ms_node))
        self.stop_service(self.ms_node, service, kill_service=kill,
                          kill_args=killarg)
        self.log("info", "Checking status of {0} service".format(service))
        self.get_service_status(self.ms_node, service,
                                assert_running=False)
        # Puppet service status check included to add a very short delay
        self.log("info", "Checking status of puppet service")
        self.get_service_status(self.ms_node, "puppet",
                                assert_running=False)

        # Start the litpd service so that the state of the plan can be checked
        self.start_litpd_if_stopped(kill, killarg)
        # Wait for plan to complete
        plan_state = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_COMPLETE)

        # Different plan state expected for kill -9 of litpd and other commands
        # For kill -9 of litpd, no further actions required
        if kill == True and killarg == "-9":
            # The plan should complete successfully
            self.assertTrue(plan_state, "Plan didn't complete successfully.")
        else:
            # The plan should be in state failed or stopped so checking that
            # the plan has not completed successfully
            self.assertFalse(plan_state, "Plan was expected to fail or stop "
                                         "but has completed successfully")

            # Check that tasks in started phases are successful
            self.log('info',
            'Check that phases started at "litpd {0}" time completed '
            'successfully, and all others are in "Initial" state'\
            .format(action))
            self.validate_phases(started_phases_at_litpd_stop)

            # Retry plan and assert success
            self.assertTrue(self._retry_callback_plan(package_names),
                            "Retry plan has failed")

    def _retry_callback_plan(self, package_names):
        """
        Description:
            This function includes the steps that need to be taken if the plan
            with callback tasks fail.
        Args:
            package_names = the name of the packages that are installed
        Result:
            Returns True if the cleanup plan and the retry plan are successful
            Returns False if the the cleanup plan or the retry plan fail
        """

        self.log("info", "Initial plan has failed.")
        self.log("info", "Attempting to remove any items created so the "
                         "original plan can be created again.")

        # For each package in the list of packages
        for package_name in package_names:
            # Remove VCS cluster service items as it has been partially
            # created
            self.log("info", "Remove VCS cluster service items as it has been "
                             "partially created")
            self.execute_cli_remove_cmd(
                self.ms_node, "{0}/services/{1}/applications/{1}"
                    .format(self.cluster_url, package_name))

            self.execute_cli_remove_cmd(
                self.ms_node, "{0}/services/{1}".format(self.cluster_url,
                                                        package_name))

        # Create removal plan
        self.log("info", "Creating remove service group plan")
        self.execute_cli_createplan_cmd(self.ms_node)

        # Run removal plan
        self.log("info", "Running remove service group plan")
        self.execute_cli_runplan_cmd(self.ms_node)

        # Wait for removal plan to complete successfully
        plan_completed_successfully = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE)
        self.assertTrue(plan_completed_successfully,
                        "The removal plan was not successful")

        # Node list names used in creating a vcs clustered service
        node_list_name1 = (self.peer_nodes[0]["url"].split("/"))[-1]
        node_list_name2 = (self.peer_nodes[1]["url"].split("/"))[-1]

        # For each package in the list of packages
        for package_name in package_names:

            # Create the VCS cluster service items again
            self.execute_cli_create_cmd(
                self.ms_node,
                "{0}/services/{1}".format(self.cluster_url, package_name),
                "vcs-clustered-service",
                "active=2 standby=0 name=vcs{0} online_timeout=220"
                " node_list={1},{2}".format(package_name,
                                            node_list_name2, node_list_name1))

            self.execute_cli_create_cmd(
                self.ms_node, "{0}/services/{1}/ha_configs/conf1"
                    .format(self.cluster_url, package_name),
                "ha-service-config", "status_interval=30 status_timeout=20 "
                                     "restart_limit=2 startup_retry_limit=2")

            self.execute_cli_inherit_cmd(
                self.ms_node,
                "{0}/services/{1}/applications/{1}".format(self.cluster_url,
                                                           package_name),
                "/software/services/{0}".format(package_name))

        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        plan_state = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_COMPLETE)

        # Check that retry plan is successful
        if plan_state:
            return True

        else:
            return False

    def start_litpd_if_stopped(self, kill, killarg):
        """
        Description:
            Private method to handle the starting of the litpd service after a
            stop/kill during a callback task
        Args:
            kill (bool) = whether you want to use kill commands. False by
                          default
            killarg (string) = string to pass argument to kill command ""
                               or "-9"
        """
        service = "litpd"
        # Expected return code when litpd is stopped
        expect_rc = 3
        if kill:
            # Expected return code when litpd is killed
            expect_rc = 2
        if killarg == "-9":
            # Expected return code when litpd is killed with '-9'
            expect_rc = 1

        status_cmd = "/sbin/service {0} status".format(service)

        # Wait for the expected return code to ensure that litpd service
        # has been stopped/killed
        successful_stop = self.wait_for_cmd(self.ms_node,
                                            status_cmd,
                                            expect_rc,
                                            su_root=True,
                                            timeout_mins=5)
        self.assertTrue(successful_stop,
                        "Service did not reach status code {0} in time"
                        .format(expect_rc))

        self.log("info", "Starting service '{0}' on node '{1}"
                 .format(service, self.ms_node))
        # Start litpd service so that the state of the plan can be checked
        self.start_service(self.ms_node, service)
        # enable debug after starting the service
        self.turn_on_litp_debug(self.ms_node)

    def create_config_plan(self):
        """
        Function to create a plan with the required config task

        Returns:
            task_desc_ms - Description of task running on MS
            task_desc_mn - Description of task running on the managed node
        """

        test_pkg1 = "vsftpd"
        test_pkg2 = "telnet"
        # Create the packages
        pkg_url2 = self._create_package(test_pkg2)
        pkg_url1 = self._create_package(test_pkg1)

        # Inherit packages on ms and node 1
        # Inherit command for ms package 1
        self._create_package_inheritance(self.ms_path, test_pkg1, pkg_url2)
        # Inherit command for ms package 2
        self._create_package_inheritance(self.ms_path, test_pkg2, pkg_url1)
        # Inherit command for node 1 package 1
        self._create_package_inheritance(self.target_url,
                                         test_pkg1,
                                         pkg_url1)
        # Inherit command for node 1 package 2
        self._create_package_inheritance(self.target_url,
                                         test_pkg2,
                                         pkg_url2)

        # Create and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        # Wait for the starting of the installation of packages
        # on the desired node
        task_desc_ms = 'Install package "{0}" on node "{1}"'.\
                        format(test_pkg2, \
                        self.ms_node)
        task_desc_mn = 'Install package "{0}" on node "{1}"'.\
                        format(test_pkg2, \
                        self.target)

        task_state_ms = self.get_task_state(self.ms_node, task_desc_ms,
                                            ignore_variables=False)
        task_state_mn = self.get_task_state(self.ms_node, task_desc_mn,
                                            ignore_variables=False)
        self.assertNotEqual(task_state_ms, test_constants.CMD_ERROR,
                            "Task doesn't exist")
        self.assertNotEqual(task_state_mn, test_constants.CMD_ERROR,
                            "Task doesn't exist")

        return task_desc_ms, task_desc_mn

    def cleanup_config_plan(self):
        """
        Undoes the actions of create_config_plan
        """
        self.execute_cli_remove_cmd(self.ms_node, "/ms/items/vsftpd",
                                add_to_cleanup=False, expect_positive=False)
        self.execute_cli_remove_cmd(self.ms_node, "/ms/items/telnet",
                                add_to_cleanup=False, expect_positive=False)
        self.execute_cli_remove_cmd(self.ms_node,
                        "/deployments/d1/clusters/c1/nodes/n1/items/vsftpd",
                                add_to_cleanup=False, expect_positive=False)
        self.execute_cli_remove_cmd(self.ms_node,
                        "/deployments/d1/clusters/c1/nodes/n1/items/telnet",
                                add_to_cleanup=False, expect_positive=False)
        self.execute_cli_remove_cmd(self.ms_node, "/software/items/telnet",
                                add_to_cleanup=False, expect_positive=False)
        self.execute_cli_remove_cmd(self.ms_node, "/software/items/vsftpd",
                                add_to_cleanup=False, expect_positive=False)

        self.execute_cli_runplan_cmd(self.ms_node)
        plan_state = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_COMPLETE)
        self.assertTrue(plan_state,
                         "Plan has failed. Expected a successful plan")

    def _stop_service_config(self, services, kill=False, killarg="", \
                             timeout=10):
        """
        Description:
            Private method that carries out service stop/kill during
            Config task. The plan is expected to succeed when these services
            are killed/stopped
        Args:
            services (list) = list of services to be stopped or killed
            kill (bool) = whether you want to use kill commands. False by
                          default
            killarg (string) = string to pass argument to kill command ""
                               or "-9"
            timeout = time in  minutes for plan to complete
        """

        # String for log messages
        action = "Stopping"
        if kill:
            action = "Killing"

        # Create and run plan with config tasks
        task_desc_ms, task_desc_mn = self.create_config_plan()

        # Wait for config task to be running on the MS
        task_running_ms = \
            self.wait_for_task_state(self.ms_node, task_desc_ms,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running_ms,
                        "Task did not reach running state in specified time")
        for service in services:
            # Stop/Kill service on MS
            self.log("info", "{0} {1} service on '{2}'".format(
                action, service, self.ms_node))
            self.stop_service(self.ms_node, service, kill_service=kill,
                              kill_args=killarg)
            # Check service status
            self.get_service_status(self.ms_node, service,
                                    assert_running=False)

        # Wait for config task to be running on peer node
        task_running_mn = \
            self.wait_for_task_state(self.ms_node, task_desc_mn,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running_mn,
                        "Task did not reach running state in specified time")
        if services[0] in self.ms_only:
            self.log("info", "Service {0} is only running on the "
                             "MS".format(services))
        else:
            for service in services:
                # Stop/Kill service on peer node
                self.log("info", "{0} {1} service on '{2}'".format(
                    action, service, self.target))
                self.stop_service(self.target, service, kill_service=kill,
                                  kill_args=killarg)

                # Get service status of puppet agent on the peer node
                self.get_service_status(self.target, service,
                                        assert_running=False)

        # Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)

        # If the initial plan doesn't succeed, re-run
        if completed_successfully:
            self.log("info", "Initial plan passed, no need to retry")
        else:
            self.log("info", "Initial plan has failed, retrying plan")
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)

            completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
            self.assertTrue(completed_successfully,
                            "Plan did not finish successfully.")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    def stop_services_config_fail_plan(self, services, kill=False, killarg=""):
        """
        Description:
            Private method that carries out service stop/kill on a list of
            services during Config task. The plan may fail when
            these services are killed/stopped. The objective is to check that
            litp can recover from the situation - either by the plan passing
            first time or being recreated and rerun
        Args:
            services (list) = list of services to kill/stop
            kill (bool) = whether you want to use kill commands. False by
                          default
            killarg (string) = string to pass argument to kill command ""
                               or "-9"
        """

        timeout = 10

        # Create and run plan with config tasks
        task_desc_ms, task_desc_mn = self.create_config_plan()
        # Wait for config task to be running on the MS
        task_running = \
            self.wait_for_task_state(self.ms_node, task_desc_ms,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False,
                                     seconds_increment=1)
        self.assertTrue(task_running,
                        "Task did not reach running state in specified time")
        # Stop the services on MS, wait for the plan to pass/fail,
        # start services and if necessary create then run plan
        self._stop_services(self.ms_node, services, kill, killarg)

        # If plan completed successfully already then undo changes, create and
        # run plan.
        plan_state = self.get_current_plan_state(self.ms_node)
        if plan_state == test_constants.PLAN_COMPLETE:
            self.cleanup_config_plan()
            task_desc_ms, task_desc_mn = self.create_config_plan()

        # Wait for config task to be running on peer node
        task_running = \
            self.wait_for_task_state(self.ms_node, task_desc_mn,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False,
                                     seconds_increment=1)
        self.assertTrue(task_running,
                        "Task did not reach running state in specified time")

        # Stop the services on peer node, wait for the plan to fail, start
        # services, create and run plan
        # If the service is rabbitmq-server, stop/kill service on the MS
        if "rabbitmq-server" in services:
            self._stop_services(self.ms_node, services, kill, killarg)

        else:
            self._stop_services(self.target, services, kill, killarg)

        # Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, self.timeout_mins)

        # Assert that the plan is successful
        self.assertTrue(completed_successfully,
                        "Plan did not finish successfully")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    def _stop_services(self, node, services, kill, killarg):
        """
        Method that stops/kills a number of services and waits for the plan to
        end. Once the plan has ended it starts the services again. If the plan
        fails, it is recreated and rerun.
        Args:
            node (string) = name of the node where you want to stop/kill the
                            services
            services (list) = list of services you want to stop or kill
            kill (bool) = whether you want to use kill commands. False by
                          default
            killarg (string) = string to pass argument to kill command ""
                               or "-9"
        """

        # String for log messages
        action = "Stopping"
        if kill:
            action = "Killing"

        # Check if the service being tested is enforced by puppet.
        # If enforced by puppet, puppet needs to be stopped so that it
        # does not try to enforce the service being enabled and therefore
        # compromise the testcase
        self.check_service_enforced_by_puppet(services, node, "stop")

        for service in services:
            # Stop/Kill services on node
            self.log("info", "{0} {1} service on '{2}'".format(action,
                                                               service,
                                                               node))
            self.stop_service(node, service, kill_service=kill,
                              kill_args=killarg)
            # Get service status after service is stopped/killed
            service_status, _, _ = \
                self.get_service_status(node,
                                        service,
                                        assert_running=False)
            # Log results of get service status
            self.log("info", "Service status: {0}".format(service_status))

            if "rabbitmq-server" in service:
                # If rabbitmq-server was the service stopped/killed, check for
                # a crash dump file and output some details about the file
                # if it is present
                # Note the file creation time vs time the service was killed.
                # Not all the info printed will be pertinent for this test.
                self.check_for_rabbitmq_crash_file()

        # Wait for plan to fail
        self.log("info", "Plan is expected to fail")
        plan_failure = self.wait_for_plan_state(self.ms_node,
                                                test_constants.PLAN_FAILED,
                                                self.timeout_mins)
        # Display service and puppet status before assertion for debugging
        self.get_service_status(node, "puppet", assert_running=False)
        for service in services:
            self.get_service_status(node, service, assert_running=False)

        # The stopped/killed services are started again before any
        # failed plan is recreated.
        for service in services:
            self.log("info", "Starting {0} service on '{1}'".format(
                service, node))
            self.start_service(node, service)

        # Check if the service being tested is enforced by puppet.
        # If enforced by puppet, the puppet service was stopped previously
        # in the testcase and needs to be started again
        self.check_service_enforced_by_puppet(services, node, "start")

        if plan_failure:
            # Create and run plan
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)

    def check_service_enforced_by_puppet(self, services, node, action):
        """
        Check if the service being tested is enforced by puppet. If enforced
        by puppet, puppet needs to be stopped so that it does not try to
        enforce the service being enabled and therefore compromise the testcase
        This method can also be used to start the puppet service after the task
        has failed by passing 'start' as the action
        Args:
            services (list) = list of services to check
            node (string) = name of the node to stop/start puppet on
            action (string) = 'stop' or 'start' depending on whether you want
                              to stop or start puppet
        """
        # list of services enforced by puppet
        stop_puppet_list = ["mcollective", "rabbitmq-server"]
        # if the only service in services list is in stop_puppet_list
        if len(services) == 1 and services[0] in stop_puppet_list:

            # Stop puppet service if the action is 'stop'
            if action == "stop":
                self.log("info", "Stopping puppet service on node '{0}'"
                         .format(node))
                self.stop_service(node, "puppet")
            # Start puppet service if the action is 'start'
            else:
                self.log("info", " Starting puppet service on node '{0}'"
                         .format(node))
                self.start_service(node, "puppet")

        # Log puppet status
        puppet_status, _, _ = \
            self.get_service_status(node, "puppet", assert_running=False)
        self.log("info", "Puppet status: {0}".format(puppet_status))

    def count_phases_in_plan(self):
        """
        Check plan for number of phases in plan
        """
        #Get show_plan output
        stdout, _, _ = self.execute_cli_showplan_cmd(self.ms_node)

        #Get number of phases in total
        number_of_phases = self.cli.get_num_phases_in_plan(stdout)
        return number_of_phases

    def count_tasks_in_phase(self, phase_checked):
        """
        Check a specified phase "phase_checked" for number of tasks in phase
        """
        #Get show_plan output
        stdout, _, _ = self.execute_cli_showplan_cmd(self.ms_node)

        #Get number of tasks in total for phase specified
        number_of_tasks_phase = self.cli.get_num_tasks_in_phase(
            stdout, phase_checked)
        return number_of_tasks_phase

    def update_node_vm_configuration(self):
        """
        Description:
            This function will
            1. Locate a specific VM on the MN.
            2. Update the vms alias_names list by adding "TestAlias1".
            3. Create and run the plan.
        Result:
            Creates plan to update a VM's node configuration
            on the node and runs the plan.
            Returns task_description to be used in other methods
        """
        # Vm alias to be added to alias list on specified vm
        test_alias_names = ["TestAlias1"]

        # 1. Locate a specific VM on the MN
        # Get paths to all vm services on MN
        path_to_vm_services = self.find(self.ms_node,
                                        '/software',
                                        "vm-service",
                                        assert_not_empty=True)

        # Get the name of the vm to be used in task description
        mn_vm_name = self.get_props_from_url(self.ms_node,
                                             path_to_vm_services[1],
                                             "service_name")

        # Task description to take action on when in state running
        task_desc_mn = 'Copy VM cloud init userdata file to node' \
                       ' "{0}" for instance "{1}" as part ' \
                       'of VM update'.format(self.target,
                                             mn_vm_name)
        # Get the collection of vm alias names
        collection_of_vm_aliases = \
            self.find(self.ms_node,
                      path_to_vm_services[1] + "/vm_aliases",
                      "vm-alias")
        alias_for_update = collection_of_vm_aliases[0]
        # Get list of alias_names list to be updated
        mn_vm_alias_list = self.get_props_from_url(self.ms_node,
                                                   alias_for_update,
                                                   "alias_names")
        # Check that the alias_names list is not empty
        self.assertTrue(mn_vm_alias_list != (),
                        "No vm-alias items on mn were found")
        # Print out the alias names list pre update
        self.log("info", "vm-aliases before update: ", mn_vm_alias_list)

        # 2.Update the vm alias_names list by
        #   adding "TestAlias1"
        # Command to update the vm alias list
        update_mn_alias_list = (mn_vm_alias_list + "," + test_alias_names[0])
        self.execute_cli_update_cmd(self.ms_node,
                                    alias_for_update,
                                    "alias_names=" + update_mn_alias_list,
                                    expect_positive=True)
        # Get vm-alias list for specified vm post update
        mn_vm_alias_list_post_update = \
            self.get_props_from_url(self.ms_node,
                                    alias_for_update,
                                    "alias_names")
        self.log("info", "Vms alias_names list post update: ",
                 mn_vm_alias_list_post_update)
        # Check to see if old vm_alias_list is same as new one
        self.assertTrue(mn_vm_alias_list != mn_vm_alias_list_post_update,
                        "Vm alias list was not updated")

        # 3. Create and run the plan
        # Create plan
        self.execute_cli_createplan_cmd(self.ms_node,
                                        expect_positive=True)

        self.log("info", "plan has been created")
        # Show plan
        self.execute_cli_showplan_cmd(self.ms_node)
        # Run the plan
        self.execute_cli_runplan_cmd(self.ms_node)
        return task_desc_mn

    def update_ms_vm_configuration(self):
        """
        Description:
            This function will
            1. Locate a specific Vm on the MS.
            2. Update the vms alias_names list by adding "TestAlias1".
            3. Create and run the plan.
        Result:
            Creates plan to update a VM's configuration
            on ms and runs the plan.
            Returns task_description to be used in other methods.
        """
        # 1. Locate a specific VM on the ms
        # Vm alias to be added to alias_names list
        test_alias_names = ["TestAlias1"]
        # Get path/paths of vm/s on ms node
        ms_vm_service_path = self.find(self.ms_node,
                                       self.ms_path,
                                       "vm-service",
                                       assert_not_empty=True)

        # Get Vm name to be used in task desc
        ms_vm_name = self.get_props_from_url(self.ms_node,
                                             ms_vm_service_path[0],
                                             "service_name")

        # Task description for ms
        task_desc_ms = 'Copy VM cloud init userdata file to node "{0}" for ' \
                    'instance "{1}" as part of VM update'.format(self.ms_node,
                                                                 ms_vm_name)

        # Log message stating which vm will be updated
        self.log("info", "Vm to be updated: '{0}'".format(ms_vm_name))

        # Get the path to the vm-alias on the ms
        ms_alias_path = self.find(self.ms_node,
                                  ms_vm_service_path[0],
                                  "vm-alias",
                                  assert_not_empty=True)

        # Get vm-alias list for specified vm
        ms_vm_alias_list = self.get_props_from_url(self.ms_node,
                                                   ms_alias_path[0],
                                                   "alias_names")

        # Check that the vm_alias_list is not empty
        self.assertTrue(ms_vm_alias_list != (),
                        "No vm-alias items on ms were found")
        # Show vm-alias list pre update
        self.log("info", "vm_aliases pre update'{0}'"
                 .format(ms_vm_alias_list))

        # 2. Update the vms alias_names list by adding "TestAlias1"
        # Command to update the vm alias list
        update_ms_alias_list = (ms_vm_alias_list + "," + test_alias_names[0])

        self.execute_cli_update_cmd(self.ms_node,
                                    ms_alias_path[0],
                                    "alias_names=" + update_ms_alias_list,
                                    expect_positive=True)

        # Show vm-alias list post update
        ms_vm_alias_list_post_update = \
            self.get_props_from_url(self.ms_node,
                                    ms_alias_path[0],
                                    "alias_names")
        self.log("info", "vm_aliases post update'{0}'"
                 .format(ms_vm_alias_list_post_update))
        # Check that the vm alias list post update
        # is not the same as list pre update
        self.assertTrue(ms_vm_alias_list !=
                        ms_vm_alias_list_post_update,
                        "Vm alias list was not updated")
        # 3. Create and run the plan
        # Create plan
        self.execute_cli_createplan_cmd(self.ms_node,
                                        expect_positive=True)

        self.log("info", "plan has been created")
        # Show plan
        self.execute_cli_showplan_cmd(self.ms_node)
        # Run the plan
        self.execute_cli_runplan_cmd(self.ms_node)
        # Returns task description for ms to be used in other methods
        return task_desc_ms

    def kill_vm_during_update_plan(self, task_desc):
        """
        Description:
            This method is used to kill a vm
            (using virsh destroy and the vm name) during a plan ,
            the plan is created in another method and is in
            running state as this method is run.
        Args:
            task_desc = task to wait for before killing the vm
        Result:
            Vm on ms will be destroyed while the vms
            configuration update is being applied.
            Vm will be recreated and plan should not fail.
        """
        # Virsh command to be used to kill vm on ms
        virsh_destroy_command = "virsh destroy "
        # Virsh command to show running VMs on MS
        show_vm_state = "virsh list "
        ms_vm_service_path = self.find(self.ms_node,
                                       self.ms_path,
                                       "vm-service",
                                       assert_not_empty=True)

        # Get Vm name to be used in task desc
        ms_vm_name = self.get_props_from_url(self.ms_node,
                                             ms_vm_service_path[0],
                                             "service_name")
        # This combines virsh destroy string with vm name to kill specified vm
        run_virsh_destroy = virsh_destroy_command + ms_vm_name
        # Wait for task to be in state running before killing the vm
        task_running = \
            self.wait_for_task_state(self.ms_node, task_desc,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     ignore_variables=True,
                                     timeout_mins=1)
        # Check to see if task was in expected state
        self.assertTrue(task_running,
                        "Task did not reach running state in specified time")
        # Show Vm state pre kill
        self.run_command(self.ms_node,
                         show_vm_state,
                         su_root=True,
                         default_asserts=True)

        # Run virsh kill command on the specified vm on specified task
        self.run_command(self.ms_node,
                         run_virsh_destroy,
                         su_root=True,
                         default_asserts=True,
                         add_to_cleanup=True)

        # Check if plan completed successfully in the allowed time
        plan_successful = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=5)

        # Assertion to check if plan was successful after vm was killed
        self.assertTrue(plan_successful, "Plan did not complete "
                                                "successfully in "
                                                "the allowed time")
        # Show Vm state to prove vm has been recreated during plan
        self.run_command(self.ms_node,
                         show_vm_state,
                         su_root=True,
                         default_asserts=True)

    def backup_restore_litp_config_file(self, backup_location,
                                        restore=False):
        """
        Description:
            Function to backup or restore the LITP model
            config file in the required procedure.
        Args:
            backup_location(str): Path to backup file.
            restore(bool): Flag on whether to backup or restore:
        """
        self.log('info',
        "Checking LITP status, and subsequently stopping if necessary.")
        _, _, retcode = \
        self.get_service_status(self.ms_node, 'litpd',
                         assert_running=False)
        if retcode == 0:
            self.stop_service(self.ms_node, 'litpd', su_root=True,
                              su_timeout_secs=self.litpd_stop_timeout_secs)

        if not restore:
            self.log('info',
            "Backing up LITP configuration file.")
            cp_cmd = \
            self.redhat.get_copy_cmd(test_constants.LITP_LAST_KNOWN_CONFIG,
                              backup_location)
            self.run_command(self.ms_node, cp_cmd, su_root=True)
        else:
            self.log('info',
            "Restoring LITP configuration file from backup.")
            mv_cmd = \
            self.redhat.get_move_cmd(backup_location,
                                     test_constants.LITP_LAST_KNOWN_CONFIG)
            self.run_command(self.ms_node, mv_cmd, su_root=True)

        self.log('info',
        "Starting LITP service, " \
        "and ensuring status is as expected afterwards.")
        self.start_service(self.ms_node, 'litpd',
                           assert_success=True, su_root=True)
        self.get_service_status(self.ms_node, 'litpd',
                                assert_running=True)
        self.turn_on_litp_debug(self.ms_node)

    def fill_fs(self, node, directory, files_to_del):
        """
        Description:
            Appends a copy of the alphabet to a file until all
            space is used on the file system.
        Args:
            node (str): Filename of the node on which to execute
                        the the command.
            directory (str): Directory in which to create the file.
            files_to_del (list): Files to be cleaned.
        Returns:
            list. files to be deleted at end of test execution.
        """
        yes_cmd = "/usr/bin/yes abcdefghijklmnoqrstuvwxyz"
        counter = 0
        space_available = True
        while space_available:
            filename = "robustness_large_file_{0}".format(counter)
            filepath = directory + "/" + filename
            files_to_del.append(filepath)
            self.log('info',
            "Creating temp file '{0}' to fill volume '{1}'".format(filename,
                                                                 directory))
            counter += 1
            space_available = \
            self.create_file_on_node(node, filepath, [],
                                     empty_file=True, add_to_cleanup=False,
                                     su_root=True)
            self.log('info',
            "Filling file at path '{0}' with data " \
            "until volume is full using " \
            "Linux 'yes' command ".format(filepath))

            fill_cmd = yes_cmd + " >> {0}".format(filepath)
            self.run_command(node, fill_cmd,
                             connection_timeout_secs=1500,
                             su_timeout_secs=1500, su_root=True)

        return files_to_del

    def chk_var_size_increase(self, orig_var_listing, cur_var_listing):
        """
        Description:
            Funcion to check that any increase in size to any of the
            /var partitions is only of the magnitude of 5mb or .1 gb
        Args:
            orig_var_listing (list): partition size layout of var at start
            cur_var_listing (list): current partition size layout of var.
        """
        # IF THE VAR LISTING IS DIFFERENT TO THE START OF THE TEST
        # CHECK TO ENSURE INCREASE IS WITHIN ALLOWABLE TOLERANCES.
        if orig_var_listing != cur_var_listing:
            # CHECK THE SIZE OF THE USED SPACE, ALLOW 5M INCREASE
            # TO ACCOUNT FOR LOGGING THAT OCCURS DURING THE EXECTION
            # OF THE TEST.
            for entry in orig_var_listing:
                split_entry = entry.split(" ")
                # COMPILE LISTING OF VAR TO USEABLE FORMAT
                # REMOVE EMPTY ENTRIES FROM LIST TO ALLOW
                # FOR EASIER COMPARISON BETWEEN ENTRIES
                elements = [x for x in split_entry if x != '']
                # MATCH ENTRY LISTINGS BETWEEN ORIG & CUR.
                for new_entry in cur_var_listing:
                    new_split_entry = new_entry.split(" ")
                    # REMOVE EMPTY ENTRIES FROM LIST TO ALLOW
                    # FOR EASIER COMPARISON BETWEEN ENTRIES
                    new_elements = \
                    [x for x in new_split_entry if x != '']
                    if elements[-1] == new_elements[-1]:
                        break
                # ASCERTAIN WHETHER USED SIZE IF Mb OR Gb
                # IF Mb ALLOW FOR A 5Mb SIZE INCREASE IN THE PARTITION
                if 'M' in elements[2]:
                    orig_value = int(elements[2][:-1])
                    new_value = int(new_elements[2][:-1])
                    diff = new_value - orig_value
                    self.assertTrue(diff < 6,
                                    "Increase of var partition " \
                                    "{0} was greater " \
                                    "than 5Mb".format(elements[-1]))
                # IF Gb ALLOW FOR AN INCREASE OF LESS THAT .2
                # NOT .1 AS PYTHON ARITHMETIC CONVERSION FROM
                # DECIMAL FLOAT TO BINARY FLOAT ADDS AN
                # EXTRA MINISCULE AMOUNT.
                elif 'G' in elements[2]:
                    orig_value = float(elements[2][:-1])
                    new_value = float(new_elements[2][:-1])
                    diff = new_value - orig_value
                    self.assertTrue(diff < .2,
                                    "Increase of var partition " \
                                    "{0} was greater " \
                                    "than .2Gb".format(elements[-1]))

    def chk_file_write_time(self, filename):
        """
        Description:
            Checks the write time of the file.
        Returns:
            str. The write time.
        """
        write_time_cmd = \
        "/bin/ls -la %s | /bin/awk '{print $8}'" % filename
        stdout, _, _ = \
        self.run_command(self.ms_node, write_time_cmd,
                         su_root=True)
        return stdout[0]

    def replace_text_in_file(self, filename, orig_text, replace_text):
        """
        Description:
            Searches through the supplied file and replaces all instances
            found of the original text with the specified replacement
            text.
        Args:
            filename(str): file in which the text is to be replaced.
            orig_text(str): text to be replaced.
            replace_text(str): text to use as replacement.
        """
        replace_cmd = \
        self.redhat.get_replace_str_in_file_cmd(orig_text,
                                                replace_text,
                                                filename)
        _, _, rtcode = \
        self.run_command(self.ms_node, replace_cmd,
                         default_asserts=True, su_root=True)
        self.assertEqual(0, rtcode)

    @staticmethod
    def remove_snapshot_xml_json(file_list):
        """
        Description:
            Searches through the received file list and removes any
            xml snapshot json files found.
            The parsed list is returned.
        Args:
            file_list(list): list of files received. This list is returned
                             without any snapshot xml entries
        """
        # Find the list indexes of all entries containing 'load snapshot'
        indexes = \
        [x for x, item in enumerate(file_list) if 'load_snapshot' in item]

        # Reverse the index list for removal sequencing
        indexes.sort(reverse=True)

        # Remove all snapshot xml entries found in the list
        # working from the highest to the lowest as otherwise
        # indexes would no longer align correctly due to reordering
        for entry in indexes:
            file_list.pop(entry)

        return file_list

    def get_file_size(self, file_path):
        """
        Description:
            Function to retrieve the size of the specified
            file.
        Args:
            file_path(str): Path to the file to be checked.
        Returns:
           str.
        """
        ls_cmd = '/bin/ls -la {0}'.format(file_path)
        stdout, _, _ = \
        self.run_command(self.ms_node, ls_cmd, su_root=True)
        return stdout[0].split(' ')[4]

    def validate_phases(self, successful_phases):
        """
        Description:
            Tests that all tasks in a completed or stopped plan are in the
            expected state
        Args:
            successful_phases(list of int): All tasks in these phases should
            be in state Success
        """
        plan = self.get_plan_data(self.ms_node)

        for phase in plan['phases']:
            if phase in successful_phases:
                for tasks in plan['phases'][phase].values():
                    for task in tasks:
                        self.assertEqual('Success',
                            task.get('state'),
                            "Task '{0}' in state '{1}'. Expected 'Success'."\
                            .format(task.get('desc'), task.get('state')))
            else:
                for tasks in plan['phases'][phase].values():
                    for task in tasks:
                        self.assertEqual('Initial', task.get('state'),
                            "Task '{0}' in state '{1}'. Expected 'Initial'."\
                            .format(task.get('desc'), task.get('state')))

    def run_cmd_with_error_validation(self, cmd, expected_error, expected_rc):
        """
        Description:
            Runs a command on the MS which is expected to return an error in
            either stdout or sterr, and asserts that the expected error and RC
            is found.
        Args:
            cmd(str): A command to run on the MS
            expected_error(str): An error expected to be found in response to
            cmd
            expected_rc (int): The expected return code from the command in cmd
        """

        stdout, stderr, ret_code = self.run_command(self.ms_node, cmd)

        # Assert expected error is found in any items in stdout or stderr lists
        error_in_stdout = any(expected_error in err for err in stdout)
        error_in_stderr = any(expected_error in err for err in stderr)
        error_found = error_in_stdout or error_in_stderr

        self.assertTrue(error_found,
                        'Expected error "{0}" was not found'.format(
                        expected_error))

        # Assert expected RC is returned
        self.assertEqual(
                    expected_rc,
                    ret_code,
                    'Return code of "{0}" was expected'.format(expected_rc))

    @staticmethod
    def get_rest_cmd(data, path, args):
        """
        Description:
            Builds a LITP rest interface command
        Args:
            data(str): A JSON to be sent with POST requests
            path(str): The model path associated with the command
            args(str): Additional curl arguements to be used.
        Returns:
            LITP rest interface command as a string
        """
        cmd_start = "curl -H 'Content-Type:application/json' -H "
        cmd_auth = "'Authorization: Basic bGl0cC1hZG1pbjpsaXRwX2FkbWlu' "
        if data == "":
            cmd_data = ""
        else:
            cmd_data = "-d '{0}' ".format(data)
        cmd_path = "https://localhost:9999/litp/rest/v1/{0} ".format(path)

        return "".join([cmd_start, cmd_auth, cmd_data, cmd_path, args])

    @attr('all', 'non-revert', 'robustness', 'robustness_tc01', 'rob_p1')
    def test_01_restart_litpd_config(self):
        """
        Description:
            Restart litpd service while plan is running.
                1. On MS when tasks are being run on the MS
                2. On MS when tasks are being run on the nodes
            It is expected that the plan will stop due to the litpd restart.
            Recreating and running the plan should be successful.
        Actions:
            1. Create the packages
            2. Inherit packages
            3. Create and run the plan
            4. Restart of litpd service on MS when package
               installed on selected nodes , causing the plan to stop.
                5. Restart litpd service on MS.
                6. Recreate and run the plan
            7. Check if plan completed successfully.
            8. Check the number of LITP services running.
        Results:
            1. The litpd service is restarted successfully
            2. The plan stopped and the retry plan is completed successfully
            3. Only 1 instance of litp process should be running
        """
        timeout = 10
        # Creates the config plan
        self.log('info', 'Creates the config plan')
        task_desc_ms, task_desc_mn = self.create_config_plan()

        task_running_ms = self.wait_for_task_state(self.ms_node, task_desc_ms,
                                 test_constants.PLAN_TASKS_RUNNING,
                                 timeout_mins=timeout,
                                 ignore_variables=False)
        # Check to see if task was in expected state
        self.log('info', 'Check to see if task was in expected state')
        self.assertTrue(task_running_ms,
                        "Task did not reach running state in specified time")

        # Get all started phases at time of restart litpd
        self.log('info', 'Get all started phases at time of restart litpd')
        started_phases_at_litpd_stop = \
                    self.get_tasks_by_state(self.ms_node, 'Running').keys() \
                    + self.get_tasks_by_state(self.ms_node, 'Success').keys()

        # Restart litpd service during MS config tasks
        self.log('info', 'Restart litpd service during MS config tasks')
        self.restart_litpd_service(self.ms_node)

        # Wait for plan to stop
        plan_stopped = self.wait_for_plan_state(self.ms_node,
                                                test_constants.PLAN_STOPPED)
        self.assertTrue(plan_stopped,
                        "Plan was expected to be stopped")

        # Check that tasks in started phases are successful
        self.log('info',
        'Check that phases started at "litpd restart" time completed '
           'successfully, and all others are in "Initial" state')
        self.validate_phases(started_phases_at_litpd_stop)

        # Recreate and run the plan
        self.log('info', 'Recreate and run the plan')
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        task_running_mn = \
            self.wait_for_task_state(self.ms_node, task_desc_mn,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.log('info', 'Check to see if task was in expected state')
        self.assertTrue(task_running_mn,
                        "Task did not reach running state in specified time")

        # Get all started phases at time of restart litpd
        self.log('info', 'Get all started phases at time of restart litpd')
        started_phases_at_litpd_stop = \
                    self.get_tasks_by_state(self.ms_node, 'Running').keys() \
                    + self.get_tasks_by_state(self.ms_node, 'Success').keys()

        # Restart litpd service during MN config tasks
        self.log('info', 'Restart litpd service during MN config tasks')
        self.restart_litpd_service(self.ms_node)

        # Wait for plan to stop
        plan_stopped = self.wait_for_plan_state(self.ms_node,
                                                test_constants.PLAN_STOPPED)
        self.assertTrue(plan_stopped,
                        "Plan was expected to be stopped")

        # Check that tasks in started phases are successful
        self.log('info',
        'Check that phases started at "litpd restart" time completed '
           'successfully, and all others are in "Initial" state')
        self.validate_phases(started_phases_at_litpd_stop)

        # Recreate and run the plan
        self.log('info', 'Recreate and run the plan')
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        # 9. Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                        test_constants.PLAN_COMPLETE,
                                        self.timeout_mins)
        self.assertTrue(completed_successfully,
                        "Plan didn't finished successfully.")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.log('info', 'CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS'
                            'RUNNING')
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness',
          'rob_p1', 'robustness_tc01_callback')
    def test_01_restart_litpd_callback(self):
        """
        Description:
            Restart the litpd service while plan is running
                1. On the Management Node when changes
                   (new service group added) are applied to the Managed Node
            It is expected that the plan will stop due to the litpd restart.
            Recreating and running the plan should be successful.
        Actions:
            1. Sets up and runs plan that contains CallbackTasks
            2. Wait for Callback task
            3. Run litpd restart on the management node
            4. Wait for plan to stop
            5. The following actions occur in the retry callback function:
                a. Remove VCS cluster service items as it has been partially
                   created in the initial stopped plan
                b. Create removal plan
                c. Run removal plan
                d. Wait for removal plan to complete successfully
                e. Create the VCS cluster service items again
                f. Check that retry plan is successful
        Results:
            1. The litpd service is restarted successfully
            2. The plan stopped and the retry plan is completed successfully
            3. Only 1 instance of litp process should be running
        """

        # 1. Set up and run plan that contains CallbackTasks
        self.log('info', '1. Set up and run plan that contains CallbackTasks')
        self.set_up_callback_tasks()

        service = "litpd"
        package_name = ["EXTR-lsbwrapper40"]

        # 2. Wait for Callback task.
        self.log('info', '2. Wait for Callback task.')
        task_running = \
            self.wait_for_task_state(
                self.ms_node,
                'Create application resource '
                    '"Res_App_c1_vcsEXTR_lsbwrapper39_EXTR_lsbwrapper39"',
                test_constants.PLAN_TASKS_RUNNING, seconds_increment=1,
                ignore_variables=False)
        # Check to see if task was in expected state
        self.log('info', 'Check to see if task was in expected state')
        self.assertTrue(task_running,
                        "Task did not reach running state in specified time")
        self.log("info", "Callback Task is running")
        # Get all started phases at time of restart litpd
        self.log('info', 'Get all started phases at time of restart litpd')
        started_phases_at_litpd_stop = \
                    self.get_tasks_by_state(self.ms_node, 'Running').keys() \
                    + self.get_tasks_by_state(self.ms_node, 'Success').keys()

        self.log("info", "Running service {0} restart on node '{1}'"
                 .format(service, self.ms_node))

        # 3. Run litpd restart on the management node
        self.log('info', '3. Run litpd restart on the management node')
        self.restart_litpd_service(self.ms_node)

        # Wait for plan to stop
        plan_stopped = self.wait_for_plan_state(self.ms_node,
                                                test_constants.PLAN_STOPPED)
        self.assertTrue(plan_stopped,
                        "Plan was expected to be stopped")

        # Check that tasks in started phases are successful
        self.log('info',
        'Check that phases started at "litpd restart" time completed '
           'successfully, and all others are in "Initial" state')
        self.validate_phases(started_phases_at_litpd_stop)

        # Assert that the retry plan is successful
        self.log('info', 'Assert that the retry plan is successful')
        self.assertTrue(self._retry_callback_plan(package_name),
                        "Retry plan has failed")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.log('info', 'Check that only a single instance of LITP is'
                            'running')
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc02')
    def test_02_restart_httpd(self):
        """
        Description:
            Restart httpd passenger service while plan is running.
                1. On MS when config tasks are being run on the MS
                2. On MS when config tasks are being run on the nodes
            It is expected that the httpd service will recover
            in time and allow the plan to succeed.
        Actions:
            1. Create the packages
            2. Inherit packages
            3. Create and run the plan
            4. Restart of httpd service on MS when package installed
               on desired nodes
            For each node do:
                5. Check if desired task exists
                6. Wait for the starting of the instalation
                    of telnet package on the chosen nodes
                7. Restart httpd service on MS
            8. Check if plan completed successfully
            9. Check the number of LITP services running.
        Results:
            1. The httpd service is restarted successfully
            2. The plan should run successfully
            3. Only 1 instance of litp process should be running
        """
        timeout = 10
        service = "httpd"

        # Check that httpd is running
        self.get_service_status(self.ms_node, service)
        # Creates the config plan
        task_desc_ms, task_desc_mn = self.create_config_plan()

        task_running_ms = \
            self.wait_for_task_state(self.ms_node,
                                     task_desc_ms,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running_ms,
                        "Task did not reach running state in specified time")
        # 6. Restart httpd service on MS
        self.restart_service_on_task(task_desc_ms, service, self.ms_node)

        task_running_mn = \
            self.wait_for_task_state(self.ms_node,
                                     task_desc_mn,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running_mn,
                        "Task did not reach running state in specified time")

        self.restart_service_on_task(task_desc_mn, service, self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)

        self.execute_cli_showplan_cmd(self.ms_node, '-j')

        # 9. Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
        self.assertTrue(completed_successfully,
                        "Plan didn't finished successfully.")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc03')
    def test_03_restart_puppet(self):
        """
        Description:
            Restart puppet (agent) service while plan is running.
                1. On MS when config tasks are being run on the MS
                2. On Managed Node when config tasks are being run on the nodes
            It is expected that the puppet service will recover in time and
            allow the plan to complete successfully.
        Actions:
            1. Create the packages
            2. Inherit packages
            3. Create and run the plan
            4. Restart of puppet service on node when package
               installed on desired nodes
            For each node do:
                5. Check if desired task exists
                6. Wait for the starting of the instalation
                    of telnet package on the node
                7. Restart puppet service on desired node
            8. Check if plan completed successfully
            9. Check the number of LITP services running.
        Results:
            1. The puppet service is restarted successfully
            2. The plan should run successfully
            3. Only 1 instance of litp process should be running
        """
        timeout = 10

        # Creates the config plan
        task_desc_ms, task_desc_mn = self.create_config_plan()

        task_running_ms = \
            self.wait_for_task_state(self.ms_node,
                                     task_desc_ms,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running_ms,
                        "Task did not reach running state in specified time")
        # 6. Restart puppet service on MS
        self.restart_service_on_task(task_desc_ms, 'puppet', self.ms_node)

        task_running_mn = \
            self.wait_for_task_state(self.ms_node,
                                     task_desc_mn,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running_mn,
                        "Task did not reach running state in specified time")
        self.restart_service_on_task(task_desc_mn, 'puppet', self.target)
        self.execute_cli_showplan_cmd(self.ms_node)

        self.execute_cli_showplan_cmd(self.ms_node, '-j')

        # 9. Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
        self.assertTrue(completed_successfully,
                        "Plan didn't finished successfully.")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc04')
    def test_04_restart_mcollective_callback(self):
        """
        Description:
            Restart of mcollective service while a plan is running.
                1. On MS when callback tasks are being run on the MS.
                2. On Managed Node when callback tasks are being run
                on the nodes.
            It is expected that the mcollective service will recover in time
            and allow the plan to succeed.
        Actions:
            1. Sets up and runs plan that contains CallbackTasks
            2. Wait for Callback task
            3. Run mcollective restart on each of the peer nodes and MS
            4. Wait for plan to complete successfully
            5. Check the number of LITP services running.
        Results:
            1. The mcollective service restarts successfully each time
            2. The plan is completed successfully
            3. Only one LITP service is running
        """

        # 1.  Set up and run plan that contains CallbackTasks
        self.set_up_callback_tasks()

        service = "mcollective"
        package_name = "EXTR-lsbwrapper40"

        # 2. Wait for Callback task.
        task_running = self.wait_for_task_state(
            self.ms_node,
            'Create VCS service group "Grp_CS_c1_EXTR_lsbwrapper39"',
            test_constants.PLAN_TASKS_RUNNING, seconds_increment=1,
            ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running,
                        "Task did not reach running state in specified time")

        self.log("info", "Callback Task is running")

        # 3. Run mcollective restart on each of the peer nodes and MS
        self.log("info", "Running mcollective restart on node '{0}'"
                 .format(self.ms_node))
        self.restart_service(self.ms_node, service)

        for node in self.peer_nodes[0:2]:
            self.log("info", "Running mcollective restart on node '{0}'"
                     .format(node["name"]))
            self.restart_service(node["name"], service)

        # 4. Wait for plan to complete successfully
        plan_state = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_COMPLETE)

        # litp remove added as cleanup was failing due to inheritance
        self.execute_cli_remove_cmd(self.ms_node,
                                    "{0}/services/{1}/applications/{1}"
                                    .format(self.cluster_url, package_name))

        # Fails testcase if plan fails
        self.assertTrue(plan_state, "Plan has failed. Expected a successful "
                                    "plan")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness',
          'rob_p1_2', 'robustness_tc04_config')
    def test_04_restart_mcollective_config(self):
        """
        Description:
            Restart of mcollective service while a plan is running.
                1. On MS when config tasks are being run on the MS
                2. On Managed Node when config tasks are being run on the nodes
            It is expected that if the mcollective service does not recover in
            time to allow the plan to succeed, a retry plan will succeed
            afterwards
        Actions:
            1. Sets up and runs plan that contains Config Tasks
            2. Wait for Config task on the MS
            3. Stop puppet service on MS
            4. Run mcollective restart on the MS
            5. Wait for Config task on the peer node
            6. Stop puppet service on peer node
            7. Run mcollective restart on the peer node
            8. Wait for plan to complete successfully either first time or
            after a retry
            9. Check the number of LITP services running.
        Results:
            1. The mcollective service restarts successfully each time
            2. The plan is completed successfully either first time or
            after a retry
            3. Only one LITP service is running
        """

        service = "mcollective"
        timeout = 10

        # 1. Sets up and runs plan that contains Config Tasks
        task_desc_ms, task_desc_mn = self.create_config_plan()

        # 2. Wait for Config task on the MS
        self.wait_for_task_state(self.ms_node, task_desc_ms,
                                 test_constants.PLAN_TASKS_RUNNING,
                                 timeout_mins=timeout,
                                 ignore_variables=False)

        # 3. Stop puppet service on MS
        self.stop_service(self.ms_node, "puppet")

        # 4. Run mcollective restart on the MS
        self.restart_service(self.ms_node, service)

        # 5. Wait for Config task on the peer node
        self.wait_for_task_state(self.ms_node, task_desc_mn,
                                 test_constants.PLAN_TASKS_RUNNING,
                                 timeout_mins=timeout,
                                 ignore_variables=False)

        # 6. Stop puppet service on peer node
        self.stop_service(self.target, "puppet")

        # 7. Run mcollective restart on the peer node
        self.restart_service(self.target, service)

        # 8. Wait for plan to complete successfully
        plan_state = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_COMPLETE)

        if not plan_state:
            # Recreate and run the plan
            self.log('info', 'Recreate and run the plan')
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_showplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)
            # Wait for retry plan to complete successfully
            plan_state = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_COMPLETE)

            # Fails testcase if plan fails
            self.assertTrue(plan_state,
                                "Plan has failed. Expected a successful plan")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc05')
    def test_05_restart_network_service(self):
        """
        Description:
            Restart the network service while plan with
            network update tasks are running
                1. On MS when tasks are being run on the MS.
                2. On Managed Node when tasks are being run on the nodes.
            It is expected that the network service will recover in time and
            allow the plans to succeed.
        Actions:
            1. Update ms bond arp_interval value
            2. Update node bonds arp_interval value
            3. create and run plan
            4. reboot network service while tasks are running on the ms
            5. reboot the network service while tasks are being run on the mn
            6. check if plan has completed successfully
            7. Check the number of LITP services running.
        Results:
            1. Plan should run to completion
            2. arp_interval values should be updated
            3. Only one LITP service is running
        """
        # Value that arp_interval will be updated to
        updated_arp_interval_value = "6000"

        # Get path to ms bond interface
        get_bond_path_ms = self.find(self.ms_node,
                                     self.ms_path,
                                     "bond",
                                     True)

        # Get path to nodes bond interface
        get_bond_path_mn = self.find(self.ms_node,
                                     self.target_url,
                                     "bond",
                                     True)

        bond_device_name_ms = self.get_props_from_url(self.ms_node,
                                               get_bond_path_ms[0],
                                               "device_name")

        bond_device_name_mn = self.get_props_from_url(self.ms_node,
                                               get_bond_path_mn[0],
                                               "device_name")

        self.assertTrue(get_bond_path_ms != "", "Bond path not found on ms")
        self.assertTrue(get_bond_path_mn != "", "Bond path not found on mn")

        #  Description of Tests Tasks
        task_desc_ms = 'Update bond "{0}" on node "{1}"'.\
                        format(bond_device_name_ms,
                               self.ms_node)
        task_desc_mn = 'Update bond "{0}" on node "{1}"'.\
                        format(bond_device_name_mn,
                               self.target)

        # 1. Update ms bond arp_interval value
        self.execute_cli_update_cmd(self.ms_node,
                                    get_bond_path_ms[0],
                                    props='arp_interval=' +
                                          updated_arp_interval_value,
                                    expect_positive=True)

        # 2. Update mn bond arp_interval value
        self.execute_cli_update_cmd(self.ms_node,
                                    get_bond_path_mn[0],
                                    props='arp_interval=' +
                                          updated_arp_interval_value,
                                    expect_positive=True)

        # 3. Create,Show and Run plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        # 4. Restart network service on the ms
        # during plan to update network on ms
        self.restart_service_on_task(task_desc_ms,
                                     "network",
                                     self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)

        # 5. Restart network service on the node
        #    during plan to update network on node
        self.restart_service_on_task(task_desc_mn,
                                     "network",
                                     self.target)

        self.execute_cli_showplan_cmd(self.ms_node)

        # 6. Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
        self.assertTrue(completed_successfully,
                        "Plan didn't finished successfully.")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc06')
    def test_06_restart_vcs(self):
        """
        Description:
            Restart the VCS service while plan is running
                1. On the Managed Node when changes (new service group added)
                   are applied to the Managed Node
            It is expected that the plan will fail when vcs is restarted.
            Removal of the Service group, recreating and running the plan
            should succeed.
        Actions:
            1. Sets up and runs plan that contains CallbackTasks
            2. Wait for Callback task
            3. Run vcs restart on each of the peer nodes
            4. Wait for plan to fail.
            5. Remove VCS cluster service items as it has been partially
               created
            6. Create removal plan
            7. Run removal plan
            8. Wait for removal plan to complete successfully
            9. Create the VCS cluster service items again
            10. Check that retry plan is successful
            11. Check the number of LITP services running.
        Results:
            1. The vcs service restarts successfully each time
            2. The plan is completed successfully
            3. Only one LITP service is running
        """

        # 1.  Set up and run plan that contains CallbackTasks
        self.set_up_callback_tasks()

        service = "vcs"
        package_name = "EXTR-lsbwrapper40"

        # 2. Wait for Callback task.
        task_running = self.wait_for_task_state(
            self.ms_node,
            'Create VCS service group "Grp_CS_c1_EXTR_lsbwrapper39"',
            test_constants.PLAN_TASKS_RUNNING,
            seconds_increment=1, ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running,
                        "Task did not reach running state in specified time")
        self.log("info", "Callback Task is running")

        # 3. Run vcs restart on each of the peer nodes
        for node in self.peer_nodes[0:2]:
            self.log("info", "Running service {0} restart on node '{1}'"
                     .format(service, node["name"]))
            self.restart_service(node["name"], service)
            # Sleep to avoid triggering TORF-182976
            time.sleep(10)

        for node in self.peer_nodes[0:2]:
            # Wait for cmd 'hastatus -sum' to have return code 0
            cmd = "hastatus -sum"
            self.wait_for_cmd(node["name"], cmd, 0, su_root=True)

        # 4. Wait for plan to fail
        plan_fail = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_FAILED)
        self.assertTrue(plan_fail, "Plan did not fail as expected")

        # Wait added to allow service groups to start up fully
        self.wait_for_service_group_start(self.target)

        self.log("info", "Initial plan has failed.")
        self.log("info", "Attempting to retry")

        # 7. Remove VCS cluster service items as it has been partially
        #    created
        self.execute_cli_remove_cmd(
            self.ms_node, "{0}/services/{1}/applications/{1}"
                .format(self.cluster_url, package_name))

        self.execute_cli_remove_cmd(
            self.ms_node, "{0}/services/{1}".format(self.cluster_url,
                                                    package_name))

        # 8. Create removal plan
        self.log("info", "Creating remove service group plan")
        self.execute_cli_createplan_cmd(self.ms_node)

        # 9. Run removal plan
        self.log("info", "Running remove service group plan")
        self.execute_cli_runplan_cmd(self.ms_node)

        # 10. Wait for removal plan to complete successfully
        plan_success = self.wait_for_plan_state(self.ms_node,
                                                test_constants.PLAN_COMPLETE)
        self.assertTrue(plan_success, "Plan did not succeed as expected")

        # Node list names used in creating a vcs clustered service
        node_list_name1 = (self.peer_nodes[0]["url"].split("/"))[-1]
        node_list_name2 = (self.peer_nodes[1]["url"].split("/"))[-1]

        # 11. Create the VCS cluster service items again
        self.execute_cli_create_cmd(self.ms_node,
            "{0}/services/{1}".format(self.cluster_url, package_name),
            "vcs-clustered-service",
            "active=2 standby=0 name=vcs111 online_timeout=220"
            " node_list={0},{1}".format(node_list_name2, node_list_name1))

        self.execute_cli_create_cmd(
            self.ms_node, "{0}/services/{1}/ha_configs/conf1"
                .format(self.cluster_url, package_name),
            "ha-service-config", "status_interval=30 status_timeout=20 "
                                 "restart_limit=2 startup_retry_limit=2")

        self.execute_cli_inherit_cmd(self.ms_node,
            "{0}/services/{1}/applications/{1}".format(self.cluster_url,
                                                       package_name),
            "/software/services/{0}".format(package_name))

        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        plan_state = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_COMPLETE)

        # litp remove added as cleanup was failing due to inheritance
        self.log("info", "Removal of service application added as cleanup was"
                         " failing due to inheritance")
        self.execute_cli_remove_cmd(self.ms_node,
                                    "{0}/services/{1}/applications/{1}"
                                    .format(self.cluster_url,
                                            package_name))
        # 12. Check that retry plan is successful
        self.assertTrue(plan_state, "Retry plan failed")

        self.log("info", "Retry plan has completed successfully")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc07')
    def test_07_restart_libvirt(self):
        """
        Description:
            Restart the libvirt service while plan is running
                1. On the Management Server while a plan is running to deploy
                   some updated networking configuration on a VM on MS.
                2. On the Managed Node while a plan is running to deploy some
                   updated networking configuration on the VM on a Peer node.
            It is expected that the libvirt service will recover in time and
            allow the plan to succeed.
        Actions:
            For both the MS and Node
                1. Call method to update a vms configuration and create plan.
                2. While the plan is running to update the vm configuration
                restart libvirt.
        Results:
            1. The libvirt service is restarted successfully
            2. The plan should run successfully
        """
        # Service that will be restarted on peer node
        service_to_restart = "libvirtd"

        # Calling method to update mn vm config and return task desc
        self.log("info", "Update MN VM config")
        mn_task_desc = self.update_node_vm_configuration()

        # Restart the service using method and
        # pass service to restart and task desc
        self.log("info", "Prepare to restart libvirtd during MN task")
        self.restart_service_on_task(mn_task_desc,
                                     service_to_restart,
                                     self.target)
        # Wait for plan to update Vm on MN to pass
        self.log("info", "Wait for plan to update VM on MN to pass")
        plan_complete_mn = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=10)
        self.assertTrue(plan_complete_mn, "Plan did not complete successfully"
                                          "in the specified time")

        # Task description to restart service on
        #  is returned when update ms vm config is successful
        self.log("info", "Update MS VM config")
        ms_task_desc = self.update_ms_vm_configuration()

        # Restart the service using method and
        # pass service to restart and task desc
        self.log("info", "Prepare to restart libvirtd during MS task")
        self.restart_service_on_task(ms_task_desc,
                                     service_to_restart,
                                     self.ms_node)

        # Wait for plan to update Vm on MS to pass
        self.log("info", "Wait for plan to update VM on MS to pass")
        plan_complete_ms = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=10)
        # Check if plan state was expected
        self.assertTrue(plan_complete_ms, "Plan did not complete successfully "
                                          "in the specified time")

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc08')
    def test_08_kill_litpd_config(self):
        """
        Description:
            Kill litpd service while plan is running.
                1. On MS when config tasks are being run on the MS.
                2. On MS when config tasks are being run on the nodes.
            It is expected that the plan will stop when litpd is killed.
            Recreating and running the plan should succeed.
        Actions:
            1. Create the packages
            2. Inherit packages
            3. Create and run the plan
            For each node do:
                4. Check if desired task exists and in running state
                5. Wait for the starting of the instalation
                    of telnet package on the chosen nodes
                6. Kill litpd service on MS , this will cause the plan to stop.
                7. Start litpd service on MS
                8. Recreate and run the plan.
            9. Check if plan completed successfully
            10. Check the number of LITP services running.
        Results:
            1. The litp service is killed
            2. The plan should stop
            3. The service is started successfully
            4. The recreated plan should succeed
            5. Only 1 instance of litp process should be running
        """
        timeout = 10

        # Creates the config plan
        self.log("info", "Step: Creates the config plan")
        task_desc_ms, task_desc_mn = self.create_config_plan()

        task_running_ms = \
            self.wait_for_task_state(self.ms_node,
                                     task_desc_ms,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.log("info", "Step: Check to see if task was in expected state")
        self.assertTrue(task_running_ms,
                        "Task did not reach running state in specified time")

        # Get all started phases at time of kill litpd
        self.log('info', 'Get all started phases at time of kill litpd')
        started_phases_at_litpd_kill = \
                    self.get_tasks_by_state(self.ms_node, 'Running').keys() \
                    + self.get_tasks_by_state(self.ms_node, 'Success').keys()

        # 7/8. kill litpd service on MS
        self.log("info", "Step: kill litpd service on MS")
        self.kill_service_on_config_task(task_desc_ms, 'litpd', self.ms_node)

        # Wait for plan to stop
        plan_stopped = self.wait_for_plan_state(self.ms_node,
                                                test_constants.PLAN_STOPPED)
        self.assertTrue(plan_stopped,
                        "Plan was expected to be stopped")

        # Check that tasks in started phases are successful
        self.log('info',
        'Check that phases started at "litpd kill" time completed '
           'successfully, and all others are in "Initial" state')
        self.validate_phases(started_phases_at_litpd_kill)

        #  Recreate and run the plan
        self.log("info", "Step: Recreate and run the plan")
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        task_running_mn = \
            self.wait_for_task_state(self.ms_node,
                                     task_desc_mn,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.log("info", "Step: Check to see if task was in expected state")
        self.assertTrue(task_running_mn,
                        "Task did not reach running state in specified time")

        # Get all started phases at time of kill litpd
        self.log('info', 'Get all started phases at time of kill litpd')
        started_phases_at_litpd_kill = \
                    self.get_tasks_by_state(self.ms_node, 'Running').keys() \
                    + self.get_tasks_by_state(self.ms_node, 'Success').keys()

        # 7/8 kill litpd service on Mn
        self.log("info", "Step: kill litpd service on Mn")
        self.kill_service_on_config_task(task_desc_mn, 'litpd', self.ms_node)

        # Wait for plan to stop
        plan_stopped = self.wait_for_plan_state(self.ms_node,
                                                test_constants.PLAN_STOPPED)
        self.assertTrue(plan_stopped,
                        "Plan was expected to be stopped")

        # Check that tasks in started phases are successful
        self.log('info',
        'Check that phases started at "litpd kill" time completed '
           'successfully, and all others are in "Initial" state')
        self.validate_phases(started_phases_at_litpd_kill)

        #  Recreate and run the plan
        self.log("info", "Step: Recreate and run the plan")
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        # 9. Check if plan completed successfully
        self.log("info", "Step: Check if plan completed successfully")
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
        self.assertTrue(completed_successfully,
                        "Plan didn't finished successfully.")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.log("info", "Step: CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS"
                            "RUNNING")
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness',
          'rob_p1', 'robustness_tc08_minus9')
    def test_08_kill_minus9_litpd_config(self):
        """
        Description:
            Kill -9 litpd service while plan is running.
                1. On MS when config tasks are being run on the MS.
                2. On MS when config tasks are being run on the nodes.
            It is expected that using kill -9 on litpd will result in the plan
            staying running and restarting the litpd service should query the
            backend DB and reconnect. Plan and tasks are expected to complete
            successfully
        Actions:
            1. Create the packages
            2. Inherit packages
            3. Create and run the plan
            4. Wait for config tags to be running on MS
            5. Kill then restart litpd service on MS when
               package installed on desired nodes
            For each node do:
                6. Check if desired task exists
                7. Wait for the starting of the installation
                    of telnet package on the chosen nodes
                8. Kill litpd service on MS
                9. Start litpd service on MS
            10. Ensure plan completes successfully
            11. Check the number of LITP services running.
        Results:
            1. The litp service is killed
            2. The service is started successfully
            3. The plan should complete successfully
            4. Only 1 instance of litp process should be running
        """
        self.log("info", "Step 1-3: Setup and run plan")
        timeout = 10
        # Creates the config plan
        task_desc_ms, task_desc_mn = self.create_config_plan()

        self.log("info", "Step 4: Wait for MS install task to be running")

        # Wait for task state
        task_running_ms = \
            self.wait_for_task_state(self.ms_node,
                                     task_desc_ms,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running_ms,
                        "Task did not reach running state in specified time")

        self.log("info",
                    "Step 5: Kill litp during MS install task and relaunch")
        # Kill -9 of litp service on node on specified task
        self.kill_service_on_config_task(task_desc_ms, 'litpd', self.ms_node,
                                         kill_arg='-9')

        self.log("info", "Step 6-7: Wait for MN install task to be running")
        task_running_mn = \
            self.wait_for_task_state(self.ms_node,
                                     task_desc_mn,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running_mn,
                        "MN install task did not reach running state in"
                        "specified time")

        self.log("info",
                    "Step 8-9: Kill litp during MN install task and relaunch")
        # Kill -9 of litp service on node on specified task
        self.kill_service_on_config_task(task_desc_mn, 'litpd', self.ms_node,
                                         kill_arg='-9')

        self.log("info", "Step 10: Check plan completes successfully")
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
        self.assertTrue(completed_successfully,
                        "Plan didn't complete successfully.")

        self.log("info", "Step 11: Check the number of LITP services running")
        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness',
          'rob_p1', 'robustness_tc08_callback')
    def test_08_kill_litpd_callback(self):
        """
        Description:
            Kill litpd service on the MS when callback tasks are running.
            It is expected that killing the litpd service will cause the plan
            to stop.
            Recreating and running the plan should succeed.
        Actions:
            1.  Set up and run plan that contains CallbackTasks
            2.  Wait for Callback task
            3.  Stop litpd service on the MS using 'kill' command , causing the
                plan to stop
            4.  Start litpd service after kill
            5.  Remove VCS cluster service items as it has been partially
                created
            6.  Create removal plan
            7.  Run removal plan
            8.  Wait for removal plan to complete successfully
            9. Create the VCS cluster service items again
            10. Check that retry plan is successful
        Results:
            1. The litp service is killed
            2. The plan stops
            3. The service is started successfully
            4. The recreated plan should run successfully
            5. Only 1 instance of litp service should be running
        """

        self._stop_litpd_callback(kill=True)

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1',
          'robustness_tc08_minus9_callback')
    def test_08_kill_minus9_litpd_callback(self):
        """
        Description:
            Kills litpd on the MS during Callback Tasks using 'kill -9'.
            It is expected that using kill -9 on litpd will result in the plan
            staying running and restarting the litpd service should query the
            backend DB and reconnect. Plan and tasks are expected to complete
            successfully
        Actions:
            1.  Set up and run plan that contains CallbackTasks
            2.  Wait for Callback task
            3.  Stop litpd service on the MS using 'kill -9' command
            4.  Start litpd service after kill
        Results:
            1. The litp service is killed with -9 signal
            2. The service is started successfully
            3. The plan should run successfully
            4. Only 1 instance of litp service should be running
        """

        self._stop_litpd_callback(kill=True, killarg="-9")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness',
          'rob_p1', 'robustness_tc09')
    def test_09_kill_httpd(self):
        """
        Description:
            Kill httpd (passenger) service while plan is running.
                1. On MS when config tasks are being run on the MS
                2. On MS when config tasks are being run on the nodes
            It is expected that the httpd service will recover in time for the
            plan to succeed.
        Actions:
            1. Create a package
            2. Inherit package onto ms and node
            3. Create and run the plan
            4. Check if desired task exists
            5. Kill then start  httpd service on MS and node when
               package is installing on desired nodes
            6. Check if plan completed successfully
            7. Check the number of LITP services running.
        Results:
            1. The httpd service is killed
            2. The service is started successfully
            3. The plan should run successfully
            4. Only 1 instance of litp service should be running
        """
        timeout_mins = 20
        test_pkg3 = "firefox"
        # 1. Create a package
        pkg_url3 = self._create_package(test_pkg3)

        # 2. Inherit packages on ms and node 1
        # Inherit command for ms package 1
        self._create_package_inheritance(self.ms_path, test_pkg3, pkg_url3)

        # Inherit command for node 1 package 1
        self._create_package_inheritance(self.target_url, test_pkg3, pkg_url3)

        # 3. Create and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        # 5. Kill httpd service on MS and node when package
        #    is being installed on selected node
        task_desc_ms = 'Install package "{0}" on node "{1}"'\
            .format(test_pkg3, self.ms_node)

        task_desc_mn = 'Install package "{0}" on node "{1}"'.\
                        format(test_pkg3, \
                        self.target)

        task_state_ms = self.get_task_state(self.ms_node, task_desc_ms, \
                    ignore_variables=False)

        task_state_mn = self.get_task_state(self.ms_node, task_desc_mn, \
                            ignore_variables=False)
        self.assertNotEqual(task_state_ms, test_constants.CMD_ERROR, \
                "Task doesn't exist")
        self.assertNotEqual(task_state_mn, test_constants.CMD_ERROR, \
                        "Task doesn't exist")

        #  Kill  httpd service on MS
        self.kill_service_on_config_task(task_desc_ms, 'httpd', \
                                         self.ms_node, timeout_mins)

        self.execute_cli_showplan_cmd(self.ms_node)

        #  Kill  httpd service on Mn
        self.kill_service_on_config_task(task_desc_mn, 'httpd', \
                                         self.ms_node, timeout_mins)

        self.execute_cli_showplan_cmd(self.ms_node)
        # 6. Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
        self.assertTrue(completed_successfully,
                        "Plan didn't finished successfully.")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness',
          'rob_p2', 'robustness_tc09_minus9')
    def test_09_kill_minus9_httpd(self):
        """
        Description:
            Kill -9 httpd (passenger) service while plan is running.
                1. On MS when config tasks are being run on the MS
                2. On MS when config tasks are being run on the nodes
            It is expected that the http service recover in time for the plan
            to succeed.
        Actions:
            1. Create a package
            2. Inherit package onto ms and node
            3. Create and run the plan
            4. Check if desired task exists
            5. Kill then start  httpd service on MS and node when
               package is installing on desired nodes
            6. Check if plan completed successfully
            7. Check the number of LITP services running.
        Results:
            1. The httpd service is killed with -9 signal
            2. The service is started successfully
            3. The plan should run successfully
            4. Only 1 instance of litp service should be running
        """
        test_pkg3 = "firefox"
        # 1. Create a package
        pkg_url3 = self._create_package(test_pkg3)

        # 2. Inherit packages on ms and node 1
        # Inherit command for ms package 1
        self._create_package_inheritance(self.ms_path, test_pkg3, pkg_url3)

        # Inherit command for node 1 package 1
        self._create_package_inheritance(self.target_url, test_pkg3, pkg_url3)

        # 3. Create and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        # 5. Kill httpd service on MS and node when package
        #    is being installed on selected node
        task_desc_ms = 'Install package "{0}" on node "{1}"'\
            .format(test_pkg3, self.ms_node)

        task_desc_mn = 'Install package "{0}" on node "{1}"'.\
                        format(test_pkg3, \
                        self.target)

        task_state_ms = self.get_task_state(self.ms_node, task_desc_ms, \
                    ignore_variables=False)

        task_state_mn = self.get_task_state(self.ms_node, task_desc_mn, \
                            ignore_variables=False)
        self.assertNotEqual(task_state_ms, test_constants.CMD_ERROR, \
                "Task doesn't exist")
        self.assertNotEqual(task_state_mn, test_constants.CMD_ERROR, \
                        "Task doesn't exist")

        #  Restart httpd service on MS
        self.kill_service_httpd_and_recover(task_desc_ms,
                                            self.ms_node)

        self.execute_cli_showplan_cmd(self.ms_node)

        self.assertTrue(self.kill_service_httpd_and_recover,
                        "Error: Test to kill -9 httpd "
                        "service returned false")

        #  Restart httpd service on Mn
        self.kill_service_httpd_and_recover(task_desc_mn,
                                            self.ms_node)
        # execute a show_plan
        self.execute_cli_showplan_cmd(self.ms_node)

        # Check if method has returned true or not
        self.assertTrue(self.kill_service_httpd_and_recover,
                        "Error: Test to kill -9 httpd"
                        "service returned false")

        # 6. Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
        self.assertTrue(completed_successfully,
                        "Plan didn't finished successfully.")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness',
          'rob_p1', 'robustness_tc10')
    def test_10_kill_puppet(self):
        """
        Description:
            Kill  puppet (agent) service while plan is running.
                1. On MS when config tasks are being run on the MS
                2. On Managed Node when config tasks are being run on the nodes
            It is expected that the puppet service will recover in time for the
            plan to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            For each node do:
                4. Wait for config task to be running on node
                5. Kill puppet service on node
            6. Check if plan completed successfully
            7. Check the number of LITP services running
        Results:
            1. The puppet service is killed
            2. The service is started successfully
            4. The recreated plan should run successfully
            5. Only 1 instance of litp service should be running
        """
        service = ["puppet"]
        self._stop_service_config(service, kill=True)

    @attr('all', 'non-revert', 'robustness',
          'rob_p2', 'robustness_tc10_minus9')
    def test_10_kill_minus9_puppet(self):
        """
        Description:
            Kill -9 puppet (agent) service while plan is running.
                1. On MS when config tasks are being run on the MS
                2. On Managed Node when config tasks are being run on the nodes
            It is expected that the puppet service will recover in time for the
            plan will succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            For each node do:
                4. Wait for config task to be running on node
                5. Kill puppet service on node
            6. Check if plan completed successfully
            7. Check the number of LITP services running
        Results:
            1. The puppet service is killed with -9 signal
            2. The plan should run successfully
            3. Only 1 instance of litp service should be running
        """
        service = ["puppet"]
        self._stop_service_config(service, kill=True, killarg="-9")

    @attr('all', 'non-revert', 'robustness',
          'rob_p1', 'robustness_tc11')
    def test_11_kill_mcollective_callback(self):
        """
        Description:
            Kill of mcollective service while a plan is running.
                1. On MS when callback tasks are being run on the MS.
                2. On Managed Node when callback tasks are being run
                on the nodes.
            It is expected that killing the mco service will cause the plan to
            fail.
            Recreating and running the plan should succeed.
        Actions:
            1.  Set up and run plan that contains CallbackTasks
            2.  Wait for Callback task
            3.  Stop service mcollective on MS using 'kill' command
            4.  Stop service mcollective on Managed Nodes using 'kill' command,
                causing the plan to fail
            5.  Remove VCS cluster service items as it has been partially
                created
            6.  Create removal plan
            7.  Run removal plan
            8.  Wait for removal plan to complete successfully
            9.  Create the VCS cluster service items again
            10. Check that retry plan is successful
            11. Check the number of LITP services running.
        Results:
            1. The mcollective service is killed
            2. The plan fails
            3. The removal plan runs successfully
            4. The recreated plan should run successfully
            5. Only 1 instance of litp service should be running
        """

        service = "mcollective"
        self._stop_service_callback(service, kill=True)

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness',
          'rob_p1_2', 'robustness_tc11_config')
    def test_11_kill_mcollective_config(self):
        """
        Description:
            Kill mcollective service while plan is running.
                1. On MS when config tasks are being run on the MS
                2. On Managed Node when config tasks are being run on the nodes
            It is expected that litp will be able to recover. Either the plan
            will succeed or if it fails then recreating and rerunning the plan
            will be successful.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            For each node do:
                4. Wait for config task to be running on node
                5. Stop puppet service on node
                6. Kill mcollective service on node
                7. Wait for the plan to finish
                8. Start service on node
                9. If plan failed, recreate plan and run plan
            10. Check if plan completed successfully
            11. Check the number of LITP services running
        Results:
            1. The mcollective service is killed
            2. The service is started successfully
            3. The plan should run or rerun successfully
        """
        service = ["mcollective"]

        self.stop_services_config_fail_plan(service, kill=True)

    @attr('all', 'non-revert', 'robustness',
          'rob_p2', 'robustness_tc11_minus9')
    def test_11_kill_minus9_mcollective_callback(self):
        """
        Description:
            Kill -9 of mcollective service while a plan is running.
                1. On MS when callback tasks are being run on the MS
                2. On Managed Node when callback tasks are being run
                on the node.
            It is expected that killing the mco service will cause the plan to
            fail.
            Recreating and running the plan should be successful
        Actions:
            1.  Set up and run plan that contains CallbackTasks
            2.  Wait for Callback task
            3.  Stop service mcollective on MS using 'kill -9' command
            4.  Stop service mcollective on Managed Nodes using 'kill -9'
                command ,causing the plan to fail
            5.  Remove VCS cluster service items as it has been partially
                created
            6.  Create removal plan
            7.  Run removal plan
            8.  Wait for removal plan to complete successfully
            9.  Create the VCS cluster service items again
            10. Check that retry plan is successful
            11. Check the number of LITP services running.
        Results:
            1. The service is successfully stopped
            2. The plan fails
            3. The recreated plan completes successfully
            4. Only one LITP service is running
        """

        service = "mcollective"
        self._stop_service_callback(service, kill=True, killarg="-9")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p2',
          'robustness_tc11_config_minus9')
    def test_11_kill_minus9_mcollective_config(self):
        """
        Description:
            Kill mcollective service while plan is running.
                1. On MS when config tasks are being run on the MS
                2. On Managed Node when config tasks are being run on the nodes
            It is expected that killing the puppet and mco service will cause
            the plan to fail.
            Recreating and running the plan should succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            For each node do:
                4. Wait for config task to be running on node
                5. Stop puppet service on node
                6. Kill mcollective service on node
                7. Wait for the plan to fail
                8. Start stopped/killed service on node
                9. Recreate plan and run plan
            10. Check if plan completed successfully
            11. Check the number of LITP services running
        Results:
            1. The mcollective service is killed and puppet is stooped
            2. The plan fails
            3. The services are started successfully
            4. The recreated plan should run successfully
        """
        service = ["mcollective"]

        self.stop_services_config_fail_plan(service, kill=True, killarg="-9")

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc12')
    def test_12_kill_vcs(self):
        """
        Description:
            Kill the VCS service while plan is running
                1. On the Managed Node when changes (new service group added)
                   are applied to the Managed Node
            It is expected that if the vcs service does not recover in time for
            the plan to succeed, then a retry after cleaning VCS cluster
            service items should succeed.
        Actions:
            1.  Set up and run plan that contains VCS tasks
            2.  Wait for VCS task
            3.  Stop VCS service on both Managed nodes using 'kill' command
            4.  Wait for plan to finish
            5.  If plan fails:
                5a.  Remove VCS cluster service items as it has been partially
                    created
                5b.  Create removal plan
                5c.  Run removal plan
                5d.  Wait for removal plan to complete successfully
                5e. Create the VCS cluster service items again
                5f. Check that retry plan is successful
            6. Check the number of LITP services running.
        Results:
            1. The vcs service is killed
            2. The plan should pass either first time, or after a retry
            3. Only 1 instance of litp service should be running
        """

        service = "vcs"
        self._stop_service_callback(service, kill=True)

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness',
          'rob_p2', 'robustness_tc12_minus9')
    def test_12_kill_minus9_vcs(self):
        """
        Description:
            Kill -9 the VCS service while plan is running
                1. On the Managed Node when changes (new service group added)
                   are applied to the Managed Node
            It is expected that the vcs service will recover in time for the
            plan to succeed.
        Actions:
            1.  Set up and run plan that contains VCS tasks
            2.  Wait for VCS task
            3.  Stop VCS service on both Managed nodes using 'kill -9' command
            4.  Wait for plan to complete successfully
            5.  If plan fails:
            6.  Remove VCS cluster service items as it has been partially
                created
            7.  Create removal plan
            8.  Run removal plan
            9.  Wait for removal plan to complete successfully
            10. Create the VCS cluster service items again
            11. Check that retry plan is successful
            12. Check the number of LITP services running.
        Results:
            1. The vcs service is killed
            2. The plan is completed successfully
            3. Only one LITP service is running
        """

        service = "vcs"
        self._stop_service_callback(service, kill=True, killarg="-9")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc13')
    def test_13_kill_libvirt(self):
        """
        Description:
            Kill libvirt service while plan is running
                When configuration updates (new vm-alias added)
                are applied to
                    1. A vm on the management server
                    2. A vm on the managed node
            It is expected that the libvirt service will recover in time for
            the plan to succeed.
        Actions:
            For Both the MS and Node
                Call Method to create plan to  update vm configuration.
                Call method to Kill libvirt service on node
                specified while plan is running to apply some
                updated vm configuration.
                Wait for plan to complete successfully.
        Results:
            1. The service is successfully killed and restarted
            2. The plan is completed successfully
            3. The updated configuration is applied to the VMs
        """
        # Service to be killed
        service = "libvirtd"
        self.log("info", "Calling method to create "
                         "plan to update vm configuration on ms")
        # Call method to update the ms vm config
        # and when successful return task description
        task_desc_ms = self.update_ms_vm_configuration()
        self.log("info", "Calling method to kill vm during specified task")
        # Call method to kill the service specified on the task specified on MS
        self.kill_service_on_config_task(task_desc_ms, service, self.ms_node,
                                         kill_arg="")

        # Wait for plan to complete successfully
        ms_plan_completed = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=8)
        # Check if plan to kill libvirt on specified task was successful
        self.assertTrue(ms_plan_completed,
                        "Plan failed to complete successfully")
        self.log("info", "Calling method to create "
                         "plan to update vm configuration on node")
        # Call method to update the ms vm config
        # and when successful return task description
        task_desc_mn = self.update_node_vm_configuration()
        self.log("info", "Calling method to kill vm during specified task")
        # Call method to kill the service specified on the task specified on MN
        self.kill_service_on_config_task(task_desc_mn, service, self.target,
                                         kill_arg="")

        # Wait for plan to complete successfully
        mn_plan_completed = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=8)
        # Check if plan to kill libvirt on specified task was successful
        self.assertTrue(mn_plan_completed,
                        "Plan failed to complete successfully")

    @attr('all', 'non-revert', 'robustness',
          'rob_p2', 'robustness_tc13_minus9')
    def test_13_kill_minus9_libvirt(self):
        """
        Description:
            Kill -9 libvirt service while plan is running
                When configuration updates (new vm-alias added)
                are applied to
                    1. A vm on the management server
                    2. A vm on the managed node
            It is expected that the libvirt service will recover in time for
            the plan to succeed.
        Actions:
            For Both the MS and Node
                Call Method to create plan to  update vm configuration.
                Call method to Kill -9 libvirt service on node
                specified while plan is running to apply some
                updated vm configuration.
                Wait for plan to complete successfully.
        Results:
            1. The service is killed and restarted successfully.
            2. The plan is completed successfully
            3. The updated configuration is applied to the VMs
        """
        # Service to be killed
        service = "libvirtd"
        # Calling method to update ms vm config and return task desc
        task_desc_ms = self.update_ms_vm_configuration()

        # Call method to kill the service specified on the task specified on MS
        self.kill_service_on_config_task(task_desc_ms, service, self.ms_node,
                                         kill_arg="-9")

        # Wait for plan to complete successfully
        ms_plan_completed_successfully = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=8)
        # Check if plan completed successfully
        self.assertTrue(ms_plan_completed_successfully,
                        "Plan failed to complete successfully")

        # Check if the plans have completed successfully after service kill
        task_desc_mn = self.update_node_vm_configuration()

        # Call method to kill the service specified on the task specified on MN
        self.kill_service_on_config_task(task_desc_mn, service, self.target,
                                         kill_arg="-9")

        # Wait for plan to complete successfully
        mn_plan_completed_successfully = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=8)

        # Check if plan completed successfully
        self.assertTrue(mn_plan_completed_successfully,
                        "Plan failed to complete successfully")

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc14')
    def test_14_reboot_ms_during_plan(self):
        """
        Description:
            Reboot of the MS while plan is applying changes to MS.
            It is expected that the plan will fail when the ms is rebooted.
            Recreating and running the plan should succeed.
        Actions:
            On the MS
            1.Import 3pp-irish-hello package from /tmp/ to new_repo on ms
            2.Create 3pp-irish-hello package in /software/items/3pp-irish-hello
            3.Inherit 3pp-irish-hello onto ms
            4.Create and run plan
            5.While plan is running reboot the MS.
            6.After Ms has come back online recreate and run the plan.
            7.Check if plan has run to completion after reboot.
            8. Check the number of LITP services running.
        Results:
            1.Node should reboot successfully.
            2.Plan should recreate and run successfully.
            3.Package should be installed on the MS .
            4. Only one LITP service is running
        """

        test_pkg1 = "3PP-irish-hello"
        # Task decription to reboot MS on
        task_desc = 'Install package "{0}" on node "{1}"'.\
                        format(test_pkg1, \
                               self.ms_node)
        package = test_pkg1
        package_rpm = "/tmp/3PP-irish-hello-1.0.0-1.noarch.rpm"
        # 1.Import 3pp-irish-hello from /tmp/ to 3pp
        self.execute_cli_import_cmd(self.ms_node, package_rpm,
                                    "3pp")

        # 2.Create the 3pp-irish-hello package
        irish_hello_url = self._create_package(package, do_cleanup=False)

        # 3.Inherit package 3pp-irish-hello onto ms
        self._create_package_inheritance(self.ms_path,
                                         package,
                                         irish_hello_url,
                                         do_cleanup=False)
        # 4.Execute create_plan
        self.execute_cli_createplan_cmd(self.ms_node)
        # Execute show_plan
        self.execute_cli_showplan_cmd(self.ms_node)

        # Check the plan for the number of tasks expected
        # Verify number of phases = 1 for created plan
        self.assertTrue(1 == self.count_phases_in_plan(),
                        "Number of phases in plan not as expected")
        # Verify number of tasks = 1 in Phase 1 of created plan
        self.assertTrue(1 == self.count_tasks_in_phase(1),
                        "Number of tasks in phase not as expected")
        # Execute run_plan
        self.execute_cli_runplan_cmd(self.ms_node)

        # 5.Reboot node when specified task is running
        self.reboot_on_specified_task(task_desc, self.ms_node)

        # Confirm litpd service is up and running
        self.assertTrue(self._litp_up())

        # Enable debug after reboot
        self.turn_on_litp_debug(self.ms_node)

        # 6. Execute create_plan
        self.execute_cli_createplan_cmd(self.ms_node)
        # Execute show_plan
        self.execute_cli_showplan_cmd(self.ms_node)
        # Check the plan for the number of tasks expected
        # Verify number of phases = 1 for created plan
        self.assertTrue(1 == self.count_phases_in_plan(),
                        "Number of phases in plan not as expected")
        # Verify number of tasks = 1 in Phase 1 of created plan
        self.assertTrue(1 == self.count_tasks_in_phase(1),
                        "Number of tasks in phase not as expected")

        # Execute run_plan
        self.execute_cli_runplan_cmd(self.ms_node)

        # 7. Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, timeout_mins=5)
        self.assertTrue(completed_successfully,
                        "error: Plan failed to install package after reboot")
        # Check if package 3pp-irish-hello  is installed on the MS
        cmd = self.redhat.check_pkg_installed("3PP-irish-hello")
        check_package_installed = self.run_command(self.ms_node, cmd)
        self.assertTrue(check_package_installed,
                        "Package was not installed on ms")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc15')
    def test_15_reboot_node_during_plan(self):
        """
        Description:
            Reboot of the Managed Node while
            plan is applying changes to Managed Node.
            It is expected that the node will recover in time to allow the
            plan to succeed.
        Actions:
            On the node
            1.Inherit 3pp-irish-hello onto the node
            2.Create and run plan .
            3.Check plan contains expected number of phases and tasks
            4.While plan is running reboot the node.
            5.Check if plan has run to completion after node reboot
              and package is installed on node.
            6. Check the number of LITP services running.
        Results:
            1.Node should reboot successfully.
            2.Plan should run to completion.
            3.Package should be installed on the node after plan completion.
            4. Only one LITP service is running
        """
        test_pkg1 = "3PP-irish-hello"

        # Task description to reboot node on
        task_desc = 'Install package "{0}" on node "{1}"'.\
                        format(test_pkg1, \
                               self.target)
        # node_with_package is the path to the
        # package on specified node under /items
        node_with_pkg = self.target_url + "/items/3PP-irish-hello"
        self.log("info",
                 "Searching for package {0} "
                 "under /software".format(test_pkg1))
        # Find package items under /software
        find_package = \
            self.find(self.ms_node,
                      "/software/",
                      "package",
                      True)
        self.assertTrue(find_package, "package was not found under /software")
        # Check if test package defined exists in package items
        for pkg in find_package:
            if "3PP-irish-hello" in pkg:
                pkg_url = pkg
        # Verify that a path to specified test package has been found
        self.assertTrue(pkg_url != "",
                        "package url for {0} was not found".format(test_pkg1))

        # 1.Inherit package 3pp-irish-hello onto node
        self.execute_cli_inherit_cmd(self.ms_node, node_with_pkg,
                                     pkg_url,
                                     add_to_cleanup=False)

        # 2.Execute create_plan and show_plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)

        # 3.Check the plan for the number of tasks expected
        # Verify number of phases = 3 for created plan
        self.assertTrue(3 == self.count_phases_in_plan(),
                        "Number of phases in plan not as expected")
        # Verify number of tasks = 1 in Phase 2 of created plan
        self.assertTrue(1 == self.count_tasks_in_phase(2),
                        "Number of tasks in phase not as expected")
        # Execute run_plan
        self.execute_cli_runplan_cmd(self.ms_node)

        # 4.Reboot node when specified task is in state running
        self.reboot_on_specified_task(task_desc, self.target)

        # 5. Check if plan has completed successfully
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE, timeout_mins=10)
        self.assertTrue(completed_successfully,
                        "error: Plan failed to install package after reboot")

        # Check if package 3pp-irish-hello is installed on node
        check_package_cmd = self.redhat.check_pkg_installed("3PP-irish-hello")
        check_package_installed = self.run_command(self.target,
                                                   check_package_cmd)
        self.assertTrue(check_package_installed,
                        "Package was not installed on node")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc17')
    def test_17_kill_a_vm_during_plan(self):
        """
        Description:
            Kill a VM while a plan is running to deploy
            some updated configuration on the VM.
            It is expected that the vm service will recover in time for the
            plan to succeed.
        Actions:
            On the ms
            1.Get vm paths and isolate vm
            2.Updated the vm's vm_aliases
            3.create and run plan
            4.While plan is running use virsh kill to kill the vm
            5.Wait for vm to be recreated and plan to succeed.
            6.Ensure updated vm configuration is applied.
        Results:
            1.Plan should run to completion.
            2.Vm should be recreated.
            3.New Vm configuration should be applied
        """
        task_desc = self.update_ms_vm_configuration()
        self.kill_vm_during_update_plan(task_desc)

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc24')
    def test_24_restart_rabbitmq_callback(self):
        """
        Description:
            Carries out 'service rabbitmq-server restart' during CallbackTasks.
            It is expected that the rabbitmq service will recover in time for
            the plan to succeed.
        Actions:
            1. Sets up and runs plan that contains CallbackTasks
            2. Wait for Callback task
            3. Run rabbitmq-server restart on the MS
            4. Wait for plan to complete successfully, either initially or
               after a retry
            5. Check the number of LITP services running.
        Results:
            1. The rabbitmq service restarts successfully each time
            2. The plan is completed successfully
            3. Only one LITP service is running
        """

        # 1.  Set up and run plan that contains CallbackTasks
        self.set_up_callback_tasks()

        service = "rabbitmq-server"
        package_name = "EXTR-lsbwrapper40"

        # 2. Wait for Callback task.
        task_running = \
            self.wait_for_task_state(
                self.ms_node,
                'Create VCS service group "Grp_CS_c1_EXTR_lsbwrapper39"',
                test_constants.PLAN_TASKS_RUNNING, seconds_increment=1,
                ignore_variables=False)
        # Check to see if task was in expected state
        self.assertTrue(task_running,
                        "Task did not reach running state in specified time")
        self.log("info", "Callback Task is running")

        # 3. Run rabbitmq-server restart on the MS
        self.log("info", "Running two rabbitmq restarts on node '{0}'"
                 .format(self.ms_node))
        self.restart_service(self.ms_node, service)

        # 4. Wait for plan to complete
        plan_state = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_COMPLETE)

        # litp remove added as cleanup was failing due to inheritance
        self.execute_cli_remove_cmd(self.ms_node,
                                    "{0}/services/{1}/applications/{1}"
                                    .format(self.cluster_url, package_name))

        # If the initial plan doesn't succeed, re-run
        if plan_state:
            self.log("info", "Initial plan passed, no need to retry")
        else:
            self.log("info", "Initial plan has failed, retrying plan")
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)

            completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
            self.assertTrue(completed_successfully,
                            "Plan did not finish successfully.")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1_2',
          'robustness_tc24_config')
    def test_24_restart_rabbitmq_config(self):
        """
        Description:
            Carries out 'service rabbitmq-server restart' during Config Tasks.
            It is expected that the rabbitmq-server service recovers in time
            for the plan to succeed.
        Actions:
            1. Sets up and runs plan that contains Config tasks
            2. Wait for Config task to be running on the MS
            3. Run rabbitmq-server restart on the MS
            4. Wait for Config task to be running on the peer node
            5. Run rabbitmq-server restart on the MS
            6. Wait for plan to complete successfully, either initially or
               after a retry
            7. Check the number of LITP services running.
        Results:
            1. The rabbitmq service restarts successfully each time
            2. The plan is completed successfully
            3. Only one LITP service is running
        """

        service = ["rabbitmq-server"]
        timeout = 10

        # 1. Sets up and runs plan that contains Config tasks
        task_desc_ms, task_desc_mn = self.create_config_plan()

        # 2. Wait for Config task to be running on the MS
        self.wait_for_task_state(self.ms_node, task_desc_ms,
                                 test_constants.PLAN_TASKS_RUNNING,
                                 timeout_mins=timeout,
                                 ignore_variables=False)

        # Check if the service being tested is enforced by puppet.
        # If enforced by puppet, puppet needs to be stopped so that it
        # does not try to enforce the service being enabled and therefore
        # compromise the testcase
        self.check_service_enforced_by_puppet(service, self.ms_node, "stop")

        # 3. Run rabbitmq-server restart on the MS
        self.log("info", "Restarting '{0}' service on the MS".format(
            service[0]))
        self.restart_service(self.ms_node, service[0])

        # 4. Wait for Config task to be running on the peer node
        self.wait_for_task_state(self.ms_node, task_desc_mn,
                                 test_constants.PLAN_TASKS_RUNNING,
                                 timeout_mins=timeout,
                                 ignore_variables=False)

        # 5. Run rabbitmq-server restart on the MS
        self.log("info", "Restarting '{0}' service on the MS".format(
            service[0]))
        self.restart_service(self.ms_node, service[0])

        # 6. Wait for plan to complete successfully
        plan_state = self.wait_for_plan_state(self.ms_node,
                                              test_constants.PLAN_COMPLETE)

        # If the initial plan doesn't succeed, re-run
        if plan_state:
            self.log("info", "Initial plan passed, no need to retry")
        else:
            self.log("info", "Initial plan has failed, retrying plan")
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)

            completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)
            self.assertTrue(completed_successfully,
                            "Plan did not finish successfully.")

        # 7. CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc25')
    def test_25_kill_rabbitmq_callback(self):
        """
        Description:
            Kills rabbitmq on the MS during Callback Tasks using 'kill'.
            It is expected that the killing the rabbitmq-server service will
            fail the plan.
            Recreating and running the plan should succeed.
        Actions:
            1.  Set up and run plan that contains CallbackTasks
            2.  Wait for Callback task
            3.  Stop rabbitmq service on the MS using 'kill' command causing
             the plan to fail
            4.  Remove VCS cluster service items as it has been partially
                created
            5.  Create removal plan
            6.  Run removal plan
            7.  Wait for removal plan to complete successfully
            8.  Create the VCS cluster service items again
            9.  Check that retry plan is successful
            10. Check the number of LITP services running.
        Results:
            1. The rabbitmq and puppet service are killed
            2. The plan fails
            3. The services are started successfully
            4. The recreated plan should run successfully
            5. Only 1 instance of litp service should be running
        """

        service = "rabbitmq-server"
        self._stop_service_callback(service, kill=True)

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1_2',
          'robustness_tc25_config')
    def test_25_kill_rabbitmq_config(self):
        """
        Description:
            Kill rabbitmq-server while plan is running
                1. On MS when config tasks are being run on the MS
                2. On MS when config tasks are being run on the MN
            It is expected that killing the rabbitmq-server service will
            cause the plan to fail.
            Recreating and running the plan should succeed.
        Actions:
            1. Sets up and runs plan that contains Config tasks
            2. Wait for the config task to be running on the MS
            3. Kill rabbitmq-server service on the MS
            4. Wait for the plan to fail
            5. Start rabbitmq-server on the MS
            6. Create and run plan
            7. Wait for the config task to be running on the MN
            8. Kill rabbitmq-server service on the MS
            7. Check if plan completed successfully
            8. Check the number of LITP services running
        Results:
            1. The rabbitmq service is killed
            2. The plan fails
            3. The service is started successfully
            4. The recreated plan should run successfully
        """
        # Service to kill
        service = ["rabbitmq-server"]

        self.stop_services_config_fail_plan(service, kill=True)

    @attr('all', 'non-revert', 'robustness',
          'rob_p2', 'robustness_tc25_minus9')
    def test_25_kill_minus9_rabbitmq(self):
        """
        Description:
            Kill rabbitmq on the MS during Callback Tasks using 'kill -9'.
            It is expected that killing rabbitmq-server service will cause
            the plan to fail.
            Recreating and running the plan should succeed
        Actions:
            1.  Set up and run plan that contains CallbackTasks
            2.  Wait for Callback task
            3.  Stop rabbitmq service on the MS using 'kill -9' command ,
                Causing the plan to fail
            4. Run and check the retry plan is successful
            5. Check the number of LITP services running.
        Results:
            1. The service is killed
            2. The plan fails
            3. The retry plan is run and completes successfully
            4. Only one LITP service is running
        """

        service = "rabbitmq-server"
        self._stop_service_callback(service, kill=True, killarg="-9")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc26')
    def test_26_stop_mcollective_callback(self):
        """
        Description:
            Carries out 'service mcollective stop' during CallbackTasks on the
            MS and the Managed Nodes.
            It is expected that stopping mco service will cause the plan
            to fail.
            Recreating and running the plan should succeed.
        Actions:
            1. Set up and run plan that contains CallbackTasks
            2. Wait for Callback task
            3. Stop mcollective and puppet service on the MS and nodes,
               Causing the plan to fail
            4. Recreating and running the retry plan should succeed.
            5. Check the number of LITP services running
        Results:
            1. The mcollective and puppet services are successfully stopped
            2. The plan will fail
            3. The retry plan should succeed
            4. Only one LITP service is running
        """

        service = "mcollective"
        self._stop_service_callback(service)

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc27')
    def test_27_stop_rabbitmq_callback(self):
        """
        Description:
            Carries out 'service rabbitmq-server stop' during CallbackTasks on
            the MS and the Managed Nodes.
            It is expected that stopping the rabbitmq-server service will
            cause the plan to fail.
            Recreating and running the plan should succeed.
        Actions:
            1.  Set up and run plan that contains CallbackTasks
            2.  Wait for Callback task
            3.  Stop rabbitmq and puppet service on the MS, Causing the plan
                to fail
            4. Running the retry plan should succeed.
        Results:
            1. The service is successfully stopped
            2. The plan fails
            3. The retry plan is successful
            4. Only one LITP service is running
        """

        service = "rabbitmq-server"
        self._stop_service_callback(service)

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1_2',
          'robustness_tc27_config')
    def test_27_stop_rabbitmq_config(self):
        """
        Description:
            Stop rabbitmq-server while a plan is running
                1. On MS when config tasks are being run on the MS
                2. On MS when config tasks are being run on the MN
            It is expected that stopping the service rabbitmq-server will cause
            the plan to fail.
            Recreating and running the plan should succeed.
        Actions:
            1. Sets up and runs plan that contains Config tasks
            2. Wait for the config task to be running on the MS
            3. Stop rabbitmq-server service on the MS, causing the plan to fail
            4. Start rabbitmq-server on the MS
            5. Create and run plan
            6. Wait for the config task to be running on the MN
            7. Stop rabbitmq-server service on the MS
            8. Check if plan completed successfully
            9. Check the number of LITP services running
        Results:
            1. The rabbitmq service is stopped
            2. The plan fails
            3. The service is started successfully
            4. The recreated plan should run successfully
        """
        # Service to stop
        service = ["rabbitmq-server"]

        self.stop_services_config_fail_plan(service)

    @attr('all', 'non-revert', 'robustness', 'rob_p1',
          'robustness_tc28')
    def test_28_stop_litpd_config(self):
        """
        Description:
            Stop litpd service while plan is running.
                1. When tasks are being run on the MS
                2. When tasks are being run on the nodes
            It is expected that stopping the litpd service will cause the plan
            to stop.
            Recreating and running the plan should succeed.
        Actions:
            1. Create the packages
            2. Inherit packages
            3. Create and run the plan
            4. Stop then start of litpd service when task is running on the MS,
               Causing the plan to stop
            5. Recreating and running the plan should succeed
        Results:
            1. The litp service is stopped successfully
            2. The plan stops
            3. The service is started successfully
            4. The recreated plan should run successfully
            5. Only 1 instance of litp service should be running
        """
        timeout = 10
        service = "litpd"
        litpd_stopped_rc = 3

        # Creates the config plan
        task_desc_ms, task_desc_mn = self.create_config_plan()

        # Wait for config task to be running on the MS
        task_state_detected_ms = \
            self.wait_for_task_state(self.ms_node, task_desc_ms,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task reached expected state in allowed time
        self.assertTrue(task_state_detected_ms,
                        "Task did not reach running state in specified time")

        # Get all started phases at time of litpd stop
        self.log('info', 'Get all started phases at time of litpd stop')
        started_phases_at_litpd_stop = \
                    self.get_tasks_by_state(self.ms_node, 'Running').keys() \
                    + self.get_tasks_by_state(self.ms_node, 'Success').keys()

        # Stop litpd service
        # Extend time waited for stop to return
        # Celery changes means that it now waits for plan to complete
        self.stop_service(self.ms_node, service,
                          su_timeout_secs=self.litpd_stop_timeout_secs)

        # Wait for status command to have return code 3 to ensure litpd
        # service has stopped
        cmd = "/sbin/service {0} status".format(service)
        litpd_stopped = self.wait_for_cmd(self.ms_node, cmd, litpd_stopped_rc,
                                          timeout_mins=timeout)
        self.assertTrue(litpd_stopped,
                        "litpd was expected to stop before timeout")

        # Start litpd service
        self.start_service(self.ms_node, service)
        # enable debug after starting the service
        self.turn_on_litp_debug(self.ms_node)
        # Show plan after service start
        self.execute_cli_showplan_cmd(self.ms_node)

        # Wait for plan to be in stopped state
        stopped_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_STOPPED,
                                     self.timeout_mins)
        self.assertTrue(stopped_successfully, "Plan did not reach stopped"
                                                "state in specified time")

        # Check that tasks in started phases are successful
        self.log('info',
        'Check that phases started at "litpd stop" time completed '
            'successfully, and all others are in "Initial" state')
        self.validate_phases(started_phases_at_litpd_stop)

        #  Recreate and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        # Wait for config task to be running on the peer node
        task_state_detected_mn = \
            self.wait_for_task_state(self.ms_node,
                                     task_desc_mn,
                                     test_constants.PLAN_TASKS_RUNNING,
                                     timeout_mins=timeout,
                                     ignore_variables=False)
        # Check to see if task reached expected state in allowed time
        self.assertTrue(task_state_detected_mn,
                        "Task did not reach running state in specified time")
        # Stop litpd service
        self.stop_service(self.ms_node, service,
                          su_timeout_secs=self.litpd_stop_timeout_secs)

        # Wait for status command to have return code 3 to ensure litpd
        # service has stopped
        cmd = "/sbin/service {0} status".format(service)
        litpd_stopped = self.wait_for_cmd(self.ms_node, cmd, litpd_stopped_rc,
                                          timeout_mins=timeout)
        self.assertTrue(litpd_stopped,
                        "litpd was expected to stop before timeout")

        # Start litpd service
        self.start_service(self.ms_node, service)
        # enable debug after starting the service
        self.turn_on_litp_debug(self.ms_node)
        # Show plan after service start
        self.execute_cli_showplan_cmd(self.ms_node)

        # Wait for plan to be in stopped state
        stopped_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_STOPPED,
                                     self.timeout_mins)
        self.assertTrue(stopped_successfully, "Plan did not reach stopped"
                                                "state in specified time")

        #  Recreate and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        # Check if plan completed successfully
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     self.timeout_mins)

        self.assertTrue(completed_successfully, "Plan did not succeed")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1',
          'robustness_tc28_callback')
    def test_28_stop_litpd_callback(self):
        """
        Description:
            Stop litpd service during Callback tasks.
            It is expected that stopping the litp service will cause the plan
            to stop.
            Recreating and running the plan should succeed.
        Actions:
            1.  Set up and run plan that contains Callback tasks
            2.  Wait for Callback task
            3.  Stop litpd service
            4.  Wait for the litpd service to be successfully stopped
            5.  Start litpd service
            6.  Remove VCS cluster service items as it has been partially
                created
            7.  Create cleanup plan
            8.  Run cleanup plan
            9.  Wait for cleanup plan to complete successfully
            10. Create the VCS cluster service items again
            11. Check that the recreated plan is successful
        Results:
            1. The litp service is killed
            2. The plan stopped
            3. The service is started successfully
            4. The recreated plan should run successfully
            5. Only 1 instance of litp service should be running
        """

        self._stop_litpd_callback()

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'non-revert', 'robustness', 'rob_p1', 'robustness_tc29')
    def test_29_stop_puppet_config(self):
        """
        Description:
            Stop puppet (agent) service while plan is running.
                1. On MS when config tasks are being run on the MS
                2. On Managed Node when config tasks are being run on the nodes
            It is expected that the puppet service recover in time for the plan
            to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            For each node do:
                4. Wait for the config task to be running
                5. Stop puppet service on node
            6. Check if plan completes successfully, either initially or after
               a retry
            7. Check the number of LITP services running
        Results:
            1. The puppet service is stopped
            2. The plan should run successfully
        """
        service = ["puppet"]
        self._stop_service_config(service)

    @attr('all', 'non-revert', 'robustness', 'rob_p1_2', 'robustness_tc29_mco')
    def test_29_stop_mco_puppet_config(self):
        """
        Description:
            Stop mcollective and puppet (agent) service while plan is running.
                1. On MS when config tasks are being run on the MS
                2. On Managed Node when config tasks are being run on the nodes
            It is expected that litp will be able to recover. Either the plan
            will succeed or if it fails then recreating and rerunning the plan
            will be successful.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            4. Wait for the config task to be running on the MS
            5. Stop mcollective and puppet service on the MS
            6. Wait for the plan to fail
            7. Start mcollective and puppet service on the MS
            8. Create and run plan
            9. Wait for the config task to be running on the peer node
            10. Stop mcollective and puppet service on the peer node
            11. Wait for the plan to fail
            18. Start mcollective and puppet service on the peer node
            19. Create and run plan
            20. Check if plan completed successfully
            21. Check the number of LITP services running
        Results:
            1. The mco and puppet services are stopped successfully
            2. The plan fails
            3. The services are started successfully
            4. The recreated plan should run successfully
            5. Only 1 instance of litp service should be running
        """
        # List of services to kill
        services = ["mcollective", "puppet"]

        self.stop_services_config_fail_plan(services)

    @attr('all', 'non-revert', 'rob_postgresql', 'robustness_tc30')
    def test_30_restart_postgresql_config(self):
        """
        Description:
            Restart the postgresql service while plan is running
                1. While config task running on the MS
                2. While config task running on the MN
            It is expected that restarting the postgresql service will cause
            the plan to fail.
        Actions:
            1. Create and run the plan with config tasks
            2. Wait for task running on MS and restart postgresql service
            3. Ensure the plan has failed
            4. Recreate and run the plan again.
            5. Wait for task running on MN and restart postgresql service
            6. Ensure the plan has failed
            7. Recreate and run the plan again.
            8. Ensure the plan has succeeded.
        Results:
            1. The postgresql service is restarted successfully
            2. The plan should fails after the service is restarted.
            3. The recreated plans should succeed without issue.
        """
        # Service that will be restarted on peer node
        service_to_restart = self.postgres_service_name

        # Calling method to update mn vm config and return task desc
        ms_task_desc, mn_task_desc = self.create_config_plan()

        # Wait for task running on MS and restart service
        self.restart_service_on_task(ms_task_desc,
                                     service_to_restart,
                                     self.ms_node)
        # Adding wait to give service time to start up fully
        time.sleep(2)
        expected_fail_plan = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_FAILED,
                                     timeout_mins=8)
        self.assertTrue(expected_fail_plan, "Plan was expected to fail but "
                                              "did not")
        # As plan is in a failed state it must be recreated and run again
        self.execute_cli_createplan_cmd(self.ms_node,
                                        expect_positive=True)
        self.execute_cli_runplan_cmd(self.ms_node,
                                     add_to_cleanup=True)

        # Wait for task running on MN and restart service
        self.restart_service_on_task(mn_task_desc,
                                     service_to_restart,
                                     self.ms_node)

        # Adding wait to give service time to start up fully
        time.sleep(2)
        # Wait for plan to fail
        expected_fail_plan_2 = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_FAILED,
                                     timeout_mins=8)
        # Ensure plan is in expected state
        self.assertTrue(expected_fail_plan_2, "Plan was expected to fail "
                                              "but did not")

        # plan should be in failed state at this point
        # Recreating and running the plan now
        self.execute_cli_createplan_cmd(self.ms_node,
                                        expect_positive=True)
        self.execute_cli_runplan_cmd(self.ms_node,
                                     add_to_cleanup=True)

        # Wait for plan to complete successfully
        plan_failed = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_FAILED,
                                     timeout_mins=8)
        # Check if plan state was expected
        self.assertTrue(plan_failed, "Plan did not fail as expected")

        self.execute_cli_createplan_cmd(self.ms_node,
                                        expect_positive=True)
        self.execute_cli_runplan_cmd(self.ms_node,
                                     add_to_cleanup=True)
        plan_complete = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=10)
        self.assertTrue(plan_complete, "The plan did not complete in the "
                                       "allowed time")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'revert', 'robustness_tc31')
    def test_31_kill_postgresql_service_config(self):
        """
        Description:
            Kill postgresql service while plan is running.
                1. On MS when config tasks are being run on the MS
            It is expected that the postgresql service will recover in time for
            the plan to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            4. Wait for the config task to be running
            5. kill postgresql service on MS
            6. Check if plan completed successfully
        Results:
            Plan should complete successfully
        """
        service = [self.postgres_service_name]
        self._stop_service_config(service, kill=True)

    @attr('all', 'revert', 'robustness_tc31_minus9')
    def test_31_kill_minus9_postgresql_service_config(self):
        """
        Description:
            Kill postgresql service while plan is running.
                1. On MS when config tasks are being run on the MS
            It is expected that the postgresql service recover in time for the
            plan to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            4. Wait for the config task to be running
            5. kill -9 postgresql service on MS
            6. Check if plan completed successfully
        Results:
            Plan should complete successfully
        """
        service = [self.postgres_service_name]
        self._stop_service_config(service, kill=True, killarg="-9")

    @attr('all', 'revert', 'robustness_tc32')
    def test_32_kill_postgresql_service_callback(self):
        """
        Description:
            Kill -9 postgresql service while plan is running.
                1. On MS when callback tasks are being run.
            It is expected that the postgresql service recover in time for the
            plan to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            4. Wait for the callback task to be running
            5. kill postgresql service on MS
            6. Check if plan completed successfully
        Results:
            Plan should complete successfully
        """
        service = self.postgres_service_name
        self._stop_service_callback(service, kill=True)

    @attr('all', 'revert', 'robustness_tc32_minus9')
    def test_32_kill_minus9_postgresql_service_callback(self):
        """
        Description:
            Kill -9 postgresql service while plan is running.
                1. On MS when callback tasks are being run on the MS
            It is expected that the postgresql service recover in time for the
            plan to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            4. Wait for the callback task to be running
            5. kill -9 postgresql service on node
            6. Check if plan completed successfully
        Results:
            Plan should complete successfully
        """
        service = self.postgres_service_name
        self._stop_service_callback(service, kill=True, killarg="-9")

    @attr('all', 'revert', 'rob_postgresql', 'robustness_tc33_callback')
    def test_33_stop_postgresql_service_callback(self):
        """
        Description:
            Stop postgresql service while plan is running.
                1. On MS when callback tasks are being run on the MS
            It is expected that the postgresql service will recover in time
            for the plan to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            4. Wait for the callback task to be running
            5. stop service on node
            6. Check if plan completed successfully
        Results:
            Plan should complete successfully
        """
        service = self.postgres_service_name
        self._stop_service_callback(service)

    @attr('all', 'revert', 'rob_postgresql', 'robustness_tc33_config')
    def test_33_stop_postgresql_service_config(self):
        """
        Description:
            Stop postgresql service while plan is running.
                1. On MS when config tasks are being run on the MS
            It is expected that the postgresql service will recover in time
            for the plan to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            4. Wait for the config task to be running
            5. stop postgresql service on node
            6. Check if plan completed successfully
        Results:
            Plan should complete successfully
        """
        service = [self.postgres_service_name]
        self._stop_service_config(service)

    @attr('all', 'non-revert', 'rob_puppetdb', 'rob_p1', 'robustness_tc34')
    def test_34_restart_puppetdb(self):
        """
        Description:
            Restart the puppetdb service while plan is running
                1. While config task running on the MS
                2. While config task running on the MN
            It is expected that the puppetdb service will recover in time and
            allow the plan to succeed.
        Actions:
            1. Create and run the plan with config tasks
            2. Wait for task running on MS and restart puppetdb service
            3. Wait for task running on MN and restart puppetdb service
            4. Check that plan completes successfully
        Results:
            1. The puppetdb service is restarted successfully
            2. The plan should run successfully
        """
        # Service that will be restarted on peer node
        service_to_restart = "puppetdb"

        # Create and run the plan with config tasks
        ms_task_desc, mn_task_desc = self.create_config_plan()

        # Wait for task running on MS and restart service
        self.restart_service_on_task(ms_task_desc,
                                     service_to_restart,
                                     self.ms_node)

        # Wait for task running on MN and restart service
        self.restart_service_on_task(mn_task_desc,
                                     service_to_restart,
                                     self.ms_node)

        # Wait for plan to finish
        plan_complete = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE)
        # Check if plan state was expected
        self.assertTrue(plan_complete, "Plan did not complete successfully "
                                       "in the specified time")

        # CHECK THAT ONLY A SINGLE INSTANCE OF LITP IS RUNNING
        self.chk_individual_litp_running()

    @attr('all', 'revert', 'rob_puppetdb', 'rob_p1', 'robustness_tc35')
    def test_35_kill_puppetdb_service(self):
        """
        Description:
            Kill puppetdb service while plan is running.
                1. On MS when config tasks are being run on MS
                2. On MS when config tasks are being run on MN
            It is expected that the puppetdb service will recover in time for
            the plan to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            4. Wait for the config task to be running
            5. kill puppetdb service on node
            6. Check if plan completed successfully
        Results:
            Plan should complete successfully
        """
        service = ["puppetdb"]
        self._stop_service_config(service, kill=True, timeout=20)

    @attr('all', 'revert', 'rob_puppetdb', 'rob_p1', 'robustness_tc35_minus9')
    def test_35_kill_minus9_puppetdb_service(self):
        """
        Description:
            Kill puppetdb service while plan is running.
                1. On MS when config tasks are being run on MS
                2. On MS when config tasks are being run on MN
            It is expected that the puppetdb service will recover in time for
            the plan to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            4. Wait for the config task to be running
            5. kill -9 puppetdb service on MS
            6. Check if plan completed successfully
        Results:
            Plan should complete successfully
        """
        service = ["puppetdb"]
        self._stop_service_config(service, kill=True, killarg="-9", \
                                  timeout=20)

    @attr('all', 'revert', 'rob_puppetdb', 'rob_p1', 'robustness_tc36')
    def test_36_stop_puppetdb_service(self):
        """
        Description:
            Stop puppetdb service while plan is running.
                1. On MS when config tasks are being run on the MS
                1. On MS when config tasks are being run on the MN
            It is expected that the puppetdb service will recover in time for
            the plan to succeed.
        Actions:
            1. Create a package
            2. Inherit packages
            3. Create and run the plan
            4. Wait for the config task to be running
            5. stop puppetdb service on the MS
            6. Check if plan completed successfully
        Results:
            Plan should complete successfully
        """
        service = ["puppetdb"]
        self._stop_service_config(service, timeout=15)

    def obsolete_98_litp_backup_frequency(self):
        """
        Description:
            Obsolete until we can add new test for puppetdb
            Ensure that when no changes are made to the litp model
            that no unnecessary backups are taken, and that
            only two json backups are retained at any one
            time.
        Actions:
            1. Update the backup time in the litpd.conf file.
            2. Restart LITP.
            3. Check the LAST_KNOWN_CONFIG write time.
            4. Check that only two .json backup exists.
            5. Check the json file write time.
            6. Check the files every 30 seconds for 5 minutes.
            7. Ensure files have not been written to since being checked.
        Results:
            The files are not written to when no changes are made to the
            LITP model.
        """
        self.log('info', "#1 Update the backup time in the litpd.conf file.")
        litp_conf = test_constants.LITPD_CONF_FILE
        # RETRIEVING VALUE SPECIFIED FOR backup_interval IN LITP
        # CONFIGURATION FILE FOR UPDATING TO 30 SECONDS AND SUBSEQUENT
        # REPLACEMENT OF ORIGINAL VALUE
        grep_cmd = \
        self.redhat.grep_path + " backup_interval {0}".format(litp_conf)
        stdout, _, _ = \
        self.run_command(self.ms_node, grep_cmd,
                         su_root=True)
        orig_value = stdout[0]
        try:
            self.replace_text_in_file(litp_conf, orig_value,
                                      "backup_interval: 30")

            self.log('info', "#2 Restart LITP.")
            self.restart_litpd_service(self.ms_node, debug_on=False)
            self.get_service_status(self.ms_node, 'litpd')

            self.log('info', "#3 Check the LAST_KNOWN_CONFIG write time.")
            lkc_file = test_constants.LITP_LAST_KNOWN_CONFIG
            lkc_orig_write_time = \
            self.chk_file_write_time(lkc_file)

            self.log('info', "#4 Check that only two .json backup exists.")
            core_path = "/var/lib/litp/core"
            stdout = self.list_dir_contents(self.ms_node,
                                            core_path,
                                            grep_args="json")
            if "model" in stdout:
                model_path = "/var/lib/litp/core/model"
                stdout = \
                    self.list_dir_contents(self.ms_node,
                                           model_path,
                                           grep_args="json")

                # Remove any xml snapshot json files from the list
                newlist = self.remove_snapshot_xml_json(stdout)

                # Ensure the correct number of json files remain
                self.assertTrue(len(newlist) == 2,
                                "Two backup .JSON files were expected, "
                                "the number found was: {0}"
                                .format(len(newlist)))

                self.log('info', "#5 Check the json file write time.")
                json1_filename = newlist[0]
                json1_path = model_path + "/{0}".format(json1_filename)
                json1_orig_write_time = self.chk_file_write_time(json1_path)

                json2_filename = newlist[1]
                json2_path = model_path + "/{0}".format(json2_filename)
                json2_orig_write_time = self.chk_file_write_time(json2_path)

                self.log('info',
                "#6 Check the files every 30 seconds for 5 minutes.")
                limit = 10
                counter = 0
                while counter < limit:
                    # CHECK AND COMPARE LKC FILE WRITE TIME
                    lkc_current_write_time = \
                    self.chk_file_write_time(lkc_file)
                    self.assertEqual(lkc_orig_write_time,
                                     lkc_current_write_time,
                                     "Write times of LKC are not the same, " \
                                     "original write time was: {0}, " \
                                     "current write time is: " \
                                     "{1}".format(lkc_orig_write_time,
                                                  lkc_current_write_time))

                    # CHECK AND COMPARE JSON FILE WRITE TIME
                    # FIND ALL JSON FILES IN LITP FILES DIRECTORY
                    stdout = \
                    self.list_dir_contents(self.ms_node, model_path,
                                           grep_args="json")

                    # Remove any xml snapshot json files from the list
                    newlist = self.remove_snapshot_xml_json(stdout)

                    # Ensure the correct number of json files remain
                    self.assertTrue(len(newlist) == 2,
                                "Two backup .JSON files were expected, " \
                                "the number found was: {0}"
                                    .format(len(newlist)))

                    # ENSURE THAT THE FILE IS THE SAME
                    self.assertTrue(json1_filename and
                                    json2_filename in
                                    newlist,
                                    "Expected JSON backup files '{0}, {1}' " \
                                    "were not found, a new backup may've " \
                                    "been created.".format(json1_filename,
                                                           json2_filename))
                    # ENSURE THAT THE FILE HASN'T BEEN
                    # WRITTEN TO SINCE LAST CHECK
                    json1_current_write_time = \
                        self.chk_file_write_time(json1_path)
                    self.assertEqual(json1_orig_write_time,
                                     json1_current_write_time,
                                     "Write time of JSON backup file " \
                                     "has changed, original write " \
                                     "time was: {0}, " \
                                     "current write time is: " \
                                     "{1}".format(json1_orig_write_time,
                                                  json1_current_write_time))
                    json2_current_write_time = \
                        self.chk_file_write_time(json2_path)
                    self.assertEqual(json2_orig_write_time,
                                     json2_current_write_time,
                                     "Write time of JSON backup file has "
                                     "changed, original write time was: {0}, "
                                     "current write time is: " \
                                     "{1}".format(json2_orig_write_time,
                                                  json2_current_write_time))
                    time.sleep(30)
                    counter += 1
        finally:
            self.log('info',
                     "Ending test case, setting backup internal " \
                     "back to its original value.")
            self.replace_text_in_file(litp_conf,
                                      "backup_interval: 30",
                                      orig_value)
            self.log('info', "Restart LITP.")
            self.restart_litpd_service(self.ms_node)
            self.get_service_status(self.ms_node, 'litpd')

    @attr('all', 'revert', 'robustness', 'rob_p2', 'robustness_tc99')
    def test_99_ensure_litp_config_robust(self):
        """
        Description:
            Ensure that should /var be filled to capacity that the litpd
            service can be stopped and appear to start successfully, but not
            be found running when checked after starting.
            After the extra files in /var are removed the service can then be
            started again without issue.
        Actions:
            1. Ascertain the status of the /var volume.
            2. Fill /var and all its partitions.
            3. Ascertain the status of the /var volume.
            4. Attempt to create a series of new LITP model items.
            5. Stop LITP.
            6. Start LITP , this is expected to appear to succeed, but service
               is expected not to be found running
            7. Removing all files created.
            8. Get status of LITP.
            9. Start LITP, ensure success.
            10. Check that only a single instance of LITP is running.
            11. Ascertain the status of the /var volume.
        Results:
            The LITP service fails to start while /var is full but starts
            successfully when extra files in /var are cleared.
            The new model items do not exist in LITP after cleanup.
        """
        # RETRIEVE THE SIZE OF THE MESSAGES LOG
        self.log('info',
                 "Messages log size: {0}".format(
                                    self.get_file_size(
                                    test_constants.GEN_SYSTEM_LOG_PATH)))

        # QUERY COMMAND OF VOLUME FOR USE IN FINALLY BLOCK TO BE
        # CONSTRUCTED IN THE TRY BLOCK
        df_cmd = self.redhat.get_df_cmd('-Th')
        grep_cmd = self.redhat.grep_path + " /var"
        size_query_cmd = df_cmd + " | " + grep_cmd
        self.log("info", "#1 Ascertaining the status of the var volume")
        self.run_command(self.ms_node, size_query_cmd, su_root=True)

        try:
            # RETRIEVE THE SIZE OF THE MESSAGES LOG
            self.log('info',
                     "Messages log size: {0}".format(
                                        self.get_file_size(
                                        test_constants.GEN_SYSTEM_LOG_PATH)))

            self.log("info", "#3 Ascertaining the status of the var volume")
            orig_var_listing, _, _ = \
            self.run_command(self.ms_node, size_query_cmd, su_root=True)

            # MULTIPLE PARTITIONS MAY EXIST BELOW /var, THUS THIS AIMS
            # TO GATHER THEM ALL FOR FILLING.
            var_dirs = []
            for line in orig_var_listing:
                var_dirs.append(line.split(' ')[-1])

            self.log("info",
            "#2 Filling /var and all partitions created below")
            files_to_del = []
            for directory in var_dirs:
                files_to_del = \
                self.fill_fs(self.ms_node, directory, files_to_del)
                # RETRIEVE THE SIZE OF THE MESSAGES LOG
                self.log('info',
                         "Messages log size: {0}".format(
                                        self.get_file_size(
                                        test_constants.GEN_SYSTEM_LOG_PATH)))

            self.log("info", "#3 Ascertaining the status of the var volumes")
            stdout, _, _ = \
            self.run_command(self.ms_node, size_query_cmd, su_root=True)
            # ENSURE THAT EACH PARTITION HAS BEEN FILLED TO 100%.
            for line in stdout:
                self.assertTrue("100%" in line)

            self.log("info",
                     "#4 Attempt to create a series of new LITP model items, "
                     "this should still work even with /var 100% full.")
            # Attempt to create some extra model items while /var is filled to
            # capacity ,
            # This is expected to still be possible despite /var being full for
            # a small amount of time , after which an internal server error
            # will be returned on litp commands
            number = 0
            while number < 500:
                if number < 10:
                    suffix = "00{0}".format(number)
                elif number < 100:
                    suffix = "0{0}".format(number)
                else:
                    suffix = "{0}".format(number)
                url = "/software/items/robustness_{0}".format(suffix)
                props = \
                "name=robustness_{0} release=1 " \
                "version=1 epoch=0".format(suffix)
                create_cmd = \
                self.cli_utils.get_create_cmd(url, 'package', props)
                _, _, rtcode = \
                self.run_command(self.ms_node, create_cmd,
                                 su_root=True)
                if rtcode != 0:
                    break
                number += 1

            # RETRIEVE THE SIZE OF THE MESSAGES LOG
            self.log('info',
                     "Messages log size: {0}".format(
                                        self.get_file_size(
                                        test_constants.GEN_SYSTEM_LOG_PATH)))

            # PRINT A LOG STATEMENT IF ANY ITEMS SUCCESSFULLY CREATED
            if number != 0:
                self.log("info", "Despite /var being full, {0} items were "
                                 "successfully created in LITP model."
                         .format(number))

            self.log("info", "#5 Stop LITP.")
            stdout, _, _ = \
            self.get_service_status(self.ms_node, 'litpd',
                                    assert_running=True)
            self.assertTrue("is running..." in stdout[0])
            _, _, rtcode = \
            self.stop_service(self.ms_node, 'litpd',
                              assert_success=False, su_root=True,
                              su_timeout_secs=self.litpd_stop_timeout_secs)
            self.assertEqual(rtcode, 0)

            stdout, _, _ = \
                self.get_service_status(self.ms_node,
                                        'litpd',
                                        assert_running=False)
            self.assertEqual('litp_service.py is stopped', stdout[0])

            self.log("info", "#6 Start LITP and ensure it appears to start.")
            self.start_service(self.ms_node,
                                'litpd',
                                assert_success=True,
                                su_root=True)

            # RETRIEVE THE SIZE OF THE MESSAGES LOG
            self.log('info',
                     "Messages log size: {0}".format(
                                        self.get_file_size(
                                        test_constants.GEN_SYSTEM_LOG_PATH)))

            # LITP IS EXPECTED TO BE DEAD AT THIS POINT DUE TO VAR BEING
            # FILLED TO 100%
            stdout, _, retcode = \
            self.get_service_status(self.ms_node, 'litpd',
                                    assert_running=False)
            self.assertNotEqual(retcode, 0)
            self.assertEqual("litp_service.py dead "
                             "but pid file exists", stdout[0])

        finally:
            self.log("info", "#7 Removing all files created.")
            rm_cmd = "/bin/rm -f {0}"
            for created_file in files_to_del:
                self.run_command(self.ms_node, rm_cmd.format(created_file),
                                 su_root=True)

            # RETRIEVE THE SIZE OF THE MESSAGES LOG
            self.log('info',
                     "Messages log size: {0}".format(
                                        self.get_file_size(
                                        test_constants.GEN_SYSTEM_LOG_PATH)))

            self.log("info", "#5 Stop litp , expect success")
            self.get_service_status(self.ms_node, 'litpd',
                                    assert_running=False)
            self.stop_service(self.ms_node, 'litpd',
                              assert_success=False, su_root=True,
                              su_timeout_secs=self.litpd_stop_timeout_secs)
            self.get_service_status(self.ms_node, 'litpd',
                                    assert_running=False)

            self.log("info", "#9 Start LITP, ensure success.")
            # A SUCCESSFUL STARTUP PROVES NO CORRUPTION HAS TAKEN PLACE TO THE
            # LITP CONFIG FILE
            self.start_service(self.ms_node, 'litpd', assert_success=True,
                               su_root=True)
            _, _, retcode = \
            self.get_service_status(self.ms_node, 'litpd',
                                    assert_running=True)
            self.assertEqual(retcode, 0)
            self.turn_on_litp_debug(self.ms_node)

            self.log("info",
            "#10 Check that only a single instance of LITP is running.")
            self.chk_individual_litp_running()

            # RETRIEVE THE SIZE OF THE MESSAGES LOG
            self.log('info',
                     "Messages log size: {0}".format(
                                        self.get_file_size(
                                        test_constants.GEN_SYSTEM_LOG_PATH)))

            self.log("info", "#11 Ascertaining the status of the var volume.")
            self.run_command(self.ms_node, size_query_cmd, su_root=True)

    @attr('all', 'robustness', 'rob_p1', 'robustness_tc20')
    def test_20_invalid_crud_messages_to_the_litp_rest_interface(self):
        """
        Description:
            Ensure that invalid CRUD messages sent to the LITP rest interface
            return the correct error
        Actions:
            1. Send invalid Create messages to the LITP rest interface
            2. Send invalid Read messages to the LITP rest interface
            3. Send invalid Update messages to the LITP rest interface
            4. Send invalid Delete messages to the LITP rest interface
        Results:
            All messages return the expected error
        """
        # All rest interface commands have expected return code 0
        expected_rc = 0

        # Create
        self.log('info', "Section: Invalid 'CREATE' (POST) messages")
        self.log('info', "Create plan using invalid data")
        data = '{"id": "plan","type": "invalid_plan"}'
        path = "plans"
        args = '-k -X POST'
        cmd = self.get_rest_cmd(data, path, args)
        expected_error = '"message": "Create plan failed: Must specify type ' \
                         'as \'plan\' or \'reboot_plan\'", ' \
                         '"type": "InvalidRequestError"'
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        self.log('info', "Inherit package from using invalid data")
        data = '{"id": "finger","inherit": "/software/items/invalid_finger"}'
        path = "deployments/d1/clusters/c1/nodes/n1/items"
        args = "-k -X POST"
        cmd = self.get_rest_cmd(data, path, args)
        expected_error = '"message": "Source item /software/items/'\
                         'invalid_finger doesn\'t exist", "type": '\
                         '"InvalidLocationError"'
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        # Read
        self.log('info', "Section: Invalid 'READ' (GET) messages")
        self.log('info', "Show nonexistant item")
        data = ''
        path = "deployments/d1/clusters/c1/nodes/n1/fake/path"
        args = "-k -X GET"
        cmd = self.get_rest_cmd(data, path, args)
        expected_error = '"type": "InvalidLocationError", "message": "Not '\
                         'found"'
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        self.log('info', "Show nonexistant plan")
        data = ''
        path = "plans/plan"
        args = "-k -X GET"
        cmd = self.get_rest_cmd(data, path, args)
        expected_error = '"message": "Plan does not exist", '\
                         '"type": "InvalidLocationError"'
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        # Update
        self.log('info', "Section: Invalid 'UPDATE' (PUT) messages")
        self.log('info', "Set plan to invalid state")
        # Valid use would be to use state:"running" or state:"stopped" to run
        # or stop a plan
        data = '{"state": "invalid"}'
        path = "plans/plan"
        args = "-k -X PUT"
        cmd = self.get_rest_cmd(data, path, args)
        expected_error = '"message": "Properties must be specified for '\
                         'update", "type": "InvalidRequestError"'
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        self.log('info', "Change name on package-list using invalid data")
        data = '{"properties": {"name": ""}}'
        path = "software/items/httpd"
        args = "-k -X PUT"
        cmd = self.get_rest_cmd(data, path, args)
        expected_error = '{"message": "Invalid value \'\'.", "type": '\
                         '"ValidationError", "property_name": "name"}'
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        # Delete
        self.log('info', "Section: Invalid 'DELETE' (DELETE) messages")
        self.log('info', "Remove an item using an invalid path")
        data = ""
        path = "deployments/d1/clusters/c1/nodes/n1/items/invalid_finger"
        args = "-k -X DELETE"
        cmd = self.get_rest_cmd(data, path, args)
        expected_error = '"message": "Path not found", '\
                         '"type": "InvalidLocationError"'
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        self.log('info', "Remove inherited finger using invalid data")
        data = ""
        path = "software/items/invalid"
        args = "-k -X DELETE"
        cmd = self.get_rest_cmd(data, path, args)
        expected_error = '"message": "Path not found", '\
                         '"type": "InvalidLocationError"'
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

    @attr('all', 'robustness', 'rob_p1', 'robustness_tc21')
    def test_21_invalid_commands_entered_via_the_litp_cli(self):
        """
        Description:
            Ensure that invalid LITP command line interface commands fail as
            expected
        Actions:
            1. Run each type of litp command in an invalid way
        Results:
            Each command fails, returning the expected error and return code
        """
        rc_returned_error = 1
        rc_invalid_input = 2

        # create Command
        self.log('info', "Invalid 'create' command: invalid type")
        cmd = self.cli_utils.get_create_cmd('/deployments/deployment1',
                                            'invalid_type')
        expected_error = "InvalidTypeError    Item type not registered: " \
                         "invalid_type"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # create_plan Command
        self.log('info', "Invalid 'create_plan' command: No tasks to create")
        cmd = self.cli_utils.get_create_plan_cmd()
        expected_error = "DoNothingPlanError    Create plan failed: " \
                         "no tasks were generated"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # create_snapshot Command
        self.log('info', "Invalid 'create_snapshot' command: Name too long")
        cmd = self.cli_utils.get_create_snapshot_cmd(
            args='-n longname')
        expected_error = "ValidationError    Create snapshot failed: "\
                     "Snapshot name tag cannot exceed 7 characters which "\
                     "is the maximum available length for a NAS file system"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # debug Command
        self.log('info', "Invalid 'debug' command: Invalid option")
        cmd = "litp debug -o invalid_option"
        expected_error = "litp debug: error: argument -o/--option: invalid "\
                         "choice: 'invalid_option' (choose from 'normal', "\
                         "'override')"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_invalid_input)

        # export Command
        self.log('info', "Invalid 'export' command: Path not specified")
        cmd = self.cli_utils.get_xml_export_cmd("")
        expected_error = "litp export: error: argument -p/--path: expected "\
                         "one argument"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_invalid_input)

        # import Command
        self.log('info', "Invalid 'import' command: Invalid source path")
        cmd = self.cli_utils.get_import_cmd("invalid_source", "litp")
        expected_error = "ValidationError    Path invalid_source is not valid"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # import_iso Command
        self.log('info', "Invalid 'import_iso' command: Non absolute source")
        cmd = self.cli_utils.get_import_iso_cmd("invalid_iso_source")
        expected_error = 'ValidationError    Source path '\
                         '"invalid_iso_source" must be an absolute path.'
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # inherit Command
        self.log('info', "Invalid 'inherit' command: Invalid source path")
        cmd = self.cli_utils.get_inherit_cmd(
            "/deployments/d1/clusters/c1/nodes/node1/example_collection",
            "/invalid_source")
        expected_error = "InvalidLocationError    "\
                         "Source item /invalid_source doesn't exist"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # load Command
        self.log('info', "Invalid 'load' command: Invalid source path")
        cmd = self.cli_utils.get_xml_load_cmd("invalid_source", "networks.xml")
        expected_error = "litp load: error: argument -p/--path: "\
                         "invalid_source is not a valid path argument"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_invalid_input)

        # load Command - legacy
        # When this KPI was based on the model soak, this load comand was the
        # only invalid CLI command run
        self.log('info', "Invalid 'load' command: Invalid argument")
        cmd = self.cli_utils.get_xml_load_cmd("/software/items/",
                                              "addPackList_inc_arg.xml",
                                              args='--Incarg')
        expected_error = "litp: error: unrecognized arguments: --Incarg"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_invalid_input)

        # prepare_restore Command
        self.log('info', "Invalid 'prepare_restore' command: Invalid argument")
        cmd = self.cli_utils.get_prepare_restore_cmd(args='--invalid_arg')
        expected_error = "litp: error: unrecognized arguments: --invalid_arg"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_invalid_input)

        # remove Command
        self.log('info', "Invalid 'remove' command: Invalid path")
        cmd = self.cli_utils.get_remove_cmd("/invalid_path")
        expected_error = "InvalidLocationError    Path not found"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # remove_plan Command
        self.log('info', "Invalid 'remove_plan' command: No plan to remove")
        cmd = self.cli_utils.get_remove_plan_cmd()
        expected_error = "InvalidLocationError    Plan does not exist"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # remove_snapshot Command
        self.log('info', "Invalid 'remove_snapshot' command: Named snapshot "\
                         "does not exist")
        cmd = self.cli_utils.get_remove_snapshot_cmd(args='-n invalid_snap')
        expected_error = 'DoNothingPlanError    no tasks were generated. No '\
                         'remove snapshot tasks added because Named Backup '\
                         'Snapshot "invalid_snap" does not exist.'
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # restore_model Command
        self.log('info', "Invalid 'restore_model' command: Invalid argument")
        cmd = 'litp restore_model --invalid_arg'
        expected_error = "litp: error: unrecognized arguments: --invalid_arg"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_invalid_input)

        # restore_snapshot Command
        self.log('info', "Invalid 'restore_snapshot' command: "\
                         "Invalid argument")
        cmd = self.cli_utils.get_restore_snapshot_cmd(args='--invalid_arg')
        expected_error = "litp: error: unrecognized arguments: --invalid_arg"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_invalid_input)

        # run_plan Command
        self.log('info', "Invalid 'run_plan' command: No plan to run")
        cmd = self.cli_utils.get_run_plan_cmd()
        expected_error = "InvalidLocationError    Plan does not exist"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # show Command
        self.log('info', "Invalid 'show' command: Nonexistant property")
        cmd = self.cli_utils.get_show_cmd("/", args="-o invalid_property")
        expected_error = 'InvalidPropertyError    '\
                         'Property "invalid_property" is not set'
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # show_plan Command
        self.log('info', "Invalid 'show_plan' command: No plan to show")
        cmd = self.cli_utils.get_show_plan_cmd()
        expected_error = "InvalidLocationError    Plan does not exist"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # stop_plan Command
        self.log('info', "Invalid 'stop_plan' command: No plan to stop")
        cmd = self.cli_utils.get_stop_plan_cmd()
        expected_error = "InvalidLocationError    Plan does not exist"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # update Command
        self.log('info', "Invalid 'update' command: Forbidden property to "\
                         "update")
        cmd = self.cli_utils.get_update_cmd("/", "invalid_property=true",
                                                 action_delete=False)
        expected_error = 'PropertyNotAllowedError in property: '\
                         '"invalid_property"    "invalid_property" is not an '\
                         'allowed property of root'
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        self.log('info', "Invalid 'update' command: Forbidden property to "\
                         "delete")
        cmd = self.cli_utils.get_update_cmd("/", "invalid_property",
                                                 action_delete=True)
        expected_error = 'InvalidRequestError in property: '\
                         '"invalid_property"    Unable to delete property: '\
                         'invalid_property'
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # upgrade Command
        self.log('info', "Invalid 'upgrade' command: Invalid upgrade path")
        cmd = self.cli_utils.get_upgrade_cmd("/invalid_path")
        expected_error = 'InvalidLocationError    Upgrade can only be run on '\
                         'deployments, clusters or nodes'
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_returned_error)

        # version Command
        self.log('info', "Invalid 'version' command: Invalid argument")
        cmd = self.cli_utils.get_litp_version_cmd(args='--invalid_arg')
        expected_error = "litp: error: unrecognized arguments: --invalid_arg"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_invalid_input)

        # Nonexistant command
        self.log('info', "Nonexistant litp command")
        cmd = "litp invalid_command"
        expected_error = "litp: error: argument : invalid choice: "\
                         "'invalid_command'"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_invalid_input)

        # Invalid username and password arguments
        self.log('info', "Invalid username and password arguments")
        cmd = "litp --username --password"
        expected_error = "litp: error: argument -u/--username: "\
                         "expected one argument"
        self.run_cmd_with_error_validation(cmd, expected_error,
                                            rc_invalid_input)

    @attr('all', 'robustness', 'rob_p1', 'robustness_tc22')
    def test_22_corrupt_model_loaded_via_xml(self):
        """
        Description:
            Ensure that attempting to load a corrupt model via xml fails with
            expected error
        Actions:
            1. Copy XML files to the MS
            2. Load XML files with corrupt model
        Results:
            All load attempts fail with expected error
        """
        # Get local directory
        local_dir = os.path.dirname(os.path.abspath(__file__))

        # Define filenames for copy
        xml_files = ["bad_pkg_01.xml", "bad_pkg_02.xml", "bad_pkg_03.xml",
                     "bad_pkg_01.xml", "xml_incomplete.xml"]

        # Copy xml files to MS
        self.log('info', "Copying XML files to MS")
        for filename in xml_files:
            local_filepath = "{0}/xml/{1}".format(local_dir, filename)
            successful_copy = self.copy_file_to(self.ms_node,
                                                local_filepath,
                                                "/tmp/")
            self.assertTrue(successful_copy,
                            "Copy of {0} failed".format(filename))

        # All invalid load commands here are expected to have return code 1
        expected_rc = 1

        # Load Invalid XML files
        self.log('info', "Load invalid XML file")
        cmd = self.cli_utils.get_xml_load_cmd("/software/items",
                                    "/tmp/bad_pkg_01.xml",
                                    "--replace")
        expected_error = "InvalidXMLError    This element is not expected. "\
                         "Expected is one of ( release, replaces,"\
                         " repository, requires, version )., line 4"
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        self.log('info', "Load invalid XML file")
        cmd = self.cli_utils.get_xml_load_cmd("/software/items",
                                    "/tmp/bad_pkg_02.xml",
                                    "--merge")
        expected_error = "InvalidRequestError    Premature end of data in tag"\
                         " package line 2, line 4, column 1"
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        self.log('info', "Load invalid XML file")
        cmd = self.cli_utils.get_xml_load_cmd("/software/items",
                                    "/tmp/bad_pkg_03.xml",
                                    "--replace")
        expected_error = "InvalidXMLError    The attribute "\
                         "'{http:///2001/XMLSchema-instance}schemaLocation' "\
                         "is not allowed., line 2"
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        # Load incomplete XMl file with merge
        self.log('info', "Load invalid XML file with merge")
        cmd = self.cli_utils.get_xml_load_cmd("/software/items",
                                    "/tmp/xml_incomplete.xml",
                                    "--merge")
        expected_error = "InvalidRequestError    expected '>', line 7, column"\
                         " 1"
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)

        # Load incomplete XMl file with replace
        self.log('info', "Load invalid XML file with replace")
        cmd = self.cli_utils.get_xml_load_cmd("/software/items",
                                    "/tmp/xml_incomplete.xml",
                                    "--replace")
        expected_error = "InvalidRequestError    expected '>', line 7, column"\
                         " 1"
        self.run_cmd_with_error_validation(cmd, expected_error, expected_rc)
