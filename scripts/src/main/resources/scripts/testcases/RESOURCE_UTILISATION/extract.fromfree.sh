#!/bin/bash

# extract info from output of free
#
#
# # Usage:
# ./extract.fromfree.sh 
#
# # Output
# output written to comma separated files
#


grep '+ ' log_free_MS > MS.extracted.free.txt
# cut out free and used from bufers/cache
cut -c32-41 MS.extracted.free.txt > MS.free.buffers.cache.csv
cut -c22-31 MS.extracted.free.txt > MS.used.buffers.cache.csv

grep '+ ' log_free_SC1 > SC1.extracted.free.txt
# cut out free and used from bufers/cache
cut -c32-41 SC1.extracted.free.txt > SC1.free.buffers.cache.csv
cut -c22-31 SC1.extracted.free.txt > SC1.used.buffers.cache.csv

grep '+ ' log_free_SC2 > SC2.extracted.free.txt
# cut out free and used from bufers/cache
cut -c32-41 SC2.extracted.free.txt > SC2.free.buffers.cache.csv
cut -c22-31 SC2.extracted.free.txt > SC2.used.buffers.cache.csv

grep 'Swap' log_free_MS > MS.extracted.swap.txt
# cut out swap used 
cut -c22-31 MS.extracted.swap.txt > MS.swap.used.csv

grep 'Swap' log_free_SC1 > SC1.extracted.swap.txt
# cut out swap used 
cut -c22-31 SC1.extracted.swap.txt > SC1.swap.used.csv

grep 'Swap' log_free_SC2 > SC2.extracted.swap.txt
# cut out swap used 
cut -c22-31 SC2.extracted.swap.txt > SC2.swap.used.csv






