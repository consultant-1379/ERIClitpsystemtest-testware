# !/usr/bin/env python
"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Dec 2015
@author:    Messers
@summary:   ST Test Suite to idempotency
"""

from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
import test_constants


class MISCTEST(GenericTest):
    """
    Description:
        This test is carried out after install job of the .150 system
        The .150 job carries out the following:
            1. Installs the MS with the latest LITP ISO
            2. Purposely fails the last task of the initial deployment plan
            3. The LAST_KNOWN_CONFIG is saved at this point to be used
               later by this test (/tmp/LAST_KNOWN_CONFIG_b4_retry)
            4. A retry script of deployment CLI is run
            5. A XML of the entire deployment is exported
               (/tmp/retry_deployment.xml)
            6. A retry plan is created and runs successfully
            7. The idempotency test runs when the retry plan finishes
            8. Load the LAST_KNOWN_CONFIG that was saved earlier
               (/tmp/LAST_KNOWN_CONFIG_b4_retry)
            9. Load the XML of the deployment after the retry script and before
               the plan is created/run (/tmp/retry_deployment.xml)
            10. Items that are in state ForRemoval when the XML was exported
                have to be removed after /tmp/retry_deployment.xml is loaded.
            11. The created plan contains tasks that are all configured on the
                system already
            12. The plan should run successfully
    """

    def setUp(self):
        super(MISCTEST, self).setUp()

        self.ms_node = self.get_management_node_filename()
        self.rhc = RHCmdUtils()

    @attr('non-revert', 'P1', 'retry_tc01')
    def test_01_idempotency(self):
        """
        Preconditions:
            1. /tmp/LAST_KNOWN_CONFIG_b4_retry has been saved
            2. /tmp/retry_deployment.xml has been saved
        Actions:
            1. Check that there is no plan created when create_plan is run
            2. Stop the litpd service
            3. Load saved LAST_KNOWN_CONFIG before retry
            4. Start litpd service
            5. Turn on DEBUG logs
            6. Load retry_deployment.xml to generate the task from the
               retry plan again
            7. Remove items that were in state ForRemoval
            8. Create and run plan
            9. Check if plan completed successfully
        Result:
            1. All tasks are recreated
            2. Plan should complete successfully
            3. System should be in the same state at the end of this plan as it
               was at the beginning.
        """
        # Path to current LAST_KNOWN_CONFIG
        last_known_config = "/var/lib/litp/core/model/LAST_KNOWN_CONFIG"

        # LAST_KNOWN_CONFIG saved before the retry script is run
        last_known_config_b4_retry = "/tmp/LAST_KNOWN_CONFIG_b4_retry"

        # Deployment XML saved after retry script has run but before plan is
        # run
        deployment_retry_xml = "/tmp/retry_deployment.xml"

        # List of items that were in state ForRemoval
        rm_path_list = ["/deployments/d1/clusters/c1/nodes/n2/items/telnet",
                        "/ms/services/ms_vm2",
                        "/deployments/d1/clusters/c1/nodes/n1/items/"
                        "test_service",
                        "/deployments/d1/clusters/c1/nodes/n2/items/"
                        "test_service",
                        "/deployments/d1/clusters/c1/services/SG_dovecot",
                        "/deployments/d1/clusters/c1/services/id_vm6/",
                        "/deployments/d1/clusters/c1/network_hosts/traf_vm105",
                        "/deployments/d1/clusters/c1/network_hosts/traf_vm205",
                        "/deployments/d1/clusters/c1/services/id_vm5/"
                        "applications/vm/vm_network_interfaces/net1",
                        "/software/services/se_vm4/vm_aliases/vm_mn2",
                        "/ms/services/ms_vm1/vm_aliases/vm_mn1",
                        "/deployments/d1/clusters/c1/services/id_vm3/"
                        "applications/vm/vm_aliases/vm_mn1"
                        ]

        # 1. Check that there is no plan created when create_plan is run
        _, _, rc = self.execute_cli_createplan_cmd(self.ms_node,
                                                   expect_positive=False)
        self.log("info", "Return code from 'litp create_plan' = {0}"
                 .format(rc))

        # Asserts that the return code is equal to 1 so that no new tasks exist
        self.assertEqual(rc, 1, "An unexpected plan was created")

        # 2. Stop litpd service before loading the saved LAST_KNOWN_CONFIG
        self.log("info", "Stopping litpd service before loading {0}"
                 .format(last_known_config_b4_retry))
        self.stop_service(self.ms_node, 'litpd')

        # 3. Load saved LAST_KNOWN_CONFIG before retry
        self.log("info", "Copying LAST_KNOWN_CONFIG from '{0}' to "
                         "'{1}'".format(last_known_config_b4_retry,
                                        last_known_config))
        cmd = self.rhc.get_copy_cmd(last_known_config_b4_retry,
                                    last_known_config)
        self.run_command(self.ms_node, cmd, su_root=True)

        # 4. Start litpd service
        self.log("info", "Starting litpd service")
        self.start_service(self.ms_node, 'litpd')

        # 5. Turn on DEBUG after the stop/start of litpd
        self.log("info", "Turn on DEBUG")
        self.turn_on_litp_debug(self.ms_node)

        # 6. Load retry_deployment.xml to generate the task from the retry
        #    plan again
        self.log("info", "Loading {0}".format(deployment_retry_xml))
        self.execute_cli_load_cmd(self.ms_node, "/", deployment_retry_xml,
                                  args="--replace")

        # 7. Remove items that were in state ForRemoval
        self.log("info", "Running the list of remove commands")
        for path in rm_path_list:
            self.execute_cli_remove_cmd(self.ms_node, path)

        # 8. Create and run plan
        self.execute_cli_createplan_cmd(self.ms_node)

        # SHOW PLAN
        self.execute_cli_showplan_cmd(self.ms_node)

        # RUN PLAN
        self.execute_cli_runplan_cmd(self.ms_node)

        # 9. Check if plan completed successfully
        completed_successfully = \
            self.wait_for_plan_state(self.ms_node,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=60)

        self.log("info", "Checking that the plan completed successfully")
        self.assertTrue(completed_successfully, "Plan was not successful")
