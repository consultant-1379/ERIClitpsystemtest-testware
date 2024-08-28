import urllib2
import os

class TrackFailures(object):

    def __init__(self, iso_ver, tarball_ver, pro_1=None, pro_2=None, pro_3=None, curr_sprint=None, non_revert=None, cli=None, network=None, network_non_revert=None ):
     
        self.filename= "results_history.html"
	self.fail_dict = dict()
        self.fail_count = dict()

        self.iso_value = iso_ver
        self.tarball_ver = tarball_ver
        self.tabl_start_str = '<table border="4" width="1400" bordercolor="3399FF">'
        self.table_end_str = '</table>'
        self.report_url = "NULL"
	self.p1_num = pro_1
	self.p2_num = pro_2
	self.p3_num = pro_3
	self.pcurr_num = curr_sprint
	self.pnonre_num = non_revert
	self.pcli_num = cli
	self.pnet_num = network
	self.pnetnon_num = network_non_revert

    def __output_header(self):
        self.__output_to_file('<head>', False)
        self.__output_to_file('<script type="text/javascript" src="http://code.jquery.com/jquery-1.8.3.min.js"></script>', False)
        self.__output_to_file('<script type="text/javascript" src="script.js"></script>', False)
        self.__output_to_file('</head>', False)


    def __output_to_file(self, text_to_write, add_break=True):
        with open(self.filename, "a") as myfile:
            myfile.write(text_to_write)
            if add_break:
                myfile.write("<br>")
                myfile.write("<br>")


    def __output_title(self, title):
        self.__output_to_file("<b>{0}</b>".format(title))

    #Generates email
    def generate_failure_history(self):
        #delete the current file
        if os.path.isfile(self.filename):
            os.remove(self.filename)
        self.__output_to_file("<html>", False)
        self.__output_header()
        self.__output_title("TEST FAILURE TRACKING")
        self.__output_to_file("The below failures are for ISO {0} with tarball {1}".format(self.iso_value, self.tarball_ver))
        self.__output_to_file("Double click on the relevent 'Explanation for failure' cell to add comments. This table will be generated after each nightly run.")
        self.__output_to_file("Only tests which failed the most recent run (with the ISO noted above) will be displayed in these tables. All comments are saved until the test successfully passes.")

	if self.p1_num:
        	self.__output_failure_history(self.p1_num, "2_1_IT_Priority_1_Multiblade", "MULTIBLADE PRIORITY 1 REGRESSION", "20")
	if self.p2_num:
        	self.__output_failure_history(self.p2_num, "2_1_IT_Priority_2_Multiblade", "MULTIBLADE PRIORITY 2 REGRESSION", "20")

	if self.p3_num:
		self.__output_failure_history(self.p3_num, "2_1_IT_Priority_3_Multiblade", "MULTIBLADE PRIORITY 3 REGRESSION", "1")

	if self.pcurr_num:
		self.__output_failure_history(self.pcurr_num, "2_1_current_sprint_multiblade", "MULTIBLADE CURRENT SPRINT", "20")

	if self.pnonre_num:
		self.__output_failure_history(self.pnonre_num, "non_revertable_system_tests_mb", "MULTIBLADE NON-REVERTIBLE", "20")

	if self.pcli_num:
		self.__output_failure_history(self.pcli_num, "ERIClitpcli", "CDB CLI TESTS", "10", True)

	if self.pnet_num:
		self.__output_failure_history(self.pnet_num, "ERIClitpnetwork", "CDB NETWORK TESTS", "10", True)

	if self.pnetnon_num:
		self.__output_failure_history(self.pnetnon_num, "ERIClitpnetwork-non-revert", "CDB NETWORK NON-REVERTIBLE TESTS", "10", True)

        self.__output_to_file("</html>", False)

        


    def __output_failure_history(self, job_num, job_name, job_title, history_length, cdb=False):
	"""
	Args:
	job_num (str): The most recent job to run.
	job_name (str): The name of the jenkins job. (this is used to construct the web link)
	job_title (str): The title you want to be displayed on the webpage.
	history_length (str): How many jobs do you want to count back when counting how long a test has been failing.
	cdb (bool): Set to True if this uses the CDB branch job.
	"""
        self.fail_dict = dict()
        self.fail_count = dict()
        self.__generate_fail_dict(job_name, job_num, history_length, cdb)
	self.__count_failures()
        self.__output_title(job_title)
        self.__output_report_link(job_name, job_num, cdb)
        self.__output_failures()
        self.__output_to_file("\n")

    def __output_report_link(self, job_name, job_num, cdb=False):
        if cdb:
            report_url = "http://10.44.86.30/jenkins/view/2.1_IT_modules/job/{0}/{1}/artifact/cdb_framework_slaves/2.1_CI1/results/test_report.html".format(job_name, job_num)
        else:
            report_url = "http://10.44.86.30/jenkins/view/2_1_IT_Priority/job/{0}/{1}/artifact/tmp2.1_CI1/src/test_runner/test_result/test_report.html".format(job_name, job_num)

        self.__output_to_file('<a href="{0}"> Click here to see the test report</a>'.format(report_url))



    def __generate_fail_dict(self, job_name, job_num, history_length, cdb=False):
	history_length_int = int(history_length)
	job_num_int = int(job_num)
        fail_dict = dict()
        try_new_url_type = False

	for index in range(0, history_length_int):
            #If CDB url type
            if cdb:
                fail_url = "http://10.44.86.30/jenkins/view/2.1_IT_modules/job/{0}/{1}/artifact/cdb_framework_slaves/2.1_CI1/results/test_failure_file.txt".format(job_name, str(job_num_int))
                try:
                    page_contents = urllib2.urlopen(fail_url).read()
                except Exception, e:
                    job_num_int -= 1
                    continue
            #If normal regression job
            else:
                try_new_url_type = False
		fail_url = "http://10.44.86.30/jenkins/view/2_1_IT_Priority/job/{0}/{1}/artifact/tmpITMB4/src/test_runner/test_result/test_failure_file.txt".format(job_name, str(job_num_int))

                try:
                    page_contents = urllib2.urlopen(fail_url).read()
                except Exception, e:
                    try_new_url_type = True

                if try_new_url_type:
                    try:
                        fail_url = "http://10.44.86.30/jenkins/view/2_1_IT_Priority/job/{0}/{1}/artifact/tmp2.1_CI1/src/test_runner/test_result/test_failure_file.txt".format(job_name, str(job_num_int))
                        page_contents = urllib2.urlopen(fail_url).read()
                    except Exception, e:
                        job_num_int -= 1
                        continue

            self.fail_dict[str(job_num_int)] = page_contents.split("\n")
            #Delete the last element as this is empty return charachter
            del self.fail_dict[str(job_num_int)][-1]
            job_num_int -= 1



    def __get_test_name(self, test_entry):
        test_parts = test_entry.split("\t")
        if len(test_parts) < 3:
            test_parts = test_entry.split()

        test_name = "{0}--{1}--{2}".format(test_parts[0], test_parts[1],
                                         test_parts[2])

        return test_name

    def __count_failures(self):
        #Sort job numbers in reverse order to get most recent first
        job_nums = self.fail_dict.keys()
        job_nums_int = map(int, job_nums)
        job_nums_int.sort(reverse=True)
        job_nums = map(str, job_nums_int)

        #Populate dict first with current failures
        for test_failure in self.fail_dict[job_nums[0]]:
            self.fail_count[self.__get_test_name(test_failure)] = 1

        #Remove 1ST job as we have already looked at this
        job_nums = job_nums[1:]

        #For each test job
        for job in job_nums:
            #Loop through all tests

            for test in self.fail_count.keys():
                consecutive_fail = False

                for test_failure in self.fail_dict[job]:
                    key_check = self.__get_test_name(test_failure)

                    if test == key_check and type(self.fail_count[key_check]) is int:
                        consecutive_fail = True
                        self.fail_count[key_check] += 1

                if not consecutive_fail:
                    self.fail_count[test] = str(self.fail_count[test])

    def __output_table_header(self):
        self.__output_to_file('<tr>\n', False)
        self.__output_to_file('<col width="10%">', False)
        self.__output_to_file('<col width="15%">', False)
        self.__output_to_file('<col width="25%">', False)
        self.__output_to_file('<col width="10%">', False)
        self.__output_to_file('<col width="40%">', False)
        self.__output_to_file("<th>{0}</th>\n".format("<b>Module</b>"), False)
        self.__output_to_file("<th>{0}</th>\n".format("<b>Filename</b>"), False)
        self.__output_to_file("<th>{0}</th>\n".format("<b>Test</b>"), False)
        self.__output_to_file("<th>{0}</th>\n".format("<b>Number of runs this has been failing</b>"), False)
        self.__output_to_file("<th>{0}</th>\n".format("<b>Explanation for failure</b>"), False)
        self.__output_to_file('</tr>\n', False)

    def __output_failures(self):
        self.__output_to_file(self.tabl_start_str, False)
        self.__output_table_header()

        #Do in alphabetical order
        fail_keys = self.fail_count.keys()
        fail_keys.sort()

        for failure in fail_keys:
            self.__output_to_file('<tr>\n', False)
            
            output_parts = failure.split("--")

            for item in output_parts:
                self.__output_to_file("<td>{0}</td>\n".format(item), False)

            if int(self.fail_count[failure]) > 8:
                text_line = '<td><font color="red"><b>{0}</b></font></td>\n'.format(self.fail_count[failure])
                self.__output_to_file(text_line,
                                    False)
            else:
                self.__output_to_file("<td>{0}</td>\n".format(self.fail_count[failure]), 
                                    False)

            cell_id = failure
            self.__output_to_file('<td id="{0}" class="selectedCol"></td>\n'.format(cell_id), False)
            self.__output_to_file('</tr>\n', False)

        self.__output_to_file(self.table_end_str, False)
