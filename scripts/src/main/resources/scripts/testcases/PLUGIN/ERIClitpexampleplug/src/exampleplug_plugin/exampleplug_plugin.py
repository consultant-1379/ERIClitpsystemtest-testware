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
from litp.core.task import OrderedTaskList, CallbackTask
import time

from litp.core.litp_logging import LitpLogger
log = LitpLogger()


class ExamplePlugPlugin(Plugin):
    """
    LITP exampleplug plugin
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

#pylint: disable=W0613
    def create_file(self, callback_api, *args, **kwargs):
        """
        This method will create a file, filename being arg[0] plus value of
        example-items updatable value
        args[0] is filename
        args[1] is name of example-item to query
        """
        log.trace.info("EXPLUG:create_file callback called")
        items = callback_api.query("example-item", name=args[1])
        val = ""
        for a in items:
            log.trace.debug("EXPLUG: Found example-item %s,%s" % \
                   (a.name, a.updatable))
            # Update child if CHILD in name, else update upper item
            if not "child" in args[1]:
                # Update example item
                if a.updatable:
                    val = a.updatable
                a.updatable = "%s1" % a.updatable
            else:
                # If has a child then also try and update that
                children = a.query("example-item-child")
                for child in children:
                    lowers = child.query("example-lower-child")
                    for lower in lowers:
                        if lower.updatable:
                            val = lower.updatable
                        lower.updatable = "%s1" % lower.updatable
        filename = "%s.%s" % (args[0], val)
        time.sleep(30)
        log.trace.info("EXPLUG:This should create file %s" % filename)
        lfile = open(filename, 'w')
        lfile.write(val)
        lfile.close()

    def create_link_file(self, callback_api, *args, **kwargs):
        """
        This method will attempt to update linked item, which is
        expected to fail
        example-items updatable value
        args[0] is filename
        args[1] is name of example-item to query
        """
        log.trace.info("EXPLUG:create_link_file callback called")
        nodes = callback_api.query("node")
        for n in nodes:
            val = ""
            items = n.query("example-item", name=args[1])
            for a in items:
                log.trace.debug("EXPLUG: Found example-item %s,%s" % \
                   (a.name, a.updatable))
                # Update child if CHILD in name, else update upper item
                if not "child" in args[1]:
                    if a.updatable:
                        val = a.updatable
                    a.updatable = "%s1" % a.updatable
                else:
                # If has a child then also try and update that
                    children = a.query("example-item-child")
                    for child in children:
                        lowers = child.query("example-lower-child")
                        for lower in lowers:
                            if lower.updatable:
                                val = lower.updatable
                            lower.updatable = "%s1" % lower.updatable

        filename = "%s.%s" % (args[0], val)
        # NEVER expect to get here as update should fail as through link
        log.trace.info("EXPLUG:This should create file %s" % filename)
        lfile = open(filename, 'w')
        lfile.write(val)
        lfile.close()

    def create_configuration(self, plugin_api_context):
        """
        Plugin can provide tasks based on the model ...

        """
        tasks = []

        log.trace.debug("EXPLUG:Createconfig called")
        nodes = plugin_api_context.query("node")
        for node in nodes:
            log.trace.debug("EXPLUG:Found node %s" % node.hostname)
            items = plugin_api_context.query("example-item")
            if len(items) == 0:
                log.trace.debug("EXPLUG:Found no example item")
            else:
                for a in items:
                    filename = "/etc/exampleplug_%s_%s_%s.txt" % \
                       (a.name, a.size, a.rubbish)
                    log.trace.debug("EXPLUG: Found item, %s" % filename)
                    if a.is_initial() or a.is_updated():
                        if "call" in a.name:
                            log.trace.debug("EXPLUG: Ordered callbacks \
                                      for %s" % filename)
                            tasks.append(OrderedTaskList(node, [
                                CallbackTask(node,
                                       "Install first file %s" % filename,
                                       self.create_file,
                                       filename, a.name),
                                CallbackTask(node,
                                       "Install second file %s" % filename,
                                       self.create_file,
                                       filename, a.name)]))
                        elif "link" in a.name:
                            log.trace.debug("EXPLUG: Ordered link callbacks \
                                      for %s" % filename)
                            tasks.append(OrderedTaskList(node, [
                                CallbackTask(node,
                                     "Install first link file %s" % filename,
                                     self.create_link_file,
                                     filename, a.name),
                                CallbackTask(node,
                                     "Install second link file %s" % filename,
                                     self.create_link_file,
                                     filename, a.name)]))
                        else:
                            log.trace.debug("EXPLUG:Create task for %s" % \
                                      filename)
                            tasks.append(ConfigTask(node,
                                        node,
                                       "Install file %s" % filename,
                                       "file", filename,
                                       ensure="present"))
        return tasks
