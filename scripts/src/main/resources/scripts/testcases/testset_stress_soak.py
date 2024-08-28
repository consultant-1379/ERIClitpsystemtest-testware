#!/usr/bin/env python
'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@author:    TheMightyDucks
@summary: This set of tests automates the running of soak and stress tests
'''

from litp_generic_test import GenericTest, attr
import test_constants
import os


class SoakStress(GenericTest):
    """
    Description:
        This set of tests measures the time taken for various tasks
    """
    def setUp(self):
        super(SoakStress, self).setUp()

        self.ms_node = self.get_management_node_filename()
        self.targets = self.get_managed_node_filenames()
        self.local_folder = os.path.dirname(os.path.abspath(__file__))

    def tearDown(self):
        pass

    def add_cron(self, cmd_cron):
        """
        Description:
            Checks if a cron already exists, and if not, creates it.
        Args:
            cmd_cron (str): The cron to add
        """
        # Check if cron already exists
        stdout, _, _ = self.run_command(self.ms_node,
                                    "cat /var/spool/cron/root", su_root=True)
        if not cmd_cron in stdout:
            stdout, _, _ = self.run_command(self.ms_node,
                'echo "{0}" | tee -a /var/spool/cron/root'.format(cmd_cron),
                su_root=True)

    def start_state_backup(self):
        """
        Description:
            Starts litp_state_backup.sh in a cron
        """
        cmd_cron = "* * * * * /opt/ericsson/nms/litp/bin/litp_state_backup.sh \
/tmp/test_backup"
        self.create_dir_on_node(self.ms_node, "/tmp/test_backup",
                                add_to_cleanup=False)
        self.add_cron(cmd_cron)

    def assert_plan_completion(self):
        """
        Description:
            Waits for running plan to complete, and asserts its success
        """
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                    test_constants.PLAN_COMPLETE)
        self.assertTrue(completed_successfully,
                        "Plan didn't finish successfully in given time")

    def remove_every_snapshot(self):
        """
        Description:
            Finds all snapshots and deletes them
        """
        snapshot_paths = self.find(self.ms_node, "/snapshots/",
            "snapshot-base", assert_not_empty=False)
        for snapshot_path in snapshot_paths:
            self.execute_cli_removesnapshot_cmd(self.ms_node,
                                add_to_cleanup=False,
                                args='--name {0}'.format(snapshot_path[11:]))
            self.assert_plan_completion()

    def start_capture_info(self):
        """
        Description:
            Starts the capture info cron after getting the litpd pid and
            transferring the script the to MS
        """
        # Get litpd pid
        stdout, _, _ = self.get_service_status_cmd(self.ms_node, "litpd")
        litpd_pid = self.get_service_pid_from_stdout(stdout, "litpd")
        script_location = self.local_folder + "/RESOURCE_UTILISATION/"
        script = "capture_info.sh"

        cmd_cron = "*/15 * * * * /root/capture_info.sh " + litpd_pid

        self.log("info", "Copy capture_info.sh to MS")
        copied = self.copy_file_to(self.ms_node,
            script_location + script,
            "/root", root_copy=True, add_to_cleanup=False,
            file_permissions=777)
        self.assertTrue(copied, "File copy failed")

        self.log("info", "Add capture_info cron")
        self.add_cron(cmd_cron)

    @attr('all', 'non-revert', 'stress_soak_start', 'stress_soak_start_01')
    def test_01_plan_soak_start(self):
        """
        Description:
            Starts the plan soak. For more details see:
            ERIClitpsystemtest-testware/scripts/src/main/resources/scripts/
                testcases/SOAK/plan_soak/README
        Actions:
            1. Ensure a snapshot does not exist on the system before running
            2. Start state backup
            3. Import dummy plugin
            4. Copy plan soak script to MS
            5. Start plan soak script
            6. Start capture info script
        Results:
            1. Plan soak is started, to be checked by other means at a later
            time
        """
        script_location = self.local_folder + "/SOAK/plan_soak/"
        script = "repeat.plan.multiple.tasks.update.sh"
        script_run_cmd = "cd /root/; nohup /root/{0} &".format(script)
        dummy_rpm = "/tmp/ERIClitpmassive_phase_CXP1234567-1.0.1-" + \
                    "SNAPSHOT20170118111648.noarch.rpm"

        self.log("info", "1. Ensure no snapshot exists")
        self.remove_every_snapshot()

        self.log("info", "2. Start state backup")
        self.start_state_backup()

        self.log("info", "3. Install dummy plugin")
        self.execute_cli_import_cmd(self.ms_node, dummy_rpm, "litp")
        self.install_rpm_on_node(self.ms_node, dummy_rpm)
        # Re-enable debugging after restart caused by install
        self.turn_on_litp_debug(self.ms_node)

        self.log("info", "4. Copy plan soak script to MS")
        copied = self.copy_file_to(self.ms_node,
            script_location + script, "/root",
             root_copy=True, add_to_cleanup=False, file_permissions=777)
        self.assertTrue(copied, "File copy failed")

        self.log("info", "5. Start plan soak script")
        self.run_command(self.ms_node,
            script_run_cmd,
            add_to_cleanup=False, su_root=True, default_asserts=True)

        self.log("info", "6. Start capture info script")
        self.start_capture_info()

    @attr('all', 'non-revert', 'stress_soak_start', 'stress_soak_start_02')
    def test_02_rest_soak_start(self):
        """
        Description:
            Starts the rest soak. For more details see:
            ERIClitpsystemtest-testware/scripts/src/main/resources/scripts/
                testcases/SOAK/REST/README
            Actions:
            1. Start state backup
            2. Show SGs before job is run
            3. Ensure snap_size is sufficient.
            4. Copy rest soak script to MS
            5. Start rest soak script
            6. Start capture info script
        Results:
            1. Rest soak is started, to be checked by other means at a later
            time
        """
        script_location = self.local_folder + "/SOAK/REST/"
        script = "rest_soak.sh"
        script_run_cmd = "nohup /root/rest_soak.sh > \
/tmp/rest_soak.out 2>&1&".format(script)

        self.log("info", "1. Start state backup")
        self.start_state_backup()

        self.log("info", "2. Show SGs before job is run")
        self.run_vcs_hastatus_sum_command(self.targets[0])

        self.log("info", "3. Ensure snap_size is sufficient")
        # Remove existing snapshots
        self.remove_every_snapshot()

        # Make deployment snapshot
        self.execute_cli_createsnapshot_cmd(self.ms_node,
            add_to_cleanup=False)
        self.assert_plan_completion()

        # Make named snapshot
        self.execute_cli_createsnapshot_cmd(self.ms_node, args='--name X',
                                                add_to_cleanup=False)
        self.assert_plan_completion()

        self.log("info", "4. Copy rest soak script to MS")
        copied = self.copy_file_to(self.ms_node,
            script_location + script, "/root",
             root_copy=True, add_to_cleanup=False, file_permissions=777)
        self.assertTrue(copied, "File copy failed")

        self.log("info", "5. Start rest soak script")
        self.run_command(self.ms_node,
            script_run_cmd,
            add_to_cleanup=False, su_root=True, default_asserts=True)

        self.log("info", "6. Start capture info script")
        self.start_capture_info()
