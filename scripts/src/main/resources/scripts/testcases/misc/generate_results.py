import urllib2
import os

class GenerateResults(object):

    def __init__(self, iso_ver, tarball_ver, pro_1=None, pro_2=None, pro_3=None, curr_sprint=None, non_revert=None, cli=None, network=None, network_non_revert=None ):
        self.filename= "results.html"
        self.current_report_url = None
        self.current_fail_url = None
        ##CHANGE ME - UPDATE ISO NUMBER + TARBALL IF CHANGED
        self.iso_value = iso_ver
        self.tarball_ver = tarball_ver
	#Job numbers
	self.p1_num = pro_1
	self.p2_num = pro_2
	self.p3_num = pro_3
	self.pcurr_num = curr_sprint
	self.pnonre_num = non_revert
	self.pcli_num = cli
	self.pnet_num = network
	self.pnetnon_num = network_non_revert

        self.results_url = "http://10.44.86.30/jan/tmp/results_history.html" #http://10.44.86.30/isolist/results/results_history.html"

    def generate_email(self):
        """
        Email is generated here.
        """
        #delete the current file
        if os.path.isfile(self.filename):
            os.remove(self.filename)
        self.output_to_file("<html>", False)
        self.output_to_file("Hi All")
        self.output_to_file("Results for ISO {0} with tarball {1} are below, please investigate failures:".format(self.iso_value, self.tarball_ver))
        self.output_to_file("Please add any notes for failures to the page here: {0}".format(self.results_url))
        ##CHANGE ME - COMMENT OUT ANY JOBS NOT RUN + UPDATE JOB NUMBER
	if self.p1_num:
        #	self.output_section(self.p1_num, "2_1_IT_Priority_1_Multiblade", "MULTIBLADE PRIORITY 1 REGRESSION")
		self.output_section(self.p1_num, "2_1_ST_Functional", "ST_Functional TESTS")
	#if self.p2_num:
        #	self.output_section(self.p2_num, "2_1_IT_Priority_2_Multiblade", "MULTIBLADE PRIORITY 2 REGRESSION")

	#if self.p3_num:
	#	self.output_section(self.p3_num, "2_1_IT_Priority_3_Multiblade", "MULTIBLADE PRIORITY 3 REGRESSION")

	#if self.pcurr_num:
	#	self.output_section(self.pcurr_num, "2_1_current_sprint_multiblade", "MULTIBLADE CURRENT SPRINT")

	#if self.pnonre_num:
	#	self.output_section(self.pnonre_num, "non_revertable_system_tests_mb", "MULTIBLADE NON-REVERTIBLE")

	#if self.pcli_num:
	#	self.output_section(self.pcli_num, "ERIClitpcli", "CDB CLI TESTS", True)

	#if self.pnet_num:
	#	self.output_section(self.pnet_num, "ERIClitpnetwork", "CDB NETWORK TESTS", True)

	#if self.pnetnon_num:
	#	self.output_section(self.pnetnon_num, "ERIClitpnetwork-non-revert", "CDB NETWORK NON-REVERTIBLE TESTS", True)
	

        self.output_to_file("Regards")
        self.output_to_file("    The CI Team")
        self.output_to_file("</html>", False)

    def output_section(self, job_num, job_name, job_title, cdb=False):
        self.generate_urls(job_name, job_num, cdb)
	print self.current_report_url
	print self.current_fail_url
        self.output_title(job_title)
        self.output_to_file("{0}".format(self.current_report_url))
        self.output_to_file(self.generate_table(cdb))
        self.generate_failures()

    def generate_table(self, cdb_job=False):
        """
        Extracts the results table from the webpage
        """
        if cdb_job:
            tabl_start_str = '<table class="myTable" border="8" width="1300" align="center">'
            table_end_str = '</table>'
            results_table = None
            page_contents = urllib2.urlopen(self.current_report_url).read()
            page_table = page_contents.split(tabl_start_str)[1].split(table_end_str)[0]
        else:
            tabl_start_str = '<table border="10" width="1000" align="center" bordercolor="3399FF">'
            table_end_str = '</table>'
            results_table = None
            page_contents = urllib2.urlopen(self.current_report_url).read()
            page_table = page_contents.split(tabl_start_str)[2].split(table_end_str)[0]

        page_list = page_table.split("/n")
        page_list.append(table_end_str)
        page_list.insert(0, tabl_start_str)

        page = "\n".join(page_list)

        return page

    def output_to_file(self, text_to_write, add_break=True):
        with open(self.filename, "a") as myfile:
            myfile.write(text_to_write)
            if add_break:
                myfile.write("<br>")
                myfile.write("<br>")

    def generate_failures(self):
        page_contents = urllib2.urlopen(self.current_fail_url).read()
        page_list = page_contents.split("\n")
        for item in page_list:
            self.output_to_file(item, False)
            self.output_to_file("<br>", False)


    def output_title(self, title):
        self.output_to_file("<b>{0}</b>".format(title))

    def generate_urls(self, job_name, job_num, cdb_job=False):
	if cdb_job:
            self.current_report_url = "http://10.44.86.30/jenkins/view/2.1_IT_modules/job/{0}/{1}/artifact/cdb_framework_slaves/2.1_CI1/results/test_report.html".format(job_name, job_num)
            self.current_fail_url = "http://10.44.86.30/jenkins/view/2.1_IT_modules/job/{0}/{1}/artifact/cdb_framework_slaves/2.1_CI1/results/test_failure_file.txt".format(job_name, job_num)
	else:
            #self.current_report_url = "http://10.44.86.30/jenkins/view/2_1_IT_Priority/job/{0}/{1}/artifact/tmp2.1_CI1/src/test_runner/test_result/test_report.html".format(job_name, job_num)
            #self.current_fail_url = "http://10.44.86.30/jenkins/view/2_1_IT_Priority/job/{0}/{1}/artifact/tmp2.1_CI1/src/test_runner/test_result/test_failure_file.txt".format(job_name, job_num)
            self.current_fail_url = "http://10.44.86.30/jenkins/view/2_1_ST/job/{0}/{1}/artifact/tmpSTMB/src/test_runner/test_result/test_failure_file.txt".format(job_name, job_num)
            self.current_report_url = "http://10.44.86.30/jenkins/view/2_1_ST/job/{0}/{1}/artifact/tmpSTMB/src/test_runner/test_result/test_report.html".format(job_name, job_num)
