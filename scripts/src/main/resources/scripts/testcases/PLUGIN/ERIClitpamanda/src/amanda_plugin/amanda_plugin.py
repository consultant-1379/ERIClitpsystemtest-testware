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
from litp.core.execution_manager import ConfigTask

from litp.core.litp_logging import LitpLogger
log = LitpLogger()


class AmandaPlugin(Plugin):
    """
    LITP amanda plugin
    """

    def validate_model(self, plugin_api_context):
        """
        This method can be used to validate the model ...
        """
        errors = []
#        nodes = plugin_api_context.query("node")
#        for node in nodes:
#            if node.domain == "NOT_ALLOWED":
#                errors.append(ValidationError(
#                                item_path=node.get_vpath(),
#                                error_message="domain is cannot "
#                                "be 'NOT_ALLOWED'
#                              ))
        return errors

    def create_configuration(self, plugin_api_context):
        """
        Plugin can provide tasks based on the model ...

        """
        tasks = []

        log.trace.debug("AMANDA:Createconfig called")
        nodes = plugin_api_context.query("node")
        for node in nodes:
            pks = node.query("package-list")
            for pk in pks:
                if "AMANDA" in pk.name:
                    if pk.is_initial() or pk.is_updated():
                        log.trace.debug("AMANDA:Found %s" % node.hostname)
                        sp = node.query("storage-profile-base")
                        if len(sp) == 0:
                            log.trace.debug("AMANDA:no storage profile base")
                        else:
                            for a in sp:
                                filename = "/etc/amanda_%s_%s.txt" % \
                                   (a.storage_profile_name, node.hostname)
                                log.trace.debug("AMANDA: Found SP, %s" % \
                                   filename)
                                tasks.append(ConfigTask(node,
                                        pk,
                                       "Install file %s" % filename,
                                       "file", filename,
                                       ensure="present"))
                        sp = node.query("storage-profile")
                        if len(sp) == 0:
                            log.trace.debug("AMANDA:no storage profile")
                            break
                        for fs in sp:
                            filename = "/etc/amandasp_%s_%s.txt" % \
                                (fs.storage_profile_name, node.hostname)
                            log.trace.debug("AMANDA: Found SP, %s" % \
                                filename)
                            tasks.append(ConfigTask(node,
                                        pk,
                                       "Install file %s" % filename,
                                       "file", filename,
                                       ensure="present"))
        return tasks
