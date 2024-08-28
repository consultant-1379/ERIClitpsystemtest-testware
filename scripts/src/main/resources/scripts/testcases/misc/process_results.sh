#/bin/sh
PATH=$PATH:$HOME/bin:/home/vinnie.mcguinness/java/jre1.7.0_40/bin:/usr/local/apache-maven-3.1.1/bin
export PATH
rm -rf /home/vinnie.mcguinness/.ssh/known_hosts

echo "Generating URLS"
python generate_items.py
###Get /var/log/messages from .100 and its nodes
echo "Copying comments history"
#expect -f get_files.sh root passw0rd 10.44.86.30 /home/admin/isolist/tmp/vinnie/fail_history.txt .
expect -f get_files.sh root passw0rd 10.44.86.30 /home/admin/jan/tmp/fail_history.txt . 
echo "Loading data"
python load_data.cgi
echo "Putting file back on .30ls"
#expect -f put_files.sh root passw0rd 10.44.86.30 /home/admin/isolist/tmp/vinnie/ results_history.html
expect -f put_files.sh root passw0rd 10.44.86.30 /home/admin/jan/tmp/ results_history.html



