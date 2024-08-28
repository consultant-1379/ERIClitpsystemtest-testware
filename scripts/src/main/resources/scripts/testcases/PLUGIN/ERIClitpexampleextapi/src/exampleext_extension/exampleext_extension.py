##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.model_type import ItemType, Property, PropertyType
from litp.core.extension import ModelExtension
from litp.core.validators import PropertyValidator, ValidationError
from litp.core.litp_logging import LitpLogger

log = LitpLogger()


class RubbishValidator(PropertyValidator):
    """
    Exampleext Item validator
    """

    def validate(self, _property_value):
        if len(_property_value) > 10:
            return ValidationError(error_message="larger than 10")
        else:
            return None


class ExampleextExtension(ModelExtension):
    """
    Exampleext Model Extension
    """

    def define_property_types(self):
        property_types = []
        property_types.append(PropertyType("example_byte_size",
                                           regex="^[1-9][0-9]{0,}B$"))
        rubValidators = [RubbishValidator()]
        property_types.append(PropertyType("rubbish",
                                           validators=rubValidators))
        return property_types

    def define_item_types(self):
        item_types = []
        item_types.append(
            #ItemType("example-item-_./",
            ItemType("example-item",
                     item_description="Example item type",
                     extend_item="software-item",
                     name=Property("basic_string",
                                   prop_description="Name of item",
                                   required=True),
                     size=Property("example_byte_size",
                                   prop_description="Size of item",
                                   default="10B"),
                     rubbish=Property("rubbish",
                                   prop_description="Contents",
                                   default=""),
                     deprecat=Property("togo",
                                   prop_description="To be removed",
                                   deprecated=True),
                     updatable=Property("basic_string",
                                   prop_description="Name of item",
                                   updatable_plugin=True,
                                   updatable_rest=True),
                     updatableconst=Property("basic_string",
                                   prop_description="Name of item",
                                   updatable_plugin=True,
                                   updatable_rest=True,
                                   default="upconst"),
                     readonly=Property("basic_string",
                                   prop_description="Name of item",
                                   updatable_plugin=True,
                                   updatable_rest=False),
                     constant=Property("basic_string",
                                   prop_description="Name of item",
                                   updatable_plugin=False,
                                   updatable_rest=False, default="cons"),
                     restonly=Property("basic_string",
                                   prop_description="Name of item",
                                   updatable_plugin=False,
                                   updatable_rest=True),
                     )
             )
        return item_types
