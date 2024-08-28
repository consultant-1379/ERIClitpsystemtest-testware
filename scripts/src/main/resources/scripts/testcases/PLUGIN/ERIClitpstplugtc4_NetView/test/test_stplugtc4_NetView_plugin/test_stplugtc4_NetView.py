##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from stplugtc4_NetView_plugin.stplugtc4_NetView_plugin import STplugtc4_NetViewPlugin

from litp.extensions.core_extension import CoreExtension
from litp.core.model_manager import ModelManager
from litp.core.plugin_manager import PluginManager
from litp.core.model_type import ItemType, Child

import unittest


class TestSTplugtc4_NetViewPlugin(unittest.TestCase):

    def setUp(self):
        """
        Construct a model, sufficient for test cases
        that you wish to implement in this suite.
        """
        self.model = ModelManager()
        self.plugin_manager = PluginManager(self.model)
        # Use add_property_types to add property types defined in 
        # model extenstions
        # For example, from CoreExtensions (recommended)
        self.plugin_manager.add_property_types(
            CoreExtension().define_property_types())
            
        # Use add_item_types to add item types defined in 
        # model extensions
        # For example, from CoreExtensions
        self.plugin_manager.add_item_types(
            CoreExtension().define_item_types())
            
        # Add default minimal model (which creates '/' root item)        
        self.plugin_manager.add_default_model()

        # Instantiate your plugin and register with PluginManager
        self.plugin = STplugtc4_NetViewPlugin()
        self.plugin_manager.add_plugin('TestPlugin', 'some.test.plugin',
                                       '1.0.0', self.plugin)

        # Additionally add new items to model, common to all test cases
        self.model.item_types.pop('root')
        self.model.register_item_type(ItemType("root",
            node1=Child("node"),
            node2=Child("node"),
        ))

    def setup_model(self):
        # Use ModelManager.crete_item and ModelManager.create_link
        # to create and reference (i.e.. link) items in the model.
        # These correspond to CLI/REST verbs to create or link
        # items.
        self.node1 = self.model.create_item("node", "/node1",
                                                 hostname="node1")
        self.node2 = self.model.create_item("node", "/node2",
                                                 hostname="special")

    def query(self, item_type=None, **kwargs):
        # Use ModelManager.query to find items in the model
        # properties to match desired item are passed as kwargs.
        # The use of this method is not required, but helps
        # plugin developer mimic the run-time environment 
        # where plugin sees QueryItem-s.
        return self.model.query(item_type, **kwargs)

    def test_validate_model(self):
        self.setup_model()
        # Invoke plugin's methods to run test cases 
        # and assert expected output.
        errors = self.plugin.validate_model(self)
        self.assertEqual(0, len(errors))

    def test_create_configuration(self):
        self.setup_model()
        # Invoke plugin's methods to run test cases 
        # and assert expected output.
        tasks = self.plugin.create_configuration(self)
        self.assertEqual(0, len(tasks))
        
