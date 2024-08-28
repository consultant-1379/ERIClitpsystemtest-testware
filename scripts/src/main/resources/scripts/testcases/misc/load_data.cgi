#!/usr/bin/python
import sys
import cgi
import os
import xml.dom.minidom
import re

class LoadData():

    def __init__(self):
 	"""
        Initialise variables
        """
	self.new_passing_testcases = list()

    def load_data(self):
        """
        Saves data to a text file. This will will be used to reload the page
        when the new table is generated.
        """

        file_handle = open('fail_history.txt', 'r')
        file_contents = file_handle.read()
        file_handle.close()

        file_list = file_contents.split("###")

        print file_list
        for failure in file_list:
            ##Catch whitespace or /n
	    if len(failure.strip()) > 5:
            	self.write_to_page(failure)


	#if self.new_passing_testcases:    
		#for tc in self.new_passing_testcases:
	#file_list = file_contents.split("\n")
	


    def write_to_page(self, data_to_write):
        """
        Writes data directly to the table cell in the html page.

        Args:

        data_to_write (str): A CSV format line with the cell id
                             and comments seperated by a ','
        """
        cell_id = data_to_write.split(",", 1)[0]
        value = data_to_write.split(",", 1)[1]
        ##READ CURRENT FILE
        file_handle = open('results_history.html', 'r')

        file_contents = file_handle.read()

        file_handle.close()

        file_list = file_contents.split("\n")

        list_index = 0
	##Keep count if we added to webpage or not
        updated_cell = False
        for line in file_list:
            if cell_id in line:
                line = re.sub(r'>.*</td>', ">{0}</td>".format(value), line)
                file_list[list_index] = line
		updated_cell = True
                break
            list_index += 1

	##If we updated cell output webpage otherwise we should remove it from log file of failed tests
	if updated_cell:
        	new_file_contents = "\n".join(file_list)

        	#OUTPUT TO NEW FILE VERSION
        	file_handle_write = open('results_history.html', 'w')
        	file_handle_write.write(new_file_contents)
        	file_handle_write.close()
	else:
		self.new_passing_testcases.append(cell_id)
	


LoadData().load_data()
