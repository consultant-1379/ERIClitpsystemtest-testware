#!/usr/bin/env python

"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     August 2016
@author:    LITP System Test (Messers)
@summary:   System Test of Performance KPIs
@change:
"""

from litp_generic_test \
     import GenericTest, CLIUtils, RHCmdUtils, attr, test_constants
from datetime import datetime
import os


class PerformanceKPIs(GenericTest):
    """
    Description:
        Measure the performance of the LITP Key Operations.
    """

    def setUp(self):
        """Run before every test"""
        super(PerformanceKPIs, self).setUp()

        self.rhcmd = RHCmdUtils()
        self.litpcli = CLIUtils()
        # define the nodes which will be checked
        self.ms_node = self.get_management_node_filename()
        self.ms_kpi_dir = "/tmp/kpi/"
        self.local_kpi_dir = os.path.dirname(__file__)

    def tearDown(self):
        """Run after every test"""
        super(PerformanceKPIs, self).tearDown()

    def check_messages_log(self, search_list):
        """
        Function to grep the messages log for a list of strings.

        Args:
           search_list(list): List of strings to be used in the grep.

        Returns:
           stdout(list) : List of strings returned from grep command.
        """

        # format the grep command
        search_list_grep = self.rhcmd.get_grep_file_cmd(
                 test_constants.GEN_SYSTEM_LOG_PATH, search_list)

        # perform the grep on the ms
        stdout, _, _ = self.run_command(
                self.ms_node, search_list_grep, default_asserts=True)

        return stdout

    @staticmethod
    def return_duration_from_log(logentry):
        """
        Function to return the duration from a log message which specifies
        the time taken to perform a certain action in seconds.

        Args:
           logentry(str): log message.

        Returns:
           logtime(float): time extracted from the log message.
        """

        # convert the string contents to a list
        entrylist = logentry.split()
        # get the position of the time in the log
        time_pos = entrylist.index("seconds")
        # get the time taken
        logtime = float(entrylist[time_pos - 1])
        # return the time entry
        return logtime

    @attr('all', 'non-revert', 'pm_kpi', 'kpi_tc01')
    def test_01_measure_restore_snapshot_operation(self):
        """
        Description:
            Measure the duration of the restore_snapshot operation.
        Actions:
            - Perform restore snapshot.
        Result:
            Output the time taken.
        """

        # Set the input parameters needed
        # Time format to be used in time calculation
        timeformat = "%H:%M:%S"

        # System should have a deployment snapshot after installation
        # Ensure that the snapshot exists
        self.log('info', "ensure that there is a snapshot on the system")
        check_snap = self.litpcli.get_show_cmd("/snapshots/snapshot")
        self.run_command(self.ms_node, check_snap, add_to_cleanup=False,
            default_asserts=True)

        # Perform restore snapshot
        self.log('info', "perform restore_snapshot")
        restore_snap = self.litpcli.get_restore_snapshot_cmd()

        # Add date before restore snapshot command
        restore_snap = "/bin/date ;" + restore_snap
        cmd_output = self.run_command(self.ms_node, restore_snap,
            add_to_cleanup=False, default_asserts=True)

        # Get the start time
        date = cmd_output[0][0]

        # convert the string contents to a list
        datelst = date.split()

        # Get the position of the timestamp
        # Cater for GMT vs IST.
        try:
            time_pos = datelst.index("GMT")
        except ValueError:
            time_pos = datelst.index("IST")

        # get the start time
        start_time = datelst[time_pos - 1]

        self.log('info', "Starting Time : {0}".format(start_time))

        # Wait for restore snapshot to finish
        self.execute_and_wait_restore_snapshot(self.ms_node, skip_cmd=True)

        # Log when finished
        self.log('info', "Restore Snapshot operation has completed")

        # Now check status of LITP, if running grab date.
        running = False
        while not running:
            stdout, _, _ = \
            self.get_service_status(self.ms_node, 'litpd',
                                    assert_running=False)
            if 'is running' in stdout[0]:
                running = True
        stdout, _, _ = \
        self.run_command(self.ms_node, '/bin/date', add_to_cleanup=False,
                         su_root=True)
        self.log('info', "Service is running at {0} : ".format(stdout[0]))

        # Extract the timestamp from the log
        end_time = stdout[0].split()
        end_time = end_time[3]

        self.log('info', "End Time : {0}".format(end_time))

        # Format the times
        end_time = datetime.strptime(end_time, timeformat)
        start_time = datetime.strptime(start_time, timeformat)

        # Determine the time taken to perform the restore snapshot
        duration = end_time - start_time
        self.log('info',
               "Time taken to perform restore snapshot : {0}".format(duration))

    @attr('all', 'non-revert', 'pm_kpi', 'kpi_tc02')
    def test_02_measure_key_litp_operations(self):
        """
        Description:
            Measure the LITP performance KPIs.

        Actions:
            - Copy KPI bash scripts to the MS.
            - Execute the run_kpi bash script.

        Result:
            Output the result of KPI scripts.
        """

        # Scripts to be copied to MS
        kpi_scripts = ["/import.sh",
                       "/litpd_restart.sh",
                       "/prepare_restore.sh",
                       "/xml.sh",
                       "/run_kpi.sh",
                       "/snapshot.sh"]

        # Generate a list of dictionaries holding the source
        # and target file paths for the scripts
        sh_list = []
        for script in kpi_scripts:

            path_dict = self.get_filelist_dict(self.local_kpi_dir + script,
                             self.ms_kpi_dir)
            sh_list.append(path_dict)

        self.log('info', "dictionary of file paths is : {0}".format(sh_list))

        # Copy the scripts to the MS KPI directory
        self.copy_filelist_to(self.ms_node, sh_list, root_copy=True,
                 add_to_cleanup=False)

        # Execute the run kpi script on the MS
        get_kpi = "/bin/sh /tmp/kpi/run_kpi.sh"
        self.run_command(self.ms_node, get_kpi, add_to_cleanup=False,
            su_root=True, su_timeout_secs=14000)

    @attr('all', 'non-revert', 'pm_kpi', 'kpi_tc03')
    def test_03_measure_feedback_processing_time(self):
        """
        Description:
            Measure the puppet feedback processing time.
        Actions:
            - Search messages for feedback processing time.
        Result:
            Pass if the processing time is below the threshold.
        """

        # Set the limit for feedback processing time
        proctime_limit = 60.00
        # Initialise a list for the failures
        failing_list = []

        # Define the string to find feedback processing time
        feedback_search = ["Feedback processed"]
        # Search messages log for this string
        results = self.check_messages_log(feedback_search)

        # Assert if messages does not contain any entries
        # for feedback processing time
        self.assertNotEqual(results, [],
                    "messages has no feedback processing logs")

        # Check for any processing time over the limit
        for entry in results:
            # Get the time entry in the log
            proctime = self.return_duration_from_log(entry)

            # Check if the feedback processing time is greater than the limit
            if proctime > proctime_limit:
                # Append to the failure list
                failing_list.append(entry)
                self.log('warning',
                         "Feedback processing time above threshold of {0}: {1}"
                         .format(int(proctime_limit), entry))
        # Assert that there are no failure entries
        self.assertTrue(len(failing_list) == 0,
                  "Feedback processing times are greater than expected")

    @attr('all', 'non-revert', 'pm_kpi', 'kpi_tc04')
    def test_04_measure_puppet_compilation_time(self):
        """
        Description:
            Measure the puppet catalog compilation time.
        Actions:
            - Search messages for catalog compilation time.
        Result:
            Pass if the compilation time is below the threshold.
        """

        # Set compile time limit
        comptime_limit = 90.00
        # Initialise a list for the failures
        failing_list = []

        # Define the string to find puppet compilation time
        compile_search = ["Compiled catalog"]
        # Search messages log for this string
        results = self.check_messages_log(compile_search)

        # Assert if messages does not contain any entries
        # for catalog compilation time
        self.assertNotEqual(results, [],
                   "messages has no catalog compilation logs")

        # Check for any compilation time over the limit
        for entry in results:
            # Get the time entry in the log
            comptime = self.return_duration_from_log(entry)

            # Check if the compile time is greater than the limit
            if comptime > comptime_limit:
                # Append to the failure list
                failing_list.append(entry)
                self.log('warning',
                         "Catalog compile time above threshold of {0} : {1}"
                         .format(int(comptime_limit), entry))
        # Assert that there are no failure entries
        self.assertTrue(len(failing_list) == 0,
                  "Catalog compile times are greater than expected")
