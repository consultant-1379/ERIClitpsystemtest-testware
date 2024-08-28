#!/usr/bin/env python
"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Nov 2015
@author:    Stefan , Gary O'COnnor
@summary:   System Test for checking "litp-admin" permissions to
            execute critical commands.
            Agile: EPIC-xxxx, STORY-xxxx, Sub-task: STORY-xxxx
"""
from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
import inspect
import time


class LitpAdminPrivs(GenericTest):
    """
    Description:
        These tests are checking "litp-admin" user permissions to execute
        critical commands. "litp-admin" user should not be allowed.
    """

    def setUp(self):
        super(LitpAdminPrivs, self).setUp()
        self.rhel = RHCmdUtils()
        self.ms_node = self.get_management_node_filename()
        self.fail_list = []

        self.stop_litpd = "/sbin/service litpd stop"
        self.start_litpd = "/sbin/service litpd start"
        self.restart_litpd = "/sbin/service litpd restart"

        self.stop_network = "/sbin/service network stop"
        self.start_network = "/sbin/service network start"
        self.restart_network = "/sbin/service network restart"

        self.stop_cobblerd = "/sbin/service cobblerd stop"
        self.start_cobblerd = "/sbin/service cobblerd start"
        self.restart_cobblerd = "/sbin/service cobblerd restart"

        self.stop_puppet = "/sbin/service puppet stop"
        self.start_puppet = "/sbin/service puppet start"
        self.restart_puppet = "/sbin/service puppet restart"

        self.start_mcollective = "/sbin/service mcollective start"
        self.restart_mcollective = "/sbin/service mcollective restart"

    def tearDown(self):
        """
        Runs after every test
        """
        super(LitpAdminPrivs, self).tearDown()

        # Checking status of services after test has run
        service_list = ["litpd",
                        "cobblerd",
                        "puppet",
                        "mcollective",
                        "rabbitmq-server"]
        for service in service_list:
            self.log("info", "Checking the status of service '{0}'"
                     .format(service))
            status_cmd = "/sbin/service {0} status".format(service)
            stdout = self.run_command(self.ms_node, status_cmd, su_root=True)
            if service == "rabbitmq-server":
                if "nodedown" not in stdout[0][1]:
                    continue
            else:
                # If service not running assert error
                self.assertTrue("pid" and "running" in stdout[0][0],
                                "Service {0} is not running".format(service))
                self.log("info", "Service '{0}' is running".format(service))

        # Remove crash file which can be created during
        # "service rabbitmq-server status"
        self.remove_rabbitmq_crash_file()

    def perform_stop_litpd(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "service litpd stop"
        Actions:
            1. Execute "service litpd stop"
            2. Checked the error messages returned
        Results:
            Executing service litpd stop using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'litpd'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Permission denied.'], [], 4]
        self.get_service_status(self.ms_node, service)
        # STOP LITPD SERVICE
        self.log("info", "perform stop litpd as litp-admin expected to fail")
        output = self.run_command(self.ms_node, self.stop_litpd,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(self.ms_node, service)

    def perform_start_litpd(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "service litpd start"
        Actions:
            1. Execute "service litpd stop" as root
            2. Execute "service litpd start" as litp-admin
            3. Checked the error messages returned
            4. Execute "service litpd start" as root
        Results:
            Executing "service litpd start" using "litp-admin"
            user should throw a specific error messages.
        """
        service = 'litpd'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Permission denied.'], [], 4]
        self.get_service_status(self.ms_node, service)
        # STOP LITPD SERVICE as ROOT
        self.log("info", "Stop litpd as root - expect success")
        self.run_command(self.ms_node, self.stop_litpd, su_root=True)
        self.get_service_status(self.ms_node, service, assert_running=False)
        # START LITPD SERVICE
        self.log("info", "perform start litpd as litp-admin - expect Failure")
        output = self.run_command(self.ms_node, self.start_litpd,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(self.ms_node, service, assert_running=False)
        # START LITPD SERVICE as ROOT
        self.log("info", "Start litpd as root - expect success")
        self.run_command(self.ms_node, self.start_litpd, su_root=True)
        self.get_service_status(self.ms_node, service)

    def perform_restart_litpd(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "litpd restart"
        Actions:
            1. Execute "litpd restart"
            2. Checked the error messages returned
        Results:
            Executing "litpd restart" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'litpd'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Permission denied.'], [], 4]
        self.get_service_status(self.ms_node, service, assert_running=False)
        # RESTART LITPD SERVICE
        self.log("info", "perform restart litpd as litp-admin - expect "
                         "Failure")
        output = self.run_command(self.ms_node, self.restart_litpd,
                                  username='litp-admin')

        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(self.ms_node, service, assert_running=False)

    def perform_stop_network(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "network stop"
        Actions:
            1. Execute "network stop"
            2. Checked the error messages returned
        Results:
            Executing "network stop" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'network'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [[], [], 4]
        self.get_service_status(self.ms_node, service)
        # STOP NETWORK
        self.log("info", "perform stop network as litp-admin - expect failure")
        stdout = self.run_command(self.ms_node, self.stop_network,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, stdout)
        self.get_service_status(self.ms_node, service)

    def perform_start_network(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "network start"
        Actions:
            1. Execute "network start"
            2. Checked the error messages returned
        Results:
            Executing "network start" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'network'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [[], [], 4]
        self.get_service_status(self.ms_node, service, assert_running=False)
        # START NETWORK
        self.log("info", "perform start network as litp-admin - expect "
                         "failure")
        output = self.run_command(self.ms_node, self.start_network,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(self.ms_node, service)

    def perform_restart_network(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "network restart"
        Actions:
            1. Execute "network restart"
            2. Checked the error messages returned
        Results:
            Executing "network restart" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'network'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [[], [], 4]
        self.get_service_status(self.ms_node, service, assert_running=False)
        # RESTART NETWORK
        self.log("info", "perform restart network as litp-admin - expect "
                         "failure")
        output = self.run_command(self.ms_node, self.restart_network,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(self.ms_node, service, assert_running=False)

    def perform_stop_cobbler(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "cobbler stop"
        Actions:
            1. Execute "cobbler stop"
            2. Checked the error messages returned
        Results:
            Executing "cobbler stop" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'cobblerd'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Stopping cobbler daemon: [FAILED]'], [], 1]
        self.get_service_status(self.ms_node, service)
        # STOP COBBLER
        self.log("info", "perform stop cobbler as litp-admin - expect failure")
        output = self.run_command(self.ms_node, self.stop_cobblerd,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(self.ms_node, service)

    def perform_start_cobbler(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "cobbler start"
        Actions:
            1. Execute "cobbler start"
            2. Checked the error messages returned
        Results:
            Executing "cobbler start" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'cobblerd'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [[], ["touch: cannot touch `/var/lock/subsys/cobblerd'"
                            ": Permission denied"], 0]
        self.get_service_status(self.ms_node, service)
        # STOP SERVICE as ROOT
        self.run_command(self.ms_node, self.stop_cobblerd, su_root=True)
        self.get_service_status(self.ms_node, service, assert_running=False)
        # START COBBLER
        self.log('info', "perform start cobbler as litp-admin - expect "
                         "failure")
        output = self.run_command(self.ms_node, self.start_cobblerd,
                                  username='litp-admin')

        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)

        self.get_service_status(self.ms_node, service, assert_running=False)
        # START SERVICE as ROOT
        self.run_command(self.ms_node, self.start_cobblerd, su_root=True)
        self.get_service_status(self.ms_node, service)

    def perform_restart_cobbler(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "cobbler restart"
        Actions:
            1. Execute "cobbler restart"
            2. Checked the error messages returned
        Results:
            Executing "cobbler restart" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'cobblerd'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [[], ["touch: cannot touch `/var/lock/subsys/cobblerd'"
                            ": Permission denied"], 0]
        self.get_service_status(self.ms_node, service, assert_running=False)
        # RESTART COBBLER
        self.log("info", "perform restart cobbler as litp-admin - expect "
                         "failure")
        output = self.run_command(self.ms_node, self.restart_cobblerd,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(self.ms_node, service, assert_running=False)

    def remove_strings(self, list_ok, list_returned):
        """
        Check list_returned for any items that are in the list_ok
        If the item in list_ok they are removed from the list_returned
        The list_returned is returned minus any OK items
        Args:
            list_ok: list of OK strings
            list_returned: list to be filtered and then returned
        """
        # Filter through lists
        for item_ok in list_ok:
            for item_ret in list(list_returned):
                if item_ok in item_ret:
                    self.log('info', item_ret)
                    list_returned.remove(item_ret)
        return list_returned

    def grep_for_pkill(self, message_list, node):
        """
        Description:
            Find pkill: PID if one exists in stdout or stderr.
        Args:
            message_list: messages to check
            node: system on which to perform checks
        Actions:
            1.Search both stdout & stderr for a pkill operation.
            2.If pkill is found in stdout or stderr the
              process is traced to find what process the PID belongs to.
            3.The returned trace details are then searched to verify
              the pkill pid belongs to puppet agent.
            4.The grep for the PID number and any child processes of the
              puppet agent should be the only other processes in the list
        Result:
            This function returns True if the expected puppet process is found
            and returns False if an unexpected process is found to have caused
            the pkill error
        """

        for pkill_error in message_list:
            if "pkill" in pkill_error:
                # Gets the PID from the pkill error
                pid = pkill_error.split(' ')[1]
                self.log('info', "Searching for process with PID: '{0}'"
                         .format(pid))
                # Creates command to grep for the PID
                cmd = self.rhel.get_grep_file_cmd(' ', pid, '', 'ps -eaf')
                self.assertNotEqual([], cmd)
                stdout = self.run_command(node, cmd)

                for line in stdout[0]:
                    self.log('info', "Checking for expected services in '{0}'"
                             .format(line))
                    # Gets the parent pid of the process
                    parent_pid = line.split()[2]

                    # If expected process in line of stdout out return True
                    if "puppet agent: applying configuration" in line:
                        self.log("info", "Expected puppet agent found for "
                                         "pkill")
                        return True

                    # Since grep is used to find the process id, there
                    # will always be a grep process present in the stdout
                    elif "grep" in line:
                        self.log("info", "Only grep found with process id - "
                                         "puppet run has completed")
                        continue

                    # If the pid we are grepping for is in the parent pid
                    # continue to next process in stdout
                    elif pid == parent_pid:
                        # Gets the process name from the line of stdout
                        process_name = line.split()[7]
                        self.log("info", "Process '{0}' is a child process of "
                                         "process with PID: '{1}'"
                                 .format(process_name, pid))
                        continue
                    else:
                        # test fails if unexpected process is found
                        self.log("error", "pkill of unexpected service "
                                          "detected: '{0}'".format(line))
                        return False
            return True

    def perform_stop_puppet(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "puppet stop"
        Args:
            node: system on which to perform checks
        Actions:
            1. Execute "puppet stop"
            2. Checked the error messages returned
        Results:
            Executing "puppet stop" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'puppet'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Stopping puppet agent: [FAILED]'],
                       ["rm: cannot remove `/var/run/puppet/agent.pid': "
                        "Permission denied"], 1]
        self.log('info', "Check puppet status")
        self.get_service_status(node, service)

        # STOP PUPPET
        self.log("info", "perform stop puppet as litp-admin - expect failure")
        stdout, stderr, exit_code = self.run_command(
            node, self.stop_puppet, username='litp-admin')
        self.log('info', "Checking for pkill errors")
        # Search for pkill errors
        search_for_pkill = self.grep_for_pkill(stderr, node)
        stderr = self.remove_strings(["pkill"], stderr)
        output = [stdout, stderr, exit_code]
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(node, service, assert_running=False)
        return search_for_pkill

    def perform_start_puppet(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "puppet start"
        Args:
            node: system on which to perform checks
        Actions:
            1. Execute "puppet start"
            2. Checked the error messages returned
        Results:
            Executing "puppet start" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'puppet'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Starting puppet agent: [FAILED]'],
                       ["Error: Could not intialize global default settings"],
                       1]
        self.get_service_status(node, service)
        # STOP SERVICE as ROOT
        self.run_command(node, self.stop_puppet, su_root=True)
        self.get_service_status(node, service, assert_running=False)

        # START PUPPET
        self.log("info", "perform start puppet as litp-admin - expect failure")
        output = self.run_command(node, self.start_puppet,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(node, service, assert_running=False)
        # START SERVICE as ROOT
        self.run_command(node, self.start_puppet, su_root=True)
        self.get_service_status(node, service)

    def perform_restart_puppet(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "puppet restart"
        Args:
            node: system on which to perform checks
        Actions:
            1. Execute "puppet restart"
            2. Checked the error messages returned
        Results:
            Executing "puppet restart" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'puppet'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Stopping puppet agent: [FAILED]',
                        'Starting puppet agent:'],
                       ["rm: cannot remove `/var/run/puppet/agent.pid': "
                        "Permission denied"], 0]
        self.get_service_status(node, service)
        # RESTART PUPPET
        stdout, stderr, exit_code = self.run_command(
            node, self.restart_puppet, username='litp-admin')
        self.log('info', "Checking for pkill errors")
        self.grep_for_pkill(stderr, node)
        stderr = self.remove_strings(["pkill"], stderr)
        # Compare the output to what is expected
        output = [stdout, stderr, exit_code]
        self.check_for_expected(expect_list, output)
        self.get_service_status(node, service, assert_running=False)

    def perform_stop_mcollective(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "mcollective stop"
        Args:
            node: system on which to perform checks
        Actions:
            1. Execute "mcollective stop"
            2. Checked the error messages returned
        Results:
            Executing "mcollective stop" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'mcollective'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Shutting down mcollective: [FAILED]'],
                       ["rm: cannot remove `/var/run/mcollectived.pid':"
                        " Permission denied"], 1]
        self.get_service_status(node, service)
        # STOP mcollective
        stop_mcollective = '/sbin/service mcollective stop'
        self.log("info", "perform stop mcollective as litp-admin - expect "
                         "failure")
        output = self.run_command(node, stop_mcollective,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(node, service)

    def perform_start_mcollective(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "mcollective start"
        Args:
            node: system on which to perform checks
        Actions:
            1. Execute "mcollective start"
            2. Checked the error messages returned
        Results:
            Executing "mcollective start" using "litp-admin" user should throw
            a specific error messages.
        """
        service = 'mcollective'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Starting mcollective: [FAILED]'],
                       ["Permission denied"], 1]
        stop_mcollective = '/sbin/service mcollective stop'
        self.get_service_status(node, service)
        # STOP SERVICE as ROOT
        self.run_command(node, stop_mcollective, su_root=True)
        self.get_service_status(node, service, assert_running=False)

        # START mcollective
        self.log("info", "perform start mcollective as litp-admin - expect "
                         "failure")
        output = self.run_command(node, self.start_mcollective,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(node, service,
                                assert_running=False)

    def perform_restart_mcollective(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "mcollective restart"
        Args:
            node: system on which to perform checks
        Actions:
            1. Execute "mcollective restart"
            2. Checked the error messages returned
        Results:
            Executing "mcollective restart" using "litp-admin" user should
            throw a specific error messages.
        """
        service = 'mcollective'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Shutting down mcollective:'],
                       ["Permission denied"], 1]
        self.get_service_status(node, service, assert_running=False)
        # RESTART mcollective
        self.log("info", "perform restart mcollective as litp-admin - "
                         "expect failure")
        output = self.run_command(node, self.restart_mcollective,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(node, service, assert_running=False)
        # START SERVICE as ROOT
        self.run_command(node, self.start_mcollective, su_root=True)
        self.get_service_status(node, service)

    def perform_stop_rabbitmq(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "rabbitmq stop"
        Actions:
            1. Execute "rabbitmq stop"
            2. Checked the error messages returned
        Results:
            Executing "rabbitmq stop" using "litp-admin" user should
            throw a specific error messages.
        """
        service = 'rabbitmq-server'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Stopping rabbitmq-server: RabbitMQ is not running',
                         'rabbitmq-server.'], [], 0]
        self.get_service_status(self.ms_node, service, assert_running=False)
        self.log("info", "Perform stop rabbitmq-server as litp-admin"
                 "-expect failure")
        stop_cmd = "/sbin/service rabbitmq-server stop"
        output = self.run_command(self.ms_node, stop_cmd,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(self.ms_node, service, assert_running=False)

    def perform_start_rabbitmq(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "rabbitmq-server start"
        Actions:
            1. Execute "rabbitmq-server start"
            2. Checked the error messages returned
            3. Remove rabbitmq crash dump file if one is created
        Results:
            Executing "rabbitmq-server start" using "litp-admin" user should
            throw a specific error messages.
        """
        service = 'rabbitmq-server'
        stop_cmd = "/sbin/service {0} stop".format(service)
        start_cmd = "/sbin/service {0} start".format(service)
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Starting rabbitmq-server:'], ["Permission denied"], 1]

        self.get_service_status(self.ms_node, service, assert_running=False)
        # STOP SERVICE as ROOT
        self.run_command(self.ms_node, stop_cmd, su_root=True)
        self.get_service_status(self.ms_node, service, assert_running=False)
        self.log("info", "Perform start {0} as litp-admin"
                 "-expect failure".format(service))

        output = self.run_command(self.ms_node, start_cmd,
                                  username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)

        self.get_service_status(self.ms_node, service, assert_running=False)
        # START SERVICE as ROOT
        self.run_command(self.ms_node, start_cmd, su_root=True)
        self.get_service_status(self.ms_node, service)
        self.remove_rabbitmq_crash_file()

    def perform_restart_rabbitmq(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "rabbitmq-server restart"
        Actions:
            1. Execute "rabbitmq-server restart"
            2. Checked the error messages returned
            3. Remove rabbitmq crash dump file if one is created
        Results:
            Executing "rabbitmq-server start" using "litp-admin" user should
            throw a specific error messages.
        """
        service = 'rabbitmq-server'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [['Restarting rabbitmq-server: RabbitMQ is not running'],
                       ["Permission denied"], 1]
        self.get_service_status(self.ms_node, service, assert_running=False)
        self.log("info", "Perform restart rabbitmq-server as litp-admin"
                 "-expect failure")
        restart_cmd = "/sbin/service rabbitmq-server restart"
        output = self.run_command(self.ms_node, restart_cmd,
                                  username='litp-admin')
        # SLEEP UNTIL THE CRASH FILE IS CREATED
        self.wait_until_crash_dump_created()

        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(self.ms_node, service, assert_running=False)
        self.remove_rabbitmq_crash_file()

    def wait_until_crash_dump_created(self):
        """
        Description:
            Function to wait until the rabbit crash dump
            is created.
        """
        self.log('info', "Waiting for crash dump file to be created.")
        found = False
        counter = 10
        crash_file = "/var/lib/rabbitmq/erl_crash.dump"
        path = "/var/lib/rabbitmq/"
        while not found and counter > 0:
            dir_contents = \
            self.list_dir_contents(self.ms_node,
                                   path, su_root=True)
            if crash_file in dir_contents:
                found = True
            time.sleep(20)
            counter = counter - 1
        if found:
            self.log('info', "Crash dump file created.")
            self.wait_until_crash_dump_finished_writing()
        else:
            self.log('info', "Crash dump file not created.")

    def wait_until_crash_dump_finished_writing(self):
        """
        Description:
            Function to wait until the rabbit crash dump
            is finished being written to.
        """
        self.log('info',
                 "Waiting for writing to crash dump file to complete.")
        finished = False
        counter = 10
        crash_file = "erl_crash.dump"
        cmd = "/usr/sbin/lsof | grep {0}".format(crash_file)
        while not finished and counter > 0:
            _, _, exit_code = \
           self.run_command(self.ms_node, cmd, su_root=True)
            if exit_code != 0:
                finished = True
            time.sleep(20)
            counter = counter - 1
        if finished:
            self.log('info',
                     "Writing to crash dump file has completed.")
            ls_cmd = "/bin/ls -l /var/lib/rabbitmq/"
            output = self.run_command(self.ms_node, ls_cmd, su_root=True)
            self.log('info',
                     "Rabbitmq dir contents: {0}".format(output))
        else:
            self.log('info',
                     "Writing to crash dump file has not completed.")

    def perform_stop_vcs(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "vcs stop"
        Actions:
            1. Execute "vcs stop"
            2. Checked the error messages returned
        Results:
            Executing "vcs stop" using "litp-admin" user should
            throw a specific error messages.
        """
        service = "vcs"
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [["This script is not allowed to stop vcs. "
                        "VCS_STOP is not set to 1."], ["Permission denied"], 2]

        self.get_service_status(node, service, assert_running=False)
        self.log("info", "Perform stop {0} as litp-admin"
                 "-expect failure".format(service))
        stop_cmd = self.rhel.get_service_stop_cmd(service)
        output = self.run_command(node, stop_cmd, username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(node, service, assert_running=False)

    def perform_start_vcs(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "vcs start"
        Actions:
            1. Execute "vcs start"
            2. Checked the error messages returned
        Results:
            Executing "vcs start" using "litp-admin" user should
            throw a specific error messages.
        """
        service = 'vcs'
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [["This script is not allowed to start vcs. "
                        "VCS_START is not set to 1."],
                       ["Permission denied"], 2]
        start_cmd = self.rhel.get_service_start_cmd(service)

        self.get_service_status(node, service, assert_running=False)
        # STOP SERVICE as ROOT
        self.stop_service(node, service)
        self.get_service_status(node, service, assert_running=False)
        self.log("info", "Perform start {0} as litp-admin"
                 "-expect failure".format(service))

        output = self.run_command(node, start_cmd, username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)

        self.get_service_status(node, service, assert_running=False)
        # START SERVICE as ROOT
        self.start_service(node, service)
        self.get_service_status(node, service, assert_running=False)

    def perform_restart_vcs(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "vcs restart"
        Actions:
            1. Execute "vcs restart"
            2. Checked the error messages returned
        Results:
            Executing "vcs start" using "litp-admin" user should
            throw a specific error messages.
        """
        service = "vcs"
        # expect_list = [['string of expected stdout'],
        # ['string of expected stderr'], expected return code(int)]
        expect_list = [["This script is not allowed to stop vcs. "
                        "VCS_STOP is not set to 1."], ["Permission denied"], 2]

        self.get_service_status(node, service, assert_running=False)
        self.log("info", "Perform restart {0} as litp-admin"
                 "-expect failure".format(service))
        restart_cmd = self.rhel.get_service_restart_cmd(service)
        output = self.run_command(node, restart_cmd, username='litp-admin')
        # Compare the output to what is expected
        self.check_for_expected(expect_list, output)
        self.get_service_status(node, service, assert_running=False)

    def perform_stop_libvirtd(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "libvirtd stop"
        Actions:
            1. Execute "libvirtd stop"
            2. Checked the error messages returned
        Results:
            Executing "vcs stop" using "litp-admin" user should
            throw a specific error messages.
        """
        service = "libvirtd"
        expect_msg = "Stopping libvirtd daemon: [FAILED]"
        expect_err = "Permission denied"
        expect_rt = 1

        self.get_service_status(node, service, assert_running=False)
        self.log("info", "Perform stop {0} as litp-admin"
                 "-expect failure".format(service))
        stop_cmd = self.rhel.get_service_stop_cmd(service)
        stdout, stderr, exit_code = self.run_command(
                node, stop_cmd, username='litp-admin')
        self.assertTrue(expect_msg in stdout)
        self.assertTrue(expect_err in stderr[0])
        self.assertEqual(expect_rt, exit_code)
        self.get_service_status(node, service, assert_running=False)

    def perform_start_libvirtd(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "libvirtd start"
        Actions:
            1. Execute "libvirtd start"
            2. Checked the error messages returned
        Results:
            Executing "libvirtd start" using "litp-admin" user should
            throw a specific error messages.
        """
        service = 'libvirtd'
        expect_err = "libvirtd: error: Unable to obtain pidfile"
        expect_rt = 1
        start_cmd = self.rhel.get_service_start_cmd(service)

        self.get_service_status(node, service, assert_running=False)
        # STOP SERVICE as ROOT
        self.stop_service(node, service)
        self.get_service_status(node, service, assert_running=False)
        self.log("info", "Perform start {0} as litp-admin"
                 "-expect failure".format(service))

        _, stderr, exit_code = self.run_command(
                node, start_cmd, username='litp-admin')

        self.assertTrue(expect_err in stderr[0])
        self.assertEqual(expect_rt, exit_code)

        self.get_service_status(node, service, assert_running=False)
        # START SERVICE as ROOT
        self.start_service(node, service)
        self.get_service_status(node, service, assert_running=False)

    def perform_restart_libvirtd(self, node):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run "libvirtd restart"
        Actions:
            1. Execute "libvirtd restart"
            2. Checked the error messages returned
        Results:
            Executing "libvirtd start" using "litp-admin" user should
            throw a specific error messages.
        """
        service = "libvirtd"
        expect_msg = "Stopping libvirtd daemon: [FAILED]"
        expect_err = "Permission denied"

        self.get_service_status(node, service, assert_running=False)
        self.log("info", "Perform restart {0} as litp-admin"
                 "-expect failure".format(service))
        restart_cmd = self.rhel.get_service_restart_cmd(service)
        stdout, stderr, exit_code = self.run_command(
                node, restart_cmd, username='litp-admin')
        self.assertTrue(expect_msg in stdout)
        self.assertTrue(expect_err in stderr[0])
        self.assertEqual(1, exit_code)
        self.get_service_status(node, service, assert_running=False)

    def check_and_move_rabbitmq_crash_file(self):
        """
        Description:
            Method to check for a rabbitmq crash file before running rabbitmq
            checks. It will move any rabbitmq crash dump file to
            /tmp/erl_crash.dump
            Check LITPCDS-12972 (Won't Fix) for details.
        """

        # Name of the expected crash dump file
        crash_file = "/var/ -name erl_crash.dump"
        # Create command to find file
        find_cmd = self.rhel.get_find_cmd(crash_file)

        self.log("info", "Checking for rabbitmq crash dump file before "
                         "running rabbitmq checks")
        # The find command is run on the MS
        stdout = self.run_command(self.ms_node, find_cmd, su_root=True)

        # If the crash dump file is found
        if len(stdout[0]) > 0:
            # String of complete path to the crash dump file
            file_path = stdout[0][0]
            # List command that will output when the file is created
            self.list_dir_contents(self.ms_node, file_path, su_root=True)
            cat_cmd = self.rhel.get_cat_cmd(file_path)
            self.run_command(self.ms_node, cat_cmd, su_root=True)
            # Path to where the crash dump will be moved to
            new_path = "/tmp/erl_crash.dump"
            self.log("info", "Rabbitmq crash dump file found")
            self.log("info", "Path = '{0}'".format(file_path))
            self.log("info", "Moving crash dump file to {0}".format(new_path))
            # Move command used to move crash dump file
            move_cmd = self.rhel.get_move_cmd(file_path, new_path)
            self.run_command(self.ms_node, move_cmd, su_root=True)

        else:
            self.log("info", "No rabbitmq crash dump file found")

    def remove_rabbitmq_crash_file(self):
        """
         Description:
            Method to remove a rabbitmq crash file that maybe created when
            running service rabbitmq-server start and restart as non-root user.
            Check LITPCDS-12972 (Won't Fix) for details.
        """

        # Name of the expected crash dump file
        crash_file = "/var/ -name erl_crash.dump"
        # Create command to find file
        self.log("info", "Checking for rabbitmq crash dump file that may have "
                         "been created due to LITPCDS-12972")
        find_cmd = self.rhel.get_find_cmd(crash_file)

        # The find command is run on the MS
        stdout = self.run_command(self.ms_node, find_cmd, su_root=True)

        # If the crash dump file is found
        if len(stdout[0]) > 0:
            # String of complete path to the crash dump file
            file_path = stdout[0][0]
            # List command that will output when the file is created
            self.list_dir_contents(self.ms_node, file_path, su_root=True)
            cat_cmd = self.rhel.get_cat_cmd(file_path)
            self.run_command(self.ms_node, cat_cmd, su_root=True)
            self.log("info", "Rabbitmq crash dump file found")
            self.log("info", "Path = '{0}'".format(file_path))
            self.log("info", "Removing the rabbitmq crash dump file")
            # The remove command is run on the MS
            self.remove_item(self.ms_node, file_path, su_root=True)

        else:
            self.log("info", "No rabbitmq crash dump file found")

    def check_for_expected(self, expect_list, output):
        """
        Description:
            Method that checks the stdout, stderr and return code of service
            commands run as non-root user. If there is a difference from
            the expect_list is. The difference is added to a failure list.
        Args:
            expect_list: List of expected output. the list is made up as
                         follows: [['string of expected stdout'], ['string of
                         expected stderr], return code(int)]
            output:      The output from running the service command as a
                         non-root user. This contains [['string of stdout'],
                         ['string of stderr'], return code(int)]
        Actions:
            1. Check that stdout matches the expected output
            2. Check that stderr matches the expected output
            3. Check that the return code matches the expected return code
            4. Create a dictionary including the caller method and the failure
               list
            5. If there are failures in the method failure list, add the output
               dictionary to the test fail list
        """

        # Use inspect.stack to get the name of the calling method
        # [1][3] is the location of the string of the name of the required
        # calling method in the output of inspect.stack
        calling_method = inspect.stack()[1][3]

        # List of differences between expect_list and the actual output
        failure_list = []

        # 1. Check that stdout from output matches what is in expect_list
        for line in expect_list[0]:
            if line not in output[0]:
                message = "Expected line '{0}' is not present in  stdout " \
                          "'{1}' = Failure".format(line, output[0])
                self.log("info", message)
                # Adds the message to failure list if stdout does not match
                # expected
                failure_list.extend([message])
            else:
                self.log("info", "stdout matches what is expected")

        # 2. Check that stderr from output matches what is in expect_list
        for line in expect_list[1]:
            if line not in output[1][0]:
                message = "Expected error '{0}' is not present in stderr" \
                          " '{1}' = Failure".format(line, output[1])
                self.log("info", message)
                # Adds the message to failure list if stderr does not match
                # expected
                failure_list.extend([message])
            else:
                self.log("info", "stderr matches what is expected")

        # 3. Check that the return code matches the expected return code
        if output[2] != expect_list[2]:
            message = "Expected return code '{0}' is not present in stdout " \
                      "'{1}' = Failure".format(expect_list[2], output[2])
            self.log("info", message)
            # Adds the message to failure list if return code does not match
            # expected
            failure_list.extend([message])
        else:
            self.log("info", "Return code matches what is expected")

        # 4. Creates a dictionary including the caller method and the failure
        #    list
        failure_dict = {calling_method: failure_list}

        # 5. If there are failures in the method failure list, add the output
        #    dictionary to the test fail list
        if failure_list:
            self.log("info", "Adding {0} to failure list".format(failure_dict))
            self.fail_list.append(failure_dict)

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc02')
    def test_02_litp_admin_privs(self):
        """
        Description:
            Checks that litp-admin user does not have
            permissions to run commands on services on MS and 1 MN
            where service is running
        Actions:
            1. As litp-admin perform service start/stop/restart litpd
            2. As litp-admin perform service start/stop/restart network
            3. As litp-admin perform service start/stop/restart cobbler
            4. As litp-admin perform service start/stop/restart puppet
            5. As litp-admin perform service start/stop/restart mcollective
            6. If a rabbitmq crash dump file is created before the rabbitmq
               tests, it will be moved to /tmp/erl_crash.dump
            7. As litp-admin perform service start/stop/restart rabbitmq-server
            8. If a rabbitmq crash file is created during the rabbitmq tests,
               the crash file will be removed. See LITPCDS-12972 for details
            9. As litp-admin perform service start/stop/restart VCS
            10. As litp-admin perform service start/stop/restart libvirt
        Results:
            Executing service start/stop/restart using "litp-admin" user
            should throw a specific error messages.
        """
        node_to_check = []
        count = 0
        # Get all managed nodes in deployment
        targets = self.get_managed_node_filenames()
        # Add MS and one managed node to node_to_check list
        node_to_check.append(self.ms_node)
        node_to_check.append(targets[0])

        self.log("info", "Finding suitable peer node to run VCS and libvirt "
                         "checks")
        # For each managed node:
        for node in targets:
            self.log("info", "Checking if libvirt service is running on node "
                             "'{0}'".format(node))
            # Check the service status on the node
            libvirt_status = self.get_service_status(node, "libvirtd",
                                                     assert_running=False)
            # Node will be used for checks if libvirt service is running
            if libvirt_status[2] == 0:
                libvirt_node = node
                count += 1

        # Asserts that libvirt is running on at least 1 managed node
        self.assertTrue(count > 0, "libvirtd is not running on any of the "
                                   "managed nodes")
        self.log("info", "Node '{0}' will be used for VCS and libvirt service "
                         "checks".format(libvirt_node))
        self.perform_stop_litpd()
        self.perform_start_litpd()
        self.perform_restart_litpd()
        # Restart litpd again and turn on debug
        self.restart_litpd_service(self.ms_node, debug_on=True)
        self.get_service_status(self.ms_node, 'litpd')
        self.check_and_move_rabbitmq_crash_file()
        self.perform_stop_rabbitmq()
        self.perform_start_rabbitmq()
        self.perform_restart_rabbitmq()
        self.perform_stop_cobbler()
        self.perform_start_cobbler()
        self.perform_restart_cobbler()
        self.perform_stop_network()
        self.perform_start_network()
        self.perform_restart_network()
        self.perform_stop_vcs(libvirt_node)
        self.perform_start_vcs(libvirt_node)
        self.perform_restart_vcs(libvirt_node)

        # Libvirt checks removed until expected behavior is established
        # self.perform_stop_libvirtd(libvirt_node)
        # self.perform_start_libvirtd(libvirt_node)
        # self.perform_restart_libvirtd(libvirt_node)

        for node in node_to_check:
            find_pkill_service = self.perform_stop_puppet(node)
            self.perform_start_puppet(node)
            self.perform_restart_puppet(node)
            self.perform_stop_mcollective(node)
            self.perform_start_mcollective(node)
            self.perform_restart_mcollective(node)
            self.assertTrue(find_pkill_service,
                            "Error:Pkill operation not caused by puppet agent")
        # If any case has failed:
        if self.fail_list:
            self.log("info", "See list of failures below:")
            for item in self.fail_list:
                self.log("info", item)
        self.assertEqual(self.fail_list, [], "Check failure list above")
