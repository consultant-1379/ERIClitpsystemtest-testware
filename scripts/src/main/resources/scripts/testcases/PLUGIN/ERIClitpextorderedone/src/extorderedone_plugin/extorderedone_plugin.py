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
from litp.core.execution_manager import ConfigTask, CallbackTask
from litp.core.task import OrderedTaskList
import datetime
import os

from litp.core.litp_logging import LitpLogger
log = LitpLogger()


class ExtOrderedOnePlugin(Plugin):
    """
    LITP extorderedone plugin
    """

    def validate_model(self, plugin_api_context):
        """
        This method can be used to validate the model ...

        .. warning::
          Please provide a summary of the model validation performed by
          extorderedone here
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
        log.trace.info("EXORD1:create_file callback called")
        filename = args[0]
        log.trace.info("EXORD1:This should create file %s" % filename)
        wfile = open(filename, 'w')
        wfile.write(datetime.datetime.now().ctime())
        wfile.close()

    def delete_file(self, callback_api, *args, **kwargs):
        """
        This method will delete a file, filename being arg[0]
        """
        log.trace.info("EXORD1:delete_file callback called")
        filename = args[0]
        log.trace.info("EXORD1:This should delete file %s" % filename)
        try:
            os.remove(filename)
        except OSError:
            pass

    def create_configuration(self, plugin_api_context):
        """
        Plugin can provide tasks based on the model ...

        *Example CLI for this plugin:*

        .. code-block:: bash

          # TODO Please provide an example CLI snippet for plugin extorderedone
          # here
        """
        tasks = []

        nodes = plugin_api_context.query("node")
        for node in nodes:
            pklists = node.query("package-list")
            for pk in pklists:
                if "ORDTEST" not in pk.name:
                    continue
                filename1 = "/etc/example_ord1_conf1_%s_%s" % \
                     (node.hostname, pk.name)
                filename2 = "/etc/example_ord1_conf2_%s_%s" % \
                     (node.hostname, pk.name)
                filename3 = "/etc/example_ord1_call1_%s_%s" % \
                     (node.hostname, pk.name)
                filename4 = "/etc/example_ord1_call2_%s_%s" % \
                     (node.hostname, pk.name)
                if pk.is_initial() or pk.is_updated():
                    log.trace.debug("EXORD1:Create task %s" % filename3)
                    log.trace.debug("EXORD1:Create task %s" % filename2)
                    log.trace.debug("EXORD1:Create task %s" % filename4)
                    log.trace.debug("EXORD1:Create task %s" % filename1)
                    tasks.append(OrderedTaskList(pk, [
                       CallbackTask(pk,
                                       "Install file %s" % filename3,
                                       self.create_file,
                                       filename3),
                       ConfigTask(node,
                                       pk,
                                       "Install file %s" % filename2,
                                       "file", filename2,
                                       ensure="present"),
                       CallbackTask(pk,
                                       "Install file %s" % filename4,
                                       self.create_file,
                                       filename4),
                       ConfigTask(node,
                                       pk,
                                       "Install file %s" % filename1,
                                       "file", filename1,
                                       ensure="present")
                    ]))
                if pk.is_updated():
                    oldname = pk.applied_properties["name"]
                    if oldname != pk.name:
                        oldfile1 = "/etc/example_ord1_conf1_%s_%s" % \
                           (node.hostname, oldname)
                        oldfile2 = "/etc/example_ord1_conf2_%s_%s" % \
                           (node.hostname, oldname)
                        oldfile3 = "/etc/example_ord1_call1_%s_%s" % \
                           (node.hostname, oldname)
                        oldfile4 = "/etc/example_ord1_call2_%s_%s" % \
                           (node.hostname, oldname)
                        log.trace.debug("EXORD1:remove old file %s" % oldfile1)
                        tasks.append(ConfigTask(node,
                                       pk,
                                       "Remove file %s" % oldfile1,
                                       "file", oldfile1,
                                       ensure="absent"))
                        log.trace.debug("EXORD1:remove old file %s" % oldfile2)
                        tasks.append(ConfigTask(node,
                                       pk,
                                       "Remove file %s" % oldfile2,
                                       "file", oldfile2,
                                       ensure="absent"))
                        log.trace.debug("EXORD1:remove old file %s" % oldfile3)
                        tasks.append(CallbackTask(pk,
                                       "Remove file %s" % oldfile3,
                                       self.delete_file,
                                       oldfile3))
                        log.trace.debug("EXORD1:remove old file %s" % oldfile4)
                        tasks.append(CallbackTask(pk,
                                       "Remove file %s" % oldfile4,
                                       self.delete_file,
                                       oldfile4))
                if pk.is_for_removal():
                    oldname = pk.applied_properties["name"]
                    oldfile1 = "/etc/example_ord1_conf1_%s_%s" % \
                           (node.hostname, oldname)
                    oldfile2 = "/etc/example_ord1_conf2_%s_%s" % \
                           (node.hostname, oldname)
                    oldfile3 = "/etc/example_ord1_call1_%s_%s" % \
                           (node.hostname, oldname)
                    oldfile4 = "/etc/example_ord1_call2_%s_%s" % \
                           (node.hostname, oldname)
                    log.trace.debug("EXORD1:remove old file %s" % oldfile1)
                    tasks.append(ConfigTask(node,
                                       pk,
                                       "Remove file %s" % oldfile1,
                                       "file", oldfile1,
                                       ensure="absent"))
                    log.trace.debug("EXORD1:remove old file %s" % oldfile2)
                    tasks.append(ConfigTask(node,
                                       pk,
                                       "Remove file %s" % oldfile2,
                                       "file", oldfile2,
                                       ensure="absent"))
                    log.trace.debug("EXORD1:remove old file %s" % oldfile3)
                    tasks.append(CallbackTask(pk,
                                       "Remove file %s" % oldfile3,
                                       self.delete_file,
                                       oldfile3))
                    log.trace.debug("EXORD1:remove old file %s" % oldfile4)
                    tasks.append(CallbackTask(pk,
                                       "Remove file %s" % oldfile4,
                                       self.delete_file,
                                       oldfile4))

        return tasks
