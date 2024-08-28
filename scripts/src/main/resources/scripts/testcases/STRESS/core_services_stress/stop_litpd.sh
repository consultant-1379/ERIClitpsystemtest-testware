#!/bin/bash
set -x
for (( c=1; c<= 10000; c++ ))
do
	service litpd stop >> /tmp/litp_info.txt
done
