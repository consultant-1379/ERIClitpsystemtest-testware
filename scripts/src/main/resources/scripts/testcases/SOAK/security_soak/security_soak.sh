set -x
now=$(date +"%m_%d_%Y_%H:%M")

dir=$"/home/vinnie.mcguinness/ERIClitpsystemtest-testware/src/main/resources/scripts/testcases/FUNCTIONAL/security/"

file1=$"testset_search_cleartxt_password.py"
file2=$"testset_search_for_string.py"

testcase07=$"test_07_search_large_dirs_4_cleartxt_password_not_in_testrun"
testcase05=$"test_05_p_search_dict_passwords_not_in_testrun"

/usr/bin/nosetests -s $dir$file1 --testmatch=$testcase07 >> /tmp/SoakRun_$now.$testcase07.log &
/usr/bin/nosetests -s $dir$file2 --testmatch=$testcase05 >> /tmp/SoakRun_$now.$testcase05.log &
/usr/bin/tail -f /tmp/SoakRun_$now.$testcase05.log
