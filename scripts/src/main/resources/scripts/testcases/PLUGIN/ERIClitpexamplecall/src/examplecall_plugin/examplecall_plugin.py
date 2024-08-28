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

from litp.core.litp_logging import LitpLogger
log = LitpLogger()


class ExamplecallPlugin(Plugin):
    """
    LITP examplecall plugin
    """

    def validate_model(self, plugin_api_context):
        """
        This method can be used to validate the model ...

        .. warning::
          Please provide a summary of the model validation performed by
          examplecall here
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
        This method will create a file, getting name from  ...
        """
        #Call an rpc command to check status of service
        nodes = []
        nodes.append(kwargs["arg1"])
        nodes.append("rubbish")
        result = callback_api.rpc_command(nodes, kwargs["arg3"],
                                                 kwargs["arg4"],
                                                {kwargs["arg5"]: "crond"})
        noderesult = result[nodes[0]]
        node2result = result[nodes[1]]

        # now write lines to file
        log.trace.info("EXCALL:create_file callback called")
        filename = args[0]
        log.trace.info("EXCALL:This should create file %s", filename)
        myfile = open(filename, 'w')
        for key, value in kwargs.iteritems():
            myfile.write("%s,%s\n" % (key, value))
        # Now write result from status lookup
        myfile.write("errors: %s\n" % noderesult["errors"])
        myfile.write("data: %s\n" % repr(noderesult["data"]))
        myfile.write("2 errors: %s\n" % node2result["errors"])
        myfile.write("2 data: %s\n" % repr(node2result["data"]))
        myfile.close()

    def create_configuration(self, plugin_api_context):
        """
        Plugin can provide tasks based on the model ...

        *Example CLI for this plugin:*

        .. code-block:: bash

          # TODO Please provide an example CLI snippet for plugin examplecall
          # here
        """
        tasks = []

        log.trace.debug("EXCALL:Createconfig called")
        nodes = plugin_api_context.query("node")
        for node in nodes:
            log.trace.debug("EXCALL:Found node %s" % node.hostname)
            pklists = node.query("package-list")
            for pk in pklists:
                if "EXCALL" in pk.name:
                    filename = "/etc/examplecall_%s_%s.txt" % \
                        (node.hostname, pk.name)
                    log.trace.debug("EXCALL: Found node, %s" % filename)
                    if pk.is_initial() or pk.is_updated():
                        log.trace.debug("EXCALL:Create task for %s" % filename)
                        service = 'service'
                        action = 'status'
                        param = 'service'
                        if "CUSTOM" in pk.name:
                            # Then use custom mcollective agent
                            service = 'exampleagent'
                            action = 'serve_as_example'
                            param = 'echo_string'
                        tasks.append(CallbackTask(pk,
                                       "Install file %s" % filename,
                                       self.create_file,
                                       filename,
                                       arg1=node.hostname, arg2='rubbish',
                                       arg3=service, arg4=action, arg5=param))
        return tasks
