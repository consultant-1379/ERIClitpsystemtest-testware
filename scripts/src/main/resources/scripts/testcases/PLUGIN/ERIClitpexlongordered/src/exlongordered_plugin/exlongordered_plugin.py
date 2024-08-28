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
from litp.core.execution_manager import CallbackTask
from litp.core.task import OrderedTaskList, RemoteExecutionTask

from litp.core.litp_logging import LitpLogger
import time
import datetime

log = LitpLogger()


class ExLongOrderedPlugin(Plugin):
    """
    LITP exlongordered plugin
    """

    def validate_model(self, plugin_api_context):
        """
        This method can be used to validate the model ...

        .. warning::
          Please provide a summary of the model validation performed by
          exlongordered here
        """
        errors = []
#        nodes = plugin_api_context.query("node")
#        for node in nodes:
#            if node.hostname == "NOT_ALLOWED":
#                errors.append(ValidationError(
#                                item_path=node.get_vpath(),
#                                error_message="hostname cannot "
#                                "be 'NOT_ALLOWED'"
#                              ))
        return errors

#pylint: disable=W0613
    def create_file(self, callback_api, *args, **kwargs):
        """
        This method will create a file, filename being arg[0]
        """
        log.trace.info("EXLONG1:create_file callback called")
        filename = args[0]
        delay = args[1]
        log.trace.info("EXLONG1: waiting for %d" % delay)
        time.sleep(delay)
        log.trace.info("EXLONG1:This should create file %s" % filename)
        lfile = open(filename, 'w')
        lfile.write(datetime.datetime.now().ctime())
        lfile.close()

    def create_configuration(self, plugin_api_context):
        """
        Plugin can provide tasks based on the model ...

        *Example CLI for this plugin:*

        .. code-block:: bash

          # TODO Please provide an example CLI snippet for plugin exlongordered
          # here
        """
        tasks = []

        nodes = plugin_api_context.query("node")
        for node in nodes:
            pklists = node.query("package-list")
            for pk in pklists:
                if "LONG" not in pk.name:
                    continue
                filename1 = "/etc/exlongord1_call1_%s_%s" % \
                     (node.hostname, pk.name)
                filename2 = "/etc/exlongord1_call2_%s_%s" % \
                     (node.hostname, pk.name)
                filename3 = "/etc/exlongord1_call3_%s_%s" % \
                     (node.hostname, pk.name)
                if pk.is_initial() or pk.is_updated():
                    log.trace.debug("EXLONG1:Create task %s" % filename1)
                    log.trace.debug("EXLONG1:Create task %s" % filename2)
                    log.trace.debug("EXLONG1:Create task %s" % filename3)
                    nodelist = []
                    nodelist.append(node)
                    serviceName = "crond"
                    action = "status"
                    agent = "service"
                    if "FAIL" in pk.name:
                        serviceName = "rubbish"
                        action = "restart"
                    if "CUSTOM" in pk.name:
                        agent = "stexample"
                        action = "my_action"
                    tasks.append(OrderedTaskList(pk, [
                        CallbackTask(pk,
                                       "Install file %s" % filename1,
                                       self.create_file,
                                       filename1, 0),
                        CallbackTask(pk,
                                       "Install delay file %s" % filename2,
                                       self.create_file,
                                       filename2, 120),
                        CallbackTask(pk,
                                       "Install file %s" % filename3,
                                       self.create_file,
                                       filename3, 0),
                        RemoteExecutionTask(nodelist, pk,
                                       "%s %s for %s" %
                                           (action, serviceName,
                                            node.hostname),
                                       agent,
                                       action,
                                       service=serviceName)
                    ]))
        return tasks
