#!/usr/bin/expect -f

###Takes command line arguments:
#1 user to scp as
#2 password for scp connection
#3 ip to go to
#4 path to get on file
#5 local path to copy to

set user [lindex $argv 0];
set pw [lindex $argv 1];
set ip [lindex $argv 2];
set path [lindex $argv 3];
set local_p [lindex $argv 4];


set scp_line "$user@$ip:$path"

# connect via scp
spawn scp $local_p "$scp_line" 
#######################
expect {
  -re ".*es.*o.*" {
    exp_send "yes\r"
    exp_continue
  }
  -re ".*sword.*" {
    exp_send "$pw\r"
  }
}
interact
