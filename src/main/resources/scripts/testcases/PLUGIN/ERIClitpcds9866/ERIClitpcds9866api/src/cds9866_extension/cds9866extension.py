from litp.core.extension import ModelExtension
from litp.core.model_type import ItemType
from litp.core.model_type import Property


class LITPCDS9866Extension(ModelExtension):

    def define_item_types(self):
        return [
            ItemType(
                "test-item",
                extend_item="software-item",
                name=Property("any_string"),
                updatable=Property("any_string", updatable_plugin=True),
                not_updatable=Property("any_string")
            ),
        ]
