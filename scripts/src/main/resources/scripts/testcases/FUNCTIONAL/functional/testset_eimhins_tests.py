"""
module docstring
"""
from litp_generic_test import GenericTest, attr


class EimhinsTests(GenericTest):
    """
    Description:
        These tests are checking the litp mechanism for updating
        and configuring VM.
    """
    def setUp(self):
        """
        method docstring
        """
        super(EimhinsTests, self).setUp()

    def tearDown(self):
        """
        Runs after every test
        """
        self.log("info", "Finishing tests")

    @attr("eimhin")
    def test_01_eimhin(self):
        """
        Description:
            Testing new jenkins job
        Actions:
            Prints "Hello World!"
        """
        self.log("info", "Hello World!")
