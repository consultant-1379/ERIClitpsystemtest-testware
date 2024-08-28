import sys
#sys.path.insert(0, '/home/david.appleton/git/test/miscUtilities/ci_tools/generate_results_email')
#sys.path.insert(0, '/home/david.appleton/git/test/miscUtilities/ci_tools/track_failures')

from track_failures import TrackFailures
from generate_results import GenerateResults

iso_version = "2.7.18"
tarball_version = "1.0.38"
###JOB numbers
pro1_job_num = "266"
pro2_job_num = "108"
pro3_job_num = "3"
currspr_job_num = None
nonrevert_job_num = None

cli_job_num = None
network_job_num = None
network_nonr_job_num = None

print "Generating Fail history page"
fail = TrackFailures(iso_version, tarball_version, pro1_job_num, pro2_job_num, pro3_job_num, currspr_job_num,
	              nonrevert_job_num, cli_job_num, network_job_num, network_nonr_job_num)
fail.generate_failure_history()
##
print "Generating Email"
gen = GenerateResults(iso_version, tarball_version, pro1_job_num, pro2_job_num, pro3_job_num, currspr_job_num,
	              nonrevert_job_num, cli_job_num, network_job_num, network_nonr_job_num)
gen.generate_email()



