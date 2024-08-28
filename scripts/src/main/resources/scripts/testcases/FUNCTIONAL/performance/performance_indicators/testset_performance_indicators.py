#!/usr/bin/env python
'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@author:    TheMightyDucks
@summary:This set of tests measures the time taken for various tasks
'''

from litp_generic_test import GenericTest, attr
import test_constants
import time
import os
import re


class PerformanceIndicators(GenericTest):
    """
    Description:
        This set of tests measures the time taken for various tasks
    """
    def setUp(self):
        super(PerformanceIndicators, self).setUp()

        self.ms_node = self.get_management_node_filename()
        self.targets = self.get_managed_node_filenames()

    def tearDown(self):
        super(PerformanceIndicators, self).tearDown()

    @staticmethod
    def regex_item_between(before_match, after_match, contents):
        """
        Description:
            Returns first match which sits between the two specified strings

        Args:
            before_match (str): pattern before the match
            after_match (str): pattern after the match
            contents (str): string to search through

        Returns:
            str. The first match which sits between the two specified strings
        """
        return re.findall('(?<={0})(.*)(?={1})'.format(before_match,
                                                 after_match), contents)[0]

    def parsetime(self, stdout):
        """
        Description:
            Parses stdout of the time command to get the real time passed

        Args:
            stdout (list): stdout of the time command

        Returns:
            float. Time real time taken by command in seconds
        """
        minutes = float(self.regex_item_between("real\t", "m", stdout[-3]))
        seconds = float(self.regex_item_between("m", "s", stdout[-3]))
        elapsed_time = 60 * minutes + seconds

        return elapsed_time

    def average_time(self, cmd, num_measurements=10):
        """
        Description:
            Runs a command on the MS repeatedly and calculates the average
            time it takes

        Args:
            cmd (str): The command to run
            num_measurements (int): How many times to repeat the measurement

        Returns:
            float. Average time taken by command in seconds
        """
        time_cmd = "time " + cmd
        total_time = 0
        for _ in range(num_measurements):
            stdout, _, rc = self.run_expects_command(self.ms_node, time_cmd,
                                                     [], timeout_secs=600)
            self.assertEqual(rc, 0,
                             'Return code of {0} was unexpected'.format(rc))
            self.assertNotEqual(stdout, [],
                                'stdout was not expected to be empty')

            total_time += self.parsetime(stdout)

        average = total_time / num_measurements

        if num_measurements > 1:
            self.log("info",
                     "Average '{0}' command took {1}s".format(cmd, average))
        else:
            self.log("info", "'{0}' command took {1}s".format(cmd, average))
        return average

    def download_files(self):
        """
        Description:
            Downloads to the MS the files needed by .68 to run pre install
            script
        """
        cmds = []
        cmds.append("wget http://10.44.235.150/cdb/\
vm_test_image-1-1.0.3.qcow2 -O /var/www/html/images/vm_image_rhel7.qcow2")
        cmds.append("wget http://10.44.235.150/st/test-packages/\
test_service-1.0-1.noarch.rpm -O /tmp/test_service-1.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/test-packages/\
test_service-2.0-1.noarch.rpm -O /tmp/test_service-2.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/test-packages/\
EXTR-lsbwrapper1-2.0.0.rpm -O /tmp/lsb_pkg/EXTR-lsbwrapper1-2.0.0.rpm")
        cmds.append("wget http://10.44.235.150/st/test-packages/\
EXTR-lsbwrapper2-2.0.0.rpm -O /tmp/lsb_pkg/EXTR-lsbwrapper2-2.0.0.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-german-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pkgApps/3PP-german-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-czech-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pkgApps/3PP-czech-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-dutch-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pkgApps/3PP-dutch-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-english-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pkgApps/3PP-english-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-french-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pkgApps/3PP-french-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-italian-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pckglist1/3PP-italian-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-klingon-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pckglist1/3PP-klingon-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-polish-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pckglist1/3PP-polish-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-portuguese-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pckglist1/3PP-portuguese-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-portuguese-hungarian-slovak-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/\
pckglist2/3PP-portuguese-hungarian-slovak-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-romanian-hello-1.0.0-1.noarch.rpm -O /var/www/html/\
pckglist2/3PP-romanian-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-russian-hello-1.0.0-1.noarch.rpm -O /var/www/html/\
pckglist2/3PP-russian-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-serbian-hello-1.0.0-1.noarch.rpm -O /var/www/html/\
pckglist2/3PP-serbian-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-spanish-hello-1.0.0-1.noarch.rpm -O /var/www/html/\
pckglist3/3PP-spanish-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-swedish-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pckglist3/3PP-swedish-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-finnish-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pckglist3/3PP-finnish-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/\
example_apps/3PP-irish-hello-1.0.0-1.noarch.rpm -O \
/var/www/html/pckglist3/3PP-irish-hello-1.0.0-1.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/test-plugins/\
ERIClitptag_CXP1234567-1.0.1-SNAPSHOT20151014152125.noarch.rpm -O \
/tmp/ERIClitptag_CXP1234567-1.0.1-SNAPSHOT20151014152125.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/test-plugins/\
ERIClitptagapi_CXP1234567-1.0.1-SNAPSHOT20160205115231.noarch.rpm -O \
/tmp/ERIClitptagapi_CXP1234567-1.0.1-SNAPSHOT20160205115231.noarch.rpm")
        cmds.append("wget http://10.44.235.150/st/test-plugins/\
root_yum_install_pkg.exp -O /tmp/root_yum_install_pkg.exp")
        cmds.append("wget http://10.44.235.150/st/test-packages/\
diff_name_srvc/test_service_name-2.0-1.noarch.rpm -O \
/tmp/test_service_name-2.0-1.noarch.rpm")

        cmds.append("wget http://10.44.235.150/st/enm-iso/enm_package_2.xml\
 -O /tmp/enm_package_2.xml")
        cmds.append("wget http://10.44.235.150/st/enm-iso/import_iso.sh -O \
/tmp/import_iso.sh")
        cmds.append("wget http://10.44.235.150/st/enm-iso/\
root_import_iso.exp -O /tmp/root_import_iso.exp")

        #Copy ENM ISO
        cmds.append("wget http://10.44.235.150/st/enm-iso/\
ERICenm_CXP9027091-1.63.96.iso -O /tmp/ERICenm_CXP9027091-1.63.96.iso")

        for cmd in cmds:
            self.run_command(self.ms_node, cmd, su_root=True,
                             su_timeout_secs=600, add_to_cleanup=False,
                             default_asserts=True)

    def wait_for_import_to_complete(self):
        """
        Description:
            Waits until import_iso completes
              ie until litp leaves maintenance mode
        """
        self.log("info", "Entering wait_for_import_to_complete")

        timeout_seconds = 7200
        start_time = time.time()

        maintenance_status = self.get_props_from_url(self.ms_node,
                                    "/litp/maintenance", filter_prop='status')
        while maintenance_status != 'Done':
            # Check for timeout
            elapsed_time = time.time() - start_time
            timeout = (elapsed_time > timeout_seconds)
            self.assertFalse(timeout,
                    "Import timed out after {0} seconds".format(elapsed_time))

            time.sleep(30)

            # Recheck maintenance status
            maintenance_status = self.get_props_from_url(self.ms_node,
                                    "/litp/maintenance", filter_prop='status')

        elapsed_time = time.time() - start_time
        self.log("info", "Exiting wait_for_import_to_complete after "
                         "{0} seconds".format(elapsed_time))

    @staticmethod
    def save_result(value):
        """
        Description:
            Writes a result to the results file. Doesn't print labels,
            intended as a convenience for when all tests are run so they can
            be copied to a spreadsheet easily
        """
        with file("performance_results.txt", "a") as results_file:
            results_file.write(str(value) + "\n")

    @attr('all', 'non-revert', 'lppi', 'lppi_install', 'lppi_00')
    def test_00_pre_install_preparation(self):
        """
        Description:
            Performs pre install actions required by .68. Not really a test,
            but required so that install via XML load can succeed.
        Actions:
            1. Transfers pre xml script and clusterfile to MS
            2. Download required files for install
            3. Run pre install script
        Results:
            1. Pre install actions are completed
        """
        local_folder = os.path.dirname(os.path.abspath(__file__))
        pre_xml_load_script = "ST_Deployment_18_pre_xml.sh"
        cluster_file = "10.44.235.68.sh"

        self.copy_file_to(self.ms_node, local_folder + "/"
                          + pre_xml_load_script, "/tmp/", root_copy=True)
        self.copy_file_to(self.ms_node, local_folder + "/" + cluster_file,
                          "/tmp/", root_copy=True)

        # Create folders for download
        self.create_dir_on_node(self.ms_node, "/var/www/html/images/",
                                add_to_cleanup=False, su_root=True)
        self.create_dir_on_node(self.ms_node, "/tmp/lsb_pkg/",
                                add_to_cleanup=False, su_root=True)
        self.create_dir_on_node(self.ms_node, "/var/www/html/pkgApps/",
                                add_to_cleanup=False, su_root=True)
        self.create_dir_on_node(self.ms_node, "/var/www/html/pckglist1/",
                                add_to_cleanup=False, su_root=True)
        self.create_dir_on_node(self.ms_node, "/var/www/html/pckglist2/",
                                add_to_cleanup=False, su_root=True)
        self.create_dir_on_node(self.ms_node, "/var/www/html/pckglist3/",
                                add_to_cleanup=False, su_root=True)

        self.download_files()

        cmd = "sh /tmp/{0} /tmp/{1}".format(pre_xml_load_script, cluster_file)
        stdout, _, rc = self.run_command(self.ms_node, cmd, su_root=True,
                                         su_timeout_secs=1800)
        self.assertEqual(rc, 0, 'Return code of {0} was unexpected'.format(rc))
        self.assertNotEqual(stdout, [], 'stdout was not expected to be empty')

    @attr('all', 'non-revert', 'lppi', 'lppi_install', 'lppi_01')
    def test_01_measure_xml_load_replace(self):
        """
        Description:
            Runs litp load replace command and records the time it takes
        Actions:
            1. Copy XML file to MS
            2. Run load replace command
        Results:
            1. Time taken is recorded
        """
        local_folder = os.path.dirname(os.path.abspath(__file__))
        install_xml = "ST_Deployment_18_scale_120fs.xml"

        self.copy_file_to(self.ms_node, local_folder + "/" + install_xml,
                          "/tmp/", root_copy=True)

        cmd = self.cli.get_xml_load_cmd("/", "/tmp/" + install_xml,
                                        args="--replace")
        elapsed_time = self.average_time(cmd, num_measurements=1)
        self.log("info", "Time for '{0}': {1}s".format(cmd, elapsed_time))

        self.save_result(elapsed_time)

    @attr('all', 'non-revert', 'lppi', 'lppi_install', 'lppi_02')
    def test_02_measure_create_plan(self):
        """
        Description:
            Runs 'litp create_plan' repeatedly and calculates the average time
            it takes
        Actions:
            1. Run litp create_plan repeatedly
        Results:
            1. Average time taken is recorded
        """
        cmd = self.cli.get_create_plan_cmd()
        elapsed_time = self.average_time(cmd)
        self.log("info", "Time for 'litp create_plan': {0}s"
                            "".format(elapsed_time))

        self.save_result(elapsed_time)

    @attr('all', 'non-revert', 'lppi', 'lppi_install', 'lppi_03')
    def test_03_measure_show_plan_initial(self):
        """
        Description:
            Runs 'litp show_plan' repeatedly and calculates the average time it
            takes. This test is intended to be run before deployment
        Actions:
            1. Run litp show_plan repeatedly
        Results:
            1. Average time taken is recorded
        """
        cmd = self.cli.get_show_plan_cmd()
        elapsed_time = self.average_time(cmd)
        self.log("info", "Time for 'litp show_plan' in initial state: {0}s"
                            "".format(elapsed_time))

        self.save_result(elapsed_time)

    @attr('all', 'non-revert', 'lppi', 'lppi_install', 'lppi_04')
    def test_04_measure_show_p_plans_plan_initial(self):
        """
        Description:
            Runs 'litp show -p /plans/plan' repeatedly and calculates the
            average time it takes. This test is intended to be run before
            deployment
        Actions:
            1. Run show_plan repeatedly
        Results:
            1. Average time taken is recorded
        """
        cmd = self.cli.get_show_cmd("/plans/plan")
        elapsed_time = self.average_time(cmd)
        self.log("info",
            "Time for 'litp show -p /plans/plan' in initial state: {0}s"
                "".format(elapsed_time))

        self.save_result(elapsed_time)

    @attr('all', 'non-revert', 'lppi', 'lppi_install', 'lppi_05')
    def test_05_measure_model_items(self):
        """
        Description:
            Counts the number of items in the model
        Actions:
            1. Count the number of items in the model
            2. Assert it is the expected number
        Results:
            1. the number of items in the model is recorded
        """
        num_expected_items = 7085

        cmd = 'time (litp show -p / -rl | wc -l)'
        stdout, _, rc = self.run_expects_command(self.ms_node, cmd, [],
                                                 timeout_secs=3600)
        self.assertEqual(rc, 0, 'Return code of {0} was unexpected'.format(rc))
        self.assertNotEqual(stdout, [], 'stdout was not expected to be empty')

        num_items = int(stdout[0])

        self.log("info", "Number of items in model: {0}".format(num_items))
        self.assertEqual(num_items, num_expected_items,
            'Expected {0} items in model, {1} were found'.format(
                num_expected_items, num_items))

        self.save_result(num_items)

    @attr('all', 'non-revert', 'lppi', 'lppi_install', 'lppi_06')
    def test_06_measure_plan_tasks(self):
        """
        Description:
            Counts the number of tasks in the plan
        Actions:
            1. Count the number of tasks in the plan
            2. Assert it is the expected number
        Results:
            1. The number of tasks in the plan is recorded
        """
        num_expected_tasks = 2208

        cmd = self.cli.get_show_plan_cmd(args='-a')
        stdout, _, rc = self.run_expects_command(self.ms_node, cmd, [],
                                                 timeout_secs=600)
        self.assertEqual(rc, 0, 'Return code of {0} was unexpected'.format(rc))
        self.assertNotEqual(stdout, [], 'stdout was not expected to be empty')

        num_tasks = int(self.regex_item_between("Tasks: ", r" \| Initial",
                                                stdout[0]))

        self.log("info", "Number of tasks in plan: {0}".format(num_tasks))
        self.assertEqual(num_tasks, num_expected_tasks,
            'Expected {0} tasks in plan, {1} were found'.format(
                num_expected_tasks, num_tasks))

        self.save_result(num_tasks)

    @attr('all', 'non-revert', 'lppi', 'lppi_install', 'lppi_07')
    def test_07_measure_run_plan(self):
        """
        Description:
            Run plan and record the time taken
        Actions:
            1. Record time before run plan
            2. Run plan and wait for completion
            3. Record time since plan start
        Results:
            1. Time taken is recorded
        """
        # Record time of start
        start_time = time.time()

        # Run Plan
        self.execute_cli_runplan_cmd(self.ms_node, add_to_cleanup=False)

        # Wait for plan
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                        test_constants.PLAN_COMPLETE,
                                        timeout_mins=300,
                                        seconds_increment=30,
                                        full_show=False)

        # Record time since plan start
        elapsed_time = time.time() - start_time

        # Show plan regardless of plan success or failure
        cmd = self.cli.get_show_plan_cmd()
        self.run_expects_command(self.ms_node, cmd, [], timeout_secs=600)

        # Assert earlier wait_for_plan_state success
        self.assertTrue(completed_successfully,
                        "Plan didn't finish successfully in given time")

        self.log("info",
            "Time for 'litp run_plan' to complete deployment: {0}s".format(
                elapsed_time))

        self.save_result(elapsed_time)

    @attr('all', 'non-revert', 'lppi', 'lppi_install', 'lppi_08')
    def test_08_measure_show_plan_successful(self):
        """
        Description:
            Runs 'litp show_plan' repeatedly and calculates the average time it
            takes. This test is intended to be run after deployment
        Actions:
            1. Run litp show_plan repeatedly
        Results:
            1. Average time taken is recorded
        """
        cmd = self.cli.get_show_plan_cmd()
        elapsed_time = self.average_time(cmd)
        self.log("info", "Time for 'litp show_plan' in successful state: {0}s"
                            "".format(elapsed_time))

        self.save_result(elapsed_time)

    @attr('all', 'non-revert', 'lppi', 'lppi_install', 'lppi_09')
    def test_09_measure_show_p_plans_plan_successful(self):
        """
        Description:
            Runs 'litp show -p /plans/plan' repeatedly and calculates the
            average time it takes. This test is intended to be run before
            deployment
        Actions:
            1. Run show_plan repeatedly
        Results:
            1. Average time taken is recorded
        """
        cmd = self.cli.get_show_cmd("/plans/plan")
        elapsed_time = self.average_time(cmd)
        self.log("info",
            "Time for 'litp show -p /plans/plan' in successful state: {0}s"
                "".format(elapsed_time))

        self.save_result(elapsed_time)

    @attr('all', 'non-revert', 'lppi', 'lppi_upgrade', 'lppi_10')
    def test_10_measure_upgrade_plan(self):
        """
        Description:
            Creates and runs upgrade plan and records the time taken
            Upgrade ISO must be linked to this location on .30:
              /ST/link-to-upgrade.iso
        Actions:
            1. Download upgrade iso
            2. Mount and import upgrade iso
            3. Run upgrade command
            4. Create upgrade plan
            5. Record time before run plan
            6. Run plan and wait for completion
            7. Record time since plan start
        Results:
            1. Time taken is recorded
        """
        # Show version to be upgraded to
        # Disabled because .14 is not set up to calculate this
        # cmd = "curl http://10.44.86.30/st/link-to-upgrade_version.txt"
        # stdout, _, _ = self.run_command(self.ms_node, cmd)
        # self.log("info", "Upgrading to litp version " + stdout[0])

        # Remove any existing ISOs to prevent disk filling
        cmd = "rm -rf /tmp/*.iso"
        self.run_command(self.ms_node, cmd, su_root=True, default_asserts=True)

        # Download upgrade iso
        cmd = "wget http://10.44.235.150/st/link-to-upgrade.iso \
               -O /tmp/upgrade.iso"
        self.run_command(self.ms_node, cmd, su_root=True,
                         su_timeout_secs=600, add_to_cleanup=False,
                         default_asserts=True)

        # Mount iso
        cmd = "mount -o loop /tmp/upgrade.iso /mnt"
        self.run_command(self.ms_node, cmd, su_root=True, default_asserts=True)

        # Import_iso
        cmd = "litp import_iso /mnt"
        self.run_command(self.ms_node, cmd, su_root=True, default_asserts=True)

        # Wait for litp to leave maintenance mode
        self.wait_for_import_to_complete()

        # Unmount iso
        cmd = "umount /mnt"
        self.run_command(self.ms_node, cmd, su_root=True, default_asserts=True)

        # Run upgrade command
        cmd = "litp upgrade -p /deployments/d1/"
        self.run_command(self.ms_node, cmd, su_root=True, default_asserts=True)

        # Create plan
        cmd = self.cli.get_create_plan_cmd()
        self.run_expects_command(self.ms_node, cmd, [], timeout_secs=600)

        # Record time of start
        start_time = time.time()

        # Run Plan
        self.execute_cli_runplan_cmd(self.ms_node, add_to_cleanup=False)

        # Wait for plan
        completed_successfully = self.wait_for_plan_state(self.ms_node,
                                        test_constants.PLAN_COMPLETE,
                                        timeout_mins=240,
                                        seconds_increment=1,
                                        full_show=False)

        # Record time since plan start
        elapsed_time = time.time() - start_time

        # Show plan regardless of plan success or failure
        cmd = self.cli.get_show_plan_cmd()
        self.run_expects_command(self.ms_node, cmd,
                                 [], timeout_secs=600)

        # Assert earlier wait_for_plan_state success
        self.assertTrue(completed_successfully,
                        "Plan didn't finish successfully in given time")

        self.log("info",
            "Time for 'litp run_plan' to complete deployment: {0}s".format(
                elapsed_time))

        self.save_result(elapsed_time)
