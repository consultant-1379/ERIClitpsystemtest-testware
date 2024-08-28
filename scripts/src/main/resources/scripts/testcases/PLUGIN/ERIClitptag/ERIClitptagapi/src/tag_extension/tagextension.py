from litp.core.model_type import ItemType
from litp.core.model_type import PropertyType
from litp.core.model_type import Property
from litp.core.extension import ModelExtension

from litp.core.litp_logging import LitpLogger
log = LitpLogger()


class TagExtension(ModelExtension):

    def define_property_types(self):
        #
        # define valid property type values for tag-model-item
        #

        return [
            # valid property values for deployment_tag regex
            PropertyType(
                'deploy_tag_name_string',
                regex='^(ms|boot|node|cluster|pre_node_cluster)$'
            ),
            # valid property values for snapshot_tag regex
            PropertyType(
                'snap_tag_name_string',
                regex='^(validation|pre_op|ms_lvm|node_lvm|node_vxvm|nas|san|'\
                      'post_op|prep_puppet|prep_vcs|node_reboot|' \
                      'node_power_off|sanitisation|node_power_on|' \
                      'node_post_on|ms_reboot)$'
            )
        ]

    def define_item_types(self):
        #
        # register tag-model-item with litp model
        #

        return [
            ItemType(
                'tag-model-item',
                extend_item='software-item',
                item_description='deployment plan(s) item type',
                deployment_tag=Property(
                    'deploy_tag_name_string',
                    required=True
                ),
                snapshot_tag=Property(
                    'snap_tag_name_string',
                    required=True
                ),
                cb_method_name=Property(
                    'basic_string',
                    default='cb_do_something',
                    required=True
                ),
                ordered=Property(
                    'basic_boolean',
                    default='false',
                    required=True
                ),
                defaults=Property(
                    'basic_boolean',
                    default='true',
                    required=True
                ),
                unique_id=Property(
                    'any_string',
                    required=False,
                    updatable_rest=False,
                    updatable_plugin=True
                )
            )
        ]
