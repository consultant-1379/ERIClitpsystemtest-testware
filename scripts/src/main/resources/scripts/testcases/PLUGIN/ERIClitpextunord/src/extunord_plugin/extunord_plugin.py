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
from litp.core.validators import ValidationError
from litp.core.execution_manager import ConfigTask, CallbackTask
import datetime
import os

from litp.core.litp_logging import LitpLogger
log = LitpLogger()


class ExtUnOrdPlugin(Plugin):
    """
    LITP extunord plugin
    """

    def validate_model(self, plugin_api_context):
        """
        This method can be used to validate the model ...

        .. warning::
          Please provide a summary of the model validation performed by
          extunord here
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

    def create_file(self, callback_api, *args, **kwargs):
        """
        This method will create a file, filename being arg[0]
        """
        log.trace.info("EXUNORD1:create_file callback called")
        filename = args[0]
        log.trace.info("EXUNORD1:This should create file %s" % filename)
        file = open(filename, 'w')
        file.write(datetime.datetime.now().ctime())
        file.close()

    def delete_file(self, callback_api, *args, **kwargs):
        """
        This method will delete a file, filename being arg[0]
        """
        log.trace.info("EXUNORD1:delete_file callback called")
        filename = args[0]
        log.trace.info("EXUNORD1:This should delete file %s" % filename)
        try:
            os.remove(filename)
        except OSError as e:
            # do nothing we don't care
            pass

    def create_configuration(self, plugin_api_context):
        """
        Plugin can provide tasks based on the model ...

        *Example CLI for this plugin:*

        .. code-block:: bash

          # TODO Please provide an example CLI snippet for plugin extunord
          # here
        """
        tasks = []

        nodes = plugin_api_context.query("node")
        for node in nodes:
            pklists = node.query("package-list")
            for pk in pklists:
                if "UNORD" not in pk.name:
                    continue
                filename1 = "/etc/example_unord1_conf1_%s_%s" % \
                     (node.hostname, pk.name)
                filename2 = "/etc/example_unord1_call1_%s_%s" % \
                     (node.hostname, pk.name)
                if pk.is_initial() or pk.is_updated():
                    log.trace.debug("EXUNORD1:Create task %s" % filename2)
                    tasks.append(CallbackTask(pk,
                                       "Install file %s" % filename2,
                                       self.create_file,
                                       filename2))
                    log.trace.debug("EXUNORD1:Create task %s" % filename1)
                    tasks.append(ConfigTask(node,
                                       pk,
                                       "Install file %s" % filename1,
                                       "file", filename1,
                                       ensure="present"))
                if pk.is_updated():
                    oldname = pk.applied_properties["name"]
                    if oldname != pk.name:
                        oldfile1 = "/etc/example_unord1_conf1_%s_%s" % \
                           (node.hostname, oldname)
                        oldfile2 = "/etc/example_unord1_call1_%s_%s" % \
                           (node.hostname, oldname)
                        log.trace.debug("EXUNORD1:remove old %s" % oldfile1)
                        tasks.append(ConfigTask(node,
                                       pk,
                                       "Remove file %s" % oldfile1,
                                       "file", oldfile1,
                                       ensure="absent"))
                        log.trace.debug("EXUNORD1:remove old %s" % oldfile2)
                        tasks.append(CallbackTask(pk,
                                       "Remove file %s" % oldfile2,
                                       self.delete_file,
                                       oldfile2))
                if pk.is_for_removal():
                    oldname = pk.applied_properties["name"]
                    oldfile1 = "/etc/example_unord1_conf1_%s_%s" % \
                           (node.hostname, oldname)
                    oldfile2 = "/etc/example_unord1_call1_%s_%s" % \
                           (node.hostname, oldname)
                    log.trace.debug("EXUNORD1:remove old file %s" % oldfile1)
                    tasks.append(ConfigTask(node,
                                       pk,
                                       "Remove file %s" % oldfile1,
                                       "file", oldfile1,
                                       ensure="absent"))
                    log.trace.debug("EXUNORD1:remove old file %s" % oldfile2)
                    tasks.append(CallbackTask(pk,
                                       "Remove file %s" % oldfile2,
                                       self.delete_file,
                                       oldfile2))

        return tasks
