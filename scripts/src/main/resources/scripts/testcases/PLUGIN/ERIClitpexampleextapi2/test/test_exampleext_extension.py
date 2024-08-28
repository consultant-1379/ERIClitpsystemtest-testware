##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################


import unittest
from exampleext_extension.exampleext_extension import ExampleextExtension


class TestExampleextExtension(unittest.TestCase):

    def setUp(self):
        self.ext = ExampleextExtension()

    def test_property_types_registered(self):
        prop_types_expected = ['example_byte_size','rubbish']
        prop_types = [pt.property_type_id for pt in
                      self.ext.define_property_types()]
        self.assertEquals(prop_types_expected, prop_types)

    def test_item_types_registered(self):
        item_types_expected = ['example-item', 'example-item-child',
                               'example-lower-child']
        item_types = [it.item_type_id for it in
                      self.ext.define_item_types()]
        self.assertEquals(item_types_expected, item_types)

if __name__ == '__main__':
    unittest.main()
