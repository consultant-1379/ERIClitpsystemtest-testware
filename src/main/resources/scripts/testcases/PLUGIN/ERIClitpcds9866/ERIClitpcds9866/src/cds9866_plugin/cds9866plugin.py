from litp.core.plugin import Plugin
from litp.core.execution_manager import CallbackTask


class LITPCDS9866Plugin(Plugin):

    def get_ms_model_item(self, plugin_api_context):
        return plugin_api_context.query("ms")[0]

    def query_model(self, node):
        return node.query("test-item")

    def create_configuration(self, plugin_api_context):
        tasks = list()
        ms_ = self.get_ms_model_item(plugin_api_context)
        for test_item in self.query_model(ms_):
            task = CallbackTask(
                ms_, "Update property of item {0}".format(test_item),
                self.cb_update_property
            )
            tasks.append(task)

        return tasks

    def cb_update_property(self, plugin_api_context):
        ms_ = self.get_ms_model_item(plugin_api_context)
        for test_item in self.query_model(ms_):
            test_item.updatable = "Z.Z.Z"

    def update_model(self, plugin_api_context):
        ms_ = self.get_ms_model_item(plugin_api_context)
        for test_item in self.query_model(ms_):
            if test_item.name == "raise_exception":
                raise Exception("update model exception")
            elif test_item.name == "update_success":
                test_item.updatable = "Y.Y.Y"
            elif test_item.name == "update_not_updatable":
                test_item.not_updatable = "X.X.X"
            else:
                pass
