#!/usr/bin/env python

"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     December 2015
@author:    Ruth, Vinnie
@summary:   System Test for Node Hardening Activities
            Tests taken from the "Node Hardening Activities" doc
            Doc updated for LITPCDS-9291
            The base for the filers in this file are taken
            from a litp install on a 16.2 iso
@change:
"""

from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils


class NodeHardening(GenericTest):
    """
    Description:
        Perform checks recommended in Node Hardening Activities Document
    """

    def setUp(self):
        """Run before every test"""
        super(NodeHardening, self).setUp()
        self.rhcmd = RHCmdUtils()
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

    def tearDown(self):
        """Run after every test"""
        super(NodeHardening, self).tearDown()

    @staticmethod
    def remove_strings(list_ok, list_returned):
        """
        Check list_returned for any items that are in the list_ok
        If the item in list_ok they are removed from the list_returned
        The list_returned is returned minus any OK items
        """
        # Filter through lists
        for item_ok in list_ok:
            for item_ret in list(list_returned):
                if item_ok in item_ret:
                    # self.log('info', item_ret)
                    list_returned.remove(item_ret)
        return list_returned

    def search_and_filter(self, node_list, sys_cmd, ms_filter, mn_filter):
        """
        Function to run a command on a list of nodes and returns
        any matches that are not filtered out.
        """
        suspect_services_list = []

        for node in node_list:
            # Get suspect services on a node
            suspects, _, _ = self.run_command(node, sys_cmd, su_root=True,
                                              default_asserts=False)
            # Filter suspect services depending on what node is been checked
            if node == self.ms_node:
                suspects = self.remove_strings(ms_filter, suspects)
            else:
                suspects = self.remove_strings(mn_filter, suspects)

            self.log('info',
                     "list of suspects items on node {0} \n {1}".format(
                             node, '\n'.join(suspects)))
            # Add list of remaing suspect services to list with node name
            for item in suspects:
                suspect_services_list.append(node + " -> " + item)
        return suspect_services_list

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc26')
    def test_26_check_enforcing_mode(self):
        """
        Description:
            Check SElinux is in enforcing mode on MS and MN
        Actions:
            Parse output from sestatus
        Result:
            Pass if SElinux is in enforcing mode on MS and MN
        """
        sys_cmd = "/usr/sbin/sestatus"
        checkforstr1 = 'Current mode:                   enforcing'
        checkforstr2 = "Mode from config file:          enforcing"
        for node in self.targets:
            assert isinstance(node, object)
            grep_cmd = self.rhcmd.get_grep_file_cmd(" ", checkforstr1,
                                                    file_access_cmd=sys_cmd)
            # run_command and check return code if match found
            _, stderr, stdrc = self.run_command(node, grep_cmd,
                                                su_root=True)
            self.assertTrue(stderr == [])
            self.assertTrue(stdrc == 0, "Expected output >>{0}<< not "
                                        "found on node {1}".format(
                    checkforstr2, node))

            grep_cmd = self.rhcmd.get_grep_file_cmd(" ", checkforstr2,
                                                    file_access_cmd=sys_cmd)
            # run_command and check return code if match found
            _, stderr, stdrc = self.run_command(node, grep_cmd,
                                                su_root=True)
            self.assertTrue(stderr == [])
            self.assertTrue(stdrc == 0, 'Expected output >>{0}<< not '
                                        'found on node {1}'.format(
                    checkforstr2, node))

    @attr('all', 'non-revert', 'security', 'P2', 'security_tc27')
    def test_27_check_no_XWindows(self):
        """
        Description:
            Verify that X-Windows is not used on MS or MN
        Actions:
            Test that this command does not return a PID:
               pidof X
        Result:
            Pass if X-Windows is not used on MS or MN
        """
        sys_cmd = '/sbin/pidof X'
        for node in self.targets:
            stdout, _, rc = self.run_command(node, sys_cmd, su_root=True)
            self.assertTrue(stdout == [], "Found X-Windows been used on node "
                                          "{0}".format(node))
            self.assertTrue(rc == 1, "Found X-Windows been used on node "
                                     "{0}".format(node))

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc28')
    def test_28_check_no_crontabs(self):
        """
        Description:
             Check no crontabs are defined for root or litp-admin
             in crontabs on MS or MN
        Actions:
             Test that this command doesn't return any jobs
             for root or litp-admin:
               crontab -u <username> -l
        Result:
            Pass if no jobs are defined in crontabs for litp-admin and root
             on MS or MN
        """
        users = ["root",
                 "litp-admin"]
        no_crontab_msg = "no crontab for "
        for user in users:
            sys_cmd = '/usr/bin/crontab -u {0} -l'.format(user)
            assert isinstance(self.targets, object)
            for node in self.targets:
                assert isinstance(node, object)
                grep_cmd = self.rhcmd.get_grep_file_cmd(
                        " ", no_crontab_msg + user, file_access_cmd=sys_cmd)
                _, _, rc = self.run_command(node, grep_cmd, su_root=True)
                self.assertTrue(rc == 1, "Found crontab on node "
                                         "{0}".format(node))

    @attr('all', 'non-revert', 'security', 'P1', 'security_tc29')
    def test_29_check_no_cronjobs(self):
        """
        Description:
             Check no unexpected cron jobs are defined on the system.
             We exclude cronjobs that are on the default rhel install
             There is currently one cron job on the MS, it removes old files
             Check there aren't any others on MS or MN
        Actions:
              Test there are no unexpected files under /etc/cron
              on MS and MN
                 ls /etc/cron.*/*
        Result:
            Pass if no unexpected cron jobs are defined
              on MS or MN
        """
        ok_ms_list = (r'/etc/cron.d/0hourly',
                      r'/etc/cron.daily/litpd',
                      r'/etc/cron.daily/logrotate',
                      r'/etc/cron.daily/makewhatis.cron',
                      r'/etc/cron.daily/rhsmd',
                      r'/etc/cron.daily/tmpwatch',
                      r'/etc/cron.d/raid-check',
                      r'/etc/cron.d/sysstat',
                      r'/etc/cron.hourly/0anacron',)

        ok_mn_list = (r'/etc/cron.d/0hourly',
                      r'/etc/cron.daily/cups',
                      r'/etc/cron.daily/logrotate',
                      r'/etc/cron.daily/makewhatis.cron',
                      r'/etc/cron.daily/rhsmd',
                      r'/etc/cron.daily/tmpwatch',
                      r'/etc/cron.d/raid-check',
                      r'/etc/cron.d/sysstat',
                      r'/etc/cron.hourly/0anacron')
        sys_cmd = "ls /etc/cron.*/* -1"
        suspect_list = (
            self.search_and_filter(self.targets, sys_cmd, ok_ms_list,
                                   ok_mn_list))
        self.assertTrue(suspect_list == [],
                        "Found cronjobs on node " + '\n'.join(
                                suspect_list))

    @attr('all', 'non-revert', 'security', 'P2', 'security_tc30')
    def test_30_check_no_telnet(self):
        """
        Description:
            Check that telnet is not installed on MS or MN
        Actions:
            Check if telnet is installed on MS or MN
        Result:
            Pass if telnet is not installed on MS or MN
        """
        package = ['telnet']
        sys_cmd = self.rhcmd.check_pkg_installed(package)
        assert isinstance(self.targets, object)
        for node in self.targets:
            stdout, stderr, rc = self.run_command(node, sys_cmd, su_root=True)
            self.assertTrue(stdout == [],
                            "Found installed package {0} on node {1}".format(
                                    package, node))
            self.assertTrue(stderr == [])
            self.assertTrue(rc == 1)

    @attr('all', 'non-revert', 'security', 'P2', 'security_tc31')
    def test_31_check_worldwritable(self):
        """
        Description:
            Check no new world-writable files or directories
               on MS or MN
        Actions:
            Check no new world-writable files or directories
               on MS or MN
               find / -perm -2 ! -type l -ls
        Result:
           Pass if no world-writable files or dirs on MS or MN
        """
        default_rhel_list = (r'/selinux/null',
                             r'/selinux/member',
                             r'/selinux/user',
                             r'/selinux/relabel',
                             r'/selinux/create',
                             r'/selinux/access',
                             r'/selinux/context',
                             r'/var/tmp',
                             r'/var/spool/postfix/private/rewrite',
                             r'/var/spool/postfix/private/relay',
                             r'/var/spool/postfix/private/smtp',
                             r'/var/spool/postfix/private/verify',
                             r'/var/spool/postfix/private/virtual',
                             r'/var/spool/postfix/private/lmtp',
                             r'/var/spool/postfix/private/error',
                             r'/var/spool/postfix/private/trace',
                             r'/var/spool/postfix/private/scache',
                             r'/var/spool/postfix/private/local',
                             r'/var/spool/postfix/private/discard',
                             r'/var/spool/postfix/private/tlsmgr',
                             r'/var/spool/postfix/private/proxymap',
                             r'/var/spool/postfix/private/retry',
                             r'/var/spool/postfix/private/anvil',
                             r'/var/spool/postfix/private/proxywrite',
                             r'/var/spool/postfix/private/defer',
                             r'/var/spool/postfix/private/bounce',
                             r'/var/spool/postfix/public/flush',
                             r'/var/spool/postfix/public/cleanup',
                             r'/var/spool/postfix/public/pickup',
                             r'/var/spool/postfix/public/qmgr',
                             r'/var/spool/postfix/public/showq',
                             r'/var/run/rpcbind.sock',
                             r'/var/run/dbus/system_bus_socket',
                             r'/tmp',
                             r'/tmp/.ICE-unix',)
        ok_ms_list = (r'cgroup.event_control',
                      r'/var/.slmbackup',
                      r'/var/.slmbackup/.lsysmbk',
                      r'/var/.slmbackup/.lsysmbk/f1x5FMB4.tgz',
                      r'/var/.slmbackup/.lsysmbk/nsprs.tgz',
                      r'/var/.slmbackup/.lsysmbk/serauth2.so',
                      r'/var/.slmbackup/.lsysmbk/p07Kwoo6.tgz',
                      r'/var/.slmbackup/.lsysmbk/serauth1.so',
                      r'/var/cache/yum/x86_64/6Server/a/',
                      r'/var/.slm',
                      r'/var/.slm/.lsysmdat',
                      r'/var/.slm/.lsysmdat/aZWzM0w2XVGHUo7OLag9B.so',
                      r'/var/.slm/.lsysmdat/f1x5FMB4.so',
                      r'/var/.slm/.lsysmdat/pX4xj6L24HGcENo66sgOG.so',
                      r'/var/.slm/.lsysmdat/nsprs.so',
                      r'/var/.slm/.lsysmdat/B5WXx7vuZylo_X2L85lbb.so',
                      r'/var/.slm/.lsysmdat/CncgwZGanE_5ky52RQMc5.so',
                      r'/var/.slm/.lsysmdat/0pfSOC3jaMWA5uO-JKe_u.so',
                      r'/var/.slm/.lsysmdat/p07Kwoo6.so',
                      r'/var/.slm/.lsysmdat/5kdSoeQOyh2zLx_R2HIEy.so',
                      r'/var/.slm/.lsysmdat/4UfNw609h5bEMZcIDNH6b.so',
                      r'/var/.slm/.lsysmdat/XmwNdORG0oB_pl6R4_N55.so',
                      r'/var/run/libvirt/libvirt-sock-ro',
                      r'/var/run/libvirt/libvirt-sock',
                      r'/var/www/html/images',
                      r'/var/www/html/newRepo_dir',
                      r'/var/www/html/newRepo_dir2',
                      r'/var/lib/libvirt/instances/vm',
                      r'/var/lib/libvirt/instances/hypericish',
                      r'/var/.slmauth',
                      r'/var/.slmauth/.lsysath',
                      r'/var/.slmauth/.lsysath/HN8I35Rg.so',
                      r'/var/.slmauth/.lsysath/62tn74K9.so',
                      r'/var/.slmauth/.lsysath/4f45D0g2.so',
                      r'/var/.slmauth/.lsysath/serauth2.so',
                      r'/var/.slmauth/.lsysath/dHe83236.so',
                      r'/var/.slmauth/.lsysath/serauth1.so',
                      r'/etc/rc.d/init.d/vm',
                      r'/etc/rc.d/init.d/hypericish',
                      r'ks.partition.snippet',
                      r'helloworld',
                      r'primary.sqlite',
                      r'repomd.xml',
                      r'/var/run/postgresql',
                      r'cachecookie') + default_rhel_list
        ok_mn_list = (r'/etc/rc.d/init.d/vm',
                      r'/var/.slmbackup',
                      r'/var/.slmbackup/.lsysmbk',
                      r'/var/.slmbackup/.lsysmbk/p07Kwoo6.tgz',
                      r'/var/.slmbackup/.lsysmbk/serauth1.so',
                      r'/var/.slmbackup/.lsysmbk/nsprs.tgz',
                      r'/var/.slmbackup/.lsysmbk/serauth2.so',
                      r'/var/.slmbackup/.lsysmbk/f1x5FMB4.tgz',
                      r'/var/opt/VRTSsfmh/sec/VRTSat_lhc',
                      r'/var/opt/VRTSsfmh/sec/profiles',
                      r'/var/lib/libvirt/instances/vm',
                      r'/var/.slmauth',
                      r'/var/.slmauth/.lsysath',
                      r'/var/.slmauth/.lsysath/62tn74K9.so',
                      r'/var/.slmauth/.lsysath/serauth1.so',
                      r'/var/.slmauth/.lsysath/4f45D0g2.so',
                      r'/var/.slmauth/.lsysath/serauth2.so',
                      r'/var/.slmauth/.lsysath/HN8I35Rg.so',
                      r'/var/.slmauth/.lsysath/dHe83236.so',
                      r'/var/run/dovecot/dns-client',
                      r'/var/run/dovecot/lmtp',
                      r'/var/run/dovecot/login/pop3',
                      r'/var/run/dovecot/login/imap',
                      r'/var/run/dovecot/login/dns-client',
                      r'/var/run/dovecot/login/login',
                      r'/var/run/dovecot/login/ssl-params',
                      r'/var/run/saslauthd/mux',
                      r'/var/run/libvirt/libvirt-sock',
                      r'/var/run/libvirt/libvirt-sock-ro',
                      r'/var/run/cups/cups.sock',
                      r'/var/.slm',
                      r'/var/.slm/.lsysmdat',
                      r'/var/.slm/.lsysmdat/CncgwZGanE_5ky52RQMc5.so',
                      r'/var/.slm/.lsysmdat/4UfNw609h5bEMZcIDNH6b.so',
                      r'/var/.slm/.lsysmdat/p07Kwoo6.so',
                      r'/var/.slm/.lsysmdat/0pfSOC3jaMWA5uO-JKe_u.so',
                      r'/var/.slm/.lsysmdat/aZWzM0w2XVGHUo7OLag9B.so',
                      r'/var/.slm/.lsysmdat/5kdSoeQOyh2zLx_R2HIEy.so',
                      r'/var/.slm/.lsysmdat/f1x5FMB4.so',
                      r'/var/.slm/.lsysmdat/pX4xj6L24HGcENo66sgOG.so',
                      r'/var/.slm/.lsysmdat/nsprs.so',
                      r'/var/.slm/.lsysmdat/XmwNdORG0oB_pl6R4_N55.so',
                      r'/var/.slm/.lsysmdat/B5WXx7vuZylo_X2L85lbb.so',
                      r'/var/coredumps',
                      r'cgroup.event_control',
                      r'/var/VRTSat_lhc',
                      r'/var/run/abrt/abrt.socket',
                      r'/etc/vx/vold_inquiry/socket') + default_rhel_list

        sys_cmd = 'find / -not -path "/proc*" -and -not -path "/dev*" ' + \
                  '-perm -2 ! -type l -ls'
        suspect_list = (
            self.search_and_filter(self.targets, sys_cmd, ok_ms_list,
                                   ok_mn_list))
        self.assertTrue(suspect_list == [],
                        "list of suspects ->" + '\n'.join(suspect_list))

    @attr('all', 'non-revert', 'security', 'P2', 'security_tc32')
    def test_32_check_no_SGID(self):
        """
        Description:
            Check that no unexpected SGID (Set Group ID up on execution)
            programs exist on MS or MN
        Actions:
            Use the following command to generate
              a list of SGID files:
              find / -perm -2000
        Result:
           Pass if no unexpected SGID programs are present
        """
        default_rhel_list = (
            r'No such file or directory',
            r'/usr/sbin/postdrop',
            r'/usr/sbin/postqueue',
            r'/usr/libexec/utempter/utempter',
            r'/usr/bin/wall',
            r'/usr/bin/write',
            r'/usr/bin/ssh-agent',
            r'/usr/bin/screen',
            r'/sbin/netreport',
            r'/bin/cgclassify',
            r'/bin/cgexec')
        ok_ms_list = (r'mcollective/util/puppet_agent_mgr',
                      r'/opt/ericsson/nms/litp/share/locale',
                      r'/opt/ericsson/nms/litp/share/locale/en',
                      r'/opt/ericsson/nms/litp/share/locale/en/LC_MESSAGES',
                      r'/opt/ericsson/nms/litp/bin',
                      r'/opt/ericsson/nms/litp/lib',
                      r'/opt/ericsson/nms/litp/lib/volmgr_plugin',
                      r'/opt/ericsson/nms/litp/lib/volmgr_plugin/drivers',
                      r'/opt/ericsson/nms/litp/lib/network_extension',
                      r'/opt/ericsson/nms/litp/lib/dhcpservice_plugin',
                      r'/opt/ericsson/nms/litp/lib/linuxfirewall_plugin',
                      r'/opt/ericsson/nms/litp/lib/serializer',
                      r'/opt/ericsson/nms/litp/lib/triggers',
                      r'/opt/ericsson/nms/litp/lib/triggers/cobbler',
                      r'/opt/ericsson/nms/litp/lib/litp',
                      r'/opt/ericsson/nms/litp/lib/litp/core',
                      r'/opt/ericsson/nms/litp/lib/litp/service',
                      r'/opt/ericsson/nms/litp/lib/litp/service/templates',
                      r'/opt/ericsson/nms/litp/lib/litp/service/template',
                      r'/opt/ericsson/nms/litp/lib/litp/service/controllers',
                      r'/opt/ericsson/nms/litp/lib/litp/plan_types',
                      r"/opt/ericsson/nms/litp/lib/litp/" \
                        "plan_types/create_snapshot",
                      r"/opt/ericsson/nms/litp/lib/litp/" \
                        "plan_types/remove_snapshot",
                      r"/opt/ericsson/nms/litp/lib/litp/" \
                        "plan_types/deployment_plan",
                      r"/opt/ericsson/nms/litp/lib/litp/" \
                       "plan_types/restore_snapshot",
                      r'/opt/ericsson/nms/litp/lib/litp/extensions',
                      r'/opt/ericsson/nms/litp/lib/litp/xml',
                      r'/opt/ericsson/nms/litp/lib/litp/plugins',
                      r'/opt/ericsson/nms/litp/lib/litp/plugins/core',
                      r'/opt/ericsson/nms/litp/lib/litp/migration',
                      r"/opt/ericsson/nms/litp/lib/litp/" \
                       "migration/operations",
                      r'/opt/ericsson/nms/litp/lib/litp/encryption',
                      r'/opt/ericsson/nms/litp/lib/vcsplugin',
                      r'/opt/ericsson/nms/litp/lib/vcsplugin/legacy',
                      r'/opt/ericsson/nms/litp/lib/ntp_plugin',
                      r'/opt/ericsson/nms/litp/lib/nas_plugin',
                      r'/opt/ericsson/nms/litp/lib/package_extension',
                      r'/opt/ericsson/nms/litp/lib/litpcli',
                      r'/opt/ericsson/nms/litp/lib/libvirt_extension',
                      r'/opt/ericsson/nms/litp/lib/yum_plugin',
                      r'/opt/ericsson/nms/litp/lib/vcs_extension',
                      r'/opt/ericsson/nms/litp/lib/ntp_extension',
                      r"/opt/ericsson/nms/litp/lib/" \
                        "linuxfirewall_extension",
                      r'/opt/ericsson/nms/litp/lib/sysparams_extension',
                      r'/opt/ericsson/nms/litp/lib/volmgr_extension',
                      r'/opt/ericsson/nms/litp/lib/hosts_plugin',
                      r'/opt/ericsson/nms/litp/lib/naslib',
                      r'/opt/ericsson/nms/litp/lib/naslib/drivers',
                      r'/opt/ericsson/nms/litp/lib/naslib/drivers/sfs',
                      r"/opt/ericsson/nms/litp/lib/" \
                       "naslib/drivers/sfs/sfsmock",
                      r'/opt/ericsson/nms/litp/lib/naslib/drivers/rhelnfs',
                      r"/opt/ericsson/nms/litp/lib/" \
                       "naslib/drivers/rhelnfs/rhelmock",
                      r'/opt/ericsson/nms/litp/lib/naslib/nasmock',
                      r'/opt/ericsson/nms/litp/lib/libvirt_plugin',
                      r'/opt/ericsson/nms/litp/lib/dnsclient_plugin',
                      r'/opt/ericsson/nms/litp/lib/service_plugin',
                      r'/opt/ericsson/nms/litp/lib/logrotate_plugin',
                      r'/opt/ericsson/nms/litp/lib/logrotate_extension',
                      r'/opt/ericsson/nms/litp/lib/network_plugin',
                      r'/opt/ericsson/nms/litp/lib/bootmgr_extension',
                      r'/opt/ericsson/nms/litp/lib/package_plugin',
                      r'/opt/ericsson/nms/litp/lib/ipmi_plugin',
                      r'/opt/ericsson/nms/litp/lib/yum_extension',
                      r'/opt/ericsson/nms/litp/lib/nas_extension',
                      r'/opt/ericsson/nms/litp/lib/dnsclient_extension',
                      r'/opt/ericsson/nms/litp/lib/hosts_extension',
                      r'/opt/ericsson/nms/litp/lib/bootmgr_plugin',
                      r'/opt/ericsson/nms/litp/lib/dhcpservice_extension',
                      r'/opt/ericsson/nms/litp/lib/sysparams_plugin',
                      r'/opt/ericsson/nms/litp/lib/cba_extension',
                      r'/opt/ericsson/nms/litp/3pps/licenses',
                      r'/opt/ericsson/nms/litp/3pps/licenses/pydot',
                      r'/opt/ericsson/nms/litp/3pps/licenses/IPy',
                      r'/opt/ericsson/nms/litp/3pps/licenses/cherrypy',
                      r'/opt/ericsson/nms/litp/3pps/licenses/pyparsing',
                      r"/opt/ericsson/nms/litp/3pps/" \
                       "licenses/python-graph-core",
                      r'/opt/ericsson/nms/litp/3pps/licenses/jsonpath',
                      r'/opt/ericsson/nms/litp/3pps/licenses/pampy',
                      r'/opt/ericsson/nms/litp/3pps/licenses/argparse',
                      r'/opt/ericsson/nms/litp/3pps/licenses/PyYAML',
                      r'/opt/ericsson/nms/litp/3pps/licenses/jsonpickle',
                      r'/etc/mcollective/mcollective/util',
                      r'/etc/mcollective/mcollective/agent',
                      r'/etc/extensions',
                      r'/opt/ericsson/nms/litp/etc/puppet/modules',
                      r"/opt/ericsson/nms/litp/" \
                       "etc/puppet/modules/network",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/network/manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/ntpd',
                      r"/opt/ericsson/nms/litp/" \
                       "etc/puppet/modules/ntpd/manifests",
                      r"/opt/ericsson/nms/litp/" \
                       "etc/puppet/modules/ntpd/templates",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/dnsclient',
                      r"/opt/ericsson/nms/litp/" \
                       "etc/puppet/modules/dnsclient/manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/litp',
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/litp/lib',
                      r"/opt/ericsson/nms/litp/" \
                       "etc/puppet/modules/litp/lib/facter",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/litp/files',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "litp/manifests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "litp/templates",
                      r"/opt/ericsson/nms/litp/" \
                       "etc/puppet/modules/litp/default_manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/landscape',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "landscape/lib",
                      r"/opt/ericsson/nms/litp/" \
                       "etc/puppet/modules/landscape/lib/puppet",
                      r"/opt/ericsson/nms/litp/" \
                       "etc/puppet/modules/landscape/lib/puppet/reports",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "landscape/manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/package',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "package/manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/dhcp6',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "dhcp6/manifests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "dhcp6/templates",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "dhcp6/templates/redhat",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/libvirt',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "libvirt/manifests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "libvirt/templates",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "libvirt/tests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobblerdata",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobblerdata/lib",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobblerdata/lib/puppet",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobblerdata/lib/puppet/type",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobblerdata/lib/puppet/parser",
                      r'/var/lib/puppet/lib/puppet/parser/functions',
                      r'/var/lib/puppet/lib/puppet/provider',
                      r'/var/lib/puppet/lib/puppet/provider/cobblerdistro',
                      r'/var/lib/puppet/lib/puppet/provider/cobblerprofile',
                      r'/var/lib/puppet/lib/puppet/provider/cobblerrepo',
                      r'/var/lib/puppet/lib/puppet/provider/cobblersystem',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobblerdata/files",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobblerdata/manifests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobblerdata/templates",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "mcollective_utils",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "mcollective_utils/files",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/hosts',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "hosts/manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/cobbler',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobbler/files",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobbler/manifests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobbler/templates",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "cobbler/templates/etc",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/yum',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/yum/manifests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules/" \
                       "yum/templates",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/vcs',
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/vcs/lib',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/vcs/lib/facter",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/vcs/files',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/vcs/manifests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/vcs/templates",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/logrotate',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/logrotate/files",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/logrotate/files/etc",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/logrotate/files/etc/cron.daily",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/logrotate/files/etc/cron.hourly",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/logrotate/manifests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/logrotate/manifests/defaults",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/logrotate/templates",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/logrotate/templates/etc",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/logrotate/templates/etc/logrotate.d",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/ssh',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/ssh/manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/litpweb',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/litpweb/manifests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/litpweb/templates",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/sysparams',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/sysparams/lib",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/sysparams/lib/augeas",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/sysparams/lib/augeas/lenses",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/sysparams/manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/firewalls',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/firewalls/files",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/firewalls/manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/dhcpservice',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/dhcpservice/manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/nas',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/nas/manifests",
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/koan',
                      r'/opt/ericsson/nms/litp/etc/puppet/modules/koan/files',
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/koan/manifests",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/mcollective_agents",
                      r"/opt/ericsson/nms/litp/etc/puppet/modules" \
                       "/mcollective_agents/files",
                      r'/etc/sysconfig',
                      r'/etc/plugins',
                      r'/etc/selinux',
                      r'/etc/pki/rsyslog',
                      r'/etc/sysconfig',
                      r'/etc/rsyslog.d',
                      r'/lib64/rsyslog',
                      r'/var/lib/rsyslog',
                      r'/var/lib/puppet/lib',
                      r'/var/lib/puppet/lib/puppet'
                      r'/var/lib/puppet/lib/augeas',
                      r'/var/lib/puppet/lib/augeas/lenses',
                      r'/var/lib/puppet/lib/facter',
                      r'/var/lib/puppet/lib/puppet/provider/cobblerrepo',
                      r'/var/lib/puppet/lib/puppet/provider/cobblerdistro',
                      r'/var/lib/puppet/lib/puppet/provider/cobblersystem',
                      r'/var/lib/puppet/lib/puppet/provider/cobblerprofile',
                      r'/var/lib/puppet/lib/puppet/reports',
                      r'/var/run/celery',
                      r'/var/log/celery',
                      r'/opt/ericsson/nms/litp/etc/migrations'
                      ) + default_rhel_list

        ok_mn_list = (r'/opt/mcollective/mcollective/agent',
                      r'/opt/mcollective/mcollective/util',
                      r'/opt/ericsson/nms/litp/lib',
                      r'/opt/ericsson/nms/litp/lib/litpmnlibvirt',
                      r'/etc/sysconfig',
                      r'/etc/rsyslog.d',
                      r'/etc/pki/rsyslog',
                      r"/usr/libexec/mcollective/mcollective" \
                       "/util/puppet_agent_mgr",
                      r'/usr/bin/lockfile',
                      r'/var/lib/rsyslog',
                      r'/var/lib/puppet/lib/augeas',
                      r'/var/lib/puppet/lib/augeas/lenses',
                      r'/var/lib/puppet/lib/facter',
                      r'/var/lib/puppet/lib',
                      r'/var/lib/puppet/lib/puppet',
                      r'/var/lib/puppet/lib/puppet/reports',
                      r'/var/lib/puppet/lib/puppet/provider/cobblerprofile',
                      r'/var/lib/puppet/lib/puppet/provider/cobblersystem',
                      r'/var/lib/puppet/lib/puppet/provider/cobblerdistro',
                      r'/var/lib/puppet/lib/puppet/provider/cobblerrepo',
                      r'/lib64/rsyslog',
                      r'/opt/ericsson/nms/litp/3pps/licenses',
                      r'/opt/ericsson/nms/litp/3pps/licenses/pampy',
                      r'/opt/ericsson/nms/litp/3pps/licenses/IPy',
                      r'/opt/ericsson/nms/litp/3pps/licenses/argparse',
                      r'/opt/ericsson/nms/litp/3pps/licenses/PyYAML',
                      r'/opt/ericsson/nms/litp/3pps/licenses/cherrypy',
                      r'/opt/ericsson/nms/litp/3pps/licenses/pydot',
                      r"/opt/ericsson/nms/litp/3pps/licenses/" \
                       "python-graph-core",
                      r'/opt/ericsson/nms/litp/3pps/licenses/pyparsing',
                      r'/opt/ericsson/nms/litp/3pps/licenses/jsonpath',
                      r'/opt/ericsson/nms/litp/3pps/licenses/jsonpickle',
                      ) + default_rhel_list

        sys_cmd = "/bin/find / -perm -2000"
        suspect_list = (
            self.search_and_filter(self.targets, sys_cmd, ok_ms_list,
                                   ok_mn_list))
        self.assertTrue(suspect_list == [],
                        "list of suspects -perm -2000 " + '\n'.join(
                                suspect_list))

    @attr('all', 'non-revert', 'security', 'P2', 'security_tc33')
    def test_33_check_no_SUID(self):
        """
        Description:
            Check that no unexpected SUID (Set owner User ID up on execution)
            programs exist on MS or MN
        Actions:
            Use the following command to generate
             a list of SUID files:
             find / -perm -4000
        Result:
           Pass if no unexpected SUID programs are present
        """
        default_rhel_list = (r'Permission denied',
                             r'No such file or directory',
                             r'/usr/sbin/usernetctl',
                             r'/usr/sbin/userhelper',
                             r'/usr/libexec/polkit-1/polkit-agent-helper-1',
                             r'/usr/libexec/openssh/ssh-keysign',
                             r'/usr/libexec/pt_chown',
                             r'/usr/bin/chage',
                             r'/usr/bin/at',
                             r'/usr/bin/passwd',
                             r'/usr/bin/gpasswd',
                             r'/usr/bin/chsh',
                             r'/usr/bin/sudo',
                             r'/usr/bin/crontab',
                             r'/usr/bin/pkexec',
                             r'/usr/bin/chfn',
                             r'/usr/bin/newgrp',
                             r'/sbin/pam_timestamp_check',
                             r'/sbin/unix_chkpwd',
                             r'/sbin/mount.nfs',
                             r'/lib64/dbus-1/dbus-daemon-launch-helper',
                             r'/bin/umount',
                             r'/bin/su',
                             r'/bin/ping',
                             r'/bin/ping6',
                             r'/bin/mount',)
        ok_ms_list = (r'/usr/sbin/suexec',
                      ) + default_rhel_list
        ok_mn_list = (r'/usr/libexec/pulse/proximity-helper',
                      r'/bin/fusermount',
                      r'/usr/sbin/suexec') + default_rhel_list

        sys_cmd = "/bin/find / -perm -4000"
        suspect_list = (
            self.search_and_filter(self.targets, sys_cmd, ok_ms_list,
                                   ok_mn_list))
        self.assertTrue(suspect_list == [],
                        "list of suspects -perm -4000 " + '\n'.join(
                                suspect_list))

    @attr('all', 'non-revert', 'security', 'P3', 'security_tc34')
    def test_34_check_running_services(self):
        """
        Description:
            Check that no unexpected services are running
             on MS or MN
        Actions:
            Compare running services against expected list
             for MS and MN, use:
              service --status-all
        Result:
           Pass if no unexpected services are running
        """
        default_rhel_list = (r'failed to initialize AT',
                             r'Permission denied',
                             r'atd',
                             r'auditd',
                             r'crond',
                             r'hald',
                             r'ksmtuned',
                             r'messagebus',
                             r'rndc: neither',
                             r'rpc.statd',
                             r'portreserve',
                             r'master',
                             r'rhsmcertd',
                             r'rpcbind',
                             r'rsyslogd',
                             r'openssh-daemon ',)
        ok_ms_list = (r'cobblerd ',  # used by litp
                      r'dhcpd ',  # used by litp
                      r'httpd ',  # used by litp
                      r'libvirtd ',  # used by litp
                      r'litp_service.py ',  # used by litp
                      r'mcollectived ',  # used by litp
                      r'ntpd ',  # Stated by core
                      r'puppet ',  # used by litp
                      r'tuned ',  # LITPCDS-11943
                      r'vm',  # used by litp deployemnt
                      r'xinetd ',
                      r'hypericish ',  # used by litp deployment
                      r'puppetdb ',  # TORF-107213
                      r'postgres',
                      r'nfsd'
                      ) + default_rhel_list
        ok_mn_list = ('STvmserv',  # used by litp deployemnt
                      r'libvirtd',  # used by litp
                      r'cupsd ',  # used by litp deployemnt
                      r'dovecot',  # used by litp deployemnt
                      r'httpd ',  # used by litp deployemnt
                      r'mcollectived ',  # used by litp
                      r'multipathd ',  # used by emc disks
                      r'ntpd ',  # used by litp
                      r'oddjobd ',  # ??
                      r'puppet ',  # used by litp
                      r'ricci ',  # used by litp deployemnt
                      r'saslauthd ',  # handles plaintext authentication
                      r'tuned ',  # used by VCS
                      r'had ',  # used by VCS
                      r'vm',  # used by litp deployemnt
                      r'PL-VM',  # used by litp deployemnt
                      r'FO-VM',  # used by litp deployemnt
                      r'vxconfigd ',  # used by VxVM
                      r'vxrelocd ',  # used by VxVM
                      r'vxattachd ',  # used by VxVM
                      r'vxcached ',  # used by VxVM
                      r'vxesd ',  # used by VxVM
                      r'vxodm',  # VCS related
                      r'vxconfigbackupd ',  # used by VxVM
                      r'dhcpd ',  # used by litp
                      r'abrtd'   # used by litp deployment
                      ) + default_rhel_list
        sys_cmd = '/sbin/service --status-all | grep  "is running..."'
        suspect_list = (
            self.search_and_filter(self.targets, sys_cmd, ok_ms_list,
                                   ok_mn_list))
        self.assertTrue(suspect_list == [],
                        "list of suspects ->" + '\n'.join(suspect_list))
