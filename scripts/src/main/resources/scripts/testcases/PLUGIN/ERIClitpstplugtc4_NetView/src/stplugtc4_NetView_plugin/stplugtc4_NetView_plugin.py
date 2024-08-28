##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.plugin import Plugin
from litp.core.execution_manager import ConfigTask
from litp.core.extension import ViewError

from litp.core.litp_logging import LitpLogger
log = LitpLogger()


class STplugtc4_NetViewPlugin(Plugin):
    """
    LITP stplugtc4_NetView plugin
    """

    def validate_model(self, plugin_api_context):
        """
        This method can be used to validate the model ...

        .. warning::
          Please provide a summary of the model validation performed by
          stplugtc4_NetView here
        """
        errors = []
        for node in plugin_api_context.query('node'):
            networks = node.query("network")
            #networks = plugin_api_context.query("network")
            for network in networks:
                log.trace.info("node id: {0} network id: {1} \
                                            interface name: {2}".format
                                (node.item_id, network.network_name, \
                                            network.view_interface_name))
        return errors

    def create_configuration(self, plugin_api_context):
        """
        Plugin can provide tasks based on the model ...

        *Example CLI for this plugin:*

        .. code-block:: bash

        """
        tasks = []

        nodes = plugin_api_context.query("node") + \
                 plugin_api_context.query("ms")
        for node in nodes:
            nets = node.query("network")
            for net in nets:
                pks = node.query("package-list")
                for pk in pks:
                    if pk.is_initial() and ("NET" in pk.name):
                        try:
                            netinfo = "%s_%s_%s_%s_%s_%s_%s" % \
                            (net.view_interface_name, net.view_ip_address,
                               net.view_mac_address,
                               net.network_name, net.view_gateway,
                               net.view_subnet, pk.name)
                        except ViewError as e:
                            log.trace.info("View Error {0} on {1}".format(\
                                str(e), net.network_name))
                            netinfo = "%s_%s_Fail get NetInfo" % \
                                (net.network_name, pk.name)
                        # Remove any / in netinfo as will break
                        netinfo = netinfo.replace('/', '_')
                        filename = "/etc/examplenet_%s.txt" % netinfo
                        tasks.append(ConfigTask(node,
                                       node,
                                       "Install file %s" % filename,
                                       "file", filename,
                                       ensure="present"
                                       )
                             )
        return tasks
